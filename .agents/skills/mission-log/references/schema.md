# Portable mission record schema

This reference is reconstructed from the original main contract; it is not a historical backend export.
Record mission_id, task, assignment_source, executor, execution_environment, status, owner, started_at, ended_at, duration, deadline, next_step, last_verified_at and metadata_status.
Every asset requires asset_id, role, filename/title, format, location_kind, location_name, exact path or stable URI, path_scope, actual version/ref, access state and location evidence.
Unknown components require missing_reason and location_next_step. Keep task completion separate from metadata completeness.
Events require stable event_id, timestamp with timezone, executor, recorder, action, result and evidence. Errors and repairs are separate append-only events.
Keep historical events unchanged; updates patch only intended properties. No whole-page replacement without a supported atomic revision guard.
See the repository templates/task-record.md for a local Markdown form. Sensitive records require the user-designated private destination.
