import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { 
  UserGroupIcon, 
  PlusIcon, 
  PencilIcon, 
  XMarkIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  HeartIcon,
  ArchiveBoxIcon,
  TrashIcon,
  ArrowPathIcon,
  CheckCircleIcon,
  ListBulletIcon
} from '@heroicons/react/24/outline';

const People = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [persons, setPersons] = useState([]);
  const [campuses, setCampuses] = useState([]);
  const [connectGroups, setConnectGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [showGroupModal, setShowGroupModal] = useState(false);
  const [editingPerson, setEditingPerson] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [campusFilter, setCampusFilter] = useState('all_campuses');
  const [pulseFilter, setPulseFilter] = useState('all');
  const [departmentFilter, setDepartmentFilter] = useState('all');
  const [includeArchived, setIncludeArchived] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  const [importFile, setImportFile] = useState(null);
  const [importing, setImporting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(null);
  const [showArchiveConfirm, setShowArchiveConfirm] = useState(null);
  const [editingDepartment, setEditingDepartment] = useState(null);
  const [tempDepartment, setTempDepartment] = useState('');
  const [isSavingDepartment, setIsSavingDepartment] = useState(false);
  const [formData, setFormData] = useState({
    full_name: '',
    preferred_name: '',
    email: '',
    phone: '',
    campus: 'all_campuses',
    department: '',
    connect_group: '',
    dream_team_roles: [],
    birthday: '',
    pastoral_notes: '',
    tags: []
  });

  useEffect(() => {
    loadCampuses();
    loadPersons();
  }, [campusFilter, pulseFilter, departmentFilter, searchTerm, includeArchived]);

  // Refresh data when window regains focus (in case mobile app updated data)
  useEffect(() => {
    const handleFocus = () => {
      loadPersons();
    };
    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, []);
  

  // Check for edit query parameter and open modal
  useEffect(() => {
    const editPersonId = searchParams.get('edit');
    if (editPersonId && persons.length > 0 && !showModal) {
      const personToEdit = persons.find(p => p.id === editPersonId);
      if (personToEdit) {
        handleOpenModal(personToEdit);
        // Remove the query parameter from URL
        const newSearchParams = new URLSearchParams(searchParams);
        newSearchParams.delete('edit');
        setSearchParams(newSearchParams, { replace: true });
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams, persons, showModal]);

  const loadCampuses = async () => {
    try {
      const response = await fetch('/api/campuses/public');
      if (response.ok) {
        const data = await response.json();
        setCampuses(data.campuses || []);
      }
    } catch (err) {
      console.error('Error loading campuses:', err);
    }
  };

  const loadConnectGroups = async (campus = null) => {
    try {
      const params = new URLSearchParams();
      if (campus && campus !== 'all_campuses') {
        params.append('campus', campus);
      }
      params.append('is_active', 'true');
      
      const response = await fetch(`/api/connect-groups?${params.toString()}`, {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setConnectGroups(data.groups || []);
      }
    } catch (err) {
      console.error('Error loading connect groups:', err);
    }
  };

  const loadPersons = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (campusFilter && campusFilter !== 'all_campuses') {
        params.append('campus', campusFilter);
      }
      if (pulseFilter && pulseFilter !== 'all') {
        params.append('pulse_status', pulseFilter);
      }
      if (departmentFilter && departmentFilter !== 'all') {
        params.append('department', departmentFilter);
      }
      if (searchTerm) {
        params.append('search', searchTerm);
      }
      if (includeArchived) {
        params.append('include_archived', 'true');
      }

      // Add cache-busting timestamp
      params.append('_t', Date.now().toString());
      
      const response = await fetch(`/api/persons?${params.toString()}`, {
        credentials: 'include',
        cache: 'no-store',
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setPersons(data.persons || []);
        setError('');
      } else if (response.status === 403) {
        setError('You do not have permission to view people data');
      } else {
        setError('Failed to load people');
      }
    } catch (err) {
      console.error('Error loading persons:', err);
      setError('Failed to connect to server');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenModal = async (person = null) => {
    if (person) {
      // Fetch fresh data from server with cache-busting
      try {
        const freshResponse = await fetch(`/api/persons/${person.id}?_t=${Date.now()}`, {
          credentials: 'include',
          cache: 'no-store',
          headers: {
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
          }
        });
        if (freshResponse.ok) {
          person = await freshResponse.json();
        }
      } catch (err) {
        console.error('Error fetching person data:', err);
      }
      
      setEditingPerson(person);
      setFormData({
        full_name: person.full_name || '',
        preferred_name: person.preferred_name || '',
        email: person.email || '',
        phone: person.phone || '',
        campus: person.campus || 'all_campuses',
        department: person.department || '',
        connect_group: person.connect_group || '',
        dream_team_roles: person.dream_team_roles || [],
        birthday: person.birthday ? person.birthday.split('T')[0] : '',
        pastoral_notes: person.pastoral_notes || '',
        tags: person.tags || []
      });
      // Load connect groups for this person's campus
      await loadConnectGroups(person.campus || 'all_campuses');
    } else {
      setEditingPerson(null);
      setFormData({
        full_name: '',
        preferred_name: '',
        email: '',
        phone: '',
        campus: 'all_campuses',
        department: '',
        connect_group: '',
        dream_team_roles: [],
        birthday: '',
        pastoral_notes: '',
        tags: []
      });
      // Load all connect groups for new person
      await loadConnectGroups('all_campuses');
    }
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setEditingPerson(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validation
    if (!formData.full_name) {
      alert('Full name is required');
      return;
    }

    if (!formData.campus || formData.campus === 'all_campuses') {
      alert('Campus is required');
      return;
    }

    try {
      const url = editingPerson 
        ? `/api/persons/${editingPerson.id}`
        : '/api/persons';
      
      const method = editingPerson ? 'PUT' : 'POST';
      
      const payload = {
        ...formData,
        dream_team_roles: Array.isArray(formData.dream_team_roles) 
          ? formData.dream_team_roles 
          : [],
        tags: Array.isArray(formData.tags) ? formData.tags : []
      };

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (response.ok) {
        // Force reload persons with cache-busting
        await loadPersons();
        handleCloseModal();
        alert(editingPerson ? 'Person updated successfully' : 'Person created successfully');
      } else {
        alert(data.error || 'Failed to save person');
      }
    } catch (err) {
      console.error('Error saving person:', err);
      alert('Failed to save person');
    }
  };

  const getPulseStatusColor = (status) => {
    const colors = {
      'green': 'bg-green-500/20 text-green-400 border-green-500/30',
      'amber': 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
      'red': 'bg-red-500/20 text-red-400 border-red-500/30'
    };
    return colors[status] || 'bg-slate-500/20 text-slate-400 border-slate-500/30';
  };

  const getPulseStatusLabel = (status) => {
    const labels = {
      'green': 'Active',
      'amber': 'At Risk',
      'red': 'Inactive'
    };
    return labels[status] || 'Unknown';
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Never';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString();
    } catch {
      return 'Never';
    }
  };

  const handleViewPerson = (personId) => {
    navigate(`/persons/${personId}`);
  };

  const handleArchive = async (person) => {
    try {
      const response = await fetch(`/api/persons/${person.id}/archive`, {
        method: 'POST',
        credentials: 'include'
      });

      const data = await response.json();

      if (response.ok) {
        await loadPersons();
        setShowArchiveConfirm(null);
        alert('Person archived successfully');
      } else {
        alert(data.error || 'Failed to archive person');
      }
    } catch (err) {
      console.error('Error archiving person:', err);
      alert('Failed to archive person');
    }
  };

  const handleRestore = async (person) => {
    try {
      const response = await fetch(`/api/persons/${person.id}/restore`, {
        method: 'POST',
        credentials: 'include'
      });

      const data = await response.json();

      if (response.ok) {
        await loadPersons();
        alert('Person restored successfully');
      } else {
        alert(data.error || 'Failed to restore person');
      }
    } catch (err) {
      console.error('Error restoring person:', err);
      alert('Failed to restore person');
    }
  };

  const handleDelete = async (person) => {
    try {
      const response = await fetch(`/api/persons/${person.id}`, {
        method: 'DELETE',
        credentials: 'include'
      });

      const data = await response.json();

      if (response.ok) {
        await loadPersons();
        setShowDeleteConfirm(null);
        alert('Person permanently deleted');
      } else {
        alert(data.error || 'Failed to delete person');
      }
    } catch (err) {
      console.error('Error deleting person:', err);
      alert('Failed to delete person');
    }
  };

  const handleDepartmentEdit = (person) => {
    setEditingDepartment(person.id);
    setTempDepartment(person.department || '');
  };

  const handleDepartmentSave = async (person) => {
    if (isSavingDepartment) return;
    setIsSavingDepartment(true);
    try {
      const response = await fetch(`/api/persons/${person.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          department: tempDepartment || null
        })
      });

      const data = await response.json();

      if (response.ok) {
        await loadPersons();
        setEditingDepartment(null);
        setTempDepartment('');
      } else {
        alert(data.error || 'Failed to update department');
      }
    } catch (err) {
      console.error('Error updating department:', err);
      alert('Failed to update department');
    } finally {
      setIsSavingDepartment(false);
    }
  };

  const handleDepartmentCancel = () => {
    setIsSavingDepartment(true); // Prevent blur save
    setEditingDepartment(null);
    setTempDepartment('');
    setTimeout(() => setIsSavingDepartment(false), 100);
  };

  const handleImportCSV = async () => {
    if (!importFile) {
      alert('Please select a CSV file');
      return;
    }

    setImporting(true);
    try {
      const formData = new FormData();
      formData.append('file', importFile);

      const response = await fetch('/api/persons/import_pco', {
        method: 'POST',
        credentials: 'include',
        body: formData
      });

      const data = await response.json();

      if (response.ok) {
        alert(data.message || `Import completed: ${data.added} added, ${data.skipped} skipped`);
        setShowImportModal(false);
        setImportFile(null);
        await loadPersons();
      } else {
        alert(data.error || 'Failed to import CSV');
      }
    } catch (err) {
      console.error('Error importing CSV:', err);
      alert('Failed to import CSV');
    } finally {
      setImporting(false);
    }
  };

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      loadPersons();
    }, 500);

    return () => clearTimeout(timer);
  }, [searchTerm]);

  // Stats (only count active people unless showing archived)
  const activePersons = includeArchived ? persons : persons.filter(p => p.is_active);
  const stats = {
    total: activePersons.length,
    green: activePersons.filter(p => p.pulse_status === 'green').length,
    amber: activePersons.filter(p => p.pulse_status === 'amber').length,
    red: activePersons.filter(p => p.pulse_status === 'red').length
  };

  if (loading && persons.length === 0) {
    return (
      <div className="min-h-screen bg-slate-900 p-6 flex items-center justify-center">
        <div className="text-white text-xl">Loading people...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2 flex items-center">
                <UserGroupIcon className="w-10 h-10 mr-3 text-blue-500" />
                People
              </h1>
              <p className="text-slate-400">Manage church members and track engagement</p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => navigate('/lists')}
                className="flex items-center px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
              >
                <ListBulletIcon className="w-5 h-5 mr-2" />
                Lists
              </button>
              <button
                onClick={() => setShowImportModal(true)}
                className="flex items-center px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
              >
                <ArrowPathIcon className="w-5 h-5 mr-2" />
                Import CSV
              </button>
              <button
                onClick={() => handleOpenModal()}
                className="flex items-center px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
              >
                <PlusIcon className="w-5 h-5 mr-2" />
                Add Person
              </button>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-500/20 border border-red-500/50 rounded-lg text-red-400">
            {error}
          </div>
        )}

        {/* Filters */}
        <div className="mb-6 bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-4">
          <div className="flex flex-wrap gap-4 items-end">
            {/* Search */}
            <div className="flex-1 min-w-[200px]">
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Search
              </label>
              <div className="relative">
                <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Search by name or email..."
                  className="w-full pl-10 pr-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>

            {/* Campus Filter */}
            <div className="min-w-[180px]">
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Campus
              </label>
              <select
                value={campusFilter}
                onChange={(e) => setCampusFilter(e.target.value)}
                className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
              >
                <option value="all_campuses">All Campuses</option>
                {campuses.map(campus => (
                  <option key={campus.id} value={campus.id}>
                    {campus.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Pulse Status Filter */}
            <div className="min-w-[150px]">
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Pulse Status
              </label>
              <select
                value={pulseFilter}
                onChange={(e) => setPulseFilter(e.target.value)}
                className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
              >
                <option value="all">All Statuses</option>
                <option value="green">Active</option>
                <option value="amber">At Risk</option>
                <option value="red">Inactive</option>
              </select>
            </div>

            {/* Department Filter */}
            <div className="min-w-[150px]">
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Department
              </label>
              <select
                value={departmentFilter}
                onChange={(e) => setDepartmentFilter(e.target.value)}
                className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
              >
                <option value="all">All Departments</option>
                <option value="Kids">Kids</option>
                <option value="Youth">Youth</option>
                <option value="Young Adults">Young Adults</option>
                <option value="Families">Families</option>
                <option value="Adults">Adults</option>
                <option value="Seniors">Seniors</option>
              </select>
            </div>

            {/* Include Archived Toggle */}
            <div className="min-w-[180px]">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeArchived}
                  onChange={(e) => setIncludeArchived(e.target.checked)}
                  className="w-4 h-4 rounded bg-slate-700 border-slate-600 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm font-medium text-slate-300">Include Archived</span>
              </label>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
          <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-6">
            <div className="text-slate-400 text-sm mb-1">Total People</div>
            <div className="text-3xl font-bold text-white">{stats.total}</div>
          </div>
          <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-6">
            <div className="text-slate-400 text-sm mb-1">Active</div>
            <div className="text-3xl font-bold text-green-400">{stats.green}</div>
          </div>
          <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-6">
            <div className="text-slate-400 text-sm mb-1">At Risk</div>
            <div className="text-3xl font-bold text-yellow-400">{stats.amber}</div>
          </div>
          <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-6">
            <div className="text-slate-400 text-sm mb-1">Inactive</div>
            <div className="text-3xl font-bold text-red-400">{stats.red}</div>
          </div>
        </div>

        {/* People Table */}
        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-700/50">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-slate-300">Name</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-slate-300">Email</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-slate-300">Campus</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-slate-300">Department</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-slate-300">Pulse Status</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-slate-300">Last Seen</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-slate-300">Connect Group</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-slate-300">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50">
                {persons.length === 0 ? (
                  <tr>
                    <td colSpan="8" className="px-6 py-12 text-center text-slate-400">
                      {loading ? 'Loading...' : 'No people found'}
                    </td>
                  </tr>
                ) : (
                  persons.map((person) => (
                    <tr 
                      key={person.id} 
                      className={`hover:bg-slate-700/30 transition-colors cursor-pointer ${
                        !person.is_active ? 'opacity-60' : ''
                      }`}
                      onClick={() => handleOpenModal(person)}
                    >
                      <td className="px-6 py-4">
                        <div className="text-white font-medium">
                          {person.preferred_name || person.full_name}
                        </div>
                        {person.preferred_name && (
                          <div className="text-slate-400 text-sm">{person.full_name}</div>
                        )}
                      </td>
                      <td className="px-6 py-4 text-slate-300">{person.email}</td>
                      <td className="px-6 py-4 text-slate-300">
                        {person.campus === 'all_campuses' ? 'All Campuses' : person.campus}
                      </td>
                      <td className="px-6 py-4" onClick={(e) => e.stopPropagation()}>
                        {editingDepartment === person.id ? (
                          <div className="flex items-center gap-2">
                            <select
                              value={tempDepartment}
                              onChange={(e) => setTempDepartment(e.target.value)}
                              onBlur={() => {
                                if (!isSavingDepartment) {
                                  handleDepartmentSave(person);
                                }
                              }}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') {
                                  handleDepartmentSave(person);
                                } else if (e.key === 'Escape') {
                                  handleDepartmentCancel();
                                }
                              }}
                              autoFocus
                              className="px-2 py-1 bg-slate-700 border border-blue-500 rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                              <option value="">No Department</option>
                              <option value="Kids">Kids</option>
                              <option value="Youth">Youth</option>
                              <option value="Young Adults">Young Adults</option>
                              <option value="Families">Families</option>
                              <option value="Adults">Adults</option>
                              <option value="Seniors">Seniors</option>
                            </select>
                            <button
                              onClick={() => handleDepartmentSave(person)}
                              className="p-1 text-green-400 hover:text-green-300"
                              title="Save"
                            >
                              <CheckCircleIcon className="w-4 h-4" />
                            </button>
                            <button
                              onClick={handleDepartmentCancel}
                              className="p-1 text-red-400 hover:text-red-300"
                              title="Cancel"
                            >
                              <XMarkIcon className="w-4 h-4" />
                            </button>
                          </div>
                        ) : (
                          <div
                            onClick={() => handleDepartmentEdit(person)}
                            className="text-slate-300 hover:text-blue-400 cursor-pointer hover:bg-slate-700/50 rounded px-2 py-1 -mx-2 -my-1 transition-colors"
                            title="Click to edit department"
                          >
                            {person.department || '—'}
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <span className={`inline-flex px-3 py-1 rounded-full text-xs font-medium border ${getPulseStatusColor(person.pulse_status)}`}>
                            <HeartIcon className="w-3 h-3 mr-1" />
                            {getPulseStatusLabel(person.pulse_status)}
                          </span>
                          {!person.is_active && (
                            <span className="inline-flex px-2 py-1 rounded-full text-xs font-medium border bg-slate-500/20 text-slate-400 border-slate-500/30">
                              Archived
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-slate-300 text-sm">
                        {formatDate(person.last_seen)}
                      </td>
                      <td className="px-6 py-4 text-slate-300">
                        {person.connect_group || '—'}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-2" onClick={(e) => e.stopPropagation()}>
                          <button
                            onClick={() => handleOpenModal(person)}
                            title="Edit Person"
                            className="p-2 text-blue-400 hover:text-blue-300 hover:bg-blue-500/10 rounded-lg transition-colors"
                          >
                            <PencilIcon className="w-5 h-5" />
                          </button>
                          {person.is_active ? (
                            <>
                              <button
                                onClick={() => setShowArchiveConfirm(person)}
                                title="Archive Person"
                                className="p-2 text-yellow-400 hover:text-yellow-300 hover:bg-yellow-500/10 rounded-lg transition-colors"
                              >
                                <ArchiveBoxIcon className="w-5 h-5" />
                              </button>
                              <button
                                onClick={() => setShowDeleteConfirm(person)}
                                title="Delete Person"
                                className="p-2 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-lg transition-colors"
                              >
                                <TrashIcon className="w-5 h-5" />
                              </button>
                            </>
                          ) : (
                            <button
                              onClick={() => handleRestore(person)}
                              title="Restore Person"
                              className="p-2 text-green-400 hover:text-green-300 hover:bg-green-500/10 rounded-lg transition-colors"
                            >
                              <ArrowPathIcon className="w-5 h-5" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Add/Edit Person Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-800 rounded-xl border border-slate-700 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-slate-700 flex items-center justify-between sticky top-0 bg-slate-800 z-10">
              <h2 className="text-2xl font-bold text-white">
                {editingPerson ? 'Edit Person' : 'Add New Person'}
              </h2>
              <button
                onClick={handleCloseModal}
                className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
              >
                <XMarkIcon className="w-6 h-6 text-slate-400" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-6">
              {/* Full Name */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Full Name <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                  placeholder="John Smith"
                />
              </div>

              {/* Preferred Name */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Preferred Name
                </label>
                <input
                  type="text"
                  value={formData.preferred_name}
                  onChange={(e) => setFormData({ ...formData, preferred_name: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                  placeholder="John"
                />
              </div>

              {/* Email */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Email
                </label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                  placeholder="john.smith@example.com (optional)"
                />
              </div>

              {/* Phone */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Phone
                </label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                  placeholder="+61 400 000 000"
                />
              </div>

              {/* Campus */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Campus <span className="text-red-400">*</span>
                </label>
                <select
                  required
                  value={formData.campus}
                  onChange={async (e) => {
                    const newCampus = e.target.value;
                    setFormData({ ...formData, campus: newCampus, connect_group: '' }); // Clear connect group when campus changes
                    await loadConnectGroups(newCampus);
                  }}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="all_campuses">Select Campus</option>
                  {campuses.map(campus => (
                    <option key={campus.id} value={campus.id}>
                      {campus.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Department */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Department
                </label>
                <select
                  value={formData.department}
                  onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="">Select Department</option>
                  <option value="Kids">Kids</option>
                  <option value="Youth">Youth</option>
                  <option value="Young Adults">Young Adults</option>
                  <option value="Families">Families</option>
                  <option value="Adults">Adults</option>
                  <option value="Seniors">Seniors</option>
                </select>
              </div>

              {/* Connect Group */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Connect Group
                </label>
                <div className="flex gap-2">
                  <select
                    value={formData.connect_group || ''}
                    onChange={(e) => {
                      if (e.target.value === '__create_new__') {
                        // Reset to empty and show message
                        setFormData({ ...formData, connect_group: '' });
                        alert('Please use the Connect Groups page to create new groups. You can access it from the navigation menu.');
                      } else {
                        setFormData({ ...formData, connect_group: e.target.value || '' });
                      }
                    }}
                    className="flex-1 px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="">No Connect Group</option>
                    {connectGroups
                      .filter(g => !formData.campus || formData.campus === 'all_campuses' || g.campus === formData.campus)
                      .map(group => (
                        <option key={group.id} value={group.id}>
                          {group.name} ({group.campus})
                        </option>
                      ))}
                    <option value="__create_new__" className="text-blue-400 font-semibold">
                      + Create New Group
                    </option>
                  </select>
                </div>
                {formData.connect_group && (
                  <p className="mt-1 text-xs text-slate-400">
                    Selected: {connectGroups.find(g => g.id === formData.connect_group)?.name || formData.connect_group}
                  </p>
                )}
                {formData.connect_group === '__create_new__' && (
                  <p className="mt-2 text-xs text-blue-400">
                    Note: Use the Connect Groups page to create new groups, then refresh this dropdown.
                  </p>
                )}
              </div>

              {/* Birthday */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Birthday
                </label>
                <input
                  type="date"
                  value={formData.birthday}
                  onChange={(e) => setFormData({ ...formData, birthday: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              {/* Pastoral Notes */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Pastoral Notes
                </label>
                <textarea
                  value={formData.pastoral_notes}
                  onChange={(e) => setFormData({ ...formData, pastoral_notes: e.target.value })}
                  rows={4}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                  placeholder="Notes about this person..."
                />
              </div>

              {/* Actions */}
              <div className="flex gap-3 pt-4 border-t border-slate-700">
                <button
                  type="button"
                  onClick={handleCloseModal}
                  className="flex-1 px-6 py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                >
                  {editingPerson ? 'Update Person' : 'Create Person'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Import CSV Modal */}
      {showImportModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-800 rounded-xl border border-slate-700 max-w-md w-full">
            <div className="p-6 border-b border-slate-700">
              <h2 className="text-2xl font-bold text-white mb-2">Import PCO CSV</h2>
              <p className="text-slate-400">
                Upload a CSV file exported from Planning Center Online to import people into the database.
              </p>
            </div>
            <div className="p-6">
              <div className="mb-4">
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  CSV File
                </label>
                <input
                  type="file"
                  accept=".csv"
                  onChange={(e) => setImportFile(e.target.files[0])}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                />
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowImportModal(false);
                    setImportFile(null);
                  }}
                  className="flex-1 px-6 py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
                  disabled={importing}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleImportCSV}
                  disabled={!importFile || importing}
                  className="flex-1 px-6 py-3 bg-green-600 hover:bg-green-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
                >
                  {importing ? 'Importing...' : 'Import CSV'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Archive Confirmation Modal */}
      {showArchiveConfirm && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-800 rounded-xl border border-slate-700 max-w-md w-full">
            <div className="p-6 border-b border-slate-700">
              <h2 className="text-2xl font-bold text-white mb-2">Archive Person</h2>
              <p className="text-slate-400">
                Are you sure you want to archive <strong className="text-white">{showArchiveConfirm.preferred_name || showArchiveConfirm.full_name}</strong>?
              </p>
              <p className="text-slate-500 text-sm mt-2">
                Archived people can be restored later. They will be hidden from the main list unless you check "Include Archived".
              </p>
            </div>
            <div className="p-6 flex gap-3">
              <button
                onClick={() => setShowArchiveConfirm(null)}
                className="flex-1 px-6 py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => handleArchive(showArchiveConfirm)}
                className="flex-1 px-6 py-3 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg transition-colors"
              >
                Archive
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-800 rounded-xl border border-red-500/50 max-w-md w-full">
            <div className="p-6 border-b border-slate-700">
              <h2 className="text-2xl font-bold text-red-400 mb-2">Delete Person</h2>
              <p className="text-slate-400 mb-2">
                Are you sure you want to <strong className="text-red-400">permanently delete</strong> <strong className="text-white">{showDeleteConfirm.preferred_name || showDeleteConfirm.full_name}</strong>?
              </p>
              <p className="text-red-400 text-sm font-semibold mb-2">
                ⚠️ This action cannot be undone!
              </p>
              <p className="text-slate-500 text-sm">
                This will permanently remove the person and all their engagement data from the database. Consider archiving instead if you might need this data later.
              </p>
            </div>
            <div className="p-6 flex gap-3">
              <button
                onClick={() => setShowDeleteConfirm(null)}
                className="flex-1 px-6 py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDelete(showDeleteConfirm)}
                className="flex-1 px-6 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
              >
                Delete Permanently
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default People;

