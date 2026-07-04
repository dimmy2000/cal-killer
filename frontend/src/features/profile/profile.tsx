import {
  Stack,
  Title,
  Text,
  TextInput,
  Select,
  Button,
  Card,
  Group,
  PasswordInput,
  Divider,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import { notifications } from "@mantine/notifications";
import { useQueryClient } from "@tanstack/react-query";
import {
  useUsersUpdateMe,
  useUsersChangePassword,
  getUsersMeQueryKey,
} from "@/api/generated/users/users";
import { useAuth } from "@/auth/auth-context";
import type { UserUpdate, PasswordChange } from "@/api/generated/models";
import { getLocalTimezone } from "@/lib/dayjs";

const COMMON_TZ = [
  "UTC",
  "Europe/Moscow",
  "Europe/Kaliningrad",
  "Europe/Samara",
  "Asia/Yekaterinburg",
  "Asia/Omsk",
  "Asia/Krasnoyarsk",
  "Asia/Irkutsk",
  "Asia/Yakutsk",
  "Asia/Vladivostok",
  "Europe/London",
  "Europe/Berlin",
  "America/New_York",
];

interface ProfileForm {
  name: string;
  username: string;
  email: string;
  timezone: string;
  avatarUrl: string;
}

interface PasswordForm {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

export function ProfilePage() {
  const { user, setUser } = useAuth();
  const queryClient = useQueryClient();

  const profileForm = useForm<ProfileForm>({
    initialValues: {
      name: user?.name ?? "",
      username: user?.username ?? "",
      email: user?.email ?? "",
      timezone: user?.timezone ?? getLocalTimezone(),
      avatarUrl: user?.avatarUrl ?? "",
    },
    validate: {
      name: (v) => (v.trim() ? null : "Введите имя"),
      username: (v) =>
        /^[a-z0-9_-]{3,32}$/i.test(v) ? null : "Латиница, цифры, _ или -, 3–32",
      email: (v) => (/^\S+@\S+\.\S+$/.test(v) ? null : "Введите корректный email"),
    },
  });

  const passwordForm = useForm<PasswordForm>({
    initialValues: {
      currentPassword: "",
      newPassword: "",
      confirmPassword: "",
    },
    validate: {
      currentPassword: (v) => (v ? null : "Введите текущий пароль"),
      newPassword: (v) =>
        v.length >= 8 ? null : "Минимум 8 символов",
      confirmPassword: (v, values) =>
        v === values.newPassword ? null : "Пароли не совпадают",
    },
  });

  const updateMutation = useUsersUpdateMe({
    mutation: {
      onSuccess: (response) => {
        setUser(response.data);
        queryClient.invalidateQueries({ queryKey: getUsersMeQueryKey() });
        notifications.show({
          title: "Сохранено",
          message: "Профиль обновлён",
          color: "green",
        });
      },
      onError: (err: unknown) => {
        notifications.show({
          title: "Ошибка",
          message: err instanceof Error ? err.message : "Не удалось сохранить",
          color: "red",
        });
      },
    },
  });

  const passwordMutation = useUsersChangePassword({
    mutation: {
      onSuccess: () => {
        notifications.show({
          title: "Пароль изменён",
          message: "Используйте новый пароль при следующем входе",
          color: "green",
        });
        passwordForm.reset();
      },
      onError: (err: unknown) => {
        notifications.show({
          title: "Ошибка",
          message: err instanceof Error ? err.message : "Не удалось изменить пароль",
          color: "red",
        });
      },
    },
  });

  const onSubmitProfile = profileForm.onSubmit((values) => {
    const payload: UserUpdate = {
      name: values.name,
      username: values.username,
      email: values.email,
      timezone: values.timezone,
      avatarUrl: values.avatarUrl || undefined,
    };
    updateMutation.mutate({ data: payload });
  });

  const onSubmitPassword = passwordForm.onSubmit((values) => {
    const payload: PasswordChange = {
      currentPassword: values.currentPassword,
      newPassword: values.newPassword,
    };
    passwordMutation.mutate({ data: payload });
  });

  return (
    <Stack gap="lg" maw={680}>
      <Stack gap={2}>
        <Title order={2}>Профиль</Title>
        <Text size="sm" c="dimmed">
          Управляйте личными данными и паролем
        </Text>
      </Stack>

      <form onSubmit={onSubmitProfile}>
        <Card withBorder padding="lg">
          <Stack gap="md">
            <Group grow>
              <TextInput
                label="Имя"
                key={profileForm.key("name")}
                {...profileForm.getInputProps("name")}
              />
              <TextInput
                label="Username"
                key={profileForm.key("username")}
                {...profileForm.getInputProps("username")}
              />
            </Group>
            <Group grow>
              <TextInput
                label="Email"
                key={profileForm.key("email")}
                {...profileForm.getInputProps("email")}
              />
              <Select
                label="Часовой пояс"
                data={COMMON_TZ}
                searchable
                key={profileForm.key("timezone")}
                {...profileForm.getInputProps("timezone")}
              />
            </Group>
            <TextInput
              label="URL аватара"
              placeholder="https://..."
              key={profileForm.key("avatarUrl")}
              {...profileForm.getInputProps("avatarUrl")}
            />
            <Group justify="flex-end">
              <Button type="submit" loading={updateMutation.isPending}>
                Сохранить
              </Button>
            </Group>
          </Stack>
        </Card>
      </form>

      <Divider />

      <form onSubmit={onSubmitPassword}>
        <Card withBorder padding="lg">
          <Stack gap="md">
            <Text fw={500}>Смена пароля</Text>
            <PasswordInput
              label="Текущий пароль"
              autoComplete="current-password"
              key={passwordForm.key("currentPassword")}
              {...passwordForm.getInputProps("currentPassword")}
            />
            <Group grow>
              <PasswordInput
                label="Новый пароль"
                autoComplete="new-password"
                key={passwordForm.key("newPassword")}
                {...passwordForm.getInputProps("newPassword")}
              />
              <PasswordInput
                label="Повторите новый пароль"
                autoComplete="new-password"
                key={passwordForm.key("confirmPassword")}
                {...passwordForm.getInputProps("confirmPassword")}
              />
            </Group>
            <Group justify="flex-end">
              <Button
                type="submit"
                loading={passwordMutation.isPending}
                color="brand"
                variant="light"
              >
                Изменить пароль
              </Button>
            </Group>
          </Stack>
        </Card>
      </form>
    </Stack>
  );
}
