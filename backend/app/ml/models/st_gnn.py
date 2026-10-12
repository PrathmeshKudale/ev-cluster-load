"""Spatio-Temporal Graph Neural Network (ST-GNN) for joint multi-station EV charging forecasting."""
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from app.ml.models.common import build_station_adjacency_matrix


class GraphConvLayer(nn.Module):
    """
    Spatial Graph Convolution layer over station adjacency:
    Z = ReLU( A_norm @ X @ W + bias )
    Supports batch dimensions (batch_size, num_nodes, in_features).
    """

    def __init__(self, in_features: int, out_features: int, bias: bool = True):
        super().__init__()
        self.weight = nn.Parameter(torch.FloatTensor(in_features, out_features))
        if bias:
            self.bias = nn.Parameter(torch.FloatTensor(out_features))
        else:
            self.register_parameter("bias", None)
        self.reset_parameters()

    def reset_parameters(self):
        math_sqrt5 = 2.236
        nn.init.kaiming_uniform_(self.weight, a=math_sqrt5)
        if self.bias is not None:
            fan_in = self.weight.size(0)
            bound = 1 / (fan_in**0.5) if fan_in > 0 else 0
            nn.init.uniform_(self.bias, -bound, bound)

    def forward(self, x: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Node features of shape (..., num_nodes, in_features)
            adj: Normalized adjacency matrix of shape (num_nodes, num_nodes) or (..., num_nodes, num_nodes)
        Returns:
            out: Tensor of shape (..., num_nodes, out_features)
        """
        # Linear transform: X @ W -> (..., num_nodes, out_features)
        support = torch.matmul(x, self.weight)
        # Message passing: A @ support -> (..., num_nodes, out_features)
        if adj.dim() == 2:
            out = torch.matmul(adj, support)
        else:
            out = torch.matmul(adj, support)
        if self.bias is not None:
            out = out + self.bias
        return out


class SpatioTemporalGNN(nn.Module):
    """
    Spatio-Temporal Graph Neural Network (ST-GNN):
    1. Spatial graph convolutions propagate load & detour signals across station_edges.
    2. Temporal GRU processes sequential spatial node embeddings across the lookback horizon.
    3. Jointly forecasts all stations with P10, P50, and P90 quantile distributions.
    4. Aggregates multi-station outputs into total cluster transformer load.
    """

    def __init__(
        self,
        num_stations: int = 4,
        in_features: int = 12,
        horizon: int = 24,
        gcn_hidden: int = 32,
        gru_hidden: int = 32,
        gru_layers: int = 1,
        num_quantiles: int = 3,
        dropout: float = 0.15,
        adj_matrix: Optional[torch.Tensor] = None,
        use_graph: bool = True,
    ):
        super().__init__()
        self.num_stations = num_stations
        self.in_features = in_features
        self.horizon = horizon
        self.num_quantiles = num_quantiles
        self.use_graph = use_graph

        # Register normalized adjacency matrix as buffer
        if adj_matrix is not None:
            self.register_buffer("adj", adj_matrix.float())
        else:
            # Default identity if not provided
            self.register_buffer("adj", torch.eye(num_stations, dtype=torch.float32))

        # Spatial Graph Convolution
        self.gcn1 = GraphConvLayer(in_features, gcn_hidden)
        self.gcn_norm1 = nn.LayerNorm(gcn_hidden)
        self.gcn2 = GraphConvLayer(gcn_hidden, gcn_hidden)
        self.gcn_norm2 = nn.LayerNorm(gcn_hidden)
        self.dropout = nn.Dropout(dropout)

        # Temporal GRU: processes (batch_size * num_stations, seq_len, gcn_hidden)
        self.gru = nn.GRU(
            input_size=gcn_hidden,
            hidden_size=gru_hidden,
            num_layers=gru_layers,
            batch_first=True,
            dropout=dropout if gru_layers > 1 else 0.0,
        )

        # Multi-Quantile Station Output Head
        self.station_head = nn.Sequential(
            nn.Linear(gru_hidden, gru_hidden),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(gru_hidden, horizon * num_quantiles),
        )

    def set_graph_mode(self, use_graph: bool):
        """Toggle graph message passing (True) vs identity ablation (False)."""
        self.use_graph = use_graph

    def forward(
        self,
        x: torch.Tensor,
        adj: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            x: Tensor of shape (batch_size, seq_len, num_stations, in_features)
            adj: Optional override adjacency matrix of shape (num_stations, num_stations)
        Returns:
            station_preds: (batch_size, num_stations, horizon, num_quantiles)
            cluster_preds: (batch_size, horizon, num_quantiles) total aggregated cluster load
        """
        batch_size, seq_len, num_stations, in_features = x.shape

        # Determine effective adjacency
        if adj is not None:
            effective_adj = adj
        elif self.use_graph:
            effective_adj = self.adj
        else:
            # Ablation mode: identity matrix (no spatial message passing)
            effective_adj = torch.eye(num_stations, device=x.device, dtype=x.dtype)

        # 1. Spatial Graph Convolution across each time step
        # x is (batch_size, seq_len, num_stations, in_features)
        gcn_out1 = F.relu(self.gcn1(x, effective_adj))
        gcn_out1 = self.gcn_norm1(gcn_out1)
        gcn_out1 = self.dropout(gcn_out1)

        gcn_out2 = F.relu(self.gcn2(gcn_out1, effective_adj))
        gcn_out2 = self.gcn_norm2(gcn_out2)
        spatial_features = self.dropout(gcn_out2)  # (batch_size, seq_len, num_stations, gcn_hidden)

        # 2. Temporal GRU per station
        # Permute to (batch_size, num_stations, seq_len, gcn_hidden) -> reshape to (batch_size * num_stations, seq_len, gcn_hidden)
        node_seqs = spatial_features.permute(0, 2, 1, 3).contiguous()
        node_seqs = node_seqs.view(batch_size * num_stations, seq_len, -1)

        _, h_n = self.gru(node_seqs)  # h_n is (gru_layers, batch_size * num_stations, gru_hidden)
        last_hidden = h_n[-1]  # (batch_size * num_stations, gru_hidden)

        # 3. Predict Quantiles for each Station
        station_out = self.station_head(last_hidden)  # (batch_size * num_stations, horizon * num_quantiles)
        station_preds = station_out.view(batch_size, num_stations, self.horizon, self.num_quantiles)

        # 4. Joint Cluster Aggregation: Sum active station loads across stations
        # (batch_size, horizon, num_quantiles)
        cluster_preds = torch.sum(station_preds, dim=1)

        return station_preds, cluster_preds

    def get_num_params(self) -> int:
        """Count trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
