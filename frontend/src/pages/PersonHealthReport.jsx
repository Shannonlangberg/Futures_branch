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

// Engagement Metric Card Component
const EngagementMetricCard = ({ icon, label, value, maxValue, color, trend, subtitle }) => {
  const percentage = maxValue > 0 ? Math.min((value / maxValue) * 100, 100) : 0;
  
  return (
    <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-xl">{icon}</span>
          <div>
            <div className="text-xs text-slate-400 uppercase tracking-wide">{label}</div>
            {subtitle && (
              <div className="text-[10px] text-slate-500 mt-0.5">{subtitle}</div>
            )}
          </div>
        </div>
        {trend && (
          <span className={`text-xs font-medium ${
            trend === 'up' ? 'text-emerald-400' : trend === 'down' ? 'text-red-400' : 'text-slate-400'
          }`}>
            {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'}
          </span>
        )}
      </div>
      <div className="flex items-baseline gap-2 mb-2">
        <div className="text-2xl font-bold text-white">{value}</div>
        {maxValue && (
          <div className="text-sm text-slate-400">/ {maxValue}</div>
        )}
      </div>
      {maxValue > 0 && (
        <div className="w-full bg-slate-900/50 rounded-full h-2 overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${color}`}
            style={{ width: `${percentage}%` }}
          />
        </div>
      )}
    </div>
  );
};

// Simple mini chart for trends
const MiniTrendChart = ({ data, color = 'blue' }) => {
  if (!data || data.length === 0) {
    return (
      <div className="h-12 flex items-center justify-center text-xs text-slate-500">
        No data
      </div>
    );
  }

  const maxValue = Math.max(...data.map(d => d.value), 1);
  const width = 100 / data.length;

  return (
    <div className="h-12 flex items-end gap-0.5">
      {data.map((point, idx) => {
        const height = (point.value / maxValue) * 100;
        return (
          <div
            key={idx}
            className={`flex-1 bg-gradient-to-t ${color} rounded-t transition-all duration-300 hover:opacity-80`}
            style={{ height: `${Math.max(height, 5)}%` }}
            title={`${point.label}: ${point.value}`}
          />
        );
      })}
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
  const [aiNextSteps, setAiNextSteps] = useState([]);

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
        setAiNextSteps(data.ai_next_steps || []);
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

  // Process all engagement logs
  const attendanceLog = engagement.attendance_log || [];
  const bibleLog = engagement.bible_log || [];
  const givingLog = engagement.giving_log || [];
  const servingLog = engagement.serving_log || [];
  const groupAttendanceLog = engagement.group_attendance_log || [];

  // Calculate metrics for last 8 weeks (56 days)
  const now = new Date();
  const eightWeeksAgo = new Date(now.getTime() - 56 * 24 * 60 * 60 * 1000);

  const recentAttendance = attendanceLog.filter((entry) => {
    if (!entry.timestamp) return false;
    return new Date(entry.timestamp) >= eightWeeksAgo;
  });

  const recentBible = bibleLog.filter((entry) => {
    if (!entry.date) return false;
    return new Date(entry.date) >= eightWeeksAgo;
  });

  const recentGiving = givingLog.filter((entry) => {
    if (!entry.date) return false;
    return new Date(entry.date) >= eightWeeksAgo;
  });

  const recentServing = servingLog.filter((entry) => {
    if (!entry.date) return false;
    return new Date(entry.date) >= eightWeeksAgo;
  });

  const recentGroupAttendance = groupAttendanceLog.filter((entry) => {
    if (!entry.date) return false;
    return new Date(entry.date) >= eightWeeksAgo;
  });

  // Calculate totals
  const totalGiving = recentGiving.reduce((sum, entry) => sum + (parseFloat(entry.amount) || 0), 0);
  const uniqueServingRoles = [...new Set(recentServing.map(s => s.role).filter(Boolean))];
  const uniqueGroups = [...new Set(recentGroupAttendance.map(g => g.group_id).filter(Boolean))];

  // Calculate frequencies (0-1 scale)
  const attendanceFreq = Math.min(recentAttendance.length / 8, 1.0);
  const bibleFreq = Math.min(recentBible.length / 56, 1.0); // Daily reading
  const givingFreq = Math.min(recentGiving.length / 8, 1.0); // Weekly giving
  const servingFreq = Math.min(recentServing.length / 8, 1.0);
  const groupFreq = Math.min(recentGroupAttendance.length / 8, 1.0);

  // Generate trend data (last 6 months, monthly buckets)
  const generateTrendData = (log, dateField = 'timestamp') => {
    const sixMonthsAgo = new Date(now.getTime() - 180 * 24 * 60 * 60 * 1000);
    const monthlyData = {};
    
    log.forEach((entry) => {
      const date = new Date(entry[dateField] || entry.date || entry.timestamp);
      if (date >= sixMonthsAgo) {
        const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
        monthlyData[monthKey] = (monthlyData[monthKey] || 0) + 1;
      }
    });

    const months = [];
    for (let i = 5; i >= 0; i--) {
      const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
      const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
      months.push({
        label: date.toLocaleDateString('en-US', { month: 'short' }),
        value: monthlyData[monthKey] || 0
      });
    }

    return months;
  };

  const attendanceTrend = generateTrendData(attendanceLog, 'timestamp');
  const bibleTrend = generateTrendData(bibleLog, 'date');
  const givingTrend = generateTrendData(givingLog, 'date');

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

  // Discipleship milestones
  const milestones = [];
  if (person.dna_completed) milestones.push({ label: 'DNA Completed', date: person.dna_completed, icon: '📚' });
  if (person.baptised_on) milestones.push({ label: 'Baptised', date: person.baptised_on, icon: '💧' });
  if (person.filled_holy_spirit) milestones.push({ label: 'Filled with Holy Spirit', date: person.filled_holy_spirit, icon: '🔥' });
  if (person.rise_attended) milestones.push({ label: 'RISE Attended', date: person.rise_attended, icon: '⭐' });
  if (person.first_served_on) milestones.push({ label: 'First Served', date: person.first_served_on, icon: '🤝' });

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="text-sm text-slate-400 hover:text-slate-200 flex items-center gap-2 transition"
        >
          ← Back to Heartbeat
        </button>

        {/* Enhanced Header Card */}
        <div className="bg-gradient-to-br from-slate-900/90 to-slate-800/90 border border-slate-700/70 rounded-2xl p-6 shadow-xl">
          <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-6">
            <div className="flex-1">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-purple-500/40 to-blue-500/40 flex items-center justify-center text-3xl font-bold text-white shadow-lg">
                  {person.full_name
                    .split(' ')
                    .map((n) => n[0])
                    .join('')
                    .toUpperCase()
                    .slice(0, 2)}
                </div>
                <div>
                  <h1 className="text-3xl font-bold text-white mb-1">{person.full_name}</h1>
                  {person.preferred_name && person.preferred_name !== person.full_name && (
                    <p className="text-sm text-slate-400">Preferred: {person.preferred_name}</p>
                  )}
                  <div className="flex flex-wrap items-center gap-3 mt-2 text-sm text-slate-300">
                    {person.campus && (
                      <span className="px-2 py-1 bg-slate-800/50 rounded-lg text-xs">
                        📍 {person.campus.replace('_', ' ')}
                      </span>
                    )}
                    {person.department && (
                      <span className="px-2 py-1 bg-slate-800/50 rounded-lg text-xs capitalize">
                        👥 {person.department.replace('_', ' ')}
                      </span>
                    )}
                  </div>
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-4 text-sm text-slate-300">
                {person.email && (
                  <div className="flex items-center gap-1">
                    <span className="text-slate-500">✉️</span>
                    <span>{person.email}</span>
                  </div>
                )}
                {person.phone && (
                  <div className="flex items-center gap-1">
                    <span className="text-slate-500">📞</span>
                    <span>{person.phone}</span>
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
                  <div className="text-xs text-slate-400 uppercase tracking-wide mb-1">Last Seen</div>
                  <div className="text-lg font-semibold text-slate-200">
                    {lastSeen.toLocaleDateString()}
                  </div>
                  <div className="text-xs text-slate-400">
                    {daysSince === 0 ? 'Today' : daysSince === 1 ? 'Yesterday' : `${daysSince} days ago`}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Engagement Breakdown - Visual Overview */}
        <div className="bg-gradient-to-br from-slate-900/90 to-slate-800/90 border border-slate-700/70 rounded-2xl p-6 shadow-xl">
          <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
            <span>📊</span>
            Engagement Breakdown
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            <EngagementMetricCard
              icon="🏛️"
              label="Attendance"
              value={recentAttendance.length}
              maxValue={8}
              color="bg-blue-500"
              subtitle="Last 8 weeks"
            />
            <EngagementMetricCard
              icon="📖"
              label="Bible Reading"
              value={recentBible.length}
              maxValue={56}
              color="bg-purple-500"
              subtitle="Last 8 weeks"
            />
            <EngagementMetricCard
              icon="💰"
              label="Giving"
              value={recentGiving.length}
              maxValue={8}
              color="bg-emerald-500"
              subtitle={`$${totalGiving.toLocaleString()}`}
            />
            <EngagementMetricCard
              icon="🤝"
              label="Serving"
              value={recentServing.length}
              maxValue={8}
              color="bg-amber-500"
              subtitle={`${uniqueServingRoles.length} role${uniqueServingRoles.length !== 1 ? 's' : ''}`}
            />
            <EngagementMetricCard
              icon="👥"
              label="Connect Groups"
              value={recentGroupAttendance.length}
              maxValue={8}
              color="bg-indigo-500"
              subtitle={`${uniqueGroups.length} group${uniqueGroups.length !== 1 ? 's' : ''}`}
            />
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          {/* Left Column: Status & Next Steps */}
          <div className="lg:col-span-2 space-y-6">
            {/* Current Status */}
            <div className="bg-slate-900/70 border border-slate-700/70 rounded-2xl p-5">
              <h2 className="text-lg font-semibold text-white mb-4">Current Status</h2>
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

            {/* Suggested Next Steps */}
            {(aiNextSteps.length > 0 || nextSteps.length > 0) && (
              <div className="bg-slate-900/70 border border-slate-700/70 rounded-2xl p-5">
                <div className="flex items-center gap-2 mb-4">
                  <h2 className="text-lg font-semibold text-white">Suggested Next Steps</h2>
                  {aiNextSteps.length > 0 && (
                    <span className="text-xs text-purple-300 bg-purple-500/20 px-2 py-1 rounded-full">
                      AI-Powered
                    </span>
                  )}
                </div>
                <div className="space-y-2">
                  {aiNextSteps.length > 0
                    ? aiNextSteps.map((step, idx) => (
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
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1">
                              <div className="font-medium mb-1">{step.action}</div>
                              <div className="text-xs opacity-90">{step.description}</div>
                              {step.milestone && (
                                <div className="text-xs text-slate-400 mt-1">
                                  Related to: {step.milestone}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ))
                    : nextSteps.map((step, idx) => (
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

            {/* Engagement Trends */}
            <div className="bg-slate-900/70 border border-slate-700/70 rounded-2xl p-5">
              <h2 className="text-lg font-semibold text-white mb-4">Engagement Trends (6 Months)</h2>
              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-slate-300">Attendance</span>
                    <span className="text-xs text-slate-400">{recentAttendance.length} in last 8 weeks</span>
                  </div>
                  <MiniTrendChart data={attendanceTrend} color="from-blue-500 to-blue-600" />
                </div>
                {recentBible.length > 0 && (
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-slate-300">Bible Reading</span>
                      <span className="text-xs text-slate-400">{recentBible.length} days in last 8 weeks</span>
                    </div>
                    <MiniTrendChart data={bibleTrend} color="from-purple-500 to-purple-600" />
                  </div>
                )}
                {recentGiving.length > 0 && (
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-slate-300">Giving</span>
                      <span className="text-xs text-slate-400">{recentGiving.length} times in last 8 weeks</span>
                    </div>
                    <MiniTrendChart data={givingTrend} color="from-emerald-500 to-emerald-600" />
                  </div>
                )}
              </div>
            </div>

            {/* Connection Info */}
            <div className="bg-slate-900/70 border border-slate-700/70 rounded-2xl p-5">
              <h2 className="text-lg font-semibold text-white mb-4">Connection</h2>
              <div className="space-y-3">
                {person.connect_group ? (
                  <div className="flex items-center gap-2 text-sm text-slate-300">
                    <span className="text-emerald-400">✓</span>
                    <span className="text-slate-500">Connect Group:</span>
                    <span className="font-medium">{person.connect_group}</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-2 text-sm text-amber-300">
                    <span>⚠️</span>
                    <span>Not in a Connect Group</span>
                  </div>
                )}
                {person.dream_team_roles && person.dream_team_roles.length > 0 ? (
                  <div className="flex items-center gap-2 text-sm text-slate-300">
                    <span className="text-emerald-400">✓</span>
                    <span className="text-slate-500">Serving:</span>
                    <div className="flex flex-wrap gap-1">
                      {person.dream_team_roles.map((role, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 bg-slate-800/50 rounded text-xs border border-slate-700/50"
                        >
                          {role}
                        </span>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center gap-2 text-sm text-slate-400">
                    <span>—</span>
                    <span>Not currently serving</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Column: Metrics & Timeline */}
          <div className="space-y-6">
            {/* Overall Engagement Score */}
            <div className="bg-gradient-to-br from-purple-900/30 to-blue-900/30 border border-purple-500/40 rounded-2xl p-5">
              <h2 className="text-lg font-semibold text-white mb-4">Overall Engagement</h2>
              <div className="text-center mb-4">
                <div className="text-5xl font-bold text-white mb-2">
                  {engagement.overall_engagement ? Math.round(engagement.overall_engagement) : 0}
                </div>
                <div className="text-sm text-slate-400">out of 100</div>
              </div>
              <div className="w-full bg-slate-900/50 rounded-full h-3 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-purple-500 to-blue-500 rounded-full transition-all duration-500"
                  style={{
                    width: `${Math.min(engagement.overall_engagement || 0, 100)}%`
                  }}
                />
              </div>
              <div className="mt-4 grid grid-cols-2 gap-3 text-xs">
                <div>
                  <div className="text-slate-400 mb-1">Attendance</div>
                  <div className="text-white font-semibold">
                    {Math.round(attendanceFreq * 100)}%
                  </div>
                </div>
                <div>
                  <div className="text-slate-400 mb-1">Frequency</div>
                  <div className="text-white font-semibold">
                    {engagement.attendance_frequency
                      ? Math.round(engagement.attendance_frequency * 100)
                      : 0}%
                  </div>
                </div>
              </div>
            </div>

            {/* Discipleship Milestones */}
            {milestones.length > 0 && (
              <div className="bg-slate-900/70 border border-slate-700/70 rounded-2xl p-5">
                <h2 className="text-lg font-semibold text-white mb-4">Discipleship Journey</h2>
                <div className="space-y-2">
                  {milestones.map((milestone, idx) => (
                    <div
                      key={idx}
                      className="flex items-center gap-3 text-sm bg-slate-800/50 rounded-lg p-3 border border-slate-700/50"
                    >
                      <span className="text-xl">{milestone.icon}</span>
                      <div className="flex-1">
                        <div className="text-slate-200 font-medium">{milestone.label}</div>
                        <div className="text-xs text-slate-400">
                          {new Date(milestone.date).toLocaleDateString()}
                        </div>
                      </div>
                      <span className="text-emerald-400">✓</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recent Attendance Timeline */}
            <div className="bg-slate-900/70 border border-slate-700/70 rounded-2xl p-5">
              <h2 className="text-lg font-semibold text-white mb-4">Recent Attendance</h2>
              {recentAttendance.length > 0 ? (
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {recentAttendance
                    .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
                    .slice(0, 10)
                    .map((entry, idx) => {
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
                          <div className="text-xs text-emerald-400">✓</div>
                        </div>
                      );
                    })}
                </div>
              ) : (
                <div className="text-sm text-slate-400 text-center py-4">
                  No attendance records in the last 8 weeks.
                </div>
              )}
            </div>

            {/* Additional Engagement Data */}
            {(recentBible.length > 0 || recentGiving.length > 0 || recentServing.length > 0) && (
              <div className="bg-slate-900/70 border border-slate-700/70 rounded-2xl p-5">
                <h2 className="text-lg font-semibold text-white mb-4">Additional Engagement</h2>
                <div className="space-y-3 text-sm">
                  {recentBible.length > 0 && (
                    <div className="flex items-center justify-between">
                      <span className="text-slate-300">📖 Bible Reading</span>
                      <span className="text-slate-200 font-medium">{recentBible.length} days</span>
                    </div>
                  )}
                  {recentGiving.length > 0 && (
                    <div className="flex items-center justify-between">
                      <span className="text-slate-300">💰 Giving</span>
                      <span className="text-slate-200 font-medium">
                        {recentGiving.length} times (${totalGiving.toLocaleString()})
                      </span>
                    </div>
                  )}
                  {recentServing.length > 0 && (
                    <div className="flex items-center justify-between">
                      <span className="text-slate-300">🤝 Serving</span>
                      <span className="text-slate-200 font-medium">
                        {recentServing.length} times
                      </span>
                    </div>
                  )}
                  {recentGroupAttendance.length > 0 && (
                    <div className="flex items-center justify-between">
                      <span className="text-slate-300">👥 Connect Groups</span>
                      <span className="text-slate-200 font-medium">
                        {recentGroupAttendance.length} meetings
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PersonHealthReport;
