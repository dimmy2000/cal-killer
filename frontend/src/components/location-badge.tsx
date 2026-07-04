import { Badge } from "@mantine/core";
import {
  IconDeviceDesktop,
  IconMapPin,
  IconPhone,
} from "@tabler/icons-react";
import type { EventLocation } from "@/api/generated/models";

const LOCATION_CONFIG: Record<
  EventLocation,
  { label: string; icon: React.ReactNode }
> = {
  online: { label: "Онлайн", icon: <IconDeviceDesktop size={14} /> },
  in_person: { label: "Лично", icon: <IconMapPin size={14} /> },
  phone: { label: "Телефон", icon: <IconPhone size={14} /> },
};

export function LocationBadge({ location }: { location: EventLocation }) {
  const config = LOCATION_CONFIG[location];
  return (
    <Badge variant="light" leftSection={config.icon}>
      {config.label}
    </Badge>
  );
}
