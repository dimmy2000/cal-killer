import { defineConfig } from "orval";

export default defineConfig({
  calKiller: {
    input: {
      target: "../tsp-output/schema/openapi.yaml",
    },
    output: {
      mode: "tags-split",
      target: "src/api/generated",
      schemas: "src/api/generated/models",
      client: "react-query",
      httpClient: "fetch",
      mock: false,
      override: {
        mutator: {
          path: "src/api/client-config.ts",
          name: "customFetch",
        },
        query: {
          useQuery: true,
          useInfinite: false,
          signal: true,
        },
      },
    },
    hooks: {
      afterAllFilesWrite: "prettier --write",
    },
  },
});
