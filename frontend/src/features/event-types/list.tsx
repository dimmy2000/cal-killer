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
  CopyButton,
  Tooltip,
  Menu,
  Divider,
  Box,
  Badge,
} from "@mantine/core";
import { useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";
import {
  IconPlus,
  IconDots,
  IconPencil,
  IconTrash,
  IconLink,
  IconCheck,
  IconCopy,
} from "@tabler/icons-react";
import type { EventType } from "@/api/generated/models";
import { useAuth } from "@/auth/auth-context";
import {
  useEventTypesList,
  useEventTypesDelete,
  getEventTypesListQueryKey,
} from "@/api/generated/event-types/event-types";
import { LocationBadge } from "@/components/location-badge";
import { EmptyState } from "@/components/empty-state";
import { LoadingState } from "@/components/loading-state";
import { ErrorState } from "@/components/error-state";
import { Pagination } from "@/components/pagination";
import { ConfirmDialog } from "@/components/confirm-dialog";
import { formatDuration } from "@/lib/dayjs";

const PAGE_SIZE = 20;

export function EventTypesListPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [cursor, setCursor] = useState<string | undefined>(undefined);
  const [accumulated, setAccumulated] = useState<EventType[]>([]);

  const listQuery = useEventTypesList({ limit: PAGE_SIZE, cursor });

  const data = listQuery.data?.data;
  const currentItems = cursor ? accumulated : data?.items ?? [];
  const nextCursor = data?.nextCursor;

  const deleteMutation = useEventTypesDelete({
    mutation: {
      onSuccess: () => {
        notifications.show({
          title: "Удалено",
          message: "Тип события удалён",
          color: "green",
        });
        queryClient.invalidateQueries({
          queryKey: getEventTypesListQueryKey(),
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

  const publicLink = (slug: string) =>
    `${window.location.origin}/${user?.username ?? ""}/${slug}`;

  if (listQuery.isLoading && !cursor)
    return <LoadingState message="Загрузка типов событий…" />;
  if (listQuery.isError && !cursor)
    return (
      <ErrorState
        message="Не удалось загрузить типы событий"
        onRetry={() => listQuery.refetch()}
      />
    );

  return (
    <Stack gap="lg">
      <Group justify="space-between">
        <Stack gap={2}>
          <Title order={2}>Типы событий</Title>
          <Text size="sm" c="dimmed">
            Создавайте бронируемые события и делитесь публичными ссылками
          </Text>
        </Stack>
        <Button
          leftSection={<IconPlus size={16} />}
          onClick={() => navigate("/event-types/new")}
        >
          Создать
        </Button>
      </Group>

      {currentItems.length === 0 ? (
        <EmptyState
          title="Нет типов событий"
          description="Создайте первый тип события, чтобы начать принимать бронирования"
          actionLabel="Создать тип события"
          onAction={() => navigate("/event-types/new")}
        />
      ) : (
        <Stack gap="sm">
          {currentItems.map((et) => (
            <Card key={et.id} withBorder padding="md">
              <Group justify="space-between" align="flex-start">
                <Stack gap="xs" style={{ flex: 1, minWidth: 0 }}>
                  <Group gap="sm">
                    <Box
                      style={{
                        width: 12,
                        height: 12,
                        borderRadius: 3,
                        background:
                          et.color ?? "var(--mantine-color-brand-filled)",
                      }}
                    />
                    <Text fw={600} truncate>
                      {et.title}
                    </Text>
                    <LocationBadge location={et.location} />
                    <Badge>{formatDuration(et.durationMin)}</Badge>
                  </Group>
                  {et.description && (
                    <Text size="sm" c="dimmed" lineClamp={2}>
                      {et.description}
                    </Text>
                  )}
                  <Group gap="xs">
                    <Text size="xs" c="dimmed">
                      Публичная ссылка:
                    </Text>
                    <Text size="xs" c="brand" truncate>
                      {publicLink(et.slug)}
                    </Text>
                    <CopyButton value={publicLink(et.slug)} timeout={2000}>
                      {({ copied, copy }) => (
                        <Tooltip label={copied ? "Скопировано" : "Копировать"}>
                          <ActionIcon
                            size="xs"
                            color={copied ? "teal" : "gray"}
                            onClick={copy}
                          >
                            {copied ? (
                              <IconCheck size={12} />
                            ) : (
                              <IconCopy size={12} />
                            )}
                          </ActionIcon>
                        </Tooltip>
                      )}
                    </CopyButton>
                  </Group>
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
                      onClick={() => navigate(`/event-types/${et.id}/edit`)}
                    >
                      Редактировать
                    </Menu.Item>
                    <Menu.Item
                      leftSection={<IconLink size={14} />}
                      onClick={() => window.open(publicLink(et.slug), "_blank")}
                    >
                      Открыть публичную страницу
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
                      title="Удалить тип события?"
                      message={`«${et.title}» будет удалён безвозвратно. Связанные бронирования останутся в истории.`}
                      confirmLabel="Удалить"
                      loading={deleteMutation.isPending}
                      onConfirm={() => deleteMutation.mutate({ id: et.id })}
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
