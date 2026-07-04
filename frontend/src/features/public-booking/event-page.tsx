import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Stack,
  Title,
  Text,
  Card,
  Group,
  SimpleGrid,
  TextInput,
  Textarea,
  Button,
  Box,
  Container,
  Center,
  Loader,
} from "@mantine/core";
import { DatePicker } from "@mantine/dates";
import { useForm } from "@mantine/form";
import { notifications } from "@mantine/notifications";
import {
  IconCheck,
  IconVideo,
  IconMapPin,
  IconPhone,
} from "@tabler/icons-react";
import {
  usePublicGetEvent,
  usePublicGetSlots,
  usePublicCreateBooking,
} from "@/api/generated/public/public";
import type { Slot, AttendeeCreate, EventLocation } from "@/api/generated/models";
import { LoadingState } from "@/components/loading-state";
import { ErrorState } from "@/components/error-state";
import {
  formatDuration,
  formatTime,
  formatDateTime,
  getLocalTimezone,
  dayjs,
} from "@/lib/dayjs";

const LOCATION_META: Record<EventLocation, { label: string; icon: React.ReactNode }> = {
  online: { label: "Онлайн", icon: <IconVideo size={16} /> },
  in_person: { label: "Лично", icon: <IconMapPin size={16} /> },
  phone: { label: "Телефон", icon: <IconPhone size={16} /> },
};

export function PublicEventPage() {
  const { ownerSlug, eventSlug } = useParams<{
    ownerSlug: string;
    eventSlug: string;
  }>();
  const navigate = useNavigate();
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [selectedSlot, setSelectedSlot] = useState<Slot | null>(null);
  const [bookedSlot, setBookedSlot] = useState<{
    id: string;
    manageToken: string;
    startUtc: string;
  } | null>(null);

  const eventQuery = usePublicGetEvent(ownerSlug ?? "", eventSlug ?? "", {
    query: { enabled: Boolean(ownerSlug && eventSlug) },
  });

  const slotsQuery = usePublicGetSlots(
    ownerSlug ?? "",
    eventSlug ?? "",
    {
      from: selectedDate
        ? dayjs(selectedDate).startOf("day").utc().toISOString()
        : dayjs().startOf("day").utc().toISOString(),
      to: selectedDate
        ? dayjs(selectedDate).endOf("day").utc().toISOString()
        : dayjs().endOf("day").utc().toISOString(),
    },
    {
      query: {
        enabled: Boolean(ownerSlug && eventSlug && selectedDate),
        staleTime: 30_000,
      },
    },
  );

  const createMutation = usePublicCreateBooking({
    mutation: {
      onSuccess: (response) => {
        notifications.show({
          title: "Забронировано",
          message: "Встреча создана",
          color: "green",
        });
        setBookedSlot({
          id: response.data.booking.id,
          manageToken: response.data.manageToken,
          startUtc: response.data.booking.startUtc,
        });
      },
      onError: (err: unknown) => {
        notifications.show({
          title: "Ошибка",
          message: err instanceof Error ? err.message : "Не удалось создать бронь",
          color: "red",
        });
      },
    },
  });

  const form = useForm<AttendeeCreate & { confirmEmail: string }>({
    initialValues: {
      name: "",
      email: "",
      notes: "",
      timezone: getLocalTimezone(),
      confirmEmail: "",
    },
    validate: {
      name: (v) => (v.trim() ? null : "Введите имя"),
      email: (v) =>
        /^\S+@\S+\.\S+$/.test(v) ? null : "Введите корректный email",
      confirmEmail: (v, values) =>
        v === values.email ? null : "Email-ы не совпадают",
    },
  });

  if (eventQuery.isLoading)
    return (
      <Center h={300}>
        <Loader />
      </Center>
    );
  if (eventQuery.isError || !eventQuery.data?.data)
    return (
      <ErrorState
        title="Событие не найдено"
        message="Возможно, ссылка устарела или была удалена"
      />
    );

  const event = eventQuery.data.data;
  const tz = getLocalTimezone();
  const slots = slotsQuery.data?.data ?? [];
  const locMeta = LOCATION_META[event.location];

  if (bookedSlot) {
    const manageUrl = `${window.location.origin}/manage/${bookedSlot.id}?token=${bookedSlot.manageToken}`;
    return (
      <Container size="sm">
        <Card withBorder padding="xl" radius="md">
          <Stack align="center" gap="md">
            <Box
              style={{
                width: 56,
                height: 56,
                borderRadius: "50%",
                background: "var(--mantine-color-green-light)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <IconCheck size={32} color="var(--mantine-color-green-6)" />
            </Box>
            <Title order={3} ta="center">
              Встреча забронирована!
            </Title>
            <Text size="sm" c="dimmed" ta="center">
              {event.title} · {formatDateTime(bookedSlot.startUtc, tz)}
            </Text>
            <Text size="sm" c="dimmed" ta="center" maw={460}>
              Сохраните ссылку ниже, чтобы управлять бронированием (отменить или перенести):
            </Text>
            <Group gap="xs">
              <Text size="xs" c="brand" style={{ wordBreak: "break-all" }}>
                {manageUrl}
              </Text>
              <Button
                size="xs"
                variant="light"
                onClick={() => {
                  navigator.clipboard?.writeText(manageUrl);
                  notifications.show({
                    message: "Ссылка скопирована",
                    color: "green",
                  });
                }}
              >
                Копировать
              </Button>
            </Group>
            <Button
              variant="subtle"
              size="xs"
              onClick={() => navigate(`/manage/${bookedSlot.id}?token=${bookedSlot.manageToken}`)}
            >
              Открыть управление бронью
            </Button>
          </Stack>
        </Card>
      </Container>
    );
  }

  const onSubmit = form.onSubmit((values) => {
    if (!selectedSlot || !ownerSlug || !eventSlug) return;
    const attendee: AttendeeCreate = {
      name: values.name,
      email: values.email,
      notes: values.notes || undefined,
      timezone: values.timezone,
    };
    createMutation.mutate({
      ownerSlug,
      eventSlug,
      data: { attendee, startUtc: selectedSlot.startUtc },
    });
  });

  return (
    <Container size="md">
      <Stack gap="lg">
        <Card withBorder padding="lg" radius="md">
          <Stack gap="xs">
            <Group gap="sm" align="center">
              <Box
                style={{
                  width: 14,
                  height: 14,
                  borderRadius: 3,
                  background: event.color ?? "var(--mantine-color-brand-filled)",
                }}
              />
              <Title order={3}>{event.title}</Title>
            </Group>
            {event.description && (
              <Text size="sm" c="dimmed">
                {event.description}
              </Text>
            )}
            <Group gap="md" mt="xs">
              <Group gap={6}>
                {locMeta.icon}
                <Text size="sm">{locMeta.label}</Text>
              </Group>
              <Text size="sm" c="dimmed">
                · {formatDuration(event.durationMin)}
              </Text>
              <Text size="sm" c="dimmed">
                · с {event.ownerName}
              </Text>
            </Group>
            {event.requiresConfirmation && (
              <Text size="xs" c="orange" mt="xs">
                Эта встреча требует подтверждения владельцем.
              </Text>
            )}
          </Stack>
        </Card>

        <Group align="flex-start" gap="lg" wrap="nowrap">
          <Stack gap="sm" style={{ flex: 1 }}>
            <Text fw={500}>Выберите дату</Text>
          <DatePicker
            value={selectedDate}
            onChange={(d) => {
              setSelectedDate(d);
              setSelectedSlot(null);
            }}
            minDate={new Date()}
          />
          </Stack>

          <Stack gap="sm" style={{ flex: 1 }}>
            <Text fw={500}>
              {selectedDate
                ? `Слоты на ${dayjs(selectedDate).format("D MMMM YYYY")}`
                : "Выберите дату"}
            </Text>
            {!selectedDate && (
              <Text size="sm" c="dimmed">
                Сначала выберите дату в календаре слева.
              </Text>
            )}
            {selectedDate && slotsQuery.isLoading && (
              <LoadingState message="Поиск слотов…" />
            )}
            {selectedDate && slotsQuery.isError && (
              <ErrorState message="Не удалось загрузить слоты" />
            )}
            {selectedDate &&
              !slotsQuery.isLoading &&
              !slotsQuery.isError &&
              slots.length === 0 && (
                <Text size="sm" c="dimmed">
                  На эту дату нет доступных слотов.
                </Text>
              )}
            {slots.length > 0 && (
              <SimpleGrid cols={3} spacing="xs">
                {slots.map((s) => {
                  const active = selectedSlot?.startUtc === s.startUtc;
                  return (
                    <Button
                      key={s.startUtc}
                      variant={active ? "filled" : "light"}
                      size="sm"
                      onClick={() => setSelectedSlot(s)}
                    >
                      {formatTime(s.startUtc, tz)}
                    </Button>
                  );
                })}
              </SimpleGrid>
            )}
            {selectedSlot && (
              <form onSubmit={onSubmit}>
                <Stack gap="sm" mt="md">
                  <Text size="sm" fw={500}>
                    Ваши данные
                  </Text>
                  <TextInput
                    label="Имя"
                    placeholder="Ваше имя"
                    key={form.key("name")}
                    {...form.getInputProps("name")}
                  />
                  <Group grow>
                    <TextInput
                      label="Email"
                      placeholder="you@example.com"
                      key={form.key("email")}
                      {...form.getInputProps("email")}
                    />
                    <TextInput
                      label="Повторите email"
                      placeholder="you@example.com"
                      key={form.key("confirmEmail")}
                      {...form.getInputProps("confirmEmail")}
                    />
                  </Group>
                  <Textarea
                    label="Заметки (необязательно)"
                    placeholder="Что-нибудь важное для встречи"
                    autosize
                    minRows={2}
                    key={form.key("notes")}
                    {...form.getInputProps("notes")}
                  />
                  <Button
                    type="submit"
                    loading={createMutation.isPending}
                    mt="sm"
                  >
                    Забронировать на {formatTime(selectedSlot.startUtc, tz)}
                  </Button>
                </Stack>
              </form>
            )}
          </Stack>
        </Group>
      </Stack>
    </Container>
  );
}
