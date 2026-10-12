"""Common utilities, multi-quantile loss functions, and evaluation metrics for deep forecasting models."""
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn

from app.graph.routing import build_station_edges


class MultiQuantileLoss(nn.Module):
    """
    Multi-quantile pinball loss for probabilistic time series forecasting.
    Computes weighted sum of asymmetric pinball losses for target quantiles (e.g. 0.10, 0.50, 0.90)
    with a soft penalty for quantile crossing (enforcing monotonicity: P10 <= P50 <= P90).
    """

    def __init__(
        self,
        quantiles: Tuple[float, ...] = (0.10, 0.50, 0.90),
        crossing_penalty_weight: float = 0.5,
    ):
        super().__init__()
        self.quantiles = quantiles
        self.crossing_penalty_weight = crossing_penalty_weight

    def forward(self, y_pred: torch.Tensor, y_true: torch.Tensor) -> torch.Tensor:
        """
        Args:
            y_pred: Tensor of shape (..., num_quantiles)
            y_true: Tensor of shape (..., ) or (..., 1)
        Returns:
            Scalar loss tensor.
        """
        if y_true.dim() == y_pred.dim() - 1:
            y_true = y_true.unsqueeze(-1)
        elif y_true.dim() == y_pred.dim() and y_true.shape[-1] == 1:
            pass  # already broadcastable

        total_loss = torch.tensor(0.0, device=y_pred.device, dtype=y_pred.dtype)

        for i, q in enumerate(self.quantiles):
            pred_q = y_pred[..., i : i + 1]
            diff = y_true - pred_q
            pinball = torch.maximum(q * diff, (q - 1.0) * diff)
            total_loss = total_loss + torch.mean(pinball)

        # Quantile crossing penalties (P10 <= P50 <= P90)
        if len(self.quantiles) >= 3 and self.crossing_penalty_weight > 0.0:
            p10 = y_pred[..., 0]
            p50 = y_pred[..., 1]
            p90 = y_pred[..., 2]
            # Cross penalty: ReLU(p10 - p50) + ReLU(p50 - p90)
            cross_loss = torch.mean(torch.relu(p10 - p50)) + torch.mean(torch.relu(p50 - p90))
            total_loss = total_loss + self.crossing_penalty_weight * cross_loss

        return total_loss


def pinball_loss(y_true: np.ndarray, y_pred: np.ndarray, alpha: float) -> float:
    """Compute empirical Pinball loss for quantile alpha."""
    diff = y_true - y_pred
    return float(np.mean(np.maximum(alpha * diff, (alpha - 1.0) * diff)))


def winkler_score(y_true: np.ndarray, lower: np.ndarray, upper: np.ndarray, alpha: float = 0.20) -> float:
    """
    Compute Winkler score for a (1 - alpha) prediction interval (lower is better).
    Penalizes both interval width and observations outside the bounds.
    """
    width = upper - lower
    under = (lower - y_true) * (2.0 / alpha)
    over = (y_true - upper) * (2.0 / alpha)
    penalty = np.where(y_true < lower, under, np.where(y_true > upper, over, 0.0))
    return float(np.mean(width + penalty))


def calculate_coverage(y_true: np.ndarray, lower: np.ndarray, upper: np.ndarray) -> float:
    """Empirical percentage of observations covered between lower and upper bounds."""
    covered = (y_true >= lower) & (y_true <= upper)
    return float(np.mean(covered) * 100.0)


def enforce_quantile_monotonicity(preds: np.ndarray) -> np.ndarray:
    """
    Enforces non-negativity and monotonicity (P10 <= P50 <= P90) on prediction arrays.
    Args:
        preds: np.ndarray of shape (..., 3) where [..., 0]=P10, [..., 1]=P50, [..., 2]=P90
    Returns:
        Monotonically sorted array of shape (..., 3)
    """
    p10 = np.maximum(preds[..., 0], 0.0)
    p50 = np.maximum(preds[..., 1], p10)
    p90 = np.maximum(preds[..., 2], p50)
    return np.stack([p10, p50, p90], axis=-1)


def build_station_adjacency_matrix(
    stations: List[Dict],
    add_self_loops: bool = True,
    normalize: bool = True,
) -> Tuple[np.ndarray, List[str]]:
    """
    Construct spatial graph adjacency matrix A from station_edges using distance-decay weights.
    Returns:
        (A, station_ids)
        A: normalized adjacency matrix of shape (num_stations, num_stations)
        station_ids: ordered list of station identifiers (e.g. ['S1', 'S2', 'S3', 'S4'])
    """
    station_ids = [s["id"] for s in stations]
    n = len(station_ids)
    id_to_idx = {sid: i for i, sid in enumerate(station_ids)}

    edges = build_station_edges(stations)
    adj = np.zeros((n, n), dtype=np.float32)

    for edge in edges:
        u = id_to_idx.get(edge["src_station_id"])
        v = id_to_idx.get(edge["dst_station_id"])
        if u is not None and v is not None:
            adj[u, v] = float(edge["weight"])

    if add_self_loops:
        np.fill_diagonal(adj, 1.0)

    if normalize:
        # Symmetric normalized Laplacian / adjacency: D^{-1/2} A D^{-1/2}
        degrees = np.sum(adj, axis=1)
        d_inv_sqrt = np.power(np.maximum(degrees, 1e-6), -0.5)
        d_mat_inv_sqrt = np.diag(d_inv_sqrt)
        adj = d_mat_inv_sqrt @ adj @ d_mat_inv_sqrt

    return adj, station_ids
