import { Capacitor } from "@capacitor/core";
import { Directory, Encoding, Filesystem } from "@capacitor/filesystem";
import { Share } from "@capacitor/share";
import {
  exportLocalDatabase,
  importLocalDatabase,
} from "./localStore";

const BACKUP_FILE = "futmanager-career-backup.json";

function assertNative() {
  if (!Capacitor.isNativePlatform()) {
    throw new Error("Backup e restauração estão disponíveis apenas no APK.");
  }
}

export async function createCareerBackup() {
  assertNative();
  const exported = await exportLocalDatabase();
  const data = JSON.stringify(
    {
      format: "futmanager-career-backup",
      version: 1,
      exportedAt: new Date().toISOString(),
      database: exported.export,
    },
    null,
    2,
  );

  const file = await Filesystem.writeFile({
    path: BACKUP_FILE,
    data,
    directory: Directory.Documents,
    encoding: Encoding.UTF8,
    recursive: true,
  });

  return { path: file.uri, fileName: BACKUP_FILE };
}

export async function shareCareerBackup() {
  const backup = await createCareerBackup();
  await Share.share({
    title: "Backup da carreira FutManager",
    text: "Backup local da carreira FutManager.",
    url: backup.path,
    dialogTitle: "Compartilhar backup",
  });
  return backup;
}

export async function restoreCareerBackup(uri: string) {
  assertNative();
  const file = await Filesystem.readFile({ path: uri, encoding: Encoding.UTF8 });
  const parsed = JSON.parse(String(file.data)) as {
    format?: string;
    version?: number;
    database?: unknown;
  };

  if (
    parsed.format !== "futmanager-career-backup" ||
    parsed.version !== 1 ||
    !parsed.database
  ) {
    throw new Error("O arquivo selecionado não é um backup FutManager válido.");
  }

  await importLocalDatabase(JSON.stringify(parsed.database));
}
