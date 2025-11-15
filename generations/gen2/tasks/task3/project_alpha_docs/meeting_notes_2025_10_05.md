# Meeting Notes – 2025-10-05

Attendees: Alice, Bob

Status update:

- Large-file upload bug:
  - Root cause: validation function reading entire file into a list of rows before checking anything.
  - Fix in progress: process file line-by-line and validate incrementally.
- Job status page:
  - Basic version implemented (shows "pending", "validating", "success", "failed").
  - Needs better empty-state UX.

New issues:

- Some customer files (EU clients) use ";" instead of "," as separator.
- Timezone handling for "event_timestamp" column is unclear.
  - Some files are in UTC, others in local time.
  - No clear standard defined yet.

Action items:

- Decide on delimiter handling strategy (auto-detect? config per customer?).
- Define a canonical timezone for event timestamps and a migration plan.
