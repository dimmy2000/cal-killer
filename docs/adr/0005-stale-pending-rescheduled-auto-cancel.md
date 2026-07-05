# Stale pending/rescheduled Bookings auto-cancel when startUtc passes

A `pending` or `rescheduled` Booking whose `startUtc` has passed transitions
to `cancelled` automatically — without any owner or attendee action. The
trigger is a sweep at read time (in `getSlots` and `Bookings.list`) or a
periodic job; either way, the transition is lazy and best-effort, not
transactional with time passing.

Chosen over keeping stale Bookings forever (which silently pollutes slot
availability — a `pending` blocks its slot indefinitely — and clutters the
owner's list) and over a creation-time TTL (which would require choosing an
arbitrary N hours and wouldn't catch `rescheduled` Bookings waiting on
re-confirmation). The `startUtc`-passed criterion is self-justifying: if the
meeting's time has gone by and it isn't confirmed, it didn't happen.

`confirmed` Bookings are deliberately excluded — they represent meetings that
*did* occur and should sit in history as completed, not be rewritten.
