'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { CapacityBadge } from '@/components/CapacityBadge';

export default function ReportsPage() {
  const router = useRouter();
  const [tracks, setTracks] = useState<any[]>([]);
  const [selectedTrack, setSelectedTrack] = useState<string>('');
  const [trackHealth, setTrackHealth] = useState<any>(null);
  const [mentorLoad, setMentorLoad] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (selectedTrack) {
      loadTrackHealth();
    }
  }, [selectedTrack]);

  const loadData = async () => {
    try {
      const [tracksData, loadData] = await Promise.all([
        api.tracks.getAll(),
        api.reports.mentorLoad(),
      ]);
      setTracks(tracksData);
      setMentorLoad(loadData);
      if (tracksData.length > 0) {
        setSelectedTrack(tracksData[0].id);
      }
    } catch (error: any) {
      if (error.message.includes('Unauthorized')) {
        router.push('/login');
      }
    } finally {
      setLoading(false);
    }
  };

  const loadTrackHealth = async () => {
    try {
      const data = await api.reports.trackHealth(selectedTrack);
      setTrackHealth(data);
    } catch (error: any) {
      console.error('Failed to load track health:', error);
    }
  };

  if (loading) {
    return <div className="p-8">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Reports</h1>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Track Health</h2>
            <select
              value={selectedTrack}
              onChange={(e) => setSelectedTrack(e.target.value)}
              className="w-full mb-4 px-4 py-2 border border-gray-300 rounded-md"
            >
              {tracks.map((track) => (
                <option key={track.id} value={track.id}>
                  {track.name}
                </option>
              ))}
            </select>

            {trackHealth && (
              <div className="space-y-3">
                {trackHealth.stops?.map((stop: any) => (
                  <div key={stop.stop_id} className="border-l-4 border-blue-500 pl-4">
                    <h3 className="font-medium">{stop.stop_name}</h3>
                    <div className="text-sm text-gray-600 mt-1">
                      New: {stop.status_counts.NEW} | In Progress: {stop.status_counts.IN_PROGRESS}{' '}
                      | Complete: {stop.status_counts.COMPLETE}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Mentor Load</h2>
            <div className="space-y-3">
              {mentorLoad.map((mentor) => (
                <div key={mentor.leader_id} className="flex items-center justify-between">
                  <span className="font-medium">{mentor.leader_id}</span>
                  <div className="flex items-center gap-2">
                    <CapacityBadge
                      active={mentor.active_assignments}
                      capacity={mentor.capacity_slots}
                    />
                    <span className="text-sm text-gray-600">
                      {mentor.load_percentage.toFixed(0)}%
                    </span>
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





