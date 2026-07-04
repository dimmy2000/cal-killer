import { Badge } from "@mantine/core";
import type { BookingStatus } from "@/api/generated/models";

const STATUS_CONFIG: Record<
  BookingStatus,
  { color: string; label: string }
> = {
  pending: { color: "yellow", label: "Ожидает" },
  confirmed: { color: "green", label: "Подтверждено" },
  cancelled: { color: "red", label: "Отменено" },
  rescheduled: { color: "blue", label: "Перенесено" },
};

export function BookingStatusBadge({ status }: { status: BookingStatus }) {
  const config = STATUS_CONFIG[status];
  return (
    <Badge color={config.color} variant="light">
      {config.label}
    </Badge>
  );
}
