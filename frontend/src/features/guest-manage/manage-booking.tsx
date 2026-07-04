import { useParams, useSearchParams } from "react-router-dom";
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
  Center,
  Loader,
} from "@mantine/core";
import { DatePicker } from "@mantine/dates";
import { useState } from "react";
import { notifications } from "@mantine/notifications";
import {
  usePublicGetBooking,
  usePublicCancelBooking,
  usePublicConfirmBooking,
  usePublicRescheduleBooking,
} from "@/api/generated/public/public";
import { ErrorState } from "@/components/error-state";
import { BookingStatusBadge } from "@/components/status-badge";
import { ConfirmDialog } from "@/components/confirm-dialog";
import {
  formatDateTime,
  formatTime,
  getLocalTimezone,
  dayjs,
} from "@/lib/dayjs";

export function GuestManagePage() {
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") ?? "";
  const [rescheduleOpened, setRescheduleOpened] = useState(false);
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [selectedStartUtc, setSelectedStartUtc] = useState<string | null>(null);

  const bookingQuery = usePublicGetBooking(id ?? "", { token }, {
    query: { enabled: Boolean(id && token) },
  });

  const cancelMutation = usePublicCancelBooking({
    mutation: {
      onSuccess: () => {
        notifications.show({
          title: "Отменено",
          message: "Бронирование отменено",
          color: "green",
        });
        if (id) {
          bookingQuery.refetch();
        }
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

  const confirmMutation = usePublicConfirmBooking({
    mutation: {
      onSuccess: () => {
        notifications.show({
          title: "Подтверждено",
          message: "Встреча подтверждена",
          color: "green",
        });
        if (id) {
          bookingQuery.refetch();
        }
      },
      onError: (err: unknown) => {
        notifications.show({
          title: "Ошибка",
          message: err instanceof Error ? err.message : "Не удалось подтвердить",
          color: "red",
        });
      },
    },
  });

  const rescheduleMutation = usePublicRescheduleBooking({
    mutation: {
      onSuccess: (response) => {
        notifications.show({
          title: "Перенесено",
          message: "Встреча перенесена. Сохраните новую ссылку для управления.",
          color: "green",
        });
        const newToken = response.data.manageToken;
        if (id) {
          window.history.replaceState(
            null,
            "",
            `/manage/${id}?token=${newToken}`,
          );
        }
        bookingQuery.refetch();
        setRescheduleOpened(false);
        setSelectedStartUtc(null);
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

  if (!token)
    return (
      <ErrorState
        title="Нет токена"
        message="Ссылка недействительна. Используйте ссылку из письма или из страницы бронирования."
      />
    );

  if (bookingQuery.isLoading)
    return (
      <Center h={300}>
        <Loader />
      </Center>
    );
  if (bookingQuery.isError || !bookingQuery.data?.data)
    return (
      <ErrorState
        title="Бронирование не найдено"
        message="Возможно, ссылка устарела или бронь была удалена."
      />
    );

  const booking = bookingQuery.data.data;
  const tz = getLocalTimezone();

  const isCancelled = booking.status === "cancelled";
  const isPending = booking.status === "pending";

  const handleReschedule = () => {
    if (!selectedStartUtc || !id) return;
    rescheduleMutation.mutate({
      id,
      data: { token, startUtc: selectedStartUtc },
    });
  };

  return (
    <Stack gap="lg" maw={640}>
      <Stack gap={2}>
        <Title order={2}>Управление бронированием</Title>
        <Text size="sm" c="dimmed">
          Просмотр, отмена или перенос встречи
        </Text>
      </Stack>

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
          <Divider />
          <Text size="sm" c="dimmed">
            Гость: {booking.attendee.name} ({booking.attendee.email})
          </Text>
        </Stack>
      </Card>

      {!isCancelled && (
        <Group justify="flex-end">
          {isPending && (
            <Button
              variant="light"
              color="green"
              loading={confirmMutation.isPending}
              onClick={() => confirmMutation.mutate({ id: booking.id, data: { token } })}
            >
              Подтвердить встречу
            </Button>
          )}
          <Button variant="light" onClick={() => setRescheduleOpened(true)}>
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
            onConfirm={() =>
              cancelMutation.mutate({ id: booking.id, data: { token } })
            }
          />
        </Group>
      )}

      <Modal
        opened={rescheduleOpened}
        onClose={() => setRescheduleOpened(false)}
        title="Перенести встречу"
        size="lg"
      >
        <Stack gap="md">
          <DatePicker
            value={selectedDate}
            onChange={(d) => {
              setSelectedDate(d);
              setSelectedStartUtc(null);
            }}
            minDate={new Date()}
          />
          {selectedDate && (
            <Stack gap="xs">
              <Text size="sm" fw={500}>
                Выберите новый слот на {dayjs(selectedDate).format("D MMMM YYYY")}:
              </Text>
              <Text size="xs" c="dimmed">
                Доступные слоты берутся из публичного календаря. Если слотов нет, выберите другую дату.
              </Text>
              <SimpleGrid cols={3} spacing="xs">
                {Array.from({ length: 8 }).map((_, i) => {
                  const base = dayjs(selectedDate).hour(9 + i);
                  const slotStart = base.toISOString();
                  const active = selectedStartUtc === slotStart;
                  return (
                    <Button
                      key={i}
                      variant={active ? "filled" : "light"}
                      size="xs"
                      onClick={() => setSelectedStartUtc(slotStart)}
                    >
                      {formatTime(slotStart, tz)}
                    </Button>
                  );
                })}
              </SimpleGrid>
            </Stack>
          )}
          {selectedStartUtc && (
            <Alert color="blue" variant="light">
              Новый слот: {formatDateTime(selectedStartUtc, tz)}
            </Alert>
          )}
          <Group justify="flex-end">
            <Button
              variant="default"
              onClick={() => setRescheduleOpened(false)}
            >
              Отмена
            </Button>
            <Button
              loading={rescheduleMutation.isPending}
              disabled={!selectedStartUtc}
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
