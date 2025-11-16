'use client';

interface AssignmentRowProps {
  assignment: {
    id: string;
    person_name: string;
    track_stop_name: string;
    status: string;
    due_at: string | null;
    completed_at: string | null;
  };
  onStart?: (id: string) => void;
  onComplete?: (id: string) => void;
  onReschedule?: (id: string) => void;
}

export function AssignmentRow({
  assignment,
  onStart,
  onComplete,
  onReschedule,
}: AssignmentRowProps) {
  const statusColors: Record<string, string> = {
    NEW: 'bg-ready text-white',
    IN_PROGRESS: 'bg-in-progress text-white',
    COMPLETE: 'bg-completed text-white',
    NO_SHOW: 'bg-at-risk text-white',
  };

  const statusColor = statusColors[assignment.status] || 'bg-gray-500 text-white';

  return (
    <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-gray-900">{assignment.person_name}</h3>
            <span className={`px-2 py-1 text-xs rounded-full ${statusColor}`}>
              {assignment.status}
            </span>
          </div>
          <p className="text-sm text-gray-600 mt-1">{assignment.track_stop_name}</p>
          {assignment.due_at && (
            <p className="text-xs text-gray-500 mt-1">
              Due: {new Date(assignment.due_at).toLocaleDateString()}
            </p>
          )}
        </div>
        <div className="flex gap-2">
          {assignment.status === 'NEW' && onStart && (
            <button
              onClick={() => onStart(assignment.id)}
              className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
            >
              Start
            </button>
          )}
          {assignment.status === 'IN_PROGRESS' && onComplete && (
            <button
              onClick={() => onComplete(assignment.id)}
              className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700"
            >
              Complete
            </button>
          )}
          {onReschedule && (
            <button
              onClick={() => onReschedule(assignment.id)}
              className="px-3 py-1 bg-gray-600 text-white text-sm rounded hover:bg-gray-700"
            >
              Reschedule
            </button>
          )}
        </div>
      </div>
    </div>
  );
}






