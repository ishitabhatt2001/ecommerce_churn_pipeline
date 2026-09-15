-- Run once: sets up the three-layer warehouse structure.
-- raw    = data exactly as it arrived, never modified
-- staging = cleaned, validated, deduplicated
-- marts   = business-ready tables (what the dashboard reads from)

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;
