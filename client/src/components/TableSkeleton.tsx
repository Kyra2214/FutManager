import { Skeleton } from "@/components/ui/skeleton";

export function TableSkeleton({ rows = 5, columns = 4 }: { rows?: number; columns?: number }) {
  return (
    <div aria-label="Carregando tabela" role="status" className="space-y-3">
      {Array.from({ length: rows }, (_, row) => (
        <div className="grid gap-3" style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }} key={row}>
          {Array.from({ length: columns }, (_, column) => <Skeleton className="h-8 rounded-md" key={column} />)}
        </div>
      ))}
    </div>
  );
}
