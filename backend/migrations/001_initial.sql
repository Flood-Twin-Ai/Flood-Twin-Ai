-- Jal-Drishti migration 001. The ORM creates the same tables for SQLite demo mode.
CREATE EXTENSION IF NOT EXISTS postgis;
-- Production migrations should be run with Alembic; this marker records the schema version.
CREATE TABLE IF NOT EXISTS schema_version (version VARCHAR(32) PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now());
INSERT INTO schema_version(version) VALUES ('001_initial') ON CONFLICT DO NOTHING;
