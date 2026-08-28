import express, { type Express } from "express";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const MODULE_ROOT = dirname(fileURLToPath(import.meta.url));
const ENGINE_ASSETS_ROOT = process.env.FUTMANAGER_ENGINE_ASSETS_ROOT || resolve(process.env.FUTMANAGER_ENGINE_ROOT || resolve(MODULE_ROOT, "../engine"), "assets");

export function registerEngineAssetFiles(app: Express) {
  app.use(
    "/engine-assets",
    express.static(resolve(ENGINE_ASSETS_ROOT), {
      fallthrough: false,
      immutable: false,
      maxAge: "1h",
    }),
  );
}
