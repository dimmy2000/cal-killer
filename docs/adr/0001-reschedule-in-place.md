# Reschedule mutates the Booking in place

When an Attendee or Owner reschedules a Booking, the existing Booking record's
`startUtc` is updated; no new Booking is created. Chosen over the "cancel +
create new" pattern to keep id lineage stable for the Attendee. After a
reschedule the Booking enters the `rescheduled` status (a resting state) and
stays there until re-confirmed via `/confirm`, or auto-advances to
`confirmed` when the EventType requires no confirmation. Prior times are not
preserved.

The ManageToken is rotated **only on attendee-initiated reschedule**, so the
attendee's existing manage link stays valid when the owner moves the meeting.
Owner-side reschedule leaves the token unchanged; the attendee is notified
out-of-band (UI/email) but keeps their original link.

The post-reschedule status transition is asymmetric by initiator:
- **Attendee-initiated**: enters `rescheduled` and waits for owner `/confirm`
  (or auto-advances to `confirmed` when `requiresConfirmation=false`).
- **Owner-initiated**: `pending → pending`, `confirmed → confirmed`,
  `rescheduled → confirmed`. The `rescheduled → confirmed` collapse treats
  the owner's own reschedule as resolving the attendee's pending request
  (they've seen it and acted); for `pending`/`confirmed` the owner has
  already confirmed the action, so no extra step is owed.
