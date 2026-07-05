# Refresh token rotation, no grace window

Each call to `/auth/refresh` issues a new `refreshToken` (plus a new
`accessToken`) and invalidates the old one. No grace window — once rotated,
the previous `refreshToken` is rejected immediately.

Chosen over a long-lived `refreshToken` that survives until logout (simpler,
but undetectable if the token leaks) and over rotation-with-grace (handles
multi-tab refresh races, but adds complexity and partially defeats theft
detection). The grace window is unnecessary here because the frontend's
`customFetch` mutator already dedupes concurrent refresh calls
(see `frontend/src/api/client-config.ts`): only one `/auth/refresh` request
flies at a time per session, so the race that grace exists to solve does not
occur.

Rotation gives replay detection for free: if a stolen token is used after the
legitimate user has refreshed, the stolen token is already invalid.
