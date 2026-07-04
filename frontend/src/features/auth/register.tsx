import { useNavigate, Navigate } from "react-router-dom";
import {
  Paper,
  Title,
  Text,
  TextInput,
  Button,
  Stack,
  PasswordInput,
  Anchor,
  Alert,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import { notifications } from "@mantine/notifications";
import { IconInfoCircle } from "@tabler/icons-react";
import { useMutation } from "@tanstack/react-query";
import { getAuthRegisterMutationOptions } from "@/api/generated/auth/auth";
import { useAuth } from "@/auth/auth-context";
import { getLocalTimezone } from "@/lib/dayjs";
import type { UserCreate } from "@/api/generated/models";

export function RegisterPage() {
  const navigate = useNavigate();
  const { login, isAuthenticated } = useAuth();

  const form = useForm<UserCreate>({
    initialValues: {
      email: "",
      password: "",
      name: "",
      username: "",
      timezone: getLocalTimezone(),
      avatarUrl: undefined,
    },
    validate: {
      email: (v) => (/^\S+@\S+\.\S+$/.test(v) ? null : "Введите корректный email"),
      password: (v) => (v.length >= 8 ? null : "Минимум 8 символов"),
      name: (v) => (v.trim().length >= 1 ? null : "Введите имя"),
      username: (v) =>
        /^[a-z0-9_-]{3,32}$/i.test(v) ? null : "Латиница, цифры, _ или -, 3–32 символа",
    },
  });

  const registerMutation = useMutation({
    ...getAuthRegisterMutationOptions(),
    onSuccess: (response) => {
      const { accessToken, refreshToken, user } = response.data;
      login(accessToken, refreshToken, user);
      notifications.show({
        title: "Аккаунт создан",
        message: `Добро пожаловать, ${user.name}!`,
        color: "green",
      });
      navigate("/", { replace: true });
    },
    onError: (err: unknown) => {
      const message =
        err instanceof Error ? err.message : "Не удалось зарегистрироваться";
      notifications.show({
        title: "Ошибка регистрации",
        message,
        color: "red",
      });
    },
  });

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return (
    <Paper radius="md" p="xl" withBorder maw={460} w="100%">
      <Stack gap="lg">
        <Stack gap={4}>
          <Title order={2}>Регистрация</Title>
          <Text size="sm" c="dimmed">
            Создайте аккаунт владельца календаря
          </Text>
        </Stack>

        <form
          onSubmit={form.onSubmit((v) => registerMutation.mutate({ data: v }))}
        >
          <Stack gap="md">
            <TextInput
              label="Имя"
              placeholder="Иван Иванов"
              key={form.key("name")}
              {...form.getInputProps("name")}
            />
            <TextInput
              label="Username"
              placeholder="ivan_ivanov"
              description="Используется в публичной ссылке: /ivan_ivanov/..."
              key={form.key("username")}
              {...form.getInputProps("username")}
            />
            <TextInput
              label="Email"
              type="email"
              autoComplete="email"
              placeholder="you@example.com"
              key={form.key("email")}
              {...form.getInputProps("email")}
            />
            <PasswordInput
              label="Пароль"
              autoComplete="new-password"
              placeholder="Минимум 8 символов"
              key={form.key("password")}
              {...form.getInputProps("password")}
            />
            <Button type="submit" loading={registerMutation.isPending} fullWidth>
              Зарегистрироваться
            </Button>
          </Stack>
        </form>

        <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
          Уже есть аккаунт?{" "}
          <Anchor component="a" href="/login" size="sm">
            Войти
          </Anchor>
        </Alert>
      </Stack>
    </Paper>
  );
}
