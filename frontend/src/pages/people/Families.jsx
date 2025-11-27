import React, { useState, useEffect } from 'react';
import { UserGroupIcon, HeartIcon, CalendarIcon, CurrencyDollarIcon } from '@heroicons/react/24/outline';

const Families = () => {
  const [families, setFamilies] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadFamilies();
  }, []);

  const loadFamilies = async () => {
    try {
      setLoading(true);
      // TODO: Implement family grouping API endpoint
      const response = await fetch('/api/persons?group_by_family=true', {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        // Group persons by household/family
        const familyMap = {};
        (data.persons || []).forEach(person => {
          const familyKey = person.family_id || person.household || 'single';
          if (!familyMap[familyKey]) {
            familyMap[familyKey] = {
              id: familyKey,
              members: [],
              household_heartbeat: 0,
              attendance_together: 0,
              attendance_drifting: false,
              parent_giving: false,
              care_needs: []
            };
          }
          familyMap[familyKey].members.push(person);
        });
        
        // Calculate household metrics
        Object.values(familyMap).forEach(family => {
          const heartbeats = family.members.map(m => {
            if (m.pulse_status === 'green') return 85;
            if (m.pulse_status === 'amber') return 65;
            if (m.pulse_status === 'red') return 35;
            return 50;
          });
          family.household_heartbeat = Math.round(
            heartbeats.reduce((a, b) => a + b, 0) / heartbeats.length
          );
        });
        
        setFamilies(Object.values(familyMap));
      }
    } catch (err) {
      console.error('Error loading families:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="mb-6">
        <h2 className="text-3xl font-bold text-white mb-2">Families</h2>
        <p className="text-white/60">Household behavior is the #1 pastoral predictor</p>
      </div>

      {loading ? (
        <div className="text-center py-12 text-white/60">Loading families...</div>
      ) : (
        <div className="space-y-4">
          {families.map((family) => (
            <div
              key={family.id}
              className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-6"
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">
                    {family.members.map(m => m.preferred_name || m.full_name).join(', ')}
                  </h3>
                  <div className="flex items-center gap-4 text-sm text-white/60">
                    <span>{family.members.length} {family.members.length === 1 ? 'member' : 'members'}</span>
                    <span className="flex items-center gap-1">
                      <HeartIcon className="h-4 w-4" />
                      Household Heartbeat: {family.household_heartbeat}
                    </span>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                <div className="bg-white/5 rounded-lg p-4">
                  <div className="text-white/60 text-sm mb-1">Attendance Together</div>
                  <div className="text-white text-lg font-semibold">
                    {family.attendance_together}%
                  </div>
                </div>
                <div className="bg-white/5 rounded-lg p-4">
                  <div className="text-white/60 text-sm mb-1">Parent Giving</div>
                  <div className="text-white text-lg font-semibold">
                    {family.parent_giving ? 'Yes' : 'No'}
                  </div>
                </div>
                <div className="bg-white/5 rounded-lg p-4">
                  <div className="text-white/60 text-sm mb-1">Status</div>
                  <div className={`text-lg font-semibold ${
                    family.attendance_drifting ? 'text-orange-400' : 'text-green-400'
                  }`}>
                    {family.attendance_drifting ? 'Drifting' : 'Stable'}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Families;

