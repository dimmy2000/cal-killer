import { useParams, useNavigate } from "react-router-dom";
import {
  Stack,
  Title,
  Text,
  Card,
  Group,
  Button,
  Divider,
  Modal,
  SimpleGrid,
  Alert,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { DatePicker } from "@mantine/dates";
import { useState } from "react";
import { notifications } from "@mantine/notifications";
import { useQueryClient } from "@tanstack/react-query";
import {
  useBookingsRead,
  getBookingsReadQueryKey,
  getBookingsListQueryKey,
  useBookingsCancel,
  useBookingsReschedule,
} from "@/api/generated/bookings/bookings";
import {
  usePublicGetSlots,
} from "@/api/generated/public/public";
import { useEventTypesRead } from "@/api/generated/event-types/event-types";
import { useAuth } from "@/auth/auth-context";
import { LoadingState } from "@/components/loading-state";
import { ErrorState } from "@/components/error-state";
import { BookingStatusBadge } from "@/components/status-badge";
import { LocationBadge } from "@/components/location-badge";
import { ConfirmDialog } from "@/components/confirm-dialog";
import {
  formatDateTime,
  formatTime,
  getLocalTimezone,
  dayjs,
} from "@/lib/dayjs";
import type { Slot } from "@/api/generated/models";

export function BookingDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [rescheduleOpened, { open, close }] = useDisclosure(false);
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [selectedSlot, setSelectedSlot] = useState<Slot | null>(null);

  const bookingQuery = useBookingsRead(id ?? "", {
    query: { enabled: Boolean(id) },
  });
  const booking = bookingQuery.data?.data;

  const eventTypeQuery = useEventTypesRead(booking?.eventTypeId ?? "", {
    query: { enabled: Boolean(booking?.eventTypeId) },
  });
  const eventType = eventTypeQuery.data?.data;

  const cancelMutation = useBookingsCancel({
    mutation: {
      onSuccess: () => {
        notifications.show({
          title: "Отменено",
          message: "Бронирование отменено",
          color: "green",
        });
        if (id) {
          queryClient.invalidateQueries({
            queryKey: getBookingsReadQueryKey(id),
          });
        }
        queryClient.invalidateQueries({
          queryKey: getBookingsListQueryKey(),
        });
      },
      onError: (err: unknown) => {
        notifications.show({
          title: "Ошибка",
          message: err instanceof Error ? err.message : "Не удалось отменить",
          color: "red",
        });
      },
    },
  });

  const rescheduleMutation = useBookingsReschedule({
    mutation: {
      onSuccess: () => {
        notifications.show({
          title: "Перенесено",
          message: "Бронирование перенесено",
          color: "green",
        });
        if (id) {
          queryClient.invalidateQueries({
            queryKey: getBookingsReadQueryKey(id),
          });
        }
        queryClient.invalidateQueries({
          queryKey: getBookingsListQueryKey(),
        });
        close();
        setSelectedSlot(null);
      },
      onError: (err: unknown) => {
        notifications.show({
          title: "Ошибка",
          message: err instanceof Error ? err.message : "Не удалось перенести",
          color: "red",
        });
      },
    },
  });

  const slotsQuery = usePublicGetSlots(
    user?.username ?? "",
    eventType?.slug ?? "",
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
        enabled: rescheduleOpened && Boolean(eventType?.slug),
        staleTime: 30_000,
      },
    },
  );

  if (bookingQuery.isLoading) return <LoadingState />;
  if (bookingQuery.isError || !booking)
    return (
      <ErrorState
        message="Не удалось загрузить бронирование"
        onRetry={() => bookingQuery.refetch()}
      />
    );

  const tz = getLocalTimezone();
  const slots = slotsQuery.data?.data ?? [];

  const handleReschedule = () => {
    if (!selectedSlot || !id) return;
    rescheduleMutation.mutate({
      id,
      data: { startUtc: selectedSlot.startUtc },
    });
  };

  return (
    <Stack gap="lg" maw={720}>
      <Group justify="space-between">
        <Stack gap={2}>
          <Title order={2}>Бронирование</Title>
          <Text size="sm" c="dimmed">
            {eventType?.title ?? "Тип события удалён"}
          </Text>
        </Stack>
        <Button variant="default" onClick={() => navigate("/bookings")}>
          Назад к списку
        </Button>
      </Group>

      <Card withBorder padding="lg">
        <Stack gap="md">
          <Group justify="space-between">
            <Text fw={500}>Статус</Text>
            <BookingStatusBadge status={booking.status} />
          </Group>
          <Divider />
          <Group justify="space-between">
            <Text fw={500}>Начало</Text>
            <Text>{formatDateTime(booking.startUtc, tz)}</Text>
          </Group>
          <Group justify="space-between">
            <Text fw={500}>Окончание</Text>
            <Text>{formatDateTime(booking.endUtc, tz)}</Text>
          </Group>
          {eventType && (
            <>
              <Divider />
              <Group justify="space-between">
                <Text fw={500}>Локация</Text>
                <LocationBadge location={booking.location} />
              </Group>
              <Group justify="space-between">
                <Text fw={500}>Длительность</Text>
                <Text>{formatDuration(eventType.durationMin)}</Text>
              </Group>
            </>
          )}
        </Stack>
      </Card>

      <Card withBorder padding="lg">
        <Stack gap="md">
          <Text fw={500}>Гость</Text>
          <Group justify="space-between">
            <Text size="sm" c="dimmed">Имя</Text>
            <Text>{booking.attendee.name}</Text>
          </Group>
          <Group justify="space-between">
            <Text size="sm" c="dimmed">Email</Text>
            <Text>{booking.attendee.email}</Text>
          </Group>
          <Group justify="space-between">
            <Text size="sm" c="dimmed">Часовой пояс гостя</Text>
            <Text>{booking.attendee.timezone}</Text>
          </Group>
          {booking.attendee.notes && (
            <Group justify="space-between" align="flex-start">
              <Text size="sm" c="dimmed">Заметки</Text>
              <Text maw={400} ta="right">
                {booking.attendee.notes}
              </Text>
            </Group>
          )}
        </Stack>
      </Card>

      {booking.status !== "cancelled" && (
        <Group justify="flex-end">
          <Button variant="light" onClick={open}>
            Перенести
          </Button>
          <ConfirmDialog
            trigger={
              <Button color="red" variant="light">
                Отменить встречу
              </Button>
            }
            title="Отменить бронирование?"
            message="Встреча будет отменена безвозвратно."
            confirmLabel="Отменить встречу"
            loading={cancelMutation.isPending}
            onConfirm={() => cancelMutation.mutate({ id: booking.id })}
          />
        </Group>
      )}

      <Modal
        opened={rescheduleOpened}
        onClose={close}
        title="Перенести встречу"
        size="lg"
      >
        <Stack gap="md">
          <DatePicker
            value={selectedDate}
            onChange={(d) => {
              setSelectedDate(d);
              setSelectedSlot(null);
            }}
            minDate={new Date()}
          />
          {selectedDate && (
            <Stack gap="xs">
              <Text size="sm" fw={500}>
                Доступные слоты на {dayjs(selectedDate).format("D MMMM YYYY")}:
              </Text>
              {slotsQuery.isLoading && <LoadingState message="Поиск слотов…" />}
              {slotsQuery.isError && (
                <ErrorState message="Не удалось загрузить слоты" />
              )}
              {!slotsQuery.isLoading &&
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
                        size="xs"
                        onClick={() => setSelectedSlot(s)}
                      >
                        {formatTime(s.startUtc, tz)}
                      </Button>
                    );
                  })}
                </SimpleGrid>
              )}
            </Stack>
          )}
          {selectedSlot && (
            <Alert color="blue" variant="light">
              Выбрано: {formatDateTime(selectedSlot.startUtc, tz)}
            </Alert>
          )}
          <Group justify="flex-end">
            <Button variant="default" onClick={close}>
              Отмена
            </Button>
            <Button
              loading={rescheduleMutation.isPending}
              disabled={!selectedSlot}
              onClick={handleReschedule}
            >
              Перенести
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Stack>
  );
}

function formatDuration(minutes: number): string {
  if (minutes < 60) return `${minutes} мин`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m === 0 ? `${h} ч` : `${h} ч ${m} мин`;
}
