'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';

export default function StampsPage() {
  const router = useRouter();
  const [stamps, setStamps] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStamps();
  }, []);

  const loadStamps = async () => {
    try {
      const data = await api.stamps.getPending();
      setStamps(data);
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

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Stamps</h1>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {stamps.length === 0 ? (
            <div className="col-span-full bg-white p-8 rounded-lg shadow text-center text-gray-500">
              No stamps found
            </div>
          ) : (
            stamps.map((stamp) => (
              <div
                key={stamp.id}
                className="bg-gradient-to-br from-yellow-400 to-yellow-600 p-6 rounded-lg shadow-lg text-white"
              >
                <h3 className="text-xl font-bold mb-2">{stamp.track_stop_name}</h3>
                <p className="text-sm opacity-90 mb-1">{stamp.person_name}</p>
                <p className="text-xs opacity-75">
                  {new Date(stamp.stamped_at).toLocaleDateString()}
                </p>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}










