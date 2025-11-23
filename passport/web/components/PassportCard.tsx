'use client';

interface Stamp {
  id: string;
  track_stop_name: string;
  track_name: string;
  stamped_at: string;
}

interface PassportCardProps {
  personName: string;
  currentZone: string;
  pulseScore: number;
  stamps: Stamp[];
  nextStep?: {
    track_stop_name: string;
    has_assignment: boolean;
  };
}

export function PassportCard({
  personName,
  currentZone,
  pulseScore,
  stamps,
  nextStep,
}: PassportCardProps) {
  return (
    <div className="bg-white rounded-lg shadow-lg p-6 border-2 border-gray-200">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">{personName}</h2>
        <div className="mt-2">
          <span className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm font-medium">
            {currentZone}
          </span>
        </div>
        <div className="mt-2 text-sm text-gray-600">
          Pulse Score: <span className="font-semibold">{pulseScore}</span>
        </div>
      </div>

      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-3">Stamps Earned</h3>
        <div className="grid grid-cols-2 gap-2">
          {stamps.length > 0 ? (
            stamps.map((stamp) => (
              <div
                key={stamp.id}
                className="bg-gradient-to-br from-yellow-400 to-yellow-600 p-3 rounded-lg text-center"
              >
                <div className="text-white font-bold text-sm">{stamp.track_stop_name}</div>
                <div className="text-yellow-100 text-xs mt-1">
                  {new Date(stamp.stamped_at).toLocaleDateString()}
                </div>
              </div>
            ))
          ) : (
            <div className="col-span-2 text-gray-500 text-sm text-center py-4">
              No stamps yet
            </div>
          )}
        </div>
      </div>

      {nextStep && (
        <div className="border-t pt-4">
          <h3 className="text-lg font-semibold text-gray-800 mb-2">Next Step</h3>
          <div className="bg-blue-50 p-3 rounded-lg">
            <div className="font-medium text-blue-900">{nextStep.track_stop_name}</div>
            {nextStep.has_assignment && (
              <div className="text-sm text-blue-700 mt-1">Assignment in progress</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}












