import React, { useState, useEffect } from 'react';
import { StarIcon, BookOpenIcon, ChartBarIcon, UserGroupIcon } from '@heroicons/react/24/outline';

const NewChristians = () => {
  const [newChristians, setNewChristians] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadNewChristians();
  }, []);

  const loadNewChristians = async () => {
    try {
      setLoading(true);
      // Use the dedicated endpoint for new Christians with full data
      const response = await fetch('/api/people/new-christians', {
        credentials: 'include',
        cache: 'no-store'
      });
      
      if (response.ok) {
        const data = await response.json();
        setNewChristians(data.new_christians || []);
      }
    } catch (err) {
      console.error('Error loading new Christians:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6 overflow-y-auto">
      <div className="mb-6">
        <h2 className="text-3xl font-bold text-white mb-2">New Christians</h2>
        <p className="text-white/60">Track discipleship progress and next steps</p>
      </div>

      {loading ? (
        <div className="text-center py-12 text-white/60">Loading new Christians...</div>
      ) : (
        <div className="space-y-4">
          {newChristians.length > 0 ? (
            newChristians.map((person) => (
              <div
                key={person.id}
                className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-6"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <StarIcon className="h-6 w-6 text-purple-400" />
                      <h3 className="text-xl font-semibold text-white">
                        {person.preferred_name || person.full_name}
                      </h3>
                    </div>
                    <div className="text-white/60 text-sm mb-4">
                      Decision logged: {person.new_christian_date ? new Date(person.new_christian_date).toLocaleDateString() : 'Unknown'}
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="bg-white/5 rounded-lg p-4">
                    <div className="text-white/60 text-sm mb-1">Foundations Progress</div>
                    <div className="text-white font-medium">
                      {person.foundations_progress || 'Not started'}
                    </div>
                  </div>
                  <div className="bg-white/5 rounded-lg p-4">
                    <div className="text-white/60 text-sm mb-1">Pathway Progress</div>
                    <div className="text-white font-medium">
                      {person.pathway_progress || 'Not started'}
                    </div>
                  </div>
                  <div className="bg-white/5 rounded-lg p-4">
                    <div className="text-white/60 text-sm mb-1">Group Attendance</div>
                    <div className="text-white font-medium">
                      {person.group_attendance || '0'}%
                    </div>
                  </div>
                  <div className="bg-white/5 rounded-lg p-4">
                    <div className="text-white/60 text-sm mb-1">Pulse TV Usage</div>
                    <div className="text-white font-medium">
                      {person.pulse_tv_usage || 'Low'}
                    </div>
                  </div>
                </div>

                {person.ai_analysis && (
                  <div className="mt-4 bg-purple-500/10 border border-purple-500/30 rounded-lg p-4">
                    <div className="text-purple-400 font-semibold mb-2">AI Analysis</div>
                    <div className="text-white/80 mb-2">{person.ai_analysis}</div>
                    <div className="text-blue-400 text-sm font-medium">
                      Suggested Next Step: {person.suggested_next_step || 'Continue discipleship'}
                    </div>
                  </div>
                )}
              </div>
            ))
          ) : (
            <div className="text-center py-12 text-white/60">
              No new Christians found
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default NewChristians;

