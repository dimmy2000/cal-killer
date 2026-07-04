import { Button, Stack, Text } from "@mantine/core";
import { IconCalendarOff } from "@tabler/icons-react";

interface EmptyStateProps {
  title?: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  icon?: React.ReactNode;
}

export function EmptyState({
  title = "Пока пусто",
  description,
  actionLabel,
  onAction,
  icon,
}: EmptyStateProps) {
  return (
    <Stack align="center" justify="center" gap="md" py={48}>
      {icon ?? <IconCalendarOff size={48} stroke={1.2} />}
      <Stack align="center" gap={4}>
        <Text fw={500}>{title}</Text>
        {description && (
          <Text size="sm" c="dimmed" maw={400} ta="center">
            {description}
          </Text>
        )}
      </Stack>
      {actionLabel && onAction && (
        <Button onClick={onAction}>{actionLabel}</Button>
      )}
    </Stack>
  );
}
