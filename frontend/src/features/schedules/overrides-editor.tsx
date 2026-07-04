import {
  Stack,
  Group,
  Text,
  Button,
  ActionIcon,
  Checkbox,
} from "@mantine/core";
import { IconTrash } from "@tabler/icons-react";
import { DateInput, TimeInput } from "@mantine/dates";
import type { ScheduleOverride } from "@/api/generated/models";

interface OverridesEditorProps {
  value: ScheduleOverride[];
  onChange: (next: ScheduleOverride[]) => void;
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

function toDate(plain: string): Date {
  return new Date(`${plain}T00:00:00`);
}

function toPlainDate(date: Date | null): string {
  if (!date) return "";
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

export function OverridesEditor({ value, onChange }: OverridesEditorProps) {
  const add = () => {
    onChange([
      ...value,
      {
        date: toPlainDate(new Date()),
        startMin: 9 * 60,
        endMin: 18 * 60,
        available: false,
      },
    ]);
  };

  const update = (idx: number, patch: Partial<ScheduleOverride>) => {
    onChange(value.map((o, i) => (i === idx ? { ...o, ...patch } : o)));
  };

  const remove = (idx: number) => {
    onChange(value.filter((_, i) => i !== idx));
  };

  return (
    <Stack gap="sm">
      {value.length === 0 && (
        <Text size="sm" c="dimmed">
          Нет исключений. Добавьте, чтобы переопределить доступность на конкретную дату.
        </Text>
      )}
      {value.map((o, idx) => (
        <Group key={idx} align="center" gap="sm" wrap="nowrap">
          <DateInput
            value={toDate(o.date)}
            valueFormat="YYYY-MM-DD"
            onChange={(d) => update(idx, { date: toPlainDate(d) })}
            maw={170}
          />
          <TimeInput
            value={minutesToTimeInput(o.startMin)}
            onChange={(e) =>
              update(idx, { startMin: timeInputToMinutes(e.currentTarget.value) })
            }
            withSeconds={false}
          />
          <Text c="dimmed">—</Text>
          <TimeInput
            value={minutesToTimeInput(o.endMin)}
            onChange={(e) =>
              update(idx, { endMin: timeInputToMinutes(e.currentTarget.value) })
            }
            withSeconds={false}
          />
          <Checkbox
            label="Доступен"
            checked={o.available}
            onChange={(e) => update(idx, { available: e.currentTarget.checked })}
          />
          <ActionIcon color="red" variant="subtle" onClick={() => remove(idx)}>
            <IconTrash size={16} />
          </ActionIcon>
        </Group>
      ))}
      <Button variant="light" size="xs" onClick={add} maw={200}>
        Добавить исключение
      </Button>
    </Stack>
  );
}
