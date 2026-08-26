import { trpc } from "@/lib/trpc";
import { getEntityAssetPresentation } from "@/lib/entityAsset";

type EntityAssetProps = {
  entityType: "team" | "selection";
  entityId: number;
  entityName: string;
  className?: string;
};

export function EntityAsset({ entityType, entityId, entityName, className = "crest-large" }: EntityAssetProps) {
  const assetQuery = trpc.assets.resolve.useQuery({ entityType, entityId });
  const asset = assetQuery.data;
  const imageUrl = asset?.crestUrl ?? asset?.miniCrestUrl ?? asset?.primaryKitUrl ?? null;
  const presentation = getEntityAssetPresentation(asset?.mappingStatus, entityType);
  const alt = imageUrl && !asset?.crestUrl && entityType === "selection" ? `Camisa de ${entityName}` : `Escudo de ${entityName}`;

  return imageUrl ? (
    <img className={`${className} crest-image`} src={imageUrl} alt={alt} title={presentation.label} />
  ) : (
    <span className={className} title={presentation.label} aria-label={presentation.label}>?</span>
  );
}
