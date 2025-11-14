# Meeting Notes – 2025-09-18

Attendees: Alice, Bob, Carol

- Frontend upload UI is mostly done. Need to hook up actual backend endpoint.
- Backend API is returning 500s when file size > 10MB.
- Bob suspects the validation step is trying to load the whole file into memory.
- Carol proposed a streaming validator, but it might be overkill for v1.
- Alice wants:
  - Clear error messages when validation fails.
  - A "job status" page for users to see progress.

Action items:

- Bob: Add logging around large-file uploads to confirm memory usage.
- Carol: Spec a minimal non-streaming fix for big files (maybe chunked read).
- Alice: Draft UX for job status page.
