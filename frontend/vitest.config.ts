import { defineConfig } from "vitest/config";
import path from "path";

const templateRoot = path.resolve(import.meta.dirname);

export default defineConfig({
  root: templateRoot,
  ssr: {
    external: ["node:sqlite"],
  },
  resolve: {
    alias: {
      "@": path.resolve(templateRoot, "client", "src"),
      "@shared": path.resolve(templateRoot, "shared"),
      "@assets": path.resolve(templateRoot, "attached_assets"),
      "sqlite": path.resolve(templateRoot, "server", "sqliteRuntime.ts"),
    },
  },
  test: {
    environment: "node",
    fileParallelism: false,
    testTimeout: 120_000,
    hookTimeout: 120_000,
    include: ["server/**/*.test.ts", "server/**/*.test.tsx", "server/**/*.spec.ts", "server/**/*.spec.tsx"],
  },
});
