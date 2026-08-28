import express, { type Express } from "express";
import { join, resolve } from "node:path";

const ENGINE_ROOT = process.env.FUTMANAGER_ENGINE_ROOT || resolve(import.meta.dirname, "../../engine");
const ENGINE_ASSETS_ROOT = join(ENGINE_ROOT, "assets");

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
