import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";

const projectRoot = resolve(import.meta.dirname, "..");
const targetRoot = join(projectRoot, "android/app/src/main/assets/public/assets");
const remoteManifestUrl = process.env.FUTMANAGER_DATA_MANIFEST_URL || "https://github.com/Kyra2214/FutManager-data/releases/download/v1.0.0/manifest.json";

mkdirSync(targetRoot, { recursive: true });
for (const heavyPath of [
  "databases",
  "escudos",
  "app",
  "offline-asset-index.json",
  "offline-countries.json",
]) {
  rmSync(join(targetRoot, heavyPath), { recursive: true, force: true });
}

writeFileSync(
  join(targetRoot, "offline-manifest.json"),
  JSON.stringify(
    {
      format: 2,
      source: "remote-data-package",
      manifestUrl: remoteManifestUrl,
      requiresInitialDownload: true,
    },
    null,
    2,
  ) + "\n",
);

console.log(`APK híbrido preparado; dados e assets serão baixados de ${remoteManifestUrl}`);
console.log("Diretório de dados embutidos removido; bytes pesados incluídos: 0");
