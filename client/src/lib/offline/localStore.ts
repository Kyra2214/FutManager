import { Capacitor } from "@capacitor/core";
import {
  CapacitorSQLite,
  SQLiteConnection,
  type SQLiteDBConnection,
} from "@capacitor-community/sqlite";

const DATABASE_NAME = "futmanager_gamestate";
const DATABASE_VERSION = 1;

let connection: SQLiteConnection | undefined;
let database: SQLiteDBConnection | undefined;

function getConnection() {
  connection ??= new SQLiteConnection(CapacitorSQLite);
  return connection;
}

/**
 * Indicates whether the local SQLite runtime is available in the installed app.
 * The web preview deliberately returns false until a browser adapter is added.
 */
export function isOfflineNativeRuntime() {
  return Capacitor.isNativePlatform();
}

async function getDatabase() {
  if (!isOfflineNativeRuntime()) {
    throw new Error("O armazenamento local SQLite está disponível apenas no aplicativo instalado.");
  }

  if (database) return database;

  const sqlite = getConnection();
  const consistency = await sqlite.checkConnectionsConsistency();
  const hasConnection = consistency.result && (await sqlite.isConnection(DATABASE_NAME, false)).result;

  database = hasConnection
    ? await sqlite.retrieveConnection(DATABASE_NAME, false)
    : await sqlite.createConnection(DATABASE_NAME, false, "no-encryption", DATABASE_VERSION, false);

  await database.open();
  await database.execute(`
    CREATE TABLE IF NOT EXISTS local_schema_versions (
      version INTEGER PRIMARY KEY NOT NULL,
      applied_at INTEGER NOT NULL
    );
  `);

  await migrate(database);
  return database;
}

async function migrate(db: SQLiteDBConnection) {
  const result = await db.query(
    "SELECT MAX(version) AS version FROM local_schema_versions",
  );
  const currentVersion = Number(result.values?.[0]?.version ?? 0);

  if (currentVersion < 1) {
    await db.execute(`
      CREATE TABLE IF NOT EXISTS local_game_state (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        payload TEXT NOT NULL,
        updated_at INTEGER NOT NULL
      );
    `);
    await db.run(
      "INSERT INTO local_schema_versions (version, applied_at) VALUES (?, ?)",
      [DATABASE_VERSION, Date.now()],
    );
  }
}

export async function readLocalGameState<T>() {
  const db = await getDatabase();
  const result = await db.query("SELECT payload FROM local_game_state WHERE id = 1");
  const payload = result.values?.[0]?.payload;
  return payload ? (JSON.parse(String(payload)) as T) : null;
}

export async function writeLocalGameState<T>(state: T) {
  const db = await getDatabase();
  await db.run(
    `
      INSERT INTO local_game_state (id, payload, updated_at)
      VALUES (1, ?, ?)
      ON CONFLICT(id) DO UPDATE SET
        payload = excluded.payload,
        updated_at = excluded.updated_at
    `,
    [JSON.stringify(state), Date.now()],
  );
}

export async function closeLocalGameState() {
  if (!database) return;
  await database.close();
  database = undefined;
}
