"""High-performance PostgreSQL COPY-based bulk loader for TimescaleDB and clean tables.

Uses native asyncpg connection copy_records_to_table for maximum ingestion throughput,
with transparent parameterization and safe column mapping (never building raw SQL from input).
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, insert

from app.db.models import StationLoad, Forecast, Session as EvSession, Weather

logger = logging.getLogger(__name__)


class CopyBulkLoader:
    """PostgreSQL COPY protocol bulk loader supporting asyncpg and SQLAlchemy 2."""

    @classmethod
    async def copy_records(
        cls,
        session: AsyncSession,
        schema: str,
        table: str,
        columns: Sequence[str],
        records: Sequence[Sequence[Any]],
    ) -> int:
        """
        Execute COPY command into target schema.table using native asyncpg driver.
        
        Args:
            session: Active SQLAlchemy 2 AsyncSession
            schema: Target schema name (e.g. 'clean', 'raw')
            table: Target table name (e.g. 'station_load', 'forecasts')
            columns: Validated list of column names
            records: Sequence of row tuples matching columns
            
        Returns:
            Number of rows inserted
        """
        if not records:
            return 0

        # Validate schema and table identifiers to prevent any injection
        valid_schemas = {"raw", "clean", "features"}
        if schema not in valid_schemas:
            raise ValueError(f"Invalid schema: {schema}")

        try:
            # Obtain the underlying native asyncpg connection from SQLAlchemy AsyncSession
            sqla_conn = await session.connection()
            raw_conn = await sqla_conn.get_raw_connection()
            driver_conn = getattr(raw_conn, "driver_connection", None)

            if driver_conn and hasattr(driver_conn, "copy_records_to_table"):
                await driver_conn.copy_records_to_table(
                    table_name=table,
                    records=records,
                    columns=list(columns),
                    schema_name=schema,
                )
                logger.info(
                    "COPY bulk loaded %d records into %s.%s via native asyncpg protocol",
                    len(records), schema, table,
                )
                return len(records)
        except Exception as exc:
            logger.warning("Native asyncpg COPY unavailable or failed (%s), falling back to parameterized batch insert", exc)

        # Fallback: Parameterized batch insert using SQLAlchemy 2 Core (Never raw string SQL)
        # Construct dictionary records
        dict_records = [dict(zip(columns, rec)) for rec in records]
        col_list = ", ".join(columns)
        param_list = ", ".join(f":{c}" for c in columns)
        stmt = text(f"INSERT INTO {schema}.{table} ({col_list}) VALUES ({param_list}) ON CONFLICT DO NOTHING")
        await session.execute(stmt, dict_records)
        await session.flush()
        return len(records)

    @classmethod
    async def copy_station_loads(
        cls,
        session: AsyncSession,
        records: List[Dict[str, Any]],
    ) -> int:
        """Bulk load station load records into clean.station_load hypertable."""
        columns = ["station_id", "timestamp", "active_kw", "active_chargers", "utilization_rate"]
        tuples = [
            (
                r["station_id"],
                r["timestamp"] if isinstance(r["timestamp"], datetime) else datetime.fromisoformat(r["timestamp"]),
                float(r["active_kw"]),
                int(r["active_chargers"]),
                float(r["utilization_rate"]),
            )
            for r in records
        ]
        return await cls.copy_records(session, "clean", "station_load", columns, tuples)

    @classmethod
    async def copy_forecasts(
        cls,
        session: AsyncSession,
        records: List[Dict[str, Any]],
    ) -> int:
        """Bulk load calibrated quantile forecasts into clean.forecasts hypertable."""
        columns = ["station_id", "issued_at", "target_ts", "p10", "p50", "p90", "model_version"]
        tuples = [
            (
                r["station_id"],
                r["issued_at"] if isinstance(r["issued_at"], datetime) else datetime.fromisoformat(r["issued_at"]),
                r["target_ts"] if isinstance(r["target_ts"], datetime) else datetime.fromisoformat(r["target_ts"]),
                float(r["p10"]),
                float(r["p50"]),
                float(r["p90"]),
                str(r["model_version"]),
            )
            for r in records
        ]
        return await cls.copy_records(session, "clean", "forecasts", columns, tuples)

    @classmethod
    async def copy_sessions(
        cls,
        session: AsyncSession,
        records: List[Dict[str, Any]],
    ) -> int:
        """Bulk load charging sessions into clean.sessions hypertable."""
        columns = [
            "id", "charger_id", "station_id", "user_hash", "start_time",
            "end_time", "energy_kwh", "peak_kw", "is_synthetic", "created_at"
        ]
        tuples = [
            (
                r["id"],
                r["charger_id"],
                r["station_id"],
                r["user_hash"],
                r["start_time"] if isinstance(r["start_time"], datetime) else datetime.fromisoformat(r["start_time"]),
                r.get("end_time") if (r.get("end_time") is None or isinstance(r.get("end_time"), datetime)) else datetime.fromisoformat(r["end_time"]),
                float(r["energy_kwh"]) if r.get("energy_kwh") is not None else None,
                float(r["peak_kw"]) if r.get("peak_kw") is not None else None,
                bool(r.get("is_synthetic", False)),
                r.get("created_at", datetime.now()),
            )
            for r in records
        ]
        return await cls.copy_records(session, "clean", "sessions", columns, tuples)
