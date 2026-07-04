import { useState } from "react";
import { useNavigate, useLocation, Outlet } from "react-router-dom";
import {
  AppShell,
  Avatar,
  Burger,
  Group,
  Menu,
  NavLink,
  Stack,
  Text,
  Title,
  Container,
  Divider,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import {
  IconCalendarEvent,
  IconClock,
  IconCalendarStats,
  IconUser,
  IconLogout,
  IconChevronDown,
} from "@tabler/icons-react";
import { useAuth } from "@/auth/auth-context";
import { getLocalTimezone, formatDateTime } from "@/lib/dayjs";

const NAV_ITEMS = [
  { to: "/event-types", label: "Типы событий", icon: IconCalendarEvent },
  { to: "/schedules", label: "Расписания", icon: IconClock },
  { to: "/bookings", label: "Бронирования", icon: IconCalendarStats },
  { to: "/profile", label: "Профиль", icon: IconUser },
];

export function AppShellLayout() {
  const [opened, { toggle }] = useDisclosure();
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const [menuOpened, setMenuOpened] = useState(false);

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <AppShell
      header={{ height: 60 }}
      navbar={{ width: 240, breakpoint: "sm", collapsed: { mobile: !opened } }}
      padding="md"
    >
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <Group gap="sm">
            <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" />
            <Title order={4} c="brand">
              Cal Killer
            </Title>
          </Group>
          <Menu
            opened={menuOpened}
            onChange={setMenuOpened}
            position="bottom-end"
            width={220}
          >
            <Menu.Target>
              <Group
                gap="xs"
                style={{ cursor: "pointer" }}
                data-testid="user-menu"
              >
                <Avatar
                  size="sm"
                  color="brand"
                  radius="xl"
                  src={user?.avatarUrl ?? undefined}
                >
                  {user?.name?.[0]?.toUpperCase()}
                </Avatar>
                <Text size="sm" fw={500} visibleFrom="sm">
                  {user?.name}
                </Text>
                <IconChevronDown size={14} />
              </Group>
            </Menu.Target>
            <Menu.Dropdown>
              <Menu.Label>
                {user?.email}
              </Menu.Label>
              <Menu.Item
                leftSection={<IconUser size={14} />}
                onClick={() => navigate("/profile")}
              >
                Профиль
              </Menu.Item>
              <Menu.Divider />
              <Menu.Item
                color="red"
                leftSection={<IconLogout size={14} />}
                onClick={handleLogout}
              >
                Выйти
              </Menu.Item>
            </Menu.Dropdown>
          </Menu>
        </Group>
      </AppShell.Header>

      <AppShell.Navbar p="md">
        <Stack gap="xs">
          {NAV_ITEMS.map((item) => {
            const active = location.pathname.startsWith(item.to);
            return (
              <NavLink
                key={item.to}
                component="button"
                active={active}
                label={item.label}
                leftSection={<item.icon size={18} />}
                onClick={() => {
                  navigate(item.to);
                  if (opened) toggle();
                }}
              />
            );
          })}
          <Divider my="sm" />
          <Stack gap={2} px="sm">
            <Text size="xs" c="dimmed">
              Часовой пояс
            </Text>
            <Text size="xs" fw={500}>
              {getLocalTimezone()}
            </Text>
          </Stack>
        </Stack>
      </AppShell.Navbar>

      <AppShell.Main>
        <Container size="xl">
          <Outlet />
        </Container>
      </AppShell.Main>
    </AppShell>
  );
}

export function getRelativeTimeLabel(utcIso: string): string {
  return formatDateTime(utcIso, getLocalTimezone());
}
