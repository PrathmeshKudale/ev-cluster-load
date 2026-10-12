"""
Backend validation tests for DriverRequestSchema and OperatorSettingsSchema.

These enforce the same limits as the Zod schemas in
  frontend/src/features/forms/schemas.ts

Run:  cd backend && python -m pytest tests/test_form_schemas.py -v
"""
import pytest
from pydantic import ValidationError

from app.api.v1.schemas import DriverRequestSchema, OperatorSettingsSchema

# ---------------------------------------------------------------------------
# DriverRequestSchema
# ---------------------------------------------------------------------------

VALID_DRIVER = {
    "battery_pct": 20.0,
    "target_pct": 80.0,
    "connector_type": "Type 2",
    "departure_window_h": 2.0,
    "priority_mode": "balanced",
}


class TestDriverRequestSchema:
    def test_valid_defaults(self):
        obj = DriverRequestSchema(**VALID_DRIVER)
        assert obj.battery_pct == 20.0
        assert obj.target_pct == 80.0

    def test_battery_pct_minimum(self):
        with pytest.raises(ValidationError, match="battery_pct"):
            DriverRequestSchema(**{**VALID_DRIVER, "battery_pct": 4.9})

    def test_battery_pct_maximum(self):
        with pytest.raises(ValidationError, match="battery_pct"):
            DriverRequestSchema(**{**VALID_DRIVER, "battery_pct": 95.1})

    def test_target_pct_minimum(self):
        with pytest.raises(ValidationError, match="target_pct"):
            DriverRequestSchema(**{**VALID_DRIVER, "target_pct": 19.9})

    def test_target_pct_maximum(self):
        with pytest.raises(ValidationError, match="target_pct"):
            DriverRequestSchema(**{**VALID_DRIVER, "target_pct": 100.1})

    def test_target_must_exceed_battery(self):
        """Cross-field: target_pct <= battery_pct must fail."""
        with pytest.raises(ValidationError, match="must be greater than battery_pct"):
            DriverRequestSchema(**{**VALID_DRIVER, "battery_pct": 70, "target_pct": 70})

    def test_target_below_battery_fails(self):
        with pytest.raises(ValidationError, match="must be greater than battery_pct"):
            DriverRequestSchema(**{**VALID_DRIVER, "battery_pct": 80, "target_pct": 60})

    def test_invalid_connector_type(self):
        with pytest.raises(ValidationError, match="connector_type"):
            DriverRequestSchema(**{**VALID_DRIVER, "connector_type": "NACS"})

    @pytest.mark.parametrize("ct", ["Type 2", "CCS", "CHAdeMO", "GB/T"])
    def test_all_valid_connector_types(self, ct: str):
        obj = DriverRequestSchema(**{**VALID_DRIVER, "connector_type": ct})
        assert obj.connector_type == ct

    def test_departure_window_minimum(self):
        with pytest.raises(ValidationError, match="departure_window_h"):
            DriverRequestSchema(**{**VALID_DRIVER, "departure_window_h": 0.4})

    def test_departure_window_maximum(self):
        with pytest.raises(ValidationError, match="departure_window_h"):
            DriverRequestSchema(**{**VALID_DRIVER, "departure_window_h": 12.1})

    def test_invalid_priority_mode(self):
        with pytest.raises(ValidationError, match="priority_mode"):
            DriverRequestSchema(**{**VALID_DRIVER, "priority_mode": "turbo"})

    @pytest.mark.parametrize("mode", ["fastest", "balanced", "grid_friendly"])
    def test_all_valid_priority_modes(self, mode: str):
        obj = DriverRequestSchema(**{**VALID_DRIVER, "priority_mode": mode})
        assert obj.priority_mode == mode

    def test_edge_values_accepted(self):
        obj = DriverRequestSchema(
            battery_pct=5,
            target_pct=100,
            connector_type="CCS",
            departure_window_h=0.5,
            priority_mode="fastest",
        )
        assert obj.battery_pct == 5
        assert obj.departure_window_h == 0.5


# ---------------------------------------------------------------------------
# OperatorSettingsSchema
# ---------------------------------------------------------------------------

VALID_OPERATOR = {
    "transformer_kva": 100.0,
    "warn_threshold_pct": 80.0,
    "crit_threshold_pct": 90.0,
    "weight_queue": 0.5,
    "weight_distance": 0.3,
    "weight_grid": 0.2,
}


class TestOperatorSettingsSchema:
    def test_valid_defaults(self):
        obj = OperatorSettingsSchema(**VALID_OPERATOR)
        assert obj.transformer_kva == 100.0

    def test_transformer_kva_minimum(self):
        with pytest.raises(ValidationError, match="transformer_kva"):
            OperatorSettingsSchema(**{**VALID_OPERATOR, "transformer_kva": 9.9})

    def test_transformer_kva_maximum(self):
        with pytest.raises(ValidationError, match="transformer_kva"):
            OperatorSettingsSchema(**{**VALID_OPERATOR, "transformer_kva": 2001})

    def test_warn_threshold_minimum(self):
        with pytest.raises(ValidationError, match="warn_threshold_pct"):
            OperatorSettingsSchema(**{**VALID_OPERATOR, "warn_threshold_pct": 49.9})

    def test_warn_threshold_maximum(self):
        with pytest.raises(ValidationError, match="warn_threshold_pct"):
            OperatorSettingsSchema(**{**VALID_OPERATOR, "warn_threshold_pct": 98.1})

    def test_crit_threshold_minimum(self):
        with pytest.raises(ValidationError, match="crit_threshold_pct"):
            OperatorSettingsSchema(**{**VALID_OPERATOR, "crit_threshold_pct": 50.9})

    def test_crit_must_exceed_warn(self):
        """Cross-field: crit_threshold_pct <= warn_threshold_pct must fail."""
        with pytest.raises(ValidationError, match="must exceed warn_threshold_pct"):
            OperatorSettingsSchema(**{**VALID_OPERATOR, "warn_threshold_pct": 85, "crit_threshold_pct": 85})

    def test_crit_below_warn_fails(self):
        with pytest.raises(ValidationError, match="must exceed warn_threshold_pct"):
            OperatorSettingsSchema(**{**VALID_OPERATOR, "warn_threshold_pct": 90, "crit_threshold_pct": 80})

    def test_weights_must_sum_to_one(self):
        with pytest.raises(ValidationError, match="sum to 1.0"):
            OperatorSettingsSchema(**{
                **VALID_OPERATOR,
                "weight_queue": 0.6,
                "weight_distance": 0.3,
                "weight_grid": 0.3,  # sum = 1.2
            })

    def test_weights_zero_sum_rejected(self):
        with pytest.raises(ValidationError, match="sum to 1.0"):
            OperatorSettingsSchema(**{
                **VALID_OPERATOR,
                "weight_queue": 0.0,
                "weight_distance": 0.0,
                "weight_grid": 0.0,
            })

    def test_weight_above_1_rejected(self):
        with pytest.raises(ValidationError, match="weight_queue"):
            OperatorSettingsSchema(**{**VALID_OPERATOR, "weight_queue": 1.5})

    def test_weight_negative_rejected(self):
        with pytest.raises(ValidationError, match="weight_distance"):
            OperatorSettingsSchema(**{**VALID_OPERATOR, "weight_distance": -0.1})

    def test_float_tolerance_accepted(self):
        """Weights that sum to 1.001 (float rounding) should be accepted."""
        obj = OperatorSettingsSchema(**{
            **VALID_OPERATOR,
            "weight_queue": 0.334,
            "weight_distance": 0.333,
            "weight_grid": 0.333,  # sum = 1.000
        })
        assert obj.weight_queue == pytest.approx(0.334)

    def test_edge_kva_values(self):
        obj = OperatorSettingsSchema(**{**VALID_OPERATOR, "transformer_kva": 10})
        assert obj.transformer_kva == 10
        obj2 = OperatorSettingsSchema(**{**VALID_OPERATOR, "transformer_kva": 2000})
        assert obj2.transformer_kva == 2000
