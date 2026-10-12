"""OpenAPI Pydantic schemas with examples for API v1."""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


# ==============================================================================
# Cluster & Station Schemas
# ==============================================================================

class StationSchema(BaseModel):
    id: str = Field(..., examples=["S1"], description="Unique station identifier")
    name: str = Field(..., examples=["Market Road"], description="Human-readable station name")
    chargers: int = Field(..., examples=[8], description="Number of active charging plugs")
    kw: float = Field(..., examples=[7.4], description="Power capacity per charger in kW")
    detour: float = Field(..., examples=[0.0], description="Average detour time in minutes from main corridor")
    latitude: Optional[float] = Field(None, examples=[12.9716], description="WGS84 latitude")
    longitude: Optional[float] = Field(None, examples=[77.5946], description="WGS84 longitude")


class ClusterResponse(BaseModel):
    transformer_kva: float = Field(..., examples=[100.0], description="Nameplate transformer capacity in kVA")
    power_factor: float = Field(..., examples=[0.95], description="Power factor (PF)")
    stations: List[StationSchema] = Field(..., description="List of charging stations connected to the cluster")


# ==============================================================================
# Forecast Schemas
# ==============================================================================

class ForecastResponse(BaseModel):
    hours: List[int] = Field(..., examples=[[14, 15, 16, 17, 18]], description="Forecast hours of day (0-23)")
    p10: List[float] = Field(..., examples=[[24.5, 32.1, 45.0]], description="10th percentile load as % of transformer rating")
    p50: List[float] = Field(..., examples=[[38.2, 48.7, 65.4]], description="50th percentile (median) load as % of transformer rating")
    p90: List[float] = Field(..., examples=[[52.1, 68.3, 86.5]], description="90th percentile load as % of transformer rating")
    warn: int = Field(80, examples=[80], description="Warning threshold percentage")
    critical: int = Field(90, examples=[90], description="Critical overload threshold percentage")
    model_version: str = Field(..., examples=["lightgbm_quantile_conformal_v1"], description="Forecasting model version")


# ==============================================================================
# Transformer Risk Schemas
# ==============================================================================

class TransformerRiskResponse(BaseModel):
    transformer_id: str = Field(..., examples=["T1"], description="Transformer identifier")
    kva: float = Field(..., examples=[100.0], description="Rated capacity in kVA")
    peak_p90_pct: float = Field(..., examples=[86.5], description="Highest P90 load expected over next 24 hours")
    peak_hour: int = Field(..., examples=[18], description="Hour of the forecast peak (0-23)")
    first_warning_hour: Optional[int] = Field(None, examples=[17], description="First hour where P90 forecast exceeds 80% limit")
    level: str = Field(..., examples=["warning"], description="Current risk tier: 'ok', 'warning', or 'critical'")
    warn_threshold_pct: float = Field(80.0, examples=[80.0])
    crit_threshold_pct: float = Field(90.0, examples=[90.0])


# ==============================================================================
# Recommendation Schemas
# ==============================================================================

class RecommendRequest(BaseModel):
    mode: str = Field(
        "balanced",
        examples=["balanced"],
        description="Dispatch strategy priority: 'fastest', 'balanced', or 'grid_friendly'",
    )
    start_hour: int = Field(14, ge=0, le=23, examples=[14], description="Search starting hour of day")
    horizon: int = Field(12, ge=1, le=24, examples=[12], description="Lookahead horizon in hours")


class CandidateSlot(BaseModel):
    station: str = Field(..., examples=["Market Road"])
    station_id: str = Field(..., examples=["S1"])
    hour: int = Field(..., examples=[15])
    starts_in_h: int = Field(..., examples=[1])
    wait_min: float = Field(..., examples=[4.2])
    detour_min: float = Field(..., examples=[0.0])
    grid_load_pct: float = Field(..., examples=[68.5])
    score: float = Field(..., examples=[0.245])


class RecommendResponse(BaseModel):
    mode: str = Field(..., examples=["balanced"])
    top3: List[CandidateSlot] = Field(..., description="Top 3 recommended station and slot combinations")


# ==============================================================================
# Simulation & Replay Schemas
# ==============================================================================

class ReplayStartRequest(BaseModel):
    speed_multiplier: float = Field(60.0, ge=1.0, le=3600.0, examples=[60.0], description="Playback speed acceleration multiplier")
    horizon_hours: int = Field(24, ge=1, le=168, examples=[24], description="Replay duration in hours")


class ReplayStartResponse(BaseModel):
    session_id: str = Field(..., examples=["replay-1728643200"])
    speed_multiplier: float = Field(..., examples=[60.0])
    horizon_hours: int = Field(..., examples=[24])
    started_at: str = Field(..., examples=["2026-10-11T05:00:00Z"])
    status: str = Field(..., examples=["running"])
    total_ticks: int = Field(..., examples=[1440])
    current_tick: int = Field(..., examples=[0])


# ==============================================================================
# Authentication Schemas
# ==============================================================================

class LoginRequest(BaseModel):
    username: str = Field(..., examples=["operator_c1"], description="User account username")
    password: str = Field(..., examples=["OperatorC1_2026!"], description="Plaintext account password")


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., examples=["eyJhbGciOiJIUzI1Ni..."], description="Valid refresh token")


class UserProfileResponse(BaseModel):
    username: str = Field(..., examples=["operator_c1"])
    role: str = Field(..., examples=["operator"], description="Role: driver, operator, admin, judge")
    cluster_id: Optional[str] = Field(None, examples=["C1"], description="Cluster identifier assigned to operator")
    email: Optional[str] = Field(None, examples=["operator_c1@cluster.ev"])


class TokenResponse(BaseModel):
    access_token: str = Field(..., examples=["eyJhbGciOiJIUzI1Ni..."])
    refresh_token: str = Field(..., examples=["eyJhbGciOiJIUzI1Ni..."])
    token_type: str = Field("bearer", examples=["bearer"])
    expires_in: int = Field(900, examples=[900], description="Access token expiration in seconds")
    user: UserProfileResponse


# ==============================================================================
# Form Schemas — same constraints as the Zod schemas in frontend/src/features/forms/schemas.ts
# MUST be kept in sync: any range change here must also update the Zod schema and vice-versa.
# ==============================================================================

CONNECTOR_TYPES = ("Type 2", "CCS", "CHAdeMO", "GB/T")
PRIORITY_MODES = ("fastest", "balanced", "grid_friendly")


class DriverRequestSchema(BaseModel):
    """
    Validated driver charging request.
    Field limits mirror frontend/src/features/forms/schemas.ts :: driverRequestSchema.
    """
    battery_pct: float = Field(
        ...,
        ge=5,
        le=95,
        examples=[20],
        description="Current battery level in percent (5–95)",
    )
    target_pct: float = Field(
        ...,
        ge=20,
        le=100,
        examples=[80],
        description="Target battery level in percent (20–100, must exceed battery_pct)",
    )
    connector_type: str = Field(
        ...,
        examples=["Type 2"],
        description=f"Connector type: {', '.join(CONNECTOR_TYPES)}",
    )
    departure_window_h: float = Field(
        ...,
        ge=0.5,
        le=12,
        examples=[2.0],
        description="Hours until departure (0.5–12)",
    )
    priority_mode: str = Field(
        "balanced",
        examples=["balanced"],
        description=f"Dispatch strategy: {', '.join(PRIORITY_MODES)}",
    )

    def model_post_init(self, __context) -> None:
        if self.target_pct <= self.battery_pct:
            raise ValueError(
                f"target_pct ({self.target_pct}) must be greater than battery_pct ({self.battery_pct})"
            )
        if self.connector_type not in CONNECTOR_TYPES:
            raise ValueError(f"connector_type must be one of {CONNECTOR_TYPES}")
        if self.priority_mode not in PRIORITY_MODES:
            raise ValueError(f"priority_mode must be one of {PRIORITY_MODES}")


class OperatorSettingsSchema(BaseModel):
    """
    Validated operator cluster settings.
    Field limits mirror frontend/src/features/forms/schemas.ts :: operatorSettingsSchema.
    """
    transformer_kva: float = Field(
        ...,
        ge=10,
        le=2000,
        examples=[100],
        description="Transformer nameplate rating in kVA (10–2000)",
    )
    warn_threshold_pct: float = Field(
        ...,
        ge=50,
        le=98,
        examples=[80],
        description="Amber warning threshold as percent of transformer rating (50–98)",
    )
    crit_threshold_pct: float = Field(
        ...,
        ge=51,
        le=99,
        examples=[90],
        description="Red critical threshold as percent of transformer rating (51–99, must exceed warn_threshold_pct)",
    )
    weight_queue: float = Field(
        ...,
        ge=0,
        le=1,
        examples=[0.5],
        description="Queue pressure weight for recommendation scoring (0–1)",
    )
    weight_distance: float = Field(
        ...,
        ge=0,
        le=1,
        examples=[0.3],
        description="Distance weight for recommendation scoring (0–1)",
    )
    weight_grid: float = Field(
        ...,
        ge=0,
        le=1,
        examples=[0.2],
        description="Grid load weight for recommendation scoring (0–1)",
    )

    def model_post_init(self, __context) -> None:
        if self.crit_threshold_pct <= self.warn_threshold_pct:
            raise ValueError(
                f"crit_threshold_pct ({self.crit_threshold_pct}) must exceed warn_threshold_pct ({self.warn_threshold_pct})"
            )
        weight_sum = self.weight_queue + self.weight_distance + self.weight_grid
        if not (0.99 <= weight_sum <= 1.01):
            raise ValueError(
                f"Recommendation weights must sum to 1.0 (got {weight_sum:.3f}). "
                "Adjust weight_queue, weight_distance, weight_grid."
            )

