import express, { type Express } from "express";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const MODULE_ROOT = dirname(fileURLToPath(import.meta.url));
const ENGINE_ROOT = process.env.FUTMANAGER_ENGINE_ROOT || resolve(MODULE_ROOT, "../../engine");
const ENGINE_ASSETS_ROOT = resolve(ENGINE_ROOT, "assets");

export function registerEngineAssetFiles(app: Express) {
  app.use(
    "/engine-assets",
    express.static(ENGINE_ASSETS_ROOT, {
      fallthrough: false,
      immutable: false,
      maxAge: "1h",
    }),
  );
}
