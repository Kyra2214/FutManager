import { trpc } from "@/lib/trpc";
import { Capacitor } from "@capacitor/core";
import { useEffect, useState } from "react";
import { getEntityAssetPresentation } from "@/lib/entityAsset";

type OfflineAsset = { entityId: number; kind: "club" | "selection"; path: string | null };
type OfflineAssetIndex = Record<string, OfflineAsset>;

let offlineAssetIndexPromise: Promise<OfflineAssetIndex> | undefined;

function loadOfflineAssetIndex() {
  offlineAssetIndexPromise ??= fetch("/assets/offline-asset-index.json").then((response) => {
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
  const assetQuery = trpc.assets.resolve.useQuery({ entityType, entityId }, { enabled: !isNative });

  useEffect(() => {
    if (!isNative) return;
    let active = true;
    loadOfflineAssetIndex()
      .then((index) => active && setOfflineAsset(index[`${entityType === "team" ? "team" : "selection"}:${entityId}`] ?? null))
      .catch(() => active && setOfflineAsset(null));
    return () => { active = false; };
  }, [entityId, entityType, isNative]);

  const asset = assetQuery.data;
  const imageUrl = isNative
    ? offlineAsset?.path ? `/${offlineAsset.path}` : null
    : asset?.crestUrl ?? asset?.miniCrestUrl ?? asset?.primaryKitUrl ?? null;
  const presentation = getEntityAssetPresentation(isNative ? (offlineAsset?.path ? "COMPLETE" : "NO_SOURCE_ASSET") : asset?.mappingStatus, entityType);
  const alt = imageUrl && !asset?.crestUrl && entityType === "selection" ? `Camisa de ${entityName}` : `Escudo de ${entityName}`;

  return imageUrl ? (
    <img className={`${className} crest-image`} src={imageUrl} alt={alt} title={presentation.label} />
  ) : (
    <span className={className} title={presentation.label} aria-label={presentation.label}>?</span>
  );
}
