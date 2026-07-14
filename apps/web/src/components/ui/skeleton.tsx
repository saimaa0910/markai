import { cn } from '@eaimos/shared';

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {}

export function Skeleton({ className, ...props }: SkeletonProps) {
  return (
    <div
      className={cn('animate-pulse rounded bg-white/5', className)}
      {...props}
    />
  );
}

export function TableSkeleton() {
  return (
    <div className="flex flex-col gap-3 w-full">
      <Skeleton className="h-10 w-full" />
      <Skeleton className="h-12 w-full" />
      <Skeleton className="h-12 w-full" />
      <Skeleton className="h-12 w-full" />
      <Skeleton className="h-12 w-full" />
    </div>
  );
}

export function CardSkeleton() {
  return (
    <div className="rounded-xl border border-white/10 bg-neutral-900/40 p-6 flex flex-col gap-4">
      <Skeleton className="h-4 w-1/3" />
      <Skeleton className="h-8 w-2/3" />
      <Skeleton className="h-3 w-1/2" />
    </div>
  );
}
