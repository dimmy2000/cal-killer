# Schedule timezone changes preserve wall-clock minutes

When a User edits a Schedule's `timezone`, existing `WorkingHours.startMin` /
`endMin` values are kept as-is and reinterpreted in the new zone (09:00–17:00
in America/New_York becomes 09:00–17:00 in Europe/London — a silent ~5 hour
shift in absolute availability). Chosen over absolute preservation (which
produces fractional-minute ugliness for non-whole-hour offset pairs and
reinterprets the owner's intent) and over rejecting the edit (which blocks a
legitimate change). WorkingHours are conceptually *relative to a zone*; an
owner who changes the zone is saying "these hours now belong to that zone."
The footgun (owner doesn't realize availability shifted) is a UI-warning
problem, not a data-model problem.
