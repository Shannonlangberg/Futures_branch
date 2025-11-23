'use client';

interface CapacityBadgeProps {
  active: number;
  capacity: number;
}

export function CapacityBadge({ active, capacity }: CapacityBadgeProps) {
  const percentage = (active / capacity) * 100;
  const colorClass =
    percentage >= 100
      ? 'bg-red-100 text-red-800'
      : percentage >= 80
      ? 'bg-amber-100 text-amber-800'
      : 'bg-green-100 text-green-800';

  return (
    <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colorClass}`}>
      {active}/{capacity} slots
    </div>
  );
}












