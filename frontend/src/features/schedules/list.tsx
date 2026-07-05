import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Stack,
  Title,
  Button,
  Group,
  Card,
  Text,
  ActionIcon,
  Menu,
  Divider,
  Badge,
} from "@mantine/core";
import { useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";
import {
  IconPlus,
  IconDots,
  IconPencil,
  IconTrash,
} from "@tabler/icons-react";
import type { Schedule } from "@/api/generated/models";
import {
  useSchedulesList,
  useSchedulesDelete,
  getSchedulesListQueryKey,
} from "@/api/generated/schedules/schedules";
import { EmptyState } from "@/components/empty-state";
import { LoadingState } from "@/components/loading-state";
import { ErrorState } from "@/components/error-state";
import { Pagination } from "@/components/pagination";
import { ConfirmDialog } from "@/components/confirm-dialog";

const DAY_LABELS = ["Вс", "Пн", "Вт", "Ср", "Чт", "Пт", "Сб"];

export function SchedulesListPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [cursor, setCursor] = useState<string | undefined>(undefined);
  const [accumulated, setAccumulated] = useState<Schedule[]>([]);

  const listQuery = useSchedulesList({ limit: 20, cursor });
  const data = listQuery.data?.data;
  const currentItems = cursor ? accumulated : data?.items ?? [];
  const nextCursor = data?.nextCursor;

  const deleteMutation = useSchedulesDelete({
    mutation: {
      onSuccess: () => {
        notifications.show({
          title: "Удалено",
          message: "Расписание удалено",
          color: "green",
        });
        queryClient.invalidateQueries({
          queryKey: getSchedulesListQueryKey(),
        });
        setAccumulated([]);
        setCursor(undefined);
      },
      onError: (err: unknown) => {
        notifications.show({
          title: "Ошибка",
          message: err instanceof Error ? err.message : "Не удалось удалить",
          color: "red",
        });
      },
    },
  });

  if (listQuery.isLoading && !cursor)
    return <LoadingState message="Загрузка расписаний…" />;
  if (listQuery.isError && !cursor)
    return (
      <ErrorState
        message="Не удалось загрузить расписания"
        onRetry={() => listQuery.refetch()}
      />
    );

  return (
    <Stack gap="lg">
      <Group justify="space-between">
        <Stack gap={2}>
          <Title order={2}>Расписания</Title>
          <Text size="sm" c="dimmed">
            Настройте рабочие часы и исключения для доступности
          </Text>
        </Stack>
        <Button
          leftSection={<IconPlus size={16} />}
          onClick={() => navigate("/schedules/new")}
        >
          Создать
        </Button>
      </Group>

      {currentItems.length === 0 ? (
        <EmptyState
          title="Нет расписаний"
          description="Создайте первое расписание с рабочими часами"
          actionLabel="Создать расписание"
          onAction={() => navigate("/schedules/new")}
        />
      ) : (
        <Stack gap="sm">
          {currentItems.map((s) => (
            <Card key={s.id} withBorder padding="md">
              <Group justify="space-between" align="flex-start">
                <Stack gap="xs" style={{ flex: 1, minWidth: 0 }}>
                  <Group gap="sm">
                    <Text fw={600}>{s.name}</Text>
                  </Group>
                  <Text size="sm" c="dimmed">
                    Часовой пояс: {s.timezone}
                  </Text>
                  <Group gap={6}>
                    {DAY_LABELS.map((d, idx) => {
                      const wh = s.workingHours.find(
                        (w) => w.dayOfWeek === idx,
                      );
                      return (
                        <Badge
                          key={d}
                          size="sm"
                          variant={wh ? "light" : "default"}
                          color={wh ? "brand" : "gray"}
                        >
                          {d}
                        </Badge>
                      );
                    })}
                  </Group>
                  {s.overrides.length > 0 && (
                    <Text size="xs" c="dimmed">
                      Исключений: {s.overrides.length}
                    </Text>
                  )}
                </Stack>
                <Menu position="bottom-end">
                  <Menu.Target>
                    <ActionIcon variant="subtle">
                      <IconDots size={16} />
                    </ActionIcon>
                  </Menu.Target>
                  <Menu.Dropdown>
                    <Menu.Item
                      leftSection={<IconPencil size={14} />}
                      onClick={() => navigate(`/schedules/${s.id}/edit`)}
                    >
                      Редактировать
                    </Menu.Item>
                    <Divider />
                    <ConfirmDialog
                      trigger={
                        <Menu.Item
                          color="red"
                          leftSection={<IconTrash size={14} />}
                          component="div"
                        >
                          Удалить
                        </Menu.Item>
                      }
                      title="Удалить расписание?"
                      message={`«${s.name}» будет удалено безвозвратно.`}
                      confirmLabel="Удалить"
                      loading={deleteMutation.isPending}
                      onConfirm={() => deleteMutation.mutate({ id: s.id })}
                    />
                  </Menu.Dropdown>
                </Menu>
              </Group>
            </Card>
          ))}
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
