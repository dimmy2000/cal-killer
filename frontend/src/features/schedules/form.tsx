import { useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  Stack,
  Title,
  Text,
  TextInput,
  Select,
  Switch,
  Button,
  Group,
  Card,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import { notifications } from "@mantine/notifications";
import { useQueryClient } from "@tanstack/react-query";
import {
  useSchedulesCreate,
  useSchedulesUpdate,
  useSchedulesRead,
  getSchedulesListQueryKey,
  getSchedulesReadQueryKey,
} from "@/api/generated/schedules/schedules";
import type {
  ScheduleCreate,
  ScheduleUpdate,
  WorkingHours,
  ScheduleOverride,
} from "@/api/generated/models";
import { LoadingState } from "@/components/loading-state";
import { ErrorState } from "@/components/error-state";
import { WorkingHoursEditor } from "./working-hours-editor";
import { OverridesEditor } from "./overrides-editor";
import { getLocalTimezone } from "@/lib/dayjs";

interface FormValues {
  name: string;
  timezone: string;
  isDefault: boolean;
  workingHours: WorkingHours[];
  overrides: ScheduleOverride[];
}

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
  "Europe/Paris",
  "America/New_York",
  "America/Los_Angeles",
];

export function ScheduleFormPage() {
  const navigate = useNavigate();
  const params = useParams();
  const id = params.id;
  const isEdit = Boolean(id);
  const queryClient = useQueryClient();

  const readQuery = useSchedulesRead(id ?? "", {
    query: { enabled: isEdit },
  });

  const form = useForm<FormValues>({
    initialValues: {
      name: "",
      timezone: getLocalTimezone(),
      isDefault: false,
      workingHours: [
        { dayOfWeek: 1, startMin: 9 * 60, endMin: 18 * 60 },
        { dayOfWeek: 2, startMin: 9 * 60, endMin: 18 * 60 },
        { dayOfWeek: 3, startMin: 9 * 60, endMin: 18 * 60 },
        { dayOfWeek: 4, startMin: 9 * 60, endMin: 18 * 60 },
        { dayOfWeek: 5, startMin: 9 * 60, endMin: 18 * 60 },
      ],
      overrides: [],
    },
    validate: {
      name: (v) => (v.trim().length >= 1 ? null : "Введите название"),
      timezone: (v) => (v ? null : "Выберите часовой пояс"),
      workingHours: (v) =>
        v.length > 0 ? null : "Укажите хотя бы один рабочий день",
    },
  });

  const schedule = readQuery.data?.data;
  useEffect(() => {
    if (isEdit && schedule) {
      form.setValues({
        name: schedule.name,
        timezone: schedule.timezone,
        isDefault: schedule.isDefault,
        workingHours: schedule.workingHours,
        overrides: schedule.overrides,
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [schedule]);

  const createMutation = useSchedulesCreate({
    mutation: {
      onSuccess: () => {
        notifications.show({
          title: "Создано",
          message: "Расписание создано",
          color: "green",
        });
        queryClient.invalidateQueries({
          queryKey: getSchedulesListQueryKey(),
        });
        navigate("/schedules");
      },
      onError: (err: unknown) => {
        notifications.show({
          title: "Ошибка",
          message: err instanceof Error ? err.message : "Не удалось создать",
          color: "red",
        });
      },
    },
  });

  const updateMutation = useSchedulesUpdate({
    mutation: {
      onSuccess: () => {
        notifications.show({
          title: "Сохранено",
          message: "Расписание обновлено",
          color: "green",
        });
        queryClient.invalidateQueries({
          queryKey: getSchedulesListQueryKey(),
        });
        if (id)
          queryClient.invalidateQueries({
            queryKey: getSchedulesReadQueryKey(id),
          });
        navigate("/schedules");
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

  if (isEdit) {
    if (readQuery.isLoading) return <LoadingState />;
    if (readQuery.isError)
      return (
        <ErrorState
          message="Не удалось загрузить расписание"
          onRetry={() => readQuery.refetch()}
        />
      );
  }

  const onSubmit = form.onSubmit((values) => {
    if (isEdit) {
      const payload: ScheduleUpdate = {
        name: values.name,
        timezone: values.timezone,
        isDefault: values.isDefault,
        workingHours: values.workingHours,
      };
      updateMutation.mutate({ id: id!, data: payload });
    } else {
      const payload: ScheduleCreate = {
        name: values.name,
        timezone: values.timezone,
        isDefault: values.isDefault,
        workingHours: values.workingHours,
        overrides: values.overrides,
      };
      createMutation.mutate({ data: payload });
    }
  });

  const isPending = createMutation.isPending || updateMutation.isPending;

  return (
    <Stack gap="lg" maw={760}>
      <Stack gap={2}>
        <Title order={2}>
          {isEdit ? "Редактировать расписание" : "Новое расписание"}
        </Title>
        <Text size="sm" c="dimmed">
          Настройте рабочие часы и исключения
        </Text>
      </Stack>

      <form onSubmit={onSubmit}>
        <Stack gap="md">
          <Card withBorder padding="lg">
            <Stack gap="md">
              <Group grow>
                <TextInput
                  label="Название"
                  placeholder="Основное рабочее время"
                  key={form.key("name")}
                  {...form.getInputProps("name")}
                />
                <Select
                  label="Часовой пояс"
                  data={COMMON_TZ}
                  searchable
                  key={form.key("timezone")}
                  {...form.getInputProps("timezone")}
                />
              </Group>
              <Switch
                label="По умолчанию"
                description="Используется для новых типов событий"
                key={form.key("isDefault")}
                {...form.getInputProps("isDefault", { type: "checkbox" })}
              />
            </Stack>
          </Card>

          <Card withBorder padding="lg">
            <Stack gap="md">
              <Text fw={500}>Рабочие часы</Text>
              <WorkingHoursEditor
                value={form.values.workingHours}
                onChange={(next) =>
                  form.setFieldValue("workingHours", next)
                }
              />
            </Stack>
          </Card>

          {isEdit && (
            <Card withBorder padding="lg">
              <Stack gap="md">
                <Text fw={500}>Исключения</Text>
                <Text size="xs" c="dimmed">
                  Переопределяют доступность на конкретные даты. Внимание: при сохранении исключения отправляются отдельными запросами.
                </Text>
                <OverridesEditor
                  value={form.values.overrides}
                  onChange={(next) =>
                    form.setFieldValue("overrides", next)
                  }
                />
              </Stack>
            </Card>
          )}

          <Group justify="flex-end">
            <Button variant="default" onClick={() => navigate("/schedules")}>
              Отмена
            </Button>
            <Button type="submit" loading={isPending}>
              {isEdit ? "Сохранить" : "Создать"}
            </Button>
          </Group>
        </Stack>
      </form>
    </Stack>
  );
}
