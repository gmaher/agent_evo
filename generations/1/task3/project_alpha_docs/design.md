# Project Alpha – Data Ingestion Service

Goal: Build a small service that ingests CSV files from customers, validates them,
and loads them into our internal analytics warehouse.

## Key Requirements

- Users upload CSV files via a web UI.
- Files are validated for:
  - Required columns present.
  - Data type checks.
  - Basic sanity checks (e.g., no negative revenues).
- Valid files are stored in cloud object storage.
- Metadata is written into a "jobs" table in the database.
- A downstream pipeline picks up successful jobs and loads them into the warehouse.

## Non-Goals

- Real-time streaming ingestion.
- Fancy transformation logic (just basic validation + load).
