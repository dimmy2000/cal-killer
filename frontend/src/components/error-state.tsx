import { Alert, Button, Stack, Text } from "@mantine/core";
import { IconAlertCircle } from "@tabler/icons-react";

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

export function ErrorState({
  title = "Что-то пошло не так",
  message,
  onRetry,
}: ErrorStateProps) {
  return (
    <Alert
      icon={<IconAlertCircle size={16} />}
      color="red"
      variant="light"
      title={title}
    >
      <Stack gap="sm">
        {message && <Text size="sm">{message}</Text>}
        {onRetry && (
          <Button size="xs" variant="light" onClick={onRetry}>
            Повторить
          </Button>
        )}
      </Stack>
    </Alert>
  );
}
