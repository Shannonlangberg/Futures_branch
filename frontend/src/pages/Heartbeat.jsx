import React from 'react';

const Heartbeat = () => (
  <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
    <div className="max-w-4xl mx-auto bg-slate-800/60 border border-slate-700/60 rounded-3xl p-10 text-center space-y-4">
      <div className="w-16 h-16 mx-auto rounded-full bg-purple-500/20 flex items-center justify-center text-3xl">
        💜
      </div>
      <h1 className="text-3xl font-bold text-white">Heartbeat Dashboard</h1>
      <p className="text-white/70">
        The Heartbeat analytics dashboard is coming soon. Our team is still wiring up the live
        reports, but you’ll be able to review engagement signals and trends for each campus here.
      </p>
      <p className="text-white/50 text-sm">
        Need something in the meantime? Reach out to the digital team and we’ll help you pull any
        stats you need.
      </p>
    </div>
  </div>
);

export default Heartbeat;

import React, { useEffect, useMemo, useState } from 'react';

const pulseOptions = [
  { value: '', label: 'All Pulse Statuses' },
  { value: 'green', label: 'Green' },
  { value: 'amber', label: 'Amber' },
  { value: 'red', label: 'Red' }
];

const Heartbeat = () => {
  const [campuses, setCampuses] = useState([{ id: 'all_campuses', name: 'All Campuses' }]);
  const [selectedCampus, setSelectedCampus] = useState('all_campuses');
  const [pulseStatus, setPulseStatus] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [persons, setPersons] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    let timeout = setTimeout(() => {
      setDebouncedSearch(searchTerm.trim());
    }, 300);

    return () => clearTimeout(timeout);
  }, [searchTerm]);

  useEffect(() => {
    const fetchCampuses = async () => {
      try {
        const response = await fetch('/api/campuses/public');
        if (!response.ok) {
          throw new Error('Failed to load campuses');
        }
        const data = await response.json();
        const campusList = Array.isArray(data.campuses) ? data.campuses : [];
        const unique = campusList.reduce((acc, campus) => {
          if (!acc.find(item => item.id === campus.id)) {
            acc.push(campus);
          }
          return acc;
        }, [{ id: 'all_campuses', name: 'All Campuses' }]);
        setCampuses(unique);
      } catch (err) {
        console.error(err);
      }
    };

    fetchCampuses();
  }, []);

  useEffect(() => {
    const fetchPersons = async () => {
      setLoading(true);
      setError('');
      try {
        const params = new URLSearchParams();
        if (selectedCampus && selectedCampus !== 'all_campuses') {
          params.append('campus', selectedCampus);
        }
        if (pulseStatus) {
          params.append('pulse_status', pulseStatus);
        }
        if (debouncedSearch) {
          params.append('search', debouncedSearch);
        }
        params.append('_t', Date.now().toString());

        const response = await fetch(`/api/persons/demo?${params.toString()}`);
        if (!response.ok) {
          throw new Error('Unable to fetch heartbeat data');
        }
        const data = await response.json();
        setPersons(Array.isArray(data.persons) ? data.persons : []);
        setLastUpdated(new Date());
      } catch (err) {
        console.error(err);
        setError(err.message || 'Failed to load heartbeat data');
      } finally {
        setLoading(false);
      }
    };

    fetchPersons();
  }, [selectedCampus, pulseStatus, debouncedSearch]);

  const summary = useMemo(() => {
    const totals = {
      total: persons.length,
      green: 0,
      amber: 0,
      red: 0
    };

    persons.forEach(person => {
      const status = (person.pulse_status || '').toLowerCase();
      if (status === 'green') totals.green += 1;
      else if (status === 'amber') totals.amber += 1;
      else if (status === 'red') totals.red += 1;
    });

    return totals;
  }, [persons]);

  const formatDate = (value) => {
    if (!value) return 'No data';
    try {
      const date = new Date(value);
      if (!Number.isNaN(date.getTime())) {
        return date.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
      }
    } catch (err) {
      return value;
    }
    return value;
  };

  const statusBadge = (status) => {
    const normalized = (status || '').toLowerCase();
    const styles = {
      green: 'bg-green-500/10 text-green-400 border-green-500/30',
      amber: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
      red: 'bg-red-500/10 text-red-400 border-red-500/30'
    };

    const labels = {
      green: 'Engaged',
      amber: 'Warm',
      red: 'Needs Attention'
    };

    const style = styles[normalized] || 'bg-slate-500/10 text-slate-300 border-slate-500/30';
    const label = labels[normalized] || (status || 'Unknown');

    return (
      <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold border ${style}`}>
        {label}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-white">Heartbeat</h1>
          <p className="text-sm text-white/60">Monitor engagement health across campuses and focus on people who need follow-up.</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-white/50">
          <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10">
            <span className="block w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            {lastUpdated ? `Updated ${lastUpdated.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}` : 'Waiting for data'}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-emerald-500/10 to-emerald-500/5 p-6">
          <p className="text-sm text-white/60">Engaged (Green)</p>
          <p className="text-3xl font-semibold text-emerald-300 mt-2">{summary.green}</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-amber-500/10 to-amber-500/5 p-6">
          <p className="text-sm text-white/60">Warm (Amber)</p>
          <p className="text-3xl font-semibold text-amber-300 mt-2">{summary.amber}</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-red-500/10 to-red-500/5 p-6">
          <p className="text-sm text-white/60">Needs Attention (Red)</p>
          <p className="text-3xl font-semibold text-red-300 mt-2">{summary.red}</p>
        </div>
      </div>

      <div className="flex flex-wrap gap-3 items-center bg-white/5 border border-white/10 rounded-2xl p-4">
        <div className="w-full md:w-60">
          <label htmlFor="campus" className="block text-xs text-white/60 mb-1">Campus</label>
          <select
            id="campus"
            value={selectedCampus}
            onChange={(event) => setSelectedCampus(event.target.value)}
            className="w-full bg-white/10 border border-white/10 rounded-xl px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
          >
            {campuses.map(campus => (
              <option key={campus.id} value={campus.id}>{campus.name}</option>
            ))}
          </select>
        </div>
        <div className="w-full md:w-52">
          <label htmlFor="pulse" className="block text-xs text-white/60 mb-1">Pulse Status</label>
          <select
            id="pulse"
            value={pulseStatus}
            onChange={(event) => setPulseStatus(event.target.value)}
            className="w-full bg-white/10 border border-white/10 rounded-xl px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
          >
            {pulseOptions.map(option => (
              <option key={option.value || 'all'} value={option.value}>{option.label}</option>
            ))}
          </select>
        </div>
        <div className="flex-1 min-w-[200px]">
          <label htmlFor="search" className="block text-xs text-white/60 mb-1">Search</label>
          <input
            id="search"
            type="search"
            placeholder="Search people by name or email..."
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
            className="w-full bg-white/10 border border-white/10 rounded-xl px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
          />
        </div>
      </div>

      <div className="border border-white/10 rounded-2xl overflow-hidden bg-white/5">
        {loading ? (
          <div className="p-6 text-center text-white/60">Loading heartbeat data...</div>
        ) : error ? (
          <div className="p-6 text-center text-red-300">{error}</div>
        ) : persons.length === 0 ? (
          <div className="p-6 text-center text-white/60">No people match the current filters.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-white/10">
              <thead className="bg-white/5">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-white/70 uppercase tracking-wider">Person</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-white/70 uppercase tracking-wider">Pulse</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-white/70 uppercase tracking-wider">Last Seen</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-white/70 uppercase tracking-wider">Campus</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-white/70 uppercase tracking-wider">Notes</th>
                </tr>
              </thead>
              <tbody className="bg-transparent divide-y divide-white/5">
                {persons.map(person => (
                  <tr key={person.id} className="hover:bg-white/5 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-white">{person.full_name}</div>
                      <div className="text-sm text-white/50">{person.email}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">{statusBadge(person.pulse_status)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-white/70">{formatDate(person.last_seen)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-white/70 capitalize">{person.campus || 'Unknown'}</td>
                    <td className="px-6 py-4 text-sm text-white/60">
                      {Array.isArray(person.pulse_reasons) && person.pulse_reasons.length > 0 ? (
                        <ul className="list-disc list-inside space-y-1">
                          {person.pulse_reasons.slice(0, 3).map((reason, index) => (
                            <li key={index}>{reason}</li>
                          ))}
                          {person.pulse_reasons.length > 3 && <li className="text-white/40">+ {person.pulse_reasons.length - 3} more</li>}
                        </ul>
                      ) : (
                        <span>No reasons recorded</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default Heartbeat;
