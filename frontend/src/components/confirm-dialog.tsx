import {
  Modal,
  Stack,
  Text,
  Button,
  Group,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";

interface ConfirmDialogProps {
  trigger: React.ReactNode;
  title?: string;
  message?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm: () => void | Promise<void>;
  loading?: boolean;
  color?: string;
}

export function ConfirmDialog({
  trigger,
  title = "Подтвердите действие",
  message,
  confirmLabel = "Подтвердить",
  cancelLabel = "Отмена",
  onConfirm,
  loading,
  color = "red",
}: ConfirmDialogProps) {
  const [opened, { open, close }] = useDisclosure(false);

  return (
    <>
      <span onClick={open} style={{ display: "inline-flex" }}>
        {trigger}
      </span>
      <Modal opened={opened} onClose={close} title={title} centered>
        <Stack>
          {message && <Text size="sm">{message}</Text>}
          <Group justify="flex-end">
            <Button variant="default" onClick={close} disabled={loading}>
              {cancelLabel}
            </Button>
            <Button
              color={color}
              loading={loading}
              onClick={async () => {
                await onConfirm();
                close();
              }}
            >
              {confirmLabel}
            </Button>
          </Group>
        </Stack>
      </Modal>
    </>
  );
}
