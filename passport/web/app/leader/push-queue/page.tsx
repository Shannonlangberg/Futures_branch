'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { CapacityBadge } from '@/components/CapacityBadge';

export default function PushQueuePage() {
  const router = useRouter();
  const [queue, setQueue] = useState<any[]>([]);
  const [leaders, setLeaders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [queueData, mentorData] = await Promise.all([
        api.pushQueue.getAll(),
        api.reports.mentorLoad(),
      ]);
      setQueue(queueData);
      setLeaders(mentorData);
    } catch (error: any) {
      if (error.message.includes('Unauthorized')) {
        router.push('/login');
      }
    } finally {
      setLoading(false);
    }
  };

  const handlePush = async (personId: string, mentorId: string) => {
    try {
      // Get tracks and stops (simplified - in real app, get from track selection)
      const tracks = await api.tracks.getAll();
      if (tracks.length === 0) {
        alert('No tracks available');
        return;
      }

      const stops = await api.tracks.getStops(tracks[0].id);
      if (stops.length === 0) {
        alert('No track stops available');
        return;
      }

      const dueDate = new Date();
      dueDate.setDate(dueDate.getDate() + 7);

      await api.push.create({
        person_id: personId,
        track_stop_id: stops[0].id,
        mentor_leader_id: mentorId,
        due_at: dueDate.toISOString(),
      });

      alert('Assignment pushed successfully!');
      loadData();
    } catch (error: any) {
      alert(`Failed to push: ${error.message}`);
    }
  };

  if (loading) {
    return <div className="p-8">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Push Queue</h1>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <h2 className="text-xl font-semibold mb-4">Ready Candidates</h2>
            <div className="space-y-4">
              {queue.length === 0 ? (
                <div className="bg-white p-8 rounded-lg shadow text-center text-gray-500">
                  No candidates ready
                </div>
              ) : (
                queue.map((candidate) => (
                  <div key={candidate.person_id} className="bg-white p-4 rounded-lg shadow">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-semibold">{candidate.full_name}</h3>
                        <p className="text-sm text-gray-600">
                          Readiness: {candidate.readiness_score} | Zone: {candidate.current_zone}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          {candidate.completed_assignments} completed, {candidate.recent_activities}{' '}
                          recent activities
                        </p>
                      </div>
                      <div className="text-right">
                        <select
                          onChange={(e) => {
                            if (e.target.value) {
                              handlePush(candidate.person_id, e.target.value);
                            }
                          }}
                          className="px-3 py-2 border border-gray-300 rounded-md text-sm"
                        >
                          <option value="">Push to...</option>
                          {leaders
                            .filter((l) => l.status === 'available')
                            .map((leader) => (
                              <option key={leader.leader_id} value={leader.leader_id}>
                                {leader.leader_id} ({leader.available_slots} slots)
                              </option>
                            ))}
                        </select>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          <div>
            <h2 className="text-xl font-semibold mb-4">Mentor Capacity</h2>
            <div className="space-y-3">
              {leaders.map((leader) => (
                <div key={leader.leader_id} className="bg-white p-4 rounded-lg shadow">
                  <div className="flex justify-between items-center">
                    <span className="font-medium">{leader.leader_id}</span>
                    <CapacityBadge
                      active={leader.active_assignments}
                      capacity={leader.capacity_slots}
                    />
                  </div>
                  <div className="mt-2 text-sm text-gray-600">
                    {leader.load_percentage.toFixed(0)}% capacity
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}










