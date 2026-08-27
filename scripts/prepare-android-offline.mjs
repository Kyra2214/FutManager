import { createHash } from "node:crypto";
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
if (!existsSync(database)) {
  throw new Error(`GameState canônico não encontrado em ${database}`);
}
if (!existsSync(shields)) {
  throw new Error(`Diretório de escudos não encontrado em ${shields}`);
}

const targetRoot = join(projectRoot, "android/app/src/main/assets/bootstrap");
mkdirSync(targetRoot, { recursive: true });
cpSync(database, join(targetRoot, "game.db"));
cpSync(shields, join(targetRoot, "escudos"), { recursive: true });

const hash = createHash("sha256");
hash.update(await readFile(join(targetRoot, "game.db")));
writeFileSync(
  join(targetRoot, "manifest.json"),
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
