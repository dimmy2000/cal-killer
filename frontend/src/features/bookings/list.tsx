import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Stack,
  Title,
  Text,
  Group,
  Card,
  Select,
  Button,
} from "@mantine/core";
import { IconChevronRight } from "@tabler/icons-react";
import type { Booking, BookingStatus } from "@/api/generated/models";
import {
  useBookingsList,
  getBookingsListQueryKey,
  useBookingsCancel,
} from "@/api/generated/bookings/bookings";
import { useEventTypesList } from "@/api/generated/event-types/event-types";
import { useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";
import { LoadingState } from "@/components/loading-state";
import { ErrorState } from "@/components/error-state";
import { EmptyState } from "@/components/empty-state";
import { BookingStatusBadge } from "@/components/status-badge";
import { Pagination } from "@/components/pagination";
import { ConfirmDialog } from "@/components/confirm-dialog";
import { formatDateTime, getLocalTimezone } from "@/lib/dayjs";

const STATUS_OPTIONS: { value: BookingStatus; label: string }[] = [
  { value: "pending", label: "Ожидает" },
  { value: "confirmed", label: "Подтверждено" },
  { value: "cancelled", label: "Отменено" },
  { value: "rescheduled", label: "Перенесено" },
];

export function BookingsListPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<BookingStatus | undefined>(undefined);
  const [eventTypeId, setEventTypeId] = useState<string | undefined>(undefined);
  const [cursor, setCursor] = useState<string | undefined>(undefined);
  const [accumulated, setAccumulated] = useState<Booking[]>([]);

  const eventTypesQuery = useEventTypesList({ limit: 100 });
  const eventTypes = eventTypesQuery.data?.data.items ?? [];

  const listQuery = useBookingsList({
    limit: 20,
    cursor,
    status,
    eventTypeId,
  });

  const data = listQuery.data?.data;
  const currentItems = cursor ? accumulated : data?.items ?? [];
  const nextCursor = data?.nextCursor;

  const cancelMutation = useBookingsCancel({
    mutation: {
      onSuccess: () => {
        notifications.show({
          title: "Отменено",
          message: "Бронирование отменено",
          color: "green",
        });
        queryClient.invalidateQueries({
          queryKey: getBookingsListQueryKey(),
        });
        setAccumulated([]);
        setCursor(undefined);
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

  if (listQuery.isLoading && !cursor)
    return <LoadingState message="Загрузка бронирований…" />;
  if (listQuery.isError && !cursor)
    return (
      <ErrorState
        message="Не удалось загрузить бронирования"
        onRetry={() => listQuery.refetch()}
      />
    );

  const tz = getLocalTimezone();

  return (
    <Stack gap="lg">
      <Stack gap={2}>
        <Title order={2}>Бронирования</Title>
        <Text size="sm" c="dimmed">
          Все бронирования ваших типов событий
        </Text>
      </Stack>

      <Group gap="sm">
        <Select
          placeholder="Статус"
          clearable
          data={STATUS_OPTIONS}
          w={180}
          value={status ?? null}
          onChange={(v) => {
            setStatus((v as BookingStatus) ?? undefined);
            setAccumulated([]);
            setCursor(undefined);
          }}
        />
        <Select
          placeholder="Тип события"
          clearable
          searchable
          data={eventTypes.map((e) => ({ value: e.id, label: e.title }))}
          w={240}
          value={eventTypeId ?? null}
          onChange={(v) => {
            setEventTypeId(v ?? undefined);
            setAccumulated([]);
            setCursor(undefined);
          }}
        />
      </Group>

      {currentItems.length === 0 ? (
        <EmptyState
          title="Нет бронирований"
          description="Здесь появятся бронирования, когда гости начнут их создавать"
        />
      ) : (
        <Stack gap="sm">
          {currentItems.map((b) => {
            const eventType = eventTypes.find((e) => e.id === b.eventTypeId);
            return (
              <Card key={b.id} withBorder padding="md">
                <Group justify="space-between" align="flex-start">
                  <Stack gap={4} style={{ flex: 1, minWidth: 0 }}>
                    <Group gap="sm">
                      <Text fw={600}>
                        {eventType?.title ?? "Тип события удалён"}
                      </Text>
                      <BookingStatusBadge status={b.status} />
                    </Group>
                    <Text size="sm">
                      {formatDateTime(b.startUtc, tz)}
                    </Text>
                    <Text size="xs" c="dimmed">
                      {b.attendee.name} · {b.attendee.email}
                    </Text>
                  </Stack>
                  <Group gap="xs">
                    <Button
                      variant="subtle"
                      size="xs"
                      rightSection={<IconChevronRight size={14} />}
                      onClick={() => navigate(`/bookings/${b.id}`)}
                    >
                      Открыть
                    </Button>
                    {b.status !== "cancelled" && (
                      <ConfirmDialog
                        trigger={
                          <Button variant="light" color="red" size="xs">
                            Отменить
                          </Button>
                        }
                        title="Отменить бронирование?"
                        message="Встреча будет отменена. Гость получит уведомление."
                        confirmLabel="Отменить встречу"
                        loading={cancelMutation.isPending}
                        onConfirm={() => cancelMutation.mutate({ id: b.id })}
                      />
                    )}
                  </Group>
                </Group>
              </Card>
            );
          })}
          <Pagination
            nextCursor={nextCursor}
            isLoading={listQuery.isFetching}
            onLoadMore={(c) => {
              setAccumulated([...currentItems]);
              setCursor(c);
            }}
          />
        </Stack>
      )}
    </Stack>
  );
}
