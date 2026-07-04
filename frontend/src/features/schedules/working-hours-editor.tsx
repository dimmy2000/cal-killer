import {
  Stack,
  Group,
  Text,
  Switch,
  Box,
} from "@mantine/core";
import { TimeInput } from "@mantine/dates";
import type { WorkingHours, DayOfWeek } from "@/api/generated/models";

const DAY_LABELS: { value: DayOfWeek; label: string }[] = [
  { value: 1, label: "Понедельник" },
  { value: 2, label: "Вторник" },
  { value: 3, label: "Среда" },
  { value: 4, label: "Четверг" },
  { value: 5, label: "Пятница" },
  { value: 6, label: "Суббота" },
  { value: 0, label: "Воскресенье" },
];

interface WorkingHoursEditorProps {
  value: WorkingHours[];
  onChange: (next: WorkingHours[]) => void;
}

function minutesToTimeInput(min: number): string {
  const h = Math.floor(min / 60);
  const m = min % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
}

function timeInputToMinutes(time: string): number {
  const [h, m] = time.split(":").map(Number);
  return h * 60 + (m || 0);
}

export function WorkingHoursEditor({ value, onChange }: WorkingHoursEditorProps) {
  const toggleDay = (day: DayOfWeek, enabled: boolean) => {
    if (enabled) {
      onChange([
        ...value,
        { dayOfWeek: day, startMin: 9 * 60, endMin: 18 * 60 },
      ]);
    } else {
      onChange(value.filter((w) => w.dayOfWeek !== day));
    }
  };

  const updateHours = (day: DayOfWeek, patch: Partial<WorkingHours>) => {
    onChange(
      value.map((w) => (w.dayOfWeek === day ? { ...w, ...patch } : w)),
    );
  };

  return (
    <Stack gap="xs">
      {DAY_LABELS.map(({ value: day, label }) => {
        const wh = value.find((w) => w.dayOfWeek === day);
        const enabled = Boolean(wh);
        return (
          <Group key={day} align="center" gap="md" wrap="nowrap">
            <Switch
              checked={enabled}
              onChange={(e) => toggleDay(day, e.currentTarget.checked)}
              aria-label={label}
            />
            <Box style={{ width: 140 }}>
              <Text size="sm" c={enabled ? undefined : "dimmed"}>
                {label}
              </Text>
            </Box>
            <TimeInput
              value={wh ? minutesToTimeInput(wh.startMin) : "09:00"}
              disabled={!enabled}
              onChange={(e) =>
                updateHours(day, {
                  startMin: timeInputToMinutes(e.currentTarget.value),
                })
              }
              withSeconds={false}
            />
            <Text c="dimmed">—</Text>
            <TimeInput
              value={wh ? minutesToTimeInput(wh.endMin) : "18:00"}
              disabled={!enabled}
              onChange={(e) =>
                updateHours(day, {
                  endMin: timeInputToMinutes(e.currentTarget.value),
                })
              }
              withSeconds={false}
            />
          </Group>
        );
      })}
    </Stack>
  );
}
