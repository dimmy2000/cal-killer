import { Button, Group, Text } from "@mantine/core";

interface PaginationProps {
  nextCursor?: string;
  onLoadMore: (cursor: string) => void;
  isLoading?: boolean;
}

export function Pagination({
  nextCursor,
  onLoadMore,
  isLoading,
}: PaginationProps) {
  if (!nextCursor) {
    return (
      <Text size="sm" c="dimmed" ta="center" py="md">
        Это все результаты
      </Text>
    );
  }

  return (
    <Group justify="center" py="md">
      <Button
        variant="light"
        loading={isLoading}
        onClick={() => onLoadMore(nextCursor)}
      >
        Загрузить ещё
      </Button>
    </Group>
  );
}
