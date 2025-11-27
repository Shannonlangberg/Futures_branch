import React, { useState, useEffect } from 'react';
import { UserCircleIcon, ExclamationTriangleIcon, ClockIcon } from '@heroicons/react/24/outline';

const PastoralCare = () => {
  const [careCases, setCareCases] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCareCases();
  }, []);

  const loadCareCases = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/pastoral-care/cases', {
        credentials: 'include',
        cache: 'no-store'
      });
      
      if (response.ok) {
        const data = await response.json();
        setCareCases(data.cases || []);
      }
    } catch (err) {
      console.error('Error loading care cases:', err);
      setCareCases([]);
    } finally {
      setLoading(false);
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high':
        return 'bg-red-500/20 text-red-400 border-red-500/50';
      case 'medium':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50';
      case 'low':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/50';
      default:
        return 'bg-slate-500/20 text-slate-400 border-slate-500/50';
    }
  };

  return (
    <div className="h-full bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6 overflow-y-auto">
      <div className="mb-6">
        <h2 className="text-3xl font-bold text-white mb-2">Pastoral Care</h2>
        <p className="text-white/60">Care engine for tracking and managing pastoral needs</p>
      </div>

      {loading ? (
        <div className="text-center py-12 text-white/60">Loading care cases...</div>
      ) : (
        <div className="space-y-4">
          {careCases.length > 0 ? (
            careCases.map((case_) => (
              <div
                key={case_.id}
                className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-6"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-xl font-semibold text-white">
                        {case_.person_name || 'Unnamed Case'}
                      </h3>
                      <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getPriorityColor(case_.priority)}`}>
                        {case_.priority || 'medium'} priority
                      </span>
                    </div>
                    <div className="text-white/60 text-sm mb-4">{case_.notes}</div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-white/5 rounded-lg p-4">
                    <div className="text-white/60 text-sm mb-1">Assigned Leader</div>
                    <div className="text-white font-medium">{case_.assigned_leader || 'Unassigned'}</div>
                  </div>
                  <div className="bg-white/5 rounded-lg p-4">
                    <div className="text-white/60 text-sm mb-1">Follow-up Timeline</div>
                    <div className="text-white font-medium">{case_.follow_up_date || 'No date set'}</div>
                  </div>
                  <div className="bg-white/5 rounded-lg p-4">
                    <div className="text-white/60 text-sm mb-1">Status</div>
                    <div className="text-white font-medium">{case_.status || 'Open'}</div>
                  </div>
                </div>

                {case_.ai_summary && (
                  <div className="mt-4 bg-purple-500/10 border border-purple-500/30 rounded-lg p-4">
                    <div className="text-purple-400 font-semibold mb-2">AI Care Summary</div>
                    <div className="text-white/80">{case_.ai_summary}</div>
                  </div>
                )}
              </div>
            ))
          ) : (
            <div className="text-center py-12 text-white/60">
              No open care cases
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PastoralCare;

