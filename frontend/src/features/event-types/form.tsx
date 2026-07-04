import { useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  Stack,
  Title,
  Text,
  TextInput,
  Textarea,
  NumberInput,
  Select,
  ColorInput,
  Switch,
  Button,
  Group,
  Card,
  Divider,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import { notifications } from "@mantine/notifications";
import { useQueryClient } from "@tanstack/react-query";
import {
  useEventTypesCreate,
  useEventTypesUpdate,
  useEventTypesRead,
  getEventTypesListQueryKey,
  getEventTypesReadQueryKey,
} from "@/api/generated/event-types/event-types";
import { useSchedulesList } from "@/api/generated/schedules/schedules";
import type {
  EventTypeCreate,
  EventTypeUpdate,
  EventLocation,
} from "@/api/generated/models";
import { LoadingState } from "@/components/loading-state";
import { ErrorState } from "@/components/error-state";

const LOCATION_OPTIONS: { value: EventLocation; label: string }[] = [
  { value: "online", label: "Онлайн" },
  { value: "in_person", label: "Лично" },
  { value: "phone", label: "Телефон" },
];

interface FormValues {
  slug: string;
  title: string;
  description: string;
  durationMin: number;
  location: EventLocation;
  color: string;
  scheduleId: string;
  paddingMinBefore: number;
  paddingMinAfter: number;
  minNoticeMin: number;
  requiresConfirmation: boolean;
}

const DEFAULT_VALUES: FormValues = {
  slug: "",
  title: "",
  description: "",
  durationMin: 30,
  location: "online",
  color: "#1a8eff",
  scheduleId: "",
  paddingMinBefore: 0,
  paddingMinAfter: 0,
  minNoticeMin: 60,
  requiresConfirmation: false,
};

export function EventTypeFormPage() {
  const navigate = useNavigate();
  const params = useParams();
  const id = params.id;
  const isEdit = Boolean(id);
  const queryClient = useQueryClient();

  const schedulesQuery = useSchedulesList({ limit: 100 });
  const readQuery = useEventTypesRead(id ?? "", {
    query: { enabled: isEdit },
  });

  const form = useForm<FormValues>({
    initialValues: DEFAULT_VALUES,
    validate: {
      slug: (v) =>
        /^[a-z0-9_-]{3,64}$/i.test(v) ? null : "Латиница, цифры, _ или -, 3–64",
      title: (v) => (v.trim().length >= 1 ? null : "Введите название"),
      durationMin: (v) => (v > 0 ? null : "Длительность должна быть больше 0"),
      scheduleId: (v) => (v ? null : "Выберите расписание"),
    },
  });

  const et = readQuery.data?.data;
  useEffect(() => {
    if (isEdit && et) {
      form.setValues({
        slug: et.slug,
        title: et.title,
        description: et.description ?? "",
        durationMin: et.durationMin,
        location: et.location,
        color: et.color ?? "#1a8eff",
        scheduleId: et.scheduleId,
        paddingMinBefore: et.paddingMinBefore,
        paddingMinAfter: et.paddingMinAfter,
        minNoticeMin: et.minNoticeMin,
        requiresConfirmation: et.requiresConfirmation,
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [et]);

  const schedules = schedulesQuery.data?.data.items ?? [];
  useEffect(() => {
    if (!isEdit && schedules.length > 0 && !form.values.scheduleId) {
      form.setFieldValue("scheduleId", schedules[0].id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [schedules]);

  const createMutation = useEventTypesCreate({
    mutation: {
      onSuccess: () => {
        notifications.show({
          title: "Создано",
          message: "Тип события создан",
          color: "green",
        });
        queryClient.invalidateQueries({
          queryKey: getEventTypesListQueryKey(),
        });
        navigate("/event-types");
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

  const updateMutation = useEventTypesUpdate({
    mutation: {
      onSuccess: () => {
        notifications.show({
          title: "Сохранено",
          message: "Тип события обновлён",
          color: "green",
        });
        queryClient.invalidateQueries({
          queryKey: getEventTypesListQueryKey(),
        });
        if (id)
          queryClient.invalidateQueries({
            queryKey: getEventTypesReadQueryKey(id),
          });
        navigate("/event-types");
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

  if (schedulesQuery.isLoading) return <LoadingState />;
  if (schedulesQuery.isError)
    return (
      <ErrorState
        message="Не удалось загрузить расписания"
        onRetry={() => schedulesQuery.refetch()}
      />
    );

  if (isEdit) {
    if (readQuery.isLoading) return <LoadingState />;
    if (readQuery.isError)
      return (
        <ErrorState
          message="Не удалось загрузить тип события"
          onRetry={() => readQuery.refetch()}
        />
      );
  }

  if (schedules.length === 0) {
    return (
      <ErrorState
        title="Нет расписаний"
        message="Сначала создайте хотя бы одно расписание, чтобы привязать к нему тип события."
      />
    );
  }

  const onSubmit = form.onSubmit((values) => {
    const payload: EventTypeCreate | EventTypeUpdate = {
      slug: values.slug,
      title: values.title,
      description: values.description || undefined,
      durationMin: values.durationMin,
      location: values.location,
      color: values.color,
      scheduleId: values.scheduleId,
      paddingMinBefore: values.paddingMinBefore,
      paddingMinAfter: values.paddingMinAfter,
      minNoticeMin: values.minNoticeMin,
      requiresConfirmation: values.requiresConfirmation,
    };
    if (isEdit) {
      updateMutation.mutate({ id: id!, data: payload as EventTypeUpdate });
    } else {
      createMutation.mutate({ data: payload as EventTypeCreate });
    }
  });

  const isPending = createMutation.isPending || updateMutation.isPending;

  return (
    <Stack gap="lg" maw={680}>
      <Stack gap={2}>
        <Title order={2}>
          {isEdit ? "Редактировать тип события" : "Новый тип события"}
        </Title>
        <Text size="sm" c="dimmed">
          Настройте параметры бронируемого события
        </Text>
      </Stack>

      <form onSubmit={onSubmit}>
        <Card withBorder padding="lg">
          <Stack gap="md">
            <TextInput
              label="Название"
              placeholder="Знакомство с продуктом"
              key={form.key("title")}
              {...form.getInputProps("title")}
            />
            <TextInput
              label="Slug"
              placeholder="intro-call"
              description="Используется в публичной ссылке"
              key={form.key("slug")}
              {...form.getInputProps("slug")}
            />
            <Textarea
              label="Описание"
              placeholder="Короткое описание встречи"
              autosize
              minRows={2}
              key={form.key("description")}
              {...form.getInputProps("description")}
            />

            <Divider label="Параметры" labelPosition="left" />

            <Group grow>
              <NumberInput
                label="Длительность, мин"
                min={5}
                step={5}
                key={form.key("durationMin")}
                {...form.getInputProps("durationMin")}
              />
              <Select
                label="Локация"
                data={LOCATION_OPTIONS}
                key={form.key("location")}
                {...form.getInputProps("location")}
              />
            </Group>

            <Group grow>
              <ColorInput
                label="Цвет"
                format="hex"
                key={form.key("color")}
                {...form.getInputProps("color")}
              />
              <Select
                label="Расписание"
                placeholder="Выберите расписание"
                data={schedules.map((s) => ({
                  value: s.id,
                  label: s.name,
                }))}
                key={form.key("scheduleId")}
                {...form.getInputProps("scheduleId")}
              />
            </Group>

            <Divider label="Дополнительно" labelPosition="left" />

            <Group grow>
              <NumberInput
                label="Отступ до, мин"
                min={0}
                step={5}
                key={form.key("paddingMinBefore")}
                {...form.getInputProps("paddingMinBefore")}
              />
              <NumberInput
                label="Отступ после, мин"
                min={0}
                step={5}
                key={form.key("paddingMinAfter")}
                {...form.getInputProps("paddingMinAfter")}
              />
            </Group>

            <Group grow>
              <NumberInput
                label="Минимум до встречи, мин"
                description="За сколько минут можно забронировать"
                min={0}
                step={15}
                key={form.key("minNoticeMin")}
                {...form.getInputProps("minNoticeMin")}
              />
              <Switch
                label="Требует подтверждения"
                description="Бронь будет в статусе pending"
                mt={22}
                key={form.key("requiresConfirmation")}
                {...form.getInputProps("requiresConfirmation", {
                  type: "checkbox",
                })}
              />
            </Group>

            <Group justify="flex-end" mt="sm">
              <Button
                variant="default"
                onClick={() => navigate("/event-types")}
              >
                Отмена
              </Button>
              <Button type="submit" loading={isPending}>
                {isEdit ? "Сохранить" : "Создать"}
              </Button>
            </Group>
          </Stack>
        </Card>
      </form>
    </Stack>
  );
}
