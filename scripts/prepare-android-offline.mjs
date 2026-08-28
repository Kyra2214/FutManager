import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, cpSync, statSync, writeFileSync, mkdtempSync, rmSync } from "node:fs";
import { readFile } from "node:fs/promises";
import { join, resolve } from "node:path";
import { tmpdir } from "node:os";

const projectRoot = resolve(import.meta.dirname, "..");
const candidates = [
  process.env.FUTMANAGER_ENGINE_ROOT,
  resolve(projectRoot, "engine"),
  resolve(projectRoot, "../engine"),
].filter(Boolean);

const engineRoot = candidates.find((candidate) => existsSync(candidate));
if (!engineRoot) {
  throw new Error(
    "Motor não encontrado. Defina FUTMANAGER_ENGINE_ROOT apontando para o diretório que contém data/state/game.db e assets/.",
  );
}

const database = join(engineRoot, "data/state/game.db");
const shields = join(engineRoot, "assets/escudos");
const assetRoots = [
  process.env.FUTMANAGER_ASSET_ROOT,
  resolve(projectRoot, "assets"),
  resolve(projectRoot, "../assets"),
  join(engineRoot, "assets"),
].filter(Boolean);
if (!existsSync(database)) {
  throw new Error(`GameState canônico não encontrado em ${database}`);
}
if (!existsSync(shields)) {
  throw new Error(`Diretório de escudos não encontrado em ${shields}`);
}

const targetRoot = join(projectRoot, "android/app/src/main/assets/public/assets");
const releaseSeedScript = join(projectRoot, "scripts/release_seed.py");
const appAssetsTarget = join(targetRoot, "app");
const editorialAssets = [
  "futmanager-program-texture.jpg",
  "futmanager-stadium-editorial.jpg",
  "futmanager-training.jpg",
  "futmanager-mark.png",
];
const databaseTarget = join(targetRoot, "databases");
const shieldsTarget = join(targetRoot, "escudos");
const assetIndexTarget = join(targetRoot, "offline-asset-index.json");
const countryIndexTarget = join(targetRoot, "offline-countries.json");
mkdirSync(databaseTarget, { recursive: true });
mkdirSync(shieldsTarget, { recursive: true });
mkdirSync(appAssetsTarget, { recursive: true });
const seedTempDir = mkdtempSync(join(tmpdir(), "futmanager-release-seed-"));
const sanitizedDatabase = join(seedTempDir, "game.db");
const sanitized = spawnSync("python3", [releaseSeedScript, "sanitize", database, sanitizedDatabase], { encoding: "utf8" });
if (sanitized.status !== 0) {
  rmSync(seedTempDir, { recursive: true, force: true });
  throw new Error(sanitized.stderr || sanitized.stdout || "Falha ao limpar o GameState para release.");
}
cpSync(sanitizedDatabase, join(databaseTarget, "game.db"));
cpSync(shields, shieldsTarget, { recursive: true });
for (const assetName of editorialAssets) {
  const source = assetRoots.map((root) => join(root, assetName)).find((candidate) => existsSync(candidate));
  if (!source) throw new Error(`Asset editorial não encontrado: ${assetName}`);
  cpSync(source, join(appAssetsTarget, assetName));
}

const hash = createHash("sha256");
hash.update(await readFile(join(databaseTarget, "game.db")));
const index = spawnSync(
  "python3",
  [
    join(projectRoot, "scripts/build-offline-asset-index.py"),
    sanitizedDatabase,
    assetIndexTarget,
  ],
  { encoding: "utf8" },
);
if (index.status !== 0) {
  throw new Error(index.stderr || "Falha ao gerar índice local de assets.");
}
console.log(index.stdout.trim());

const countries = spawnSync(
  "python3",
  [
    join(projectRoot, "scripts/build-offline-country-index.py"),
    engineRoot,
    countryIndexTarget,
  ],
  { encoding: "utf8", env: { ...process.env, PYTHONPATH: [resolve(engineRoot, ".."), engineRoot, process.env.PYTHONPATH].filter(Boolean).join(":") } },
);
if (countries.status !== 0) {
  throw new Error(countries.stderr || "Falha ao gerar catálogo local de países.");
}
console.log(countries.stdout.trim());

writeFileSync(
  join(targetRoot, "offline-manifest.json"),
  JSON.stringify(
    {
      format: 1,
      source: "GameState",
      database: "game.db",
      databaseSha256: hash.digest("hex"),
      generatedAt: new Date().toISOString(),
    },
    null,
    2,
  ) + "\n",
);

const sizeMb = (statSync(sanitizedDatabase).size / 1024 / 1024).toFixed(1);
rmSync(seedTempDir, { recursive: true, force: true });
console.log(`Assets offline preparados a partir de ${engineRoot}`);
console.log(`GameState de release sanitizado: ${sizeMb} MB`);
console.log(`Destino: ${targetRoot}`);
