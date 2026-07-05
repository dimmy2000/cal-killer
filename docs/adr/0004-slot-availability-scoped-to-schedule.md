# Slot availability is scoped to Schedule, not EventType

When computing Slots for an EventType, existing Bookings are subtracted at the
**Schedule** level, not the EventType level: every Booking on every EventType
that references the same Schedule consumes from one shared availability pool.
Two EventTypes pointing at one Schedule cannot be double-booked against each
other.

Chosen over scoping at the EventType level (which silently permits overbooking
when one owner has multiple EventTypes on a shared Schedule) and at the User
level (which prevents legitimate multi-calendar setups — e.g., a separate
Schedule for pro-bono slots that shouldn't block paid ones). Schedule is the
unit of availability by definition in this model; that's where the boundary
sits.
