import { Center, Loader, Stack, Text } from "@mantine/core";

export function LoadingState({ message }: { message?: string }) {
  return (
    <Center h={300}>
      <Stack align="center" gap="xs">
        <Loader size="lg" />
        {message && (
          <Text size="sm" c="dimmed">
            {message}
          </Text>
        )}
      </Stack>
    </Center>
  );
}
