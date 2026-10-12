"""PatchTST (Patch Time Series Transformer) implementation for multi-quantile forecasting."""
import math
from typing import Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F


class PatchTST(nn.Module):
    """
    Patch Time Series Transformer (PatchTST) in PyTorch (CPU-friendly configuration).
    1. Unfolds lookback time series into sub-sequence patches (patch_len, stride).
    2. Projects patches into transformer embedding space with learnable positional encoding.
    3. Multi-head self-attention models cross-patch temporal dependencies efficiently.
    4. Projects representations to P10, P50, and P90 quantile forecasts for a 24-hour horizon.
    """

    def __init__(
        self,
        in_features: int,
        seq_len: int = 48,
        horizon: int = 24,
        patch_len: int = 4,
        stride: int = 2,
        d_model: int = 32,
        n_heads: int = 4,
        n_layers: int = 2,
        d_ff: int = 64,
        num_quantiles: int = 3,
        dropout: float = 0.10,
    ):
        super().__init__()
        self.in_features = in_features
        self.seq_len = seq_len
        self.horizon = horizon
        self.patch_len = patch_len
        self.stride = stride
        self.num_quantiles = num_quantiles

        # Calculate number of patches
        if seq_len < patch_len:
            raise ValueError(f"seq_len ({seq_len}) must be >= patch_len ({patch_len})")
        self.num_patches = (seq_len - patch_len) // stride + 1

        # Linear projection of flattened patch (patch_len * in_features) to d_model
        patch_dim = patch_len * in_features
        self.patch_embedding = nn.Linear(patch_dim, d_model)

        # Learnable positional embeddings
        self.pos_embedding = nn.Parameter(torch.randn(1, self.num_patches, d_model) * 0.02)
        self.dropout = nn.Dropout(dropout)

        # Transformer Encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=n_heads,
            dim_feedforward=d_ff,
            dropout=dropout,
            activation="gelu",
            batch_first=True,
            norm_first=True,
        )
        self.transformer_encoder = nn.TransformerEncoder(
            encoder_layer,
            num_layers=n_layers,
        )
        self.norm = nn.LayerNorm(d_model)

        # Forecast Flatten & Output Head
        flat_dim = self.num_patches * d_model
        self.head = nn.Sequential(
            nn.Linear(flat_dim, d_model * 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_model * 2, horizon * num_quantiles),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Tensor of shape (batch_size, seq_len, in_features)
        Returns:
            preds: Tensor of shape (batch_size, horizon, num_quantiles)
        """
        batch_size, seq_len, in_features = x.shape

        # Patching: unfold along temporal dimension (dim=1)
        # x.unfold(1, patch_len, stride) gives (batch_size, num_patches, in_features, patch_len)
        patches = x.unfold(dimension=1, size=self.patch_len, step=self.stride)
        # Transpose and flatten: (batch_size, num_patches, patch_len, in_features) -> (batch_size, num_patches, patch_dim)
        patches = patches.transpose(2, 3).contiguous().view(batch_size, self.num_patches, -1)

        # Patch embedding + Positional encoding
        emb = self.patch_embedding(patches) + self.pos_embedding
        emb = self.dropout(emb)

        # Transformer Encoder
        enc_out = self.transformer_encoder(emb)
        enc_out = self.norm(enc_out)

        # Flatten all patch tokens and project
        flat = enc_out.view(batch_size, -1)
        out = self.head(flat)

        preds = out.view(batch_size, self.horizon, self.num_quantiles)
        return preds

    def get_num_params(self) -> int:
        """Count trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
