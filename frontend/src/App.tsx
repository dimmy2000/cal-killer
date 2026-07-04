import {
  createBrowserRouter,
  RouterProvider,
  Navigate,
} from "react-router-dom";
import { MantineProvider } from "@mantine/core";
import { Notifications } from "@mantine/notifications";
import { DatesProvider } from "@mantine/dates";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { theme } from "./theme";
import { AuthProvider } from "./auth/auth-context";
import { ProtectedRoute } from "./auth/protected-route";
import { AppShellLayout } from "./layouts/app-shell";
import { PublicLayout } from "./layouts/public-layout";
import { LoginPage } from "./features/auth/login";
import { RegisterPage } from "./features/auth/register";
import { EventTypesListPage } from "./features/event-types/list";
import { EventTypeFormPage } from "./features/event-types/form";
import { SchedulesListPage } from "./features/schedules/list";
import { ScheduleFormPage } from "./features/schedules/form";
import { BookingsListPage } from "./features/bookings/list";
import { BookingDetailPage } from "./features/bookings/detail";
import { ProfilePage } from "./features/profile/profile";
import { PublicEventPage } from "./features/public-booking/event-page";
import { GuestManagePage } from "./features/guest-manage/manage-booking";
import "dayjs/locale/ru";
import "@mantine/core/styles.css";
import "@mantine/dates/styles.css";
import "@mantine/notifications/styles.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 30_000,
    },
  },
});

const router = createBrowserRouter([
  {
    path: "/login",
    element: (
      <PublicLayout>
        <LoginPage />
      </PublicLayout>
    ),
  },
  {
    path: "/register",
    element: (
      <PublicLayout>
        <RegisterPage />
      </PublicLayout>
    ),
  },
  {
    element: (
      <ProtectedRoute>
        <AppShellLayout />
      </ProtectedRoute>
    ),
    children: [
      { path: "/", element: <Navigate to="/event-types" replace /> },
      { path: "/event-types", element: <EventTypesListPage /> },
      { path: "/event-types/new", element: <EventTypeFormPage /> },
      { path: "/event-types/:id/edit", element: <EventTypeFormPage /> },
      { path: "/schedules", element: <SchedulesListPage /> },
      { path: "/schedules/new", element: <ScheduleFormPage /> },
      { path: "/schedules/:id/edit", element: <ScheduleFormPage /> },
      { path: "/bookings", element: <BookingsListPage /> },
      { path: "/bookings/:id", element: <BookingDetailPage /> },
      { path: "/profile", element: <ProfilePage /> },
    ],
  },
  {
    path: "/manage/:id",
    element: (
      <PublicLayout>
        <GuestManagePage />
      </PublicLayout>
    ),
  },
  {
    path: "/:ownerSlug/:eventSlug",
    element: <PublicEventPage />,
  },
]);

export function App() {
  return (
    <MantineProvider theme={theme}>
      <DatesProvider settings={{ locale: "ru", firstDayOfWeek: 1 }}>
        <Notifications position="top-right" />
        <QueryClientProvider client={queryClient}>
          <AuthProvider>
            <RouterProvider router={router} />
          </AuthProvider>
        </QueryClientProvider>
      </DatesProvider>
    </MantineProvider>
  );
}
