import React, { useState, useEffect } from 'react';
import { UserPlusIcon, CalendarIcon, MapPinIcon, CheckCircleIcon } from '@heroicons/react/24/outline';

const NewPeople = () => {
  const [newPeople, setNewPeople] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadNewPeople();
  }, []);

  const loadNewPeople = async () => {
    try {
      setLoading(true);
      
      const response = await fetch('/api/persons?new_people=true', {
        credentials: 'include',
        cache: 'no-store'
      });
      
      if (response.ok) {
        const data = await response.json();
        setNewPeople(data.persons || []);
      }
    } catch (err) {
      console.error('Error loading new people:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString();
    } catch {
      return 'Unknown';
    }
  };

  return (
    <div className="h-full bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6 overflow-y-auto">
      <div className="mb-6">
        <h2 className="text-3xl font-bold text-white mb-2">New People</h2>
        <p className="text-white/60">People who joined in the last 30 days</p>
      </div>

      {loading ? (
        <div className="text-center py-12 text-white/60">Loading new people...</div>
      ) : (
        <div className="space-y-4">
          {newPeople.length > 0 ? (
            newPeople.map((person) => (
              <div
                key={person.id}
                className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-6"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-xl font-semibold text-white mb-2">
                      {person.preferred_name || person.full_name}
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-white/60">
                      <div className="flex items-center gap-2">
                        <CalendarIcon className="h-4 w-4" />
                        Visit Date: {formatDate(person.created_at || person.date_added)}
                      </div>
                      <div className="flex items-center gap-2">
                        <MapPinIcon className="h-4 w-4" />
                        Campus: {person.campus || 'Unknown'}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                  <div className="bg-white/5 rounded-lg p-4">
                    <div className="text-white/60 text-sm mb-1">Service Attended</div>
                    <div className="text-white font-medium">{person.service_attended || 'Unknown'}</div>
                  </div>
                  <div className="bg-white/5 rounded-lg p-4">
                    <div className="text-white/60 text-sm mb-1">Follow-up Status</div>
                    <div className="text-white font-medium">
                      {person.follow_up_status || 'Needed'}
                    </div>
                  </div>
                  <div className="bg-white/5 rounded-lg p-4">
                    <div className="text-white/60 text-sm mb-1">Next Steps</div>
                    <div className="text-white font-medium">
                      {person.next_steps || 'Connect to group'}
                    </div>
                  </div>
                </div>

                {person.ai_follow_up_message && (
                  <div className="mt-4 bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                    <div className="text-blue-400 font-semibold mb-2">AI Follow-up Message</div>
                    <div className="text-white/80">{person.ai_follow_up_message}</div>
                  </div>
                )}
              </div>
            ))
          ) : (
            <div className="text-center py-12 text-white/60">
              No new people in the last 30 days
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default NewPeople;

