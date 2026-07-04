import { useNavigate, useLocation, Navigate } from "react-router-dom";
import {
  Paper,
  Title,
  Text,
  TextInput,
  Button,
  Stack,
  PasswordInput,
  Alert,
  Anchor,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import { notifications } from "@mantine/notifications";
import { IconInfoCircle } from "@tabler/icons-react";
import { useMutation } from "@tanstack/react-query";
import { getAuthLoginMutationOptions } from "@/api/generated/auth/auth";
import { useAuth } from "@/auth/auth-context";
import type { LoginRequest } from "@/api/generated/models";

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isAuthenticated } = useAuth();

  const form = useForm<LoginRequest>({
    initialValues: { email: "", password: "" },
    validate: {
      email: (v) => (/^\S+@\S+\.\S+$/.test(v) ? null : "Введите корректный email"),
      password: (v) => (v.length >= 1 ? null : "Введите пароль"),
    },
  });

  const loginMutation = useMutation({
    ...getAuthLoginMutationOptions(),
    onSuccess: (response) => {
      const { accessToken, refreshToken, user } = response.data;
      login(accessToken, refreshToken, user);
      notifications.show({
        title: "Добро пожаловать",
        message: `Вы вошли как ${user.name}`,
        color: "green",
      });
      const from = (location.state as { from?: { pathname: string } })?.from?.pathname ?? "/";
      navigate(from, { replace: true });
    },
    onError: (err: unknown) => {
      const message =
        err instanceof Error ? err.message : "Не удалось войти";
      notifications.show({
        title: "Ошибка входа",
        message,
        color: "red",
      });
    },
  });

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return (
    <Paper radius="md" p="xl" withBorder maw={440} w="100%">
      <Stack gap="lg">
        <Stack gap={4}>
          <Title order={2}>Вход</Title>
          <Text size="sm" c="dimmed">
            Войдите в личный кабинет Cal Killer
          </Text>
        </Stack>

        <form onSubmit={form.onSubmit((v) => loginMutation.mutate({ data: v }))}>
          <Stack gap="md">
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
              autoComplete="current-password"
              placeholder="••••••••"
              key={form.key("password")}
              {...form.getInputProps("password")}
            />
            <Button type="submit" loading={loginMutation.isPending} fullWidth>
              Войти
            </Button>
          </Stack>
        </form>

        <Alert icon={<IconInfoCircle size={16} />} color="blue" variant="light">
          Нет аккаунта?{" "}
          <Anchor component="a" href="/register" size="sm">
            Зарегистрироваться
          </Anchor>
        </Alert>
      </Stack>
    </Paper>
  );
}
