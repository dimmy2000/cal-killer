import { createTheme, MantineColorsTuple } from "@mantine/core";

const brand: MantineColorsTuple = [
  "#e6f4ff",
  "#cce8ff",
  "#99d0ff",
  "#66b7ff",
  "#339eff",
  "#1a8eff",
  "#0080ff",
  "#0066cc",
  "#004d99",
  "#003366",
];

export const theme = createTheme({
  primaryColor: "brand",
  colors: {
    brand,
  },
  defaultRadius: "md",
  fontFamily:
    '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
  headings: {
    fontWeight: "600",
  },
});
