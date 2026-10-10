# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - feat/d9-migrations
- Explicit Alembic and SQLAlchemy constraint naming conventions (`ix_`, `uq_`, `ck_`, `fk_`, `pk_`).
- Timestamped Alembic revision file naming template.
- Verified reversible migration downgrades (`alembic downgrade base`).
- Strict separation of schema DDL from seed data (`make migrate` vs `make seed`).
- Comprehensive GitHub Actions CI workflow applying migrations to blank DB, running upgrade/downgrade/upgrade cycle, seeding, and applying migrations to seeded DB.
- Comprehensive documentation in `docs/db/migrations.md` detailing the migration lifecycle and the Expand-then-Contract zero-downtime evolution pattern.

### Added - feat/d3-modeling
- Multi-schema PostgreSQL 16 architecture with `raw`, `clean`, and `features` schemas.
- TimescaleDB hypertables for `clean.sessions`, `clean.station_load`, `clean.weather`, and `clean.forecasts`.
- PostGIS geometry support for spatial station coordinates.
- Spatial-Temporal GNN graph edges table (`features.station_edges`) populated via OSRM routing with graceful Haversine fallback.
- Externalized configuration tables for transformer parameters (`clean.config_transformer`), IEEE/IEC thermal derating (`clean.config_derating_curve`), and Indian Time-of-Day tariffs (`clean.config_tod_tariff`).
- Deterministic idempotent seeder (`make seed` / `python -m app.db.seed`) generating the 4-station demo cluster on a 100 kVA transformer.
- Documentation for database ER diagram (`docs/db/schema.md`) and modeling layers (`docs/db/modeling.md`).
- Root `Makefile` with targets: `seed`, `migrate`, `migrate-down`, `migrate-check`, `test`, `up`, `down`.
