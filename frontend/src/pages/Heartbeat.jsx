import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

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
      className={`inline-flex items-center px-3 py-1 rounded-full border text-xs font-medium ${
        colorMap[key] || colorMap.default
      }`}
    >
      <span className="w-2 h-2 rounded-full bg-current mr-2" />
      <span className="uppercase tracking-wide">
        {labelMap[status] || 'Unknown'}
      </span>
      {typeof score === 'number' && (
        <span className="ml-2 text-slate-200">{Math.round(score)}</span>
      )}
    </div>
  );
};

// Simple donut chart component
const DonutChart = ({ data, size = 120 }) => {
  const { green, amber, red, total } = data;
  const radius = size / 2 - 8;
  const circumference = 2 * Math.PI * radius;
  
  const greenPercent = total > 0 ? (green / total) * 100 : 0;
  const amberPercent = total > 0 ? (amber / total) * 100 : 0;
  const redPercent = total > 0 ? (red / total) * 100 : 0;
  
  const greenOffset = circumference - (greenPercent / 100) * circumference;
  const amberOffset = circumference - ((greenPercent + amberPercent) / 100) * circumference;
  const redOffset = circumference - ((greenPercent + amberPercent + redPercent) / 100) * circumference;
  
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(51, 65, 85, 0.5)"
          strokeWidth="8"
        />
        {/* Red segment */}
        {redPercent > 0 && (
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="#ef4444"
            strokeWidth="8"
            strokeDasharray={circumference}
            strokeDashoffset={redOffset}
            strokeLinecap="round"
            className="transition-all duration-500"
          />
        )}
        {/* Amber segment */}
        {amberPercent > 0 && (
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="#f59e0b"
            strokeWidth="8"
            strokeDasharray={circumference}
            strokeDashoffset={amberOffset}
            strokeLinecap="round"
            className="transition-all duration-500"
          />
        )}
        {/* Green segment */}
        {greenPercent > 0 && (
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="#10b981"
            strokeWidth="8"
            strokeDasharray={circumference}
            strokeDashoffset={greenOffset}
            strokeLinecap="round"
            className="transition-all duration-500"
          />
        )}
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="text-center">
          <div className="text-2xl font-bold text-white">{total}</div>
          <div className="text-xs text-slate-400">Total</div>
        </div>
      </div>
    </div>
  );
};

const Heartbeat = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [people, setPeople] = useState([]);
  const [needingAttention, setNeedingAttention] = useState([]);
  const [campuses, setCampuses] = useState([]);
  const [aiInsights, setAiInsights] = useState(null);
  const [aiAlerts, setAiAlerts] = useState([]);
  const [loadingAlerts, setLoadingAlerts] = useState(false);
  const [summary, setSummary] = useState({
    total: 0,
    green: 0,
    amber: 0,
    red: 0
  });
  const [filters, setFilters] = useState({
    campus: 'all_campuses',
    pulse_status: '',
    department: 'all',
    search: ''
  });

  // Load campuses for filter (honours backend scoping per role)
  useEffect(() => {
    const controller = new AbortController();

    const fetchCampuses = async () => {
      try {
        const response = await fetch('/api/campuses', {
          credentials: 'include',
          signal: controller.signal
        });
        if (!response.ok) return;
        const data = await response.json();
        const items = data.campuses || [];
        setCampuses(items);
        if (data.default && data.default !== 'all_campuses') {
          setFilters((prev) => ({
            ...prev,
            campus: data.default
          }));
        }
      } catch (err) {
        if (err.name !== 'AbortError') {
          console.error('Error loading campuses for heartbeat:', err);
        }
      }
    };

    fetchCampuses();

    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    const fetchHeartbeat = async () => {
      try {
        setLoading(true);
        setError('');

        const params = new URLSearchParams();
        if (filters.campus && filters.campus !== 'all_campuses') {
          params.append('campus', filters.campus);
        }
        if (filters.pulse_status) {
          params.append('pulse_status', filters.pulse_status);
        }
        if (filters.department && filters.department !== 'all') {
          params.append('department', filters.department);
        }
        if (filters.search.trim()) {
          params.append('search', filters.search.trim());
        }

        const response = await fetch(`/api/heartbeat?${params.toString()}`, {
          credentials: 'include',
          signal: controller.signal
        });

        if (!response.ok) {
          throw new Error('Failed to load heartbeat data');
        }

        const data = await response.json();
        const persons = data.persons || [];
        setPeople(persons);
        setAiInsights(data.ai_insights || null);

        // Build simple summary for cards
        const counts = persons.reduce(
          (acc, p) => {
            acc.total += 1;
            if (p.pulse_status === 'green') acc.green += 1;
            else if (p.pulse_status === 'amber') acc.amber += 1;
            else if (p.pulse_status === 'red') acc.red += 1;
            return acc;
          },
          { total: 0, green: 0, amber: 0, red: 0 }
        );
        setSummary(counts);

        // Identify people needing attention (red + high-priority amber)
        const needingAttention = persons
          .filter((p) => {
            if (p.pulse_status === 'red') return true;
            if (p.pulse_status === 'amber') {
              // Include amber if last seen > 21 days ago
              if (p.last_seen) {
                const daysSince = Math.floor(
                  (new Date() - new Date(p.last_seen)) / (1000 * 60 * 60 * 24)
                );
                return daysSince > 21;
              }
              return true; // Include amber with no attendance
            }
            return false;
          })
          .sort((a, b) => {
            // Sort red first, then by last_seen (oldest first)
            if (a.pulse_status === 'red' && b.pulse_status !== 'red') return -1;
            if (a.pulse_status !== 'red' && b.pulse_status === 'red') return 1;
            const aDate = a.last_seen ? new Date(a.last_seen) : new Date(0);
            const bDate = b.last_seen ? new Date(b.last_seen) : new Date(0);
            return aDate - bDate;
          })
          .slice(0, 10); // Top 10 priorities

        setNeedingAttention(needingAttention);
      } catch (err) {
        if (err.name !== 'AbortError') {
          console.error('Heartbeat load error:', err);
          setError('Unable to load heartbeat right now. Please try again soon.');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchHeartbeat();

    return () => controller.abort();
  }, [filters.campus, filters.pulse_status, filters.department, filters.search]);

  // Load AI alerts
  useEffect(() => {
    const controller = new AbortController();

    const fetchAlerts = async () => {
      try {
        setLoadingAlerts(true);
        const params = new URLSearchParams();
        if (filters.campus && filters.campus !== 'all_campuses') {
          params.append('campus', filters.campus);
        }
        params.append('status', 'active');
        params.append('limit', '10');

        const response = await fetch(`/api/heartbeat/alerts?${params.toString()}`, {
          credentials: 'include',
          signal: controller.signal
        });

        if (response.ok) {
          const data = await response.json();
          setAiAlerts(data.alerts || []);
        }
      } catch (err) {
        if (err.name !== 'AbortError') {
          console.error('Error loading AI alerts:', err);
        }
      } finally {
        setLoadingAlerts(false);
      }
    };

    fetchAlerts();
    // Refresh alerts every 30 seconds
    const interval = setInterval(fetchAlerts, 30000);

    return () => {
      controller.abort();
      clearInterval(interval);
    };
  }, [filters.campus]);

  const handleFilterChange = (field, value) => {
    setFilters((prev) => ({
      ...prev,
      [field]: value
    }));
  };

  const pulseFilters = [
    { value: '', label: 'All' },
    { value: 'green', label: 'Healthy' },
    { value: 'amber', label: 'Watch' },
    { value: 'red', label: 'At Risk' }
  ];

  const departmentFilters = [
    { value: 'all', label: 'All' },
    { value: 'kids', label: 'Kids' },
    { value: 'youth', label: 'Youth' },
    { value: 'young_adults', label: 'Young Adults' },
    { value: 'families', label: 'Families' },
    { value: 'adults', label: 'Adults' },
    { value: 'seniors', label: 'Seniors' }
  ];

  const healthyPercent = summary.total > 0 ? Math.round((summary.green / summary.total) * 100) : 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-4xl font-bold text-white flex items-center gap-3">
              <span className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-purple-500 to-blue-500 text-2xl shadow-lg">
                💜
              </span>
              Heartbeat Dashboard
            </h1>
            <p className="text-sm text-slate-400 mt-2">
              Live view of your people&apos;s engagement health to help pastors see who&apos;s thriving and who may need a touch.
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            {pulseFilters.map((pf) => (
              <button
                key={pf.value || 'all'}
                type="button"
                onClick={() => handleFilterChange('pulse_status', pf.value)}
                className={`px-3 py-1.5 rounded-full text-xs font-medium border transition ${
                  filters.pulse_status === pf.value
                    ? 'bg-slate-100 text-slate-900 border-slate-100'
                    : 'bg-slate-800/60 text-slate-300 border-slate-700 hover:bg-slate-700'
                }`}
              >
                {pf.label}
              </button>
            ))}
            <div className="w-full sm:w-auto border-l border-slate-700 pl-2 sm:pl-0 sm:border-l-0">
              <span className="text-xs text-slate-400 mr-2">Department:</span>
              {departmentFilters.map((df) => (
                <button
                  key={df.value}
                  type="button"
                  onClick={() => handleFilterChange('department', df.value)}
                  className={`px-3 py-1.5 rounded-full text-xs font-medium border transition mr-1 ${
                    filters.department === df.value
                      ? 'bg-purple-500/20 text-purple-200 border-purple-500/60'
                      : 'bg-slate-800/60 text-slate-300 border-slate-700 hover:bg-slate-700'
                  }`}
                >
                  {df.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Summary Cards with Visual Chart */}
        <div className="grid gap-6 md:grid-cols-5">
          <div className="md:col-span-2 bg-gradient-to-br from-slate-900/90 to-slate-800/90 border border-slate-700/70 rounded-2xl p-6 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <div>
                <div className="text-xs text-slate-400 uppercase tracking-wide mb-1">
                  Campus Overview
                </div>
                <div className="text-3xl font-bold text-white">
                  {summary.total} {summary.total === 1 ? 'Person' : 'People'}
                </div>
              </div>
              <DonutChart data={summary} size={100} />
            </div>
            <div className="grid grid-cols-3 gap-3 mt-4">
              <div className="text-center">
                <div className="text-lg font-semibold text-emerald-300">{summary.green}</div>
                <div className="text-xs text-slate-400">Healthy</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-semibold text-amber-300">{summary.amber}</div>
                <div className="text-xs text-slate-400">Watch</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-semibold text-red-300">{summary.red}</div>
                <div className="text-xs text-slate-400">At Risk</div>
              </div>
            </div>
          </div>

          <div className="bg-emerald-900/30 border border-emerald-500/40 rounded-2xl p-6 shadow-lg backdrop-blur-sm">
            <div className="text-xs text-emerald-300 uppercase tracking-wide mb-2">
              Healthy
            </div>
            <div className="text-4xl font-bold text-emerald-100 mb-2">
              {summary.green}
            </div>
            <div className="text-sm text-emerald-400/80 mb-3">
              {healthyPercent}% of total
            </div>
            <div className="text-xs text-emerald-300/70">
              Thriving & engaged
            </div>
          </div>

          <div className="bg-amber-900/30 border border-amber-500/40 rounded-2xl p-6 shadow-lg backdrop-blur-sm">
            <div className="text-xs text-amber-300 uppercase tracking-wide mb-2">
              Watch
            </div>
            <div className="text-4xl font-bold text-amber-100 mb-2">
              {summary.amber}
            </div>
            <div className="text-sm text-amber-400/80 mb-3">
              {summary.total > 0 ? Math.round((summary.amber / summary.total) * 100) : 0}% of total
            </div>
            <div className="text-xs text-amber-300/70">
              Needs attention soon
            </div>
          </div>

          <div className="bg-red-900/30 border border-red-500/40 rounded-2xl p-6 shadow-lg backdrop-blur-sm">
            <div className="text-xs text-red-300 uppercase tracking-wide mb-2">
              At Risk
            </div>
            <div className="text-4xl font-bold text-red-100 mb-2">
              {summary.red}
            </div>
            <div className="text-sm text-red-400/80 mb-3">
              {summary.total > 0 ? Math.round((summary.red / summary.total) * 100) : 0}% of total
            </div>
            <div className="text-xs text-red-300/70">
              Urgent follow-up needed
            </div>
          </div>
        </div>

        {/* AI Monitoring Section - The AI Pastor */}
        <div className="bg-gradient-to-br from-indigo-900/40 via-purple-900/30 to-blue-900/40 border border-indigo-500/40 rounded-2xl p-6 shadow-xl backdrop-blur-sm">
          <div className="flex items-start gap-4 mb-4">
            <div className="text-3xl">🤖</div>
            <div className="flex-1">
              <h2 className="text-xl font-semibold text-white mb-1">AI Monitoring Active</h2>
              <p className="text-xs text-indigo-300/80">
                Your AI assistant is watching {summary.total} people, acting like 100 new people pastors monitoring engagement and escalating to staff when needed.
              </p>
            </div>
          </div>

          {/* AI Alerts */}
          {aiAlerts.length > 0 && (
            <div className="mt-4 space-y-2">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-semibold text-white">Active Alerts ({aiAlerts.length})</h3>
                <span className="text-xs text-indigo-300/70">
                  {aiAlerts.filter(a => a.priority === 'urgent' || a.priority === 'high').length} need immediate attention
                </span>
              </div>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {aiAlerts.slice(0, 5).map((alert) => {
                  const priorityColors = {
                    urgent: 'bg-red-500/20 border-red-500/50 text-red-200',
                    high: 'bg-orange-500/20 border-orange-500/50 text-orange-200',
                    medium: 'bg-amber-500/20 border-amber-500/50 text-amber-200',
                    low: 'bg-blue-500/20 border-blue-500/50 text-blue-200'
                  };
                  return (
                    <div
                      key={alert.id}
                      className={`p-3 rounded-lg border ${priorityColors[alert.priority] || priorityColors.medium}`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-xs font-semibold uppercase">
                              {alert.priority}
                            </span>
                            <span className="text-xs">•</span>
                            <span className="text-xs font-medium truncate">
                              {alert.person_name}
                            </span>
                          </div>
                          <p className="text-xs font-semibold mb-1">{alert.title}</p>
                          <p className="text-xs opacity-90 mb-2">{alert.message}</p>
                          {alert.ai_recommendation && (
                            <p className="text-xs opacity-75 italic">
                              💡 {alert.ai_recommendation}
                            </p>
                          )}
                        </div>
                        <button
                          type="button"
                          onClick={() => navigate(`/persons/${alert.person_id}`)}
                          className="text-xs px-2 py-1 rounded border border-current/30 hover:bg-white/10 transition"
                        >
                          View →
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
              {aiAlerts.length > 5 && (
                <p className="text-xs text-indigo-300/70 text-center pt-2">
                  +{aiAlerts.length - 5} more alerts
                </p>
              )}
            </div>
          )}

          {/* AI Insights */}
          {aiInsights && (
            <div className="mt-4 pt-4 border-t border-indigo-500/30">
              <h3 className="text-sm font-semibold text-white mb-2">Campus Health Overview</h3>
              <p className="text-sm text-indigo-100 leading-relaxed">{aiInsights}</p>
            </div>
          )}

          {aiAlerts.length === 0 && !loadingAlerts && (
            <div className="mt-4 text-center py-4">
              <p className="text-sm text-indigo-300/70">
                ✨ All clear! No active alerts. AI is monitoring and will notify you when action is needed.
              </p>
            </div>
          )}
        </div>

        {/* People Needing Attention - Enhanced Visual Section */}
        {needingAttention.length > 0 && (
          <div className="bg-slate-900/70 border border-slate-700/70 rounded-2xl p-6 shadow-xl">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-2xl font-semibold text-white flex items-center gap-2">
                  <span className="text-red-400">⚠️</span>
                  People Needing Attention
                </h2>
                <p className="text-xs text-slate-400 mt-1">
                  Top priorities for follow-up this week
                </p>
              </div>
              <div className="px-4 py-2 bg-red-500/20 border border-red-500/40 rounded-full text-sm font-medium text-red-300">
                {needingAttention.length} {needingAttention.length === 1 ? 'Priority' : 'Priorities'}
              </div>
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              {needingAttention.map((person) => {
                const lastSeen = person.last_seen
                  ? new Date(person.last_seen)
                  : null;
                const daysSince = lastSeen
                  ? Math.floor((new Date() - lastSeen) / (1000 * 60 * 60 * 24))
                  : null;
                const primaryReason =
                  person.pulse_reasons && person.pulse_reasons.length > 0
                    ? person.pulse_reasons[0]
                    : 'No engagement data';

                return (
                  <button
                    key={person.id}
                    type="button"
                    onClick={() => navigate(`/persons/${person.id}`)}
                    className="text-left bg-gradient-to-br from-slate-800/80 to-slate-900/80 hover:from-slate-800 hover:to-slate-900 border border-slate-700/60 hover:border-slate-600 rounded-xl p-4 transition-all shadow-md hover:shadow-lg"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-slate-100 font-semibold truncate">
                            {person.full_name}
                          </span>
                          <PulseBadge
                            status={person.pulse_status}
                            score={person.overall_engagement}
                          />
                        </div>
                        <div className="flex items-center gap-3 text-xs text-slate-400 mb-2">
                          {person.department && (
                            <span className="capitalize px-2 py-0.5 bg-slate-700/50 rounded">
                              {person.department.replace('_', ' ')}
                            </span>
                          )}
                          {person.campus && <span>• {person.campus}</span>}
                          {daysSince !== null && (
                            <span className={daysSince > 30 ? 'text-red-400 font-medium' : ''}>
                              • {daysSince === 0 ? 'Today' : `${daysSince} days ago`}
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-slate-300 line-clamp-2">
                          {primaryReason}
                        </p>
                      </div>
                      <div className="text-slate-500 text-lg">→</div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Quick Filters */}
        <div className="bg-slate-900/60 border border-slate-700/60 rounded-2xl p-4">
          <div className="flex flex-col sm:flex-row gap-3">
            {campuses.length > 0 && (
              <select
                value={filters.campus}
                onChange={(e) => handleFilterChange('campus', e.target.value)}
                className="bg-slate-800/70 text-slate-100 text-sm rounded-lg px-3 py-2 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/60 focus:border-blue-500/60"
              >
                <option value="all_campuses">All campuses</option>
                {campuses.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            )}

            <input
              type="text"
              placeholder="Search by name or email..."
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
              className="flex-1 bg-slate-800/70 text-slate-100 text-sm rounded-lg px-3 py-2 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/60 focus:border-blue-500/60 placeholder:text-slate-500"
            />
          </div>
        </div>

        {loading && (
          <div className="py-12 flex items-center justify-center">
            <div className="flex items-center gap-3 text-slate-400 text-sm">
              <span className="inline-block w-5 h-5 border-2 border-slate-500 border-t-transparent rounded-full animate-spin" />
              Loading heartbeat data...
            </div>
          </div>
        )}

        {error && (
          <div className="py-6 text-center text-sm text-red-300 bg-red-900/20 rounded-lg border border-red-800/40">
            {error}
          </div>
        )}
      </div>
    </div>
  );
};

export default Heartbeat;
