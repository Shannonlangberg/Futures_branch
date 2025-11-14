import React from 'react';

const Heartbeat = () => (
  <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
    <div className="max-w-4xl mx-auto bg-slate-800/60 border border-slate-700/60 rounded-3xl p-10 text-center space-y-4">
      <div className="w-16 h-16 mx-auto rounded-full bg-purple-500/20 flex items-center justify-center text-3xl">
        💜
      </div>
      <h1 className="text-3xl font-bold text-white">Heartbeat Dashboard</h1>
      <p className="text-white/70">
        Our data team is still wiring this one up. Soon you’ll be able to see real-time pulse stats
        and follow-up priorities here.
      </p>
      <p className="text-white/50 text-sm">
        Need immediate stats? Touch base with the digital team and we’ll grab what you need.
      </p>
    </div>
  </div>
);

export default Heartbeat;


