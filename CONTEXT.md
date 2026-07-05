# Cal Killer

A self-hosted scheduling and booking tool. Users (owners) publish bookable
meeting templates; attendees book time slots without an account.

## Language

### People

**User**:
An authenticated account holder who owns EventTypes, Schedules, and Bookings.
Carries a `timezone` used as the create-time default for new Schedules and for
rendering the owner-facing UI; not authoritative for availability computation.
Authenticates by `email` (so changing `username` does not affect login). The
`username` may be freely renamed; the old `/{ownerSlug}/...` URLs then 404,
but attendee manage links (`/public/bookings/{id}`) are unaffected. Both
`username` and `email` are globally unique at any moment, but neither is
reserved after release — a freed `username` can be re-registered by another
User, who then owns any stale `/{ownerSlug}/...` links that still circulate.
_Avoid_: account, member, profile

**Owner**:
A read-only projection of a User exposed on the public booking surface,
comprising `username` (as the `ownerSlug` path component), `name`, and
`timezone` (the latter two surfaced as `ownerName` / `ownerTimezone` inside
`PublicEventType`). Not a separate entity; not writable from public routes.
The projection is **live**: any change the User makes to their own fields is
immediately reflected on the public surface, with no owner action required.
_Avoid_: host, organizer, account

**Attendee**:
The unauthenticated person who books a slot on an EventType. Identified by
email + name; authorized to manage their booking only via a ManageToken.
Each Booking is independent — there is no Attendee profile entity, and email
is contact information, not a key. The same email may book multiple slots
on the same EventType as long as their `[start, end]` intervals do not
overlap (padding is not factored into this check, only direct overlap).
`AttendeeCreate.email` is validated as an email address on input. `notes`
are fixed at creation and never edited afterward; the only way to change
them is to cancel and rebook. The owner sees attendee PII (email, name,
notes, timezone) — it is part of the booking contract on a self-hosted
system.
_Avoid_: guest, invitee, client, booker

### Scheduling

**EventType**:
A bookable meeting template (duration, location, padding, notice, confirmation
policy) owned by a User and published at `/{ownerSlug}/{eventSlug}`. Cannot be
deleted while it has non-`cancelled` Bookings — the delete returns
`409 Conflict` and the owner must first cancel those Bookings. An EventType
with only `cancelled` Bookings can be deleted (their history is dropped with
it). `minNoticeMin` is enforced both in `getSlots` (filtering) and in
`createBooking` (validation), so a slot that slips past the notice window
between the two calls is still rejected. The same check applies to both
attendee- and owner-initiated reschedule — `minNoticeMin` also protects the
attendee from being moved into a slot they cannot make. `color` (optional,
surfaced on the public booking page) is a hex color `^#[0-9A-Fa-f]{6}$`,
validated on input on both backend and frontend; arbitrary strings are
rejected to prevent CSS injection on the unauthenticated surface.
_Avoid_: event, meeting type, calendar event, appointment type

**Schedule**:
A per-User, private set of recurring WorkingHours plus date-specific Overrides
that an EventType references to compute availability. Cannot be deleted while
EventTypes reference it — the delete returns `409 Conflict` and the owner must
first rebind or delete those EventTypes.
_Avoid_: calendar, availability profile, working calendar

**WorkingHours**:
The baseline weekly availability for a Schedule, expressed as (dayOfWeek,
startMin, endMin) intervals in the Schedule's timezone. Wall-clock preserved:
if `Schedule.timezone` changes, the minute values stay and are reinterpreted
in the new zone (09:00–17:00 EST becomes 09:00–17:00 London). Localized to
absolute UTC per specific date by the slot compiler using `zoneinfo`:
non-existent local moments during a spring-forward gap are skipped, ambiguous
moments during a fall-back overlap resolve to the first (earlier) occurrence.
_Avoid_: hours, business hours, availability window

**ScheduleOverride**:
A date-specific full replacement of WorkingHours for one Schedule. One
override per date — adding a second replaces the first. `available=true` with
`(startMin, endMin)` means "on this date, work from X to Y instead of the
day-of-week's WorkingHours." `available=false` means "on this date, do not
work at all" (the interval fields are ignored).
_Avoid_: exception, blackout, special hours

**Slot**:
A computed, currently-bookable time interval on an EventType. The interval is
the meeting itself (`endUtc = startUtc + durationMin`); padding is a
server-side conflict-detection concern that affects *which* slots are
available but is not reflected in the slot's own boundaries. Derived from
the referenced Schedule minus existing Bookings — and "existing Bookings"
here means **every Booking on every EventType that references the same
Schedule**, not just Bookings on this EventType. Two EventTypes sharing one
Schedule draw from one shared availability pool; the owner creates separate
Schedules to isolate them. Conflict detection uses each Booking's *padded*
interval `[start - paddingMinBefore, end + paddingMinAfter]` from its own
EventType, so padding from both sides of any pair is respected. Not persisted.
On `createBooking` and `reschedule`, the requested `startUtc` must satisfy
the same invariants (inside WorkingHours, no conflict, `minNoticeMin`) **and**
be grid-aligned: `(startMin - workingHours.startMin) mod durationMin == 0`
in the Schedule's timezone, so slots begin at predictable boundaries
(9:00, 9:30, 10:00, never 10:17). Conflicts are checked against all other
Bookings on the Schedule; the rescheduled Booking's own old interval is
excluded. `Public.getSlots` rejects requests where `to - from > 60 days`
with `400 Bad Request` to bound slot-computation cost.
_Avoid_: opening, available time, appointment

### Bookings

**Booking**:
A reserved time interval on an EventType for one Attendee, with a lifecycle
status. A Booking is an immutable snapshot of the EventType's state at
creation: fields derived from the EventType (`location`, `endUtc` via
`durationMin`, the effect of `requiresConfirmation` on lifecycle) are fixed
and never recomputed when the EventType is later edited. The only mutations
possible after creation are explicit lifecycle transitions (`pending →
confirmed`, `* → cancelled`, `* → rescheduled → confirmed`) triggered by
owner or attendee actions, and `reschedule` which updates `startUtc` and
rotates the ManageToken in place (same `id`) per ADR-0001. `updatedAt`
advances only on these explicit Booking mutations (status transitions,
reschedule) — never on reads, and never on edits to the related EventType or
Schedule (those don't touch the Booking under the snapshot principle).
`location` is copied from the parent EventType at creation and held as a
denormalized, frozen snapshot — editing the EventType's location afterward
affects only future Bookings; the owner must reschedule or cancel to change
an existing Booking's location. `Bookings.list` is ordered by `updatedAt`
DESC by default. A Booking remains accessible via `Public.getBooking` even
after its parent EventType is deleted — the snapshot carries enough data
(times, status, attendee) for the attendee to understand its state; the
missing EventType title is a display concern for the frontend.
_Avoid_: appointment, reservation, meeting, event

**BookingStatus**:
The lifecycle state of a Booking. `pending` — awaiting confirmation;
`confirmed` — ready to occur; `cancelled` — will not occur (soft state: the
Booking record remains queryable; cancellation is not physical deletion, and
the status is terminal — no further `cancel` or `reschedule` is accepted);
`rescheduled` — resting state entered **only after an attendee-initiated
reschedule**, until re-confirmed via `/confirm` (or auto-advanced to
`confirmed` when no confirmation is required). An owner-initiated reschedule
preserves the current status (`pending → pending`, `confirmed → confirmed`),
**except** `rescheduled → confirmed` — the owner's own action resolves the
attendee's pending request. Transitions out of `pending`/`confirmed`/`rescheduled` to
`cancelled` or `rescheduled` are free for both owner and attendee; only
`cancelled` is a sink. In addition, `pending` and `rescheduled` Bookings
whose `startUtc` has passed auto-transition to `cancelled` (a sweep at read
time or via a periodic job) so they don't pollute slot availability or the
owner's list. `confirmed` Bookings are **not** auto-cancelled after their
time passes — they simply sit in history as completed meetings.
_Avoid_: state

**ManageToken**:
A per-Booking secret issued to the Attendee at creation and rotated only on
attendee-initiated reschedule (not on owner-initiated reschedule, so the
attendee's existing manage link stays valid when the owner moves the meeting).
Authorizes confirm, cancel, and reschedule on the public routes without an
account. Distinct from a User's Bearer token.
_Avoid_: booking token, guest token, edit link

**Slug**:
The URL-stable identifier component for an EventType (eventSlug) on the public
booking surface. A User has no separate slug — its `username` serves as the
`ownerSlug` path component. Together they form `/{ownerSlug}/{eventSlug}`.
`eventSlug` is unique per User (so the URL resolves unambiguously) but may be
freely renamed by the owner; the old URL then 404s. Attendee manage links
(`/public/bookings/{id}`) are unaffected by slug changes.
_Avoid_: handle, permalink, key
