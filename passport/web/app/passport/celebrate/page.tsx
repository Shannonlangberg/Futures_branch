'use client';

import { useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import confetti from 'canvas-confetti';

export default function CelebratePage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const stampName = searchParams.get('stamp') || 'Stamp';

  useEffect(() => {
    // Trigger confetti
    const duration = 3000;
    const end = Date.now() + duration;

    const interval = setInterval(() => {
      if (Date.now() > end) {
        clearInterval(interval);
        return;
      }

      confetti({
        particleCount: 3,
        angle: 60,
        spread: 55,
        origin: { x: 0 },
      });
      confetti({
        particleCount: 3,
        angle: 120,
        spread: 55,
        origin: { x: 1 },
      });
    }, 200);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-yellow-200 via-yellow-300 to-yellow-400 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-yellow-900 mb-4">🎉</h1>
        <h2 className="text-4xl font-bold text-yellow-900 mb-2">Congratulations!</h2>
        <p className="text-2xl text-yellow-800 mb-8">You earned: {stampName}</p>
        <button
          onClick={() => router.push('/passport/me')}
          className="px-6 py-3 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 text-lg font-semibold"
        >
          View Passport
        </button>
      </div>
    </div>
  );
}








