import { trpc } from "@/lib/trpc";
import { Capacitor } from "@capacitor/core";
import { useEffect, useState } from "react";
import { getEntityAssetPresentation } from "@/lib/entityAsset";
import { NativeEngine } from "@/lib/offline/nativeEngine";

type OfflineAsset = { entityId: number; kind: "club" | "selection"; path: string | null };
type OfflineAssetIndex = Record<string, OfflineAsset>;

let offlineAssetIndexPromise: Promise<OfflineAssetIndex> | undefined;

function loadOfflineAssetIndex() {
  offlineAssetIndexPromise ??= Capacitor.isNativePlatform()
    ? NativeEngine.readDataFile({ path: "offline-asset-index.json" }).then(({ content }) => JSON.parse(content) as OfflineAssetIndex)
    : fetch("/assets/offline-asset-index.json").then((response) => {
      if (!response.ok) throw new Error("Índice de assets offline indisponível.");
      return response.json() as Promise<OfflineAssetIndex>;
    });
  return offlineAssetIndexPromise;
}

type EntityAssetProps = {
  entityType: "team" | "selection";
  entityId: number;
  entityName: string;
  className?: string;
};

export function EntityAsset({ entityType, entityId, entityName, className = "crest-large" }: EntityAssetProps) {
  const isNative = Capacitor.isNativePlatform();
  const [offlineAsset, setOfflineAsset] = useState<OfflineAsset | null>(null);
  const [nativeImageUrl, setNativeImageUrl] = useState<string | null>(null);
  const assetQuery = trpc.assets.resolve.useQuery({ entityType, entityId }, { enabled: !isNative });

  useEffect(() => {
    if (!isNative) return;
    let active = true;
    setNativeImageUrl(null);
    loadOfflineAssetIndex()
      .then(async (index) => {
        const entry = index[`${entityType === "team" ? "team" : "selection"}:${entityId}`] ?? null;
        if (!active) return;
        setOfflineAsset(entry);
        if (entry?.path) {
          const { uri } = await NativeEngine.getDataAssetUrl({ path: entry.path });
          if (active) setNativeImageUrl(Capacitor.convertFileSrc(uri));
        }
      })
      .catch(() => active && setOfflineAsset(null));
    return () => { active = false; };
  }, [entityId, entityType, isNative]);

  const asset = assetQuery.data;
  const imageUrl = isNative
    ?   nativeImageUrl ?? (offlineAsset?.path ? `/${offlineAsset.path}` : null)
    : asset?.crestUrl ?? asset?.miniCrestUrl ?? asset?.primaryKitUrl ?? null;
  const presentation = getEntityAssetPresentation(isNative ? (offlineAsset?.path ? "COMPLETE" : "NO_SOURCE_ASSET") : asset?.mappingStatus, entityType);
  const alt = imageUrl && !asset?.crestUrl && entityType === "selection" ? `Camisa de ${entityName}` : `Escudo de ${entityName}`;

  return imageUrl ? (
    <img className={`${className} crest-image`} src={imageUrl} alt={alt} title={presentation.label} />
  ) : (
    <span className={className} title={presentation.label} aria-label={presentation.label}>?</span>
  );
}
