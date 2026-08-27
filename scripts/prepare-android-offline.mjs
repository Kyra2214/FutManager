import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, cpSync, statSync, writeFileSync } from "node:fs";
import { readFile } from "node:fs/promises";
import { join, resolve } from "node:path";

const projectRoot = resolve(import.meta.dirname, "..");
const candidates = [
  process.env.FUTMANAGER_ENGINE_ROOT,
  resolve(projectRoot, "../engine"),
  resolve(projectRoot, "../brasfoot_engine"),
  "/home/ubuntu/brasfoot_engine",
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
  resolve(projectRoot, "../FutManager/assets"),
  "/home/ubuntu/webdev-static-assets",
  join(engineRoot, "assets"),
].filter(Boolean);
if (!existsSync(database)) {
  throw new Error(`GameState canônico não encontrado em ${database}`);
}
if (!existsSync(shields)) {
  throw new Error(`Diretório de escudos não encontrado em ${shields}`);
}

const targetRoot = join(projectRoot, "android/app/src/main/assets/public/assets");
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
mkdirSync(databaseTarget, { recursive: true });
mkdirSync(shieldsTarget, { recursive: true });
mkdirSync(appAssetsTarget, { recursive: true });
cpSync(database, join(databaseTarget, "game.db"));
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
    database,
    assetIndexTarget,
  ],
  { encoding: "utf8" },
);
if (index.status !== 0) {
  throw new Error(index.stderr || "Falha ao gerar índice local de assets.");
}
console.log(index.stdout.trim());

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

const sizeMb = (statSync(database).size / 1024 / 1024).toFixed(1);
console.log(`Assets offline preparados a partir de ${engineRoot}`);
console.log(`GameState: ${sizeMb} MB`);
console.log(`Destino: ${targetRoot}`);
