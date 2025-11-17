import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

const PulseBadge = ({ status, score }) => {
  const colorMap = {
    green: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
    amber: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
    red: 'bg-red-500/20 text-red-300 border-red-500/40',
    default: 'bg-slate-500/20 text-slate-300 border-slate-500/40'
  };

  const labelMap = {
    green: 'Healthy',
    amber: 'Watch',
    red: 'At Risk'
  };

  const key = status || 'default';

  return (
    <div
      className={`inline-flex items-center px-4 py-2 rounded-full border text-sm font-medium ${
        colorMap[key] || colorMap.default
      }`}
    >
      <span className="w-3 h-3 rounded-full bg-current mr-2" />
      <span className="uppercase tracking-wide">
        {labelMap[status] || 'Unknown'}
      </span>
      {typeof score === 'number' && (
        <span className="ml-3 text-slate-200 font-semibold">{Math.round(score)}</span>
      )}
    </div>
  );
};

const PersonHealthReport = () => {
  const { personId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [person, setPerson] = useState(null);
  const [engagement, setEngagement] = useState(null);

  useEffect(() => {
    const controller = new AbortController();

    const fetchPerson = async () => {
      try {
        setLoading(true);
        setError('');

        const response = await fetch(`/api/persons/${personId}`, {
          credentials: 'include',
          signal: controller.signal
        });

        if (!response.ok) {
          if (response.status === 404) {
            throw new Error('Person not found');
          }
          throw new Error('Failed to load person details');
        }

        const data = await response.json();
        setPerson(data);
        setEngagement(data.engagement || {});
      } catch (err) {
        if (err.name !== 'AbortError') {
          console.error('Person health report load error:', err);
          setError(err.message || 'Unable to load person details right now.');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchPerson();
    return () => controller.abort();
  }, [personId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
        <div className="max-w-6xl mx-auto flex items-center justify-center py-20">
          <div className="flex items-center gap-3 text-slate-400 text-sm">
            <span className="inline-block w-4 h-4 border-2 border-slate-500 border-t-transparent rounded-full animate-spin" />
            Loading health report...
          </div>
        </div>
      </div>
    );
  }

  if (error || !person) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
        <div className="max-w-6xl mx-auto">
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="mb-4 text-sm text-slate-400 hover:text-slate-200"
          >
            ← Back
          </button>
          <div className="py-6 text-center text-sm text-red-300 bg-red-900/20 rounded-lg border border-red-800/40">
            {error || 'Person not found'}
          </div>
        </div>
      </div>
    );
  }

  const lastSeen = engagement.last_seen ? new Date(engagement.last_seen) : null;
  const daysSince = lastSeen
    ? Math.floor((new Date() - lastSeen) / (1000 * 60 * 60 * 24))
    : null;

  // Process attendance log for timeline
  const attendanceLog = engagement.attendance_log || [];
  const recentAttendance = attendanceLog
    .filter((entry) => {
      if (!entry.timestamp) return false;
      const entryDate = new Date(entry.timestamp);
      const sixMonthsAgo = new Date();
      sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6);
      return entryDate >= sixMonthsAgo;
    })
    .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
    .slice(0, 12); // Last 12 attendance records

  // Generate suggested next steps
  const generateNextSteps = () => {
    const steps = [];
    const status = engagement.pulse_status || 'red';

    if (status === 'red') {
      if (!lastSeen) {
        steps.push({
          action: 'Reach out',
          description: 'No attendance recorded. Consider a personal call or visit.',
          priority: 'high'
        });
      } else if (daysSince > 28) {
        steps.push({
          action: 'Pastoral follow-up',
          description: `Haven't seen them in ${daysSince} days. Check in on their wellbeing.`,
          priority: 'high'
        });
      }
      if (!person.connect_group) {
        steps.push({
          action: 'Invite to Connect Group',
          description: 'Not currently in a group. Connection is key to engagement.',
          priority: 'medium'
        });
      }
    } else if (status === 'amber') {
      if (daysSince > 21) {
        steps.push({
          action: 'Gentle check-in',
          description: "Consider reaching out to see how they're doing.",
          priority: 'medium'
        });
      }
      if (!person.connect_group) {
        steps.push({
          action: 'Connect Group invitation',
          description: 'Encourage joining a group for deeper community.',
          priority: 'low'
        });
      }
    } else {
      steps.push({
        action: 'Maintain connection',
        description: 'Keep encouraging and celebrating their engagement.',
        priority: 'low'
      });
    }

    return steps;
  };

  const nextSteps = generateNextSteps();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="text-sm text-slate-400 hover:text-slate-200 flex items-center gap-2"
        >
          ← Back to Heartbeat
        </button>

        {/* Header Card */}
        <div className="bg-slate-900/70 border border-slate-700/70 rounded-2xl p-6">
          <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
            <div className="flex-1">
              <div className="flex items-center gap-4 mb-3">
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-purple-500/30 to-blue-500/30 flex items-center justify-center text-2xl font-bold text-white">
                  {person.full_name
                    .split(' ')
                    .map((n) => n[0])
                    .join('')
                    .toUpperCase()
                    .slice(0, 2)}
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-white">{person.full_name}</h1>
                  {person.preferred_name && person.preferred_name !== person.full_name && (
                    <p className="text-sm text-slate-400">Preferred: {person.preferred_name}</p>
                  )}
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-4 text-sm text-slate-300">
                {person.email && (
                  <div>
                    <span className="text-slate-500">Email:</span> {person.email}
                  </div>
                )}
                {person.phone && (
                  <div>
                    <span className="text-slate-500">Phone:</span> {person.phone}
                  </div>
                )}
                {person.campus && (
                  <div>
                    <span className="text-slate-500">Campus:</span>{' '}
                    <span className="capitalize">{person.campus}</span>
                  </div>
                )}
                {person.department && (
                  <div>
                    <span className="text-slate-500">Department:</span>{' '}
                    <span className="capitalize">{person.department.replace('_', ' ')}</span>
                  </div>
                )}
              </div>
            </div>
            <div className="flex flex-col items-end gap-3">
              <PulseBadge
                status={engagement.pulse_status}
                score={engagement.overall_engagement}
              />
              {lastSeen && (
                <div className="text-right">
                  <div className="text-xs text-slate-400 uppercase tracking-wide">Last Seen</div>
                  <div className="text-sm text-slate-200">
                    {lastSeen.toLocaleDateString()} ({daysSince === 0 ? 'Today' : `${daysSince} days ago`})
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          {/* Left Column: Overview & Reasons */}
          <div className="space-y-6">
            {/* Pulse Status Explanation */}
            <div className="bg-slate-900/70 border border-slate-700/70 rounded-2xl p-5">
              <h2 className="text-lg font-semibold text-white mb-3">Current Status</h2>
              <div className="space-y-2">
                {engagement.pulse_reasons && engagement.pulse_reasons.length > 0 ? (
                  engagement.pulse_reasons.map((reason, idx) => (
                    <div
                      key={idx}
                      className="text-sm text-slate-300 bg-slate-800/50 rounded-lg p-3 border border-slate-700/50"
                    >
                      {reason}
                    </div>
                  ))
                ) : (
                  <div className="text-sm text-slate-400">No engagement data available yet.</div>
                )}
              </div>
            </div>

            {/* Next Steps */}
            {nextSteps.length > 0 && (
              <div className="bg-slate-900/70 border border-slate-700/70 rounded-2xl p-5">
                <h2 className="text-lg font-semibold text-white mb-3">Suggested Next Steps</h2>
                <div className="space-y-2">
                  {nextSteps.map((step, idx) => (
                    <div
                      key={idx}
                      className={`text-sm rounded-lg p-3 border ${
                        step.priority === 'high'
                          ? 'bg-red-900/20 border-red-500/40 text-red-200'
                          : step.priority === 'medium'
                          ? 'bg-amber-900/20 border-amber-500/40 text-amber-200'
                          : 'bg-slate-800/50 border-slate-700/50 text-slate-300'
                      }`}
                    >
                      <div className="font-medium mb-1">{step.action}</div>
                      <div className="text-xs opacity-90">{step.description}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Connection Info */}
            <div className="bg-slate-900/70 border border-slate-700/70 rounded-2xl p-5">
              <h2 className="text-lg font-semibold text-white mb-3">Connection</h2>
              <div className="space-y-2 text-sm text-slate-300">
                {person.connect_group ? (
                  <div>
                    <span className="text-slate-500">Connect Group:</span> {person.connect_group}
                  </div>
                ) : (
                  <div className="text-amber-300">Not in a Connect Group</div>
                )}
                {person.dream_team_roles && person.dream_team_roles.length > 0 ? (
                  <div>
                    <span className="text-slate-500">Serving:</span>{' '}
                    {person.dream_team_roles.join(', ')}
                  </div>
                ) : (
                  <div className="text-slate-400">Not currently serving</div>
                )}
              </div>
            </div>
          </div>

          {/* Right Column: Timeline & Metrics */}
          <div className="space-y-6">
            {/* Attendance Timeline */}
            <div className="bg-slate-900/70 border border-slate-700/70 rounded-2xl p-5">
              <h2 className="text-lg font-semibold text-white mb-3">Recent Attendance</h2>
              {recentAttendance.length > 0 ? (
                <div className="space-y-2">
                  {recentAttendance.map((entry, idx) => {
                    const entryDate = new Date(entry.timestamp);
                    return (
                      <div
                        key={idx}
                        className="flex items-center justify-between text-sm bg-slate-800/50 rounded-lg p-3 border border-slate-700/50"
                      >
                        <div>
                          <div className="text-slate-200 font-medium">
                            {entryDate.toLocaleDateString()}
                          </div>
                          {entry.campus && (
                            <div className="text-xs text-slate-400">{entry.campus}</div>
                          )}
                        </div>
                        <div className="text-xs text-emerald-400">✓ Attended</div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="text-sm text-slate-400">No attendance records in the last 6 months.</div>
              )}
            </div>

            {/* Engagement Metrics */}
            <div className="bg-slate-900/70 border border-slate-700/70 rounded-2xl p-5">
              <h2 className="text-lg font-semibold text-white mb-3">Engagement Metrics</h2>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700/50">
                  <div className="text-xs text-slate-400 uppercase tracking-wide mb-1">
                    Attendance Frequency
                  </div>
                  <div className="text-xl font-semibold text-white">
                    {engagement.attendance_frequency
                      ? Math.round(engagement.attendance_frequency * 100)
                      : 0}
                    %
                  </div>
                </div>
                <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700/50">
                  <div className="text-xs text-slate-400 uppercase tracking-wide mb-1">
                    Overall Engagement
                  </div>
                  <div className="text-xl font-semibold text-white">
                    {engagement.overall_engagement
                      ? Math.round(engagement.overall_engagement)
                      : 0}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PersonHealthReport;

