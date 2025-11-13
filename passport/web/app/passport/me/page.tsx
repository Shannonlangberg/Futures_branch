'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { api } from '@/lib/api';
import { PassportCard } from '@/components/PassportCard';

export default function PassportMePage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const personId = searchParams.get('person_id') || 'default-person-id';
  const [passport, setPassport] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPassport();
  }, [personId]);

  const loadPassport = async () => {
    try {
      const data = await api.passport.getByPerson(personId);
      setPassport(data);
    } catch (error: any) {
      console.error('Failed to load passport:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-8">Loading...</div>;
  }

  if (!passport) {
    return (
      <div className="p-8">
        <div className="text-center">
          <p className="text-gray-600">Passport not found</p>
          <button
            onClick={() => router.push('/login')}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 p-8">
      <div className="max-w-4xl mx-auto">
        <PassportCard
          personName={passport.full_name}
          currentZone={passport.current_zone}
          pulseScore={passport.pulse_score}
          stamps={passport.stamps}
          nextStep={passport.next_step}
        />
      </div>
    </div>
  );
}





