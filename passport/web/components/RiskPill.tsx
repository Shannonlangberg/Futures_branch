'use client';

interface RiskPillProps {
  level: 'low' | 'medium' | 'high';
  label: string;
}

export function RiskPill({ level, label }: RiskPillProps) {
  const colorClasses = {
    low: 'bg-green-100 text-green-800',
    medium: 'bg-amber-100 text-amber-800',
    high: 'bg-red-100 text-red-800',
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colorClasses[level]}`}>
      {label}
    </span>
  );
}





