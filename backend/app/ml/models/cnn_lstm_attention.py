"""CNN-LSTM-Attention neural network for multi-quantile time series forecasting."""
from typing import Dict, Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F


class TemporalAttention(nn.Module):
    """
    Additive (Bahdanau-style) temporal attention layer over recurrent hidden states.
    Weights each time step dynamically to produce a summary context vector.
    """

    def __init__(self, hidden_dim: int, attention_dim: Optional[int] = None):
        super().__init__()
        attn_dim = attention_dim or max(16, hidden_dim // 2)
        self.w_proj = nn.Linear(hidden_dim, attn_dim)
        self.v_proj = nn.Linear(attn_dim, 1, bias=False)

    def forward(self, rnn_outputs: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            rnn_outputs: Tensor of shape (batch_size, seq_len, hidden_dim)
        Returns:
            context: Tensor of shape (batch_size, hidden_dim)
            weights: Attention weights of shape (batch_size, seq_len)
        """
        # (batch_size, seq_len, attn_dim)
        energy = torch.tanh(self.w_proj(rnn_outputs))
        # (batch_size, seq_len, 1) -> (batch_size, seq_len)
        scores = self.v_proj(energy).squeeze(-1)
        weights = F.softmax(scores, dim=-1)
        # Context vector as weighted sum: (batch_size, hidden_dim)
        context = torch.bmm(weights.unsqueeze(1), rnn_outputs).squeeze(1)
        return context, weights


class CNNLSTMAttention(nn.Module):
    """
    CNN-LSTM-Attention forecaster for probabilistic quantile prediction:
    1. 1D Temporal Convolution captures multi-hour local load features and rate of change.
    2. Recurrent LSTM layers model long-range diurnal seasonality and weekday transitions.
    3. Temporal Attention focuses on peak demand hours and historical lag points.
    4. Dense output head produces calibrated P10, P50, and P90 quantile forecasts for 24h horizon.
    """

    def __init__(
        self,
        in_features: int,
        horizon: int = 24,
        cnn_channels: int = 32,
        kernel_size: int = 3,
        lstm_hidden: int = 32,
        lstm_layers: int = 2,
        num_quantiles: int = 3,
        dropout: float = 0.15,
    ):
        super().__init__()
        self.in_features = in_features
        self.horizon = horizon
        self.num_quantiles = num_quantiles

        # 1. 1D Temporal Convolutional Block
        self.conv1d = nn.Conv1d(
            in_channels=in_features,
            out_channels=cnn_channels,
            kernel_size=kernel_size,
            padding=kernel_size // 2,
        )
        self.conv_norm = nn.BatchNorm1d(cnn_channels)
        self.conv_dropout = nn.Dropout(dropout)

        # 2. LSTM Block
        self.lstm = nn.LSTM(
            input_size=cnn_channels,
            hidden_size=lstm_hidden,
            num_layers=lstm_layers,
            batch_first=True,
            dropout=dropout if lstm_layers > 1 else 0.0,
        )

        # 3. Temporal Attention
        self.attention = TemporalAttention(hidden_dim=lstm_hidden)

        # 4. Multi-Quantile Prediction Head
        # Inputs: attention context (lstm_hidden) + last recurrent state (lstm_hidden)
        head_in = lstm_hidden * 2
        self.head = nn.Sequential(
            nn.Linear(head_in, head_in),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(head_in, horizon * num_quantiles),
        )

    def forward(
        self,
        x: torch.Tensor,
        return_attention: bool = False,
    ) -> torch.Tensor:
        """
        Args:
            x: Tensor of shape (batch_size, seq_len, in_features)
            return_attention: If True, returns (preds, attention_weights)
        Returns:
            preds: Tensor of shape (batch_size, horizon, num_quantiles)
        """
        # Conv1d expects (batch_size, in_channels, seq_len)
        x_conv_in = x.transpose(1, 2)
        conv_out = F.relu(self.conv_norm(self.conv1d(x_conv_in)))
        conv_out = self.conv_dropout(conv_out)
        # Back to (batch_size, seq_len, cnn_channels)
        lstm_in = conv_out.transpose(1, 2)

        # LSTM forward
        lstm_out, (h_n, _) = self.lstm(lstm_in)
        last_hidden = h_n[-1]  # (batch_size, lstm_hidden)

        # Temporal attention
        context, attn_weights = self.attention(lstm_out)

        # Combine context and last hidden state
        combined = torch.cat([context, last_hidden], dim=-1)

        # Output projection
        out = self.head(combined)
        # Reshape to (batch_size, horizon, num_quantiles)
        preds = out.view(-1, self.horizon, self.num_quantiles)

        if return_attention:
            return preds, attn_weights
        return preds

    def get_num_params(self) -> int:
        """Count trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
