import "@typespec/http";

using Http;

@service(#{ title: "Cal Killer" })
namespace CalKiller;

// ============================================================================
// Common models
// ============================================================================

@error
model Error {
  code: int32;
  message: string;
  details?: string;
}

model Paginated<T> {
  items: T[];
  nextCursor?: string;
}

model Created<T> {
  @header createdAt: utcDateTime;
  @body resource: T;
}

// ============================================================================
// Domain enums / unions
// ============================================================================

enum BookingStatus {
  pending: "pending",
  confirmed: "confirmed",
  cancelled: "cancelled",
  rescheduled: "rescheduled",
}

union EventLocation {
  online: "online",
  inPerson: "in_person",
  phone: "phone",
}

enum DayOfWeek {
  sunday: 0,
  monday: 1,
  tuesday: 2,
  wednesday: 3,
  thursday: 4,
  friday: 5,
  saturday: 6,
}

// ============================================================================
// User
// ============================================================================

model User {
  id: string;
  email: string;
  name: string;
  username: string;
  timezone: string;
  avatarUrl?: string;
  createdAt: utcDateTime;
}

model UserCreate {
  email: string;
  password: string;
  name: string;
  username: string;
  timezone: string;
  avatarUrl?: string;
}

model UserUpdate {
  email?: string;
  name?: string;
  username?: string;
  timezone?: string;
  avatarUrl?: string;
}

model PasswordChange {
  currentPassword: string;
  newPassword: string;
}

model AuthTokens {
  accessToken: string;
  refreshToken: string;
  user: User;
}

model LoginRequest {
  email: string;
  password: string;
}

model RefreshRequest {
  refreshToken: string;
}

// ============================================================================
// Schedule
// ============================================================================

model WorkingHours {
  dayOfWeek: DayOfWeek;
  startMin: int32;
  endMin: int32;
}

model ScheduleOverride {
  date: plainDate;
  startMin: int32;
  endMin: int32;
  available: boolean;
}

model Schedule {
  id: string;
  name: string;
  timezone: string;
  isDefault: boolean;
  workingHours: WorkingHours[];
  overrides: ScheduleOverride[];
  createdAt: utcDateTime;
}

model ScheduleCreate {
  name: string;
  timezone: string;
  isDefault?: boolean;
  workingHours: WorkingHours[];
  overrides?: ScheduleOverride[];
}

model ScheduleUpdate {
  name?: string;
  timezone?: string;
  isDefault?: boolean;
  workingHours?: WorkingHours[];
}

// ============================================================================
// EventType
// ============================================================================

model EventType {
  id: string;
  slug: string;
  title: string;
  description?: string;
  durationMin: int32;
  location: EventLocation;
  color?: string;
  scheduleId: string;
  paddingMinBefore: int32;
  paddingMinAfter: int32;
  minNoticeMin: int32;
  requiresConfirmation: boolean;
  createdAt: utcDateTime;
}

model EventTypeCreate {
  slug: string;
  title: string;
  description?: string;
  durationMin: int32;
  location: EventLocation;
  color?: string;
  scheduleId: string;
  paddingMinBefore?: int32;
  paddingMinAfter?: int32;
  minNoticeMin?: int32;
  requiresConfirmation?: boolean;
}

model EventTypeUpdate {
  slug?: string;
  title?: string;
  description?: string;
  durationMin?: int32;
  location?: EventLocation;
  color?: string;
  scheduleId?: string;
  paddingMinBefore?: int32;
  paddingMinAfter?: int32;
  minNoticeMin?: int32;
  requiresConfirmation?: boolean;
}

model PublicEventType {
  title: string;
  description?: string;
  durationMin: int32;
  location: EventLocation;
  color?: string;
  ownerName: string;
  ownerTimezone: string;
  requiresConfirmation: boolean;
}

// ============================================================================
// Booking
// ============================================================================

model Attendee {
  name: string;
  email: string;
  notes?: string;
  timezone: string;
}

model Booking {
  id: string;
  status: BookingStatus;
  startUtc: utcDateTime;
  endUtc: utcDateTime;
  eventTypeId: string;
  attendee: Attendee;
  location: EventLocation;
  createdAt: utcDateTime;
}

model BookingWithToken {
  booking: Booking;
  manageToken: string;
}

model AttendeeCreate {
  name: string;
  email: string;
  notes?: string;
  timezone: string;
}

model PublicBookingCreate {
  attendee: AttendeeCreate;
  startUtc: utcDateTime;
}

model Slot {
  startUtc: utcDateTime;
  endUtc: utcDateTime;
}

model ManageToken {
  token: string;
}

model RescheduleRequest {
  token: string;
  startUtc: utcDateTime;
}

// ============================================================================
// Pagination query
// ============================================================================

model PageQuery {
  @query limit?: int32;
  @query cursor?: string;
}

// ============================================================================
// Auth interface
// ============================================================================

@route("/auth")
@tag("Auth")
interface Auth {
  @route("/register") @post register(@body body: UserCreate): AuthTokens;
  @route("/login") @post login(@body body: LoginRequest): AuthTokens;
  @route("/refresh") @post refresh(@body body: RefreshRequest): AuthTokens;
  @route("/logout") @post logout(@body body: RefreshRequest): void;
}

// ============================================================================
// Users interface
// ============================================================================

@route("/users")
@tag("Users")
@useAuth(BearerAuth)
interface Users {
  @route("/me") @get me(): User;
  @route("/me") @patch updateMe(@body body: UserUpdate): User;
  @route("/me/password") @patch changePassword(@body body: PasswordChange): void;
}

// ============================================================================
// Schedules interface
// ============================================================================

@route("/schedules")
@tag("Schedules")
@useAuth(BearerAuth)
interface Schedules {
  @get list(...PageQuery): Paginated<Schedule>;
  @post create(@body body: ScheduleCreate): Schedule;
  @route("/{id}") @get read(@path id: string): Schedule;
  @route("/{id}") @patch update(@path id: string, @body body: ScheduleUpdate): Schedule;
  @route("/{id}") @delete delete(@path id: string): void;

  @route("/{id}/overrides") @get listOverrides(@path id: string): ScheduleOverride[];
  @route("/{id}/overrides") @post addOverride(@path id: string, @body body: ScheduleOverride): ScheduleOverride;
  @route("/{id}/overrides/{date}") @delete removeOverride(@path id: string, @path date: plainDate): void;
}

// ============================================================================
// EventTypes interface
// ============================================================================

@route("/event-types")
@tag("Event Types")
@useAuth(BearerAuth)
interface EventTypes {
  @get list(...PageQuery, @query scheduleId?: string): Paginated<EventType>;
  @post create(@body body: EventTypeCreate): EventType;
  @route("/{id}") @get read(@path id: string): EventType;
  @route("/{id}") @patch update(@path id: string, @body body: EventTypeUpdate): EventType;
  @route("/{id}") @delete delete(@path id: string): void;
}

// ============================================================================
// Bookings interface (owner)
// ============================================================================

@route("/bookings")
@tag("Bookings")
@useAuth(BearerAuth)
interface Bookings {
  @get list(
    ...PageQuery,
    @query status?: BookingStatus,
    @query eventTypeId?: string,
    @query from?: utcDateTime,
    @query to?: utcDateTime,
  ): Paginated<Booking>;
  @route("/{id}") @get read(@path id: string): Booking;
  @route("/{id}/cancel") @post cancel(@path id: string): Booking;
  @route("/{id}/reschedule") @post reschedule(@path id: string, @body body: { startUtc: utcDateTime }): Booking;
}

// ============================================================================
// Public booking interface (no auth)
// ============================================================================

@route("/public")
@tag("Public")
interface Public {
  @route("/{ownerSlug}/{eventSlug}") @get getEvent(
    @path ownerSlug: string,
    @path eventSlug: string,
  ): PublicEventType;

  @route("/{ownerSlug}/{eventSlug}/slots") @get getSlots(
    @path ownerSlug: string,
    @path eventSlug: string,
    @query from: utcDateTime,
    @query to: utcDateTime,
    @query tz?: string,
  ): Slot[];

  @route("/{ownerSlug}/{eventSlug}/bookings") @post createBooking(
    @path ownerSlug: string,
    @path eventSlug: string,
    @body body: PublicBookingCreate,
  ): BookingWithToken;

  @route("/bookings/{id}") @get getBooking(
    @path id: string,
    @query token: string,
  ): Booking;

  @route("/bookings/{id}/confirm") @post confirmBooking(
    @path id: string,
    @body body: ManageToken,
  ): Booking;

  @route("/bookings/{id}/cancel") @post cancelBooking(
    @path id: string,
    @body body: ManageToken,
  ): Booking;

  @route("/bookings/{id}/reschedule") @post rescheduleBooking(
    @path id: string,
    @body body: RescheduleRequest,
  ): BookingWithToken;
}
