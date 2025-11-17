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

const People = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [people, setPeople] = useState([]);
  const [campuses, setCampuses] = useState([]);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingPerson, setEditingPerson] = useState(null);
  const [savingPerson, setSavingPerson] = useState(false);
  const [addError, setAddError] = useState('');
  const [editError, setEditError] = useState('');
  const [newPerson, setNewPerson] = useState({
    firstName: '',
    lastName: '',
    preferredName: '',
    email: '',
    phone: '',
    campus: '',
    department: '',
    connectGroup: '',
    dreamTeamRoles: ''
  });
  const [editPerson, setEditPerson] = useState({
    full_name: '',
    preferred_name: '',
    email: '',
    phone: '',
    campus: '',
    department: '',
    connect_group: '',
    dream_team_roles: '',
    pastoral_notes: ''
  });
  const [pagination, setPagination] = useState({ page: 1, pageSize: 200, total: 0 });
  const [filters, setFilters] = useState({
    campus: 'all_campuses',
    pulse_status: '',
    department: 'all',
    search: ''
  });

  // Load campuses for filter
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
          console.error('Error loading campuses for people directory:', err);
        }
      }
    };

    fetchCampuses();
    return () => controller.abort();
  }, []);

  // Load people
  useEffect(() => {
    const controller = new AbortController();

    const fetchPeople = async () => {
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
        params.append('page', String(pagination.page));
        params.append('page_size', String(pagination.pageSize));

        const response = await fetch(`/api/people?${params.toString()}`, {
          credentials: 'include',
          signal: controller.signal
        });

        if (!response.ok) {
          throw new Error('Failed to load people directory');
        }

        const data = await response.json();
        setPeople(data.people || []);
        setPagination((prev) => ({
          ...prev,
          total: data.total || 0
        }));
      } catch (err) {
        if (err.name !== 'AbortError') {
          console.error('People directory load error:', err);
          setError('Unable to load people directory right now. Please try again soon.');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchPeople();
    return () => controller.abort();
  }, [filters.campus, filters.pulse_status, filters.department, filters.search, pagination.page, pagination.pageSize]);

  const handleFilterChange = (field, value) => {
    setPagination((prev) => ({ ...prev, page: 1 }));
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

  const totalPages = Math.max(1, Math.ceil((pagination.total || 0) / pagination.pageSize));

  const handleImportClick = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.csv,text/csv';

    input.onchange = async (event) => {
      const file = event.target.files && event.target.files[0];
      if (!file) return;

      const formData = new FormData();
      formData.append('file', file);

      try {
        setImporting(true);
        setImportResult(null);
        setError('');

        const response = await fetch('/api/people/import_pco', {
          method: 'POST',
          body: formData,
          credentials: 'include'
        });

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
          throw new Error(data.error || 'Import failed');
        }

        setImportResult({
          created: data.created,
          skipped: data.skipped,
          errors: data.errors || []
        });

        // Refresh people list from first page
        setPagination((prev) => ({ ...prev, page: 1 }));
      } catch (err) {
        console.error('PCO import error:', err);
        setError(err.message || 'Failed to import Planning Center CSV.');
      } finally {
        setImporting(false);
      }
    };

    input.click();
  };

  const openAddModal = () => {
    setAddError('');
    setNewPerson((prev) => ({
      ...prev,
      campus: filters.campus && filters.campus !== 'all_campuses' ? filters.campus : prev.campus
    }));
    setShowAddModal(true);
  };

  const handleNewPersonChange = (field, value) => {
    setNewPerson((prev) => ({ ...prev, [field]: value }));
  };

  const handleSavePerson = async () => {
    setAddError('');
    const firstName = newPerson.firstName.trim();
    const lastName = newPerson.lastName.trim();
    const email = newPerson.email.trim();
    const campusValue =
      newPerson.campus ||
      (filters.campus && filters.campus !== 'all_campuses' ? filters.campus : '');

    if (!firstName && !lastName) {
      setAddError('Please enter at least a first or last name.');
      return;
    }
    // Email is now optional (for kids/families)
    if (!campusValue) {
      setAddError('Please select a campus.');
      return;
    }

    const fullName = `${firstName} ${lastName}`.trim();
    const dreamTeamRoles = newPerson.dreamTeamRoles
      ? newPerson.dreamTeamRoles
          .split(',')
          .map((r) => r.trim())
          .filter(Boolean)
      : [];

    try {
      setSavingPerson(true);
      const response = await fetch('/api/persons', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          full_name: fullName,
          preferred_name: newPerson.preferredName || firstName || fullName,
          email,
          phone: newPerson.phone || null,
          campus: campusValue,
          department: newPerson.department || null,
          connect_group: newPerson.connectGroup || null,
          dream_team_roles: dreamTeamRoles
        })
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(data.error || 'Failed to create person');
      }

      // Reset form and refresh list from first page
      setShowAddModal(false);
      setNewPerson({
        firstName: '',
        lastName: '',
        preferredName: '',
        email: '',
        phone: '',
        campus: campusValue,
        department: '',
        connectGroup: '',
        dreamTeamRoles: ''
      });
      setPagination((prev) => ({ ...prev, page: 1 }));
    } catch (err) {
      console.error('Add person error:', err);
      setAddError(err.message || 'Failed to save person.');
    } finally {
      setSavingPerson(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-white">People</h1>
            <p className="text-sm text-slate-400 mt-1">
              Directory of everyone in your care, scoped to your campus and role, with heartbeat
              context so you can see who&apos;s thriving and who might need follow-up.
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
            <button
              type="button"
              onClick={openAddModal}
              className="px-3 py-1.5 rounded-full text-xs font-medium border border-emerald-500/60 text-emerald-200 bg-emerald-500/10 hover:bg-emerald-500/20"
            >
              Add Person
            </button>
            <button
              type="button"
              onClick={handleImportClick}
              disabled={importing}
              className="px-3 py-1.5 rounded-full text-xs font-medium border border-blue-500/60 text-blue-200 bg-blue-500/10 hover:bg-blue-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {importing ? 'Importing PCO CSV…' : 'Import PCO CSV'}
            </button>
          </div>
        </div>

        <div className="bg-slate-900/60 border border-slate-700/60 rounded-2xl p-4 sm:p-5 space-y-4">
          {importResult && (
            <div className="mb-3 text-xs text-emerald-200 bg-emerald-900/30 border border-emerald-500/40 rounded-lg px-3 py-2">
              Imported {importResult.created} people, skipped {importResult.skipped}.
              {importResult.errors && importResult.errors.length > 0 && (
                <div className="mt-1 text-[11px] text-emerald-100/90">
                  Some rows were skipped. First few errors:
                  <ul className="list-disc list-inside">
                    {importResult.errors.slice(0, 3).map((err, idx) => (
                      <li key={idx}>{err}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
            <div className="flex flex-col">
              <span className="text-xs text-slate-400 uppercase tracking-wide">
                Filters
              </span>
              <span className="text-[11px] text-slate-500">
                Campus limits are applied by your role automatically.
              </span>
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
                  Loading people...
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
              <>
                <div className="overflow-x-auto">
                  <table className="min-w-full text-left text-sm">
                    <thead>
                      <tr className="text-xs uppercase tracking-wide text-slate-400 border-b border-slate-800">
                        <th className="py-2 pr-4">Person</th>
                        <th className="py-2 px-4">Campus</th>
                        <th className="py-2 px-4">Group</th>
                        <th className="py-2 px-4">Dream Team</th>
                        <th className="py-2 px-4">Heartbeat</th>
                        <th className="py-2 px-4">Last Seen</th>
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

                        const roles = person.dream_team_roles || [];

                        return (
                          <tr
                            key={person.id}
                            className="border-b border-slate-800/60 hover:bg-slate-800/40 transition-colors"
                          >
                            <td className="py-3 pr-4">
                              <div className="flex items-center gap-2">
                                <button
                                  type="button"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setEditingPerson(person);
                                    setEditPerson({
                                      full_name: person.full_name || '',
                                      preferred_name: person.preferred_name || '',
                                      email: person.email || '',
                                      phone: person.phone || '',
                                      campus: person.campus || '',
                                      department: person.department || '',
                                      connect_group: person.connect_group || '',
                                      dream_team_roles: Array.isArray(person.dream_team_roles)
                                        ? person.dream_team_roles.join(', ')
                                        : person.dream_team_roles || '',
                                      pastoral_notes: person.pastoral_notes || ''
                                    });
                                    setShowEditModal(true);
                                  }}
                                  className="flex flex-col text-left hover:text-blue-300 focus:outline-none flex-1 cursor-pointer"
                                >
                                  <span className="text-slate-100 font-medium">
                                    {person.full_name}
                                  </span>
                                  <span className="text-xs text-slate-400">
                                    {person.email || 'No email'}
                                  </span>
                                </button>
                                <button
                                  type="button"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    navigate(`/persons/${person.id}`);
                                  }}
                                  className="text-slate-500 hover:text-blue-400 text-xs px-2 py-1 rounded border border-slate-700 hover:border-blue-500/50"
                                  title="View health report"
                                >
                                  📊
                                </button>
                              </div>
                            </td>
                            <td className="py-3 px-4 text-slate-300">
                              {person.campus || '—'}
                            </td>
                            <td className="py-3 px-4 text-slate-300">
                              {person.connect_group || (
                                <span className="text-slate-500 text-xs">
                                  Not in group
                                </span>
                              )}
                            </td>
                            <td className="py-3 px-4 text-slate-300">
                              {roles.length > 0 ? (
                                <div className="flex flex-wrap gap-1">
                                  {roles.map((role) => (
                                    <span
                                      key={role}
                                      className="inline-flex items-center px-2 py-0.5 rounded-full bg-slate-800 text-[11px]"
                                    >
                                      {role}
                                    </span>
                                  ))}
                                </div>
                              ) : (
                                <span className="text-slate-500 text-xs">
                                  Not serving
                                </span>
                              )}
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
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                <div className="flex items-center justify-between mt-4 text-xs text-slate-400">
                  <div>
                    Page {pagination.page} of {totalPages} • {pagination.total}{' '}
                    people
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      disabled={pagination.page <= 1}
                      onClick={() =>
                        setPagination((prev) => ({
                          ...prev,
                          page: Math.max(1, prev.page - 1)
                        }))
                      }
                      className="px-2 py-1 rounded border border-slate-700 text-slate-300 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-800/70"
                    >
                      Prev
                    </button>
                    <button
                      type="button"
                      disabled={pagination.page >= totalPages}
                      onClick={() =>
                        setPagination((prev) => ({
                          ...prev,
                          page: Math.min(totalPages, prev.page + 1)
                        }))
                      }
                      className="px-2 py-1 rounded border border-slate-700 text-slate-300 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-800/70"
                    >
                      Next
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

  const handleEditPersonChange = (field, value) => {
    setEditPerson((prev) => ({ ...prev, [field]: value }));
  };

  const handleSaveEdit = async () => {
    setEditError('');
    if (!editingPerson) return;

    try {
      setSavingPerson(true);
      const dreamTeamRoles = editPerson.dream_team_roles
        ? editPerson.dream_team_roles
            .split(',')
            .map((r) => r.trim())
            .filter(Boolean)
        : [];

      const response = await fetch(`/api/persons/${editingPerson.id}`, {
        method: 'PUT',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          full_name: editPerson.full_name,
          preferred_name: editPerson.preferred_name || null,
          email: editPerson.email || null,
          phone: editPerson.phone || null,
          campus: editPerson.campus,
          department: editPerson.department || null,
          connect_group: editPerson.connect_group || null,
          dream_team_roles: dreamTeamRoles,
          pastoral_notes: editPerson.pastoral_notes || null
        })
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(data.error || 'Failed to update person');
      }

      // Close modal and refresh list
      setShowEditModal(false);
      setEditingPerson(null);
      // Trigger refresh by toggling a filter state to force re-fetch
      setFilters((prev) => ({ ...prev }));
    } catch (err) {
      console.error('Edit person error:', err);
      setEditError(err.message || 'Failed to save changes.');
    } finally {
      setSavingPerson(false);
    }
  };

  const handleLoadPersonDetail = async (personId) => {
    try {
      const response = await fetch(`/api/persons/${personId}`, {
        credentials: 'include'
      });
      if (!response.ok) return;
      const data = await response.json();
      const person = data.person || {};
      setEditingPerson(person);
      setEditPerson({
        full_name: person.full_name || '',
        preferred_name: person.preferred_name || '',
        email: person.email || '',
        phone: person.phone || '',
        campus: person.campus || '',
        department: person.department || '',
        connect_group: person.connect_group || '',
        dream_team_roles: Array.isArray(person.dream_team_roles)
          ? person.dream_team_roles.join(', ')
          : person.dream_team_roles || '',
        pastoral_notes: person.pastoral_notes || ''
      });
    } catch (err) {
      console.error('Error loading person detail:', err);
    }
  };

  // Load full person details when edit modal opens
  useEffect(() => {
    if (showEditModal && editingPerson && !editPerson.full_name) {
      handleLoadPersonDetail(editingPerson.id);
    }
  }, [showEditModal, editingPerson]);

      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl max-w-lg w-full mx-4 p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white">Add Person</h2>
              <button
                type="button"
                onClick={() => {
                  if (!savingPerson) setShowAddModal(false);
                }}
                className="text-slate-400 hover:text-slate-200"
              >
                ×
              </button>
            </div>

            <p className="text-xs text-slate-400">
              Quick add for new people in your campus. You can fill in more details later from their
              profile.
            </p>

            {addError && (
              <div className="text-xs text-red-200 bg-red-900/40 border border-red-500/50 rounded-lg px-3 py-2">
                {addError}
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] uppercase tracking-wide text-slate-400 mb-1">
                  First name
                </label>
                <input
                  type="text"
                  value={newPerson.firstName}
                  onChange={(e) => handleNewPersonChange('firstName', e.target.value)}
                  className="w-full bg-slate-800/80 text-slate-100 text-sm rounded-lg px-3 py-2 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/60"
                />
              </div>
              <div>
                <label className="block text-[11px] uppercase tracking-wide text-slate-400 mb-1">
                  Last name
                </label>
                <input
                  type="text"
                  value={newPerson.lastName}
                  onChange={(e) => handleNewPersonChange('lastName', e.target.value)}
                  className="w-full bg-slate-800/80 text-slate-100 text-sm rounded-lg px-3 py-2 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/60"
                />
              </div>
              <div>
                <label className="block text-[11px] uppercase tracking-wide text-slate-400 mb-1">
                  Preferred name
                </label>
                <input
                  type="text"
                  value={newPerson.preferredName}
                  onChange={(e) => handleNewPersonChange('preferredName', e.target.value)}
                  className="w-full bg-slate-800/80 text-slate-100 text-sm rounded-lg px-3 py-2 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/60"
                />
              </div>
              <div>
                <label className="block text-[11px] uppercase tracking-wide text-slate-400 mb-1">
                  Email
                </label>
                <input
                  type="email"
                  value={newPerson.email}
                  onChange={(e) => handleNewPersonChange('email', e.target.value)}
                  className="w-full bg-slate-800/80 text-slate-100 text-sm rounded-lg px-3 py-2 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/60"
                />
              </div>
              <div>
                <label className="block text-[11px] uppercase tracking-wide text-slate-400 mb-1">
                  Phone
                </label>
                <input
                  type="tel"
                  value={newPerson.phone}
                  onChange={(e) => handleNewPersonChange('phone', e.target.value)}
                  className="w-full bg-slate-800/80 text-slate-100 text-sm rounded-lg px-3 py-2 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/60"
                />
              </div>
              <div>
                <label className="block text-[11px] uppercase tracking-wide text-slate-400 mb-1">
                  Campus
                </label>
                <select
                  value={
                    newPerson.campus ||
                    (filters.campus !== 'all_campuses' ? filters.campus : newPerson.campus)
                  }
                  onChange={(e) => handleNewPersonChange('campus', e.target.value)}
                  className="w-full bg-slate-800/80 text-slate-100 text-sm rounded-lg px-3 py-2 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/60"
                >
                  <option value="">Select campus</option>
                  {campuses.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-[11px] uppercase tracking-wide text-slate-400 mb-1">
                  Department
                </label>
                <select
                  value={newPerson.department}
                  onChange={(e) => handleNewPersonChange('department', e.target.value)}
                  className="w-full bg-slate-800/80 text-slate-100 text-sm rounded-lg px-3 py-2 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/60"
                >
                  <option value="">Select department</option>
                  <option value="kids">Kids</option>
                  <option value="youth">Youth</option>
                  <option value="young_adults">Young Adults</option>
                  <option value="families">Families</option>
                  <option value="adults">Adults</option>
                  <option value="seniors">Seniors</option>
                </select>
              </div>
              <div className="md:col-span-2">
                <label className="block text-[11px] uppercase tracking-wide text-slate-400 mb-1">
                  Connect group
                </label>
                <input
                  type="text"
                  value={newPerson.connectGroup}
                  onChange={(e) => handleNewPersonChange('connectGroup', e.target.value)}
                  className="w-full bg-slate-800/80 text-slate-100 text-sm rounded-lg px-3 py-2 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/60"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-[11px] uppercase tracking-wide text-slate-400 mb-1">
                  Dream team roles
                </label>
                <input
                  type="text"
                  placeholder="Comma separated, e.g. Host, Kids, Worship"
                  value={newPerson.dreamTeamRoles}
                  onChange={(e) => handleNewPersonChange('dreamTeamRoles', e.target.value)}
                  className="w-full bg-slate-800/80 text-slate-100 text-sm rounded-lg px-3 py-2 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/60 placeholder:text-slate-500"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => {
                  if (!savingPerson) setShowAddModal(false);
                }}
                className="px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 border border-slate-600 hover:bg-slate-800"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSavePerson}
                disabled={savingPerson}
                className="px-4 py-1.5 rounded-lg text-xs font-medium bg-emerald-500 text-white hover:bg-emerald-400 disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {savingPerson ? 'Saving…' : 'Save person'}
              </button>
            </div>
          </div>
        </div>
      )}

      {showEditModal && editingPerson && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 backdrop-blur-sm overflow-y-auto p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl max-w-2xl w-full mx-4 my-8 p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-white">Edit Person</h2>
                <p className="text-xs text-slate-400 mt-1">
                  Update {editingPerson.full_name}&apos;s information
                </p>
              </div>
              <button
                type="button"
                onClick={() => {
                  if (!savingPerson) {
                    setShowEditModal(false);
                    setEditingPerson(null);
                  }
                }}
                className="text-slate-400 hover:text-slate-200 text-2xl"
              >
                ×
              </button>
            </div>

            {editError && (
              <div className="text-xs text-red-200 bg-red-900/40 border border-red-500/50 rounded-lg px-3 py-2">
                {editError}
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-[11px] uppercase tracking-wide text-slate-400 mb-1">
                  Full Name *
                </label>
                <input
                  type="text"
                  value={editPerson.full_name}
                  onChange={(e) => handleEditPersonChange('full_name', e.target.value)}
                  className="w-full bg-slate-800/80 text-slate-100 text-sm rounded-lg px-3 py-2 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/60"
                />
              </div>
              <div>
                <label className="block text-[11px] uppercase tracking-wide text-slate-400 mb-1">
                  Preferred Name
                </label>
                <input
                  type="text"
                  value={editPerson.preferred_name}
                  onChange={(e) => handleEditPersonChange('preferred_name', e.target.value)}
                  className="w-full bg-slate-800/80 text-slate-100 text-sm rounded-lg px-3 py-2 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/60"
                />
              </div>
              <div>
                <label className="block text-[11px] uppercase tracking-wide text-slate-400 mb-1">
                  Email
                </label>
                <input
                  type="email"
                  value={editPerson.email}
                  onChange={(e) => handleEditPersonChange('email', e.target.value)}
                  className="w-full bg-slate-800/80 text-slate-100 text-sm rounded-lg px-3 py-2 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/60"
                />
              </div>
              <div>
                <label className="block text-[11px] uppercase tracking-wide text-slate-400 mb-1">
                  Phone
                </label>
                <input
                  type="tel"
                  value={editPerson.phone}
                  onChange={(e) => handleEditPersonChange('phone', e.target.value)}
                  className="w-full bg-slate-800/80 text-slate-100 text-sm rounded-lg px-3 py-2 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/60"
                />
              </div>
              <div>
                <label className="block text-[11px] uppercase tracking-wide text-slate-400 mb-1">
                  Campus *
                </label>
                <select
                  value={editPerson.campus}
                  onChange={(e) => handleEditPersonChange('campus', e.target.value)}
                  className="w-full bg-slate-800/80 text-slate-100 text-sm rounded-lg px-3 py-2 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/60"
                >
                  <option value="">Select campus</option>
                  {campuses.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-[11px] uppercase tracking-wide text-slate-400 mb-1">
                  Department
                </label>
                <select
                  value={editPerson.department}
                  onChange={(e) => handleEditPersonChange('department', e.target.value)}
                  className="w-full bg-slate-800/80 text-slate-100 text-sm rounded-lg px-3 py-2 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/60"
                >
                  <option value="">Select department</option>
                  <option value="kids">Kids</option>
                  <option value="youth">Youth</option>
                  <option value="young_adults">Young Adults</option>
                  <option value="families">Families</option>
                  <option value="adults">Adults</option>
                  <option value="seniors">Seniors</option>
                </select>
              </div>
              <div className="md:col-span-2">
                <label className="block text-[11px] uppercase tracking-wide text-slate-400 mb-1">
                  Connect Group
                </label>
                <input
                  type="text"
                  value={editPerson.connect_group}
                  onChange={(e) => handleEditPersonChange('connect_group', e.target.value)}
                  className="w-full bg-slate-800/80 text-slate-100 text-sm rounded-lg px-3 py-2 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/60"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-[11px] uppercase tracking-wide text-slate-400 mb-1">
                  Dream Team Roles
                </label>
                <input
                  type="text"
                  placeholder="Comma separated, e.g. Host, Kids, Worship"
                  value={editPerson.dream_team_roles}
                  onChange={(e) => handleEditPersonChange('dream_team_roles', e.target.value)}
                  className="w-full bg-slate-800/80 text-slate-100 text-sm rounded-lg px-3 py-2 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/60 placeholder:text-slate-500"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-[11px] uppercase tracking-wide text-slate-400 mb-1">
                  Pastoral Notes / Comments
                </label>
                <textarea
                  value={editPerson.pastoral_notes}
                  onChange={(e) => handleEditPersonChange('pastoral_notes', e.target.value)}
                  rows={4}
                  placeholder="Add notes, comments, or follow-up reminders..."
                  className="w-full bg-slate-800/80 text-slate-100 text-sm rounded-lg px-3 py-2 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/60 placeholder:text-slate-500 resize-none"
                />
              </div>
            </div>

            <div className="flex justify-between items-center pt-4 border-t border-slate-800">
              <button
                type="button"
                onClick={() => navigate(`/persons/${editingPerson.id}`)}
                className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1"
              >
                📊 View Health Report
              </button>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => {
                    if (!savingPerson) {
                      setShowEditModal(false);
                      setEditingPerson(null);
                    }
                  }}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 border border-slate-600 hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleSaveEdit}
                  disabled={savingPerson || !editPerson.full_name || !editPerson.campus}
                  className="px-4 py-1.5 rounded-lg text-xs font-medium bg-blue-500 text-white hover:bg-blue-400 disabled:opacity-60 disabled:cursor-not-allowed"
                >
                  {savingPerson ? 'Saving…' : 'Save Changes'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default People;


