'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { KpiTiles } from '@/components/KpiTiles';

export default function LeaderHomePage() {
  const router = useRouter();
  const [leader, setLeader] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadLeader();
  }, []);

  const loadLeader = async () => {
    try {
      const data = await api.leaders.getMe();
      setLeader(data);
    } catch (error: any) {
      if (error.message.includes('Unauthorized')) {
        router.push('/login');
      }
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-8">Loading...</div>;
  }

  if (!leader) {
    return <div className="p-8">Error loading leader data</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">
          Welcome, {leader.full_name}
        </h1>

        <KpiTiles
          kpis={[
            {
              title: 'Active Assignments',
              value: leader.active_assignments,
              subtitle: `${leader.available_slots} slots available`,
              color: 'blue',
            },
            {
              title: 'Capacity',
              value: `${leader.active_assignments}/${leader.capacity_slots}`,
              subtitle: leader.available_slots > 0 ? 'Available' : 'Full',
              color: leader.available_slots > 0 ? 'green' : 'amber',
            },
            {
              title: 'Role',
              value: leader.role,
              color: 'purple',
            },
            {
              title: 'Campus',
              value: leader.campus_id || 'All',
              color: 'blue',
            },
          ]}
        />

        <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
            <div className="space-y-2">
              <button
                onClick={() => router.push('/leader/inbox')}
                className="w-full text-left px-4 py-2 bg-blue-50 hover:bg-blue-100 rounded-lg"
              >
                View Inbox
              </button>
              <button
                onClick={() => router.push('/leader/push-queue')}
                className="w-full text-left px-4 py-2 bg-purple-50 hover:bg-purple-100 rounded-lg"
              >
                Push Queue
              </button>
              <button
                onClick={() => router.push('/leader/people')}
                className="w-full text-left px-4 py-2 bg-green-50 hover:bg-green-100 rounded-lg"
              >
                View People
              </button>
              <button
                onClick={() => router.push('/leader/reports')}
                className="w-full text-left px-4 py-2 bg-amber-50 hover:bg-amber-100 rounded-lg"
              >
                Reports
              </button>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Recent Activity</h2>
            <p className="text-gray-600 text-sm">No recent activity</p>
          </div>
        </div>
      </div>
    </div>
  );
}








