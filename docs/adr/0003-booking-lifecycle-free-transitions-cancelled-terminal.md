# Booking lifecycle: free transitions except `cancelled` is terminal

Both owner (Bearer-authenticated User) and attendee (ManageToken-authenticated)
may invoke `cancel` and `reschedule` on a Booking from any non-terminal status
(`pending`, `confirmed`, `rescheduled`); `rescheduled` is entered via
reschedule and stays until re-`confirm` or auto-advance. The only sink is
`cancelled` — once a Booking is `cancelled`, no further `cancel` or
`reschedule` is accepted (the endpoint returns `409 Conflict`).

Chosen over stricter state machines (e.g., reschedule only from `confirmed`,
or asymmetric owner/attendee permissions) because: (1) it matches the mental
model of calendar tools (Cal.com, Calendly) where any non-cancelled booking
can be moved or scrapped; (2) it avoids UX dead-ends like "you can't
reschedule a pending booking" — the attendee just wants a different time; (3)
the only real invariant is that cancellation is final, which is the one rule
worth enforcing in code.
