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

const Heartbeat = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [people, setPeople] = useState([]);
  const [campuses, setCampuses] = useState([]);
  const [summary, setSummary] = useState({
    total: 0,
    green: 0,
    amber: 0,
    red: 0
  });
  const [filters, setFilters] = useState({
    campus: 'all_campuses',
    pulse_status: '',
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
  }, [filters.campus, filters.pulse_status, filters.search]);

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

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-3">
              <span className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-purple-500/20 text-2xl">
                💜
              </span>
              Heartbeat
            </h1>
            <p className="text-sm text-slate-400 mt-1">
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
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-4">
          <div className="bg-slate-900/70 border border-slate-700/70 rounded-2xl p-4">
            <div className="text-xs text-slate-400 uppercase tracking-wide mb-1">
              Total people
            </div>
            <div className="text-2xl font-semibold text-white">
              {summary.total}
            </div>
            <div className="text-xs text-slate-500 mt-1">
              Scoped to your campus unless you have cross-campus access.
            </div>
          </div>
          <div className="bg-emerald-900/20 border border-emerald-500/40 rounded-2xl p-4">
            <div className="text-xs text-emerald-300 uppercase tracking-wide mb-1">
              Healthy
            </div>
            <div className="text-2xl font-semibold text-emerald-100">
              {summary.green}
            </div>
          </div>
          <div className="bg-amber-900/20 border border-amber-500/40 rounded-2xl p-4">
            <div className="text-xs text-amber-300 uppercase tracking-wide mb-1">
              Watch
            </div>
            <div className="text-2xl font-semibold text-amber-100">
              {summary.amber}
            </div>
          </div>
          <div className="bg-red-900/20 border border-red-500/40 rounded-2xl p-4">
            <div className="text-xs text-red-300 uppercase tracking-wide mb-1">
              At Risk
            </div>
            <div className="text-2xl font-semibold text-red-100">
              {summary.red}
            </div>
          </div>
        </div>

        <div className="bg-slate-900/60 border border-slate-700/60 rounded-2xl p-4 sm:p-5 space-y-4">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="flex flex-col">
                <span className="text-xs text-slate-400 uppercase tracking-wide">
                  Filters
                </span>
                <span className="text-[11px] text-slate-500">
                  Campus limits are applied by your role automatically.
                </span>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-3 w-full md:w-auto">
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
                placeholder="Search by name or email"
                value={filters.search}
                onChange={(e) => handleFilterChange('search', e.target.value)}
                className="flex-1 bg-slate-800/70 text-slate-100 text-sm rounded-lg px-3 py-2 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/60 focus:border-blue-500/60 placeholder:text-slate-500"
              />
            </div>
          </div>

          <div className="border-t border-slate-800/70 pt-4">
            {loading ? (
              <div className="py-8 flex items-center justify-center">
                <div className="flex items-center gap-3 text-slate-400 text-sm">
                  <span className="inline-block w-4 h-4 border-2 border-slate-500 border-t-transparent rounded-full animate-spin" />
                  Loading heartbeat...
                </div>
              </div>
            ) : error ? (
              <div className="py-6 text-center text-sm text-red-300 bg-red-900/20 rounded-lg border border-red-800/40">
                {error}
              </div>
            ) : people.length === 0 ? (
              <div className="py-8 text-center text-sm text-slate-400">
                No people matched your filters yet.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full text-left text-sm">
                  <thead>
                    <tr className="text-xs uppercase tracking-wide text-slate-400 border-b border-slate-800">
                      <th className="py-2 pr-4">Person</th>
                      <th className="py-2 px-4">Campus</th>
                      <th className="py-2 px-4">Heartbeat</th>
                      <th className="py-2 px-4">Last Seen</th>
                      <th className="py-2 pl-4">Highlights</th>
                    </tr>
                  </thead>
                  <tbody>
                    {people.map((person) => {
                      const lastSeen = person.last_seen
                        ? new Date(person.last_seen)
                        : null;

                      const lastSeenLabel = lastSeen
                        ? lastSeen.toLocaleDateString()
                        : 'No attendance yet';

                      const headlineReason =
                        person.pulse_reasons && person.pulse_reasons.length > 0
                          ? person.pulse_reasons[0]
                          : 'No pulse reasons yet';

                      return (
                        <tr
                          key={person.id}
                          className="border-b border-slate-800/60 hover:bg-slate-800/40 transition-colors"
                        >
                          <td className="py-3 pr-4">
                            <button
                              type="button"
                              onClick={() => navigate(`/persons/${person.id}`)}
                              className="flex flex-col text-left hover:text-blue-300 focus:outline-none"
                            >
                              <span className="text-slate-100 font-medium">
                                {person.full_name}
                              </span>
                              <span className="text-xs text-slate-400">
                                {person.email}
                              </span>
                            </button>
                          </td>
                          <td className="py-3 px-4 text-slate-300">
                            {person.campus || '—'}
                          </td>
                          <td className="py-3 px-4">
                            <PulseBadge
                              status={person.pulse_status}
                              score={person.overall_engagement}
                            />
                          </td>
                          <td className="py-3 px-4 text-slate-300">
                            {lastSeenLabel}
                          </td>
                          <td className="py-3 pl-4 text-slate-300">
                            <span className="block text-xs text-slate-300">
                              {headlineReason}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Heartbeat;
