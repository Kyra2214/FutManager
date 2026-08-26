import express, { type Express } from "express";
import { resolve } from "node:path";

const ENGINE_ASSETS_ROOT = "/home/ubuntu/brasfoot_engine/assets";

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
