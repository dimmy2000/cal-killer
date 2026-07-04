import { Container, Title, Anchor, Stack } from "@mantine/core";
import { Link, Outlet } from "react-router-dom";

export function PublicLayout({ children }: { children?: React.ReactNode }) {
  return (
    <Container size="md" py="xl">
      <Stack align="center" gap="xl">
        <Anchor component={Link} to="/">
          <Title order={3} c="brand">
            Cal Killer
          </Title>
        </Anchor>
        {children ?? <Outlet />}
      </Stack>
    </Container>
  );
}
