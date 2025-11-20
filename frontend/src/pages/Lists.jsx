import React, { useState, useEffect } from 'react';
import {
  MagnifyingGlassIcon,
  ArrowDownTrayIcon,
  FunnelIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';

const Lists = () => {
  const [people, setPeople] = useState([]);
  const [filteredPeople, setFilteredPeople] = useState([]);
  const [loading, setLoading] = useState(true);
  const [campuses, setCampuses] = useState([]);
  
  // Filters
  const [campusFilter, setCampusFilter] = useState('all_campuses');
  const [departmentFilter, setDepartmentFilter] = useState('all');
  const [pulseFilter, setPulseFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [includeArchived, setIncludeArchived] = useState(false);
  
  // Export state
  const [exporting, setExporting] = useState(false);
  const [showFilters, setShowFilters] = useState(true);

  useEffect(() => {
    loadCampuses();
    loadPersons();
  }, []);

  useEffect(() => {
    loadPersons();
  }, [campusFilter, departmentFilter, pulseFilter, searchTerm, includeArchived]);

  const loadCampuses = async () => {
    try {
      const response = await fetch('/api/campuses', {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setCampuses(data.campuses || []);
      }
    } catch (err) {
      console.error('Error loading campuses:', err);
    }
  };

  const loadPersons = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (campusFilter && campusFilter !== 'all_campuses') {
        params.append('campus', campusFilter);
      }
      if (departmentFilter && departmentFilter !== 'all') {
        params.append('department', departmentFilter);
      }
      if (pulseFilter && pulseFilter !== 'all') {
        params.append('pulse_status', pulseFilter);
      }
      if (searchTerm) {
        params.append('search', searchTerm);
      }
      if (includeArchived) {
        params.append('include_archived', 'true');
      }

      const response = await fetch(`/api/persons?${params.toString()}`, {
        credentials: 'include',
        cache: 'no-store'
      });
      
      if (response.ok) {
        const data = await response.json();
        setPeople(data.people || []);
        setFilteredPeople(data.people || []);
      }
      setLoading(false);
    } catch (err) {
      console.error('Error loading people:', err);
      setLoading(false);
    }
  };

  const exportToCSV = async () => {
    try {
      setExporting(true);
      
      // Build export parameters
      const params = new URLSearchParams();
      if (campusFilter && campusFilter !== 'all_campuses') {
        params.append('campus', campusFilter);
      }
      if (departmentFilter && departmentFilter !== 'all') {
        params.append('department', departmentFilter);
      }
      if (pulseFilter && pulseFilter !== 'all') {
        params.append('pulse_status', pulseFilter);
      }
      if (searchTerm) {
        params.append('search', searchTerm);
      }
      if (includeArchived) {
        params.append('include_archived', 'true');
      }
      params.append('format', 'csv');

      const response = await fetch(`/api/persons/export?${params.toString()}`, {
        credentials: 'include'
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        
        // Generate filename with filters
        const filenameParts = ['people-export'];
        if (campusFilter && campusFilter !== 'all_campuses') {
          filenameParts.push(campusFilter);
        }
        if (departmentFilter && departmentFilter !== 'all') {
          filenameParts.push(departmentFilter.toLowerCase().replace(' ', '-'));
        }
        if (pulseFilter && pulseFilter !== 'all') {
          filenameParts.push(pulseFilter);
        }
        const filename = `${filenameParts.join('-')}-${new Date().toISOString().split('T')[0]}.csv`;
        
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        alert('Failed to export CSV. Please try again.');
      }
      setExporting(false);
    } catch (err) {
      console.error('Error exporting CSV:', err);
      alert('Error exporting CSV. Please try again.');
      setExporting(false);
    }
  };

  const clearFilters = () => {
    setCampusFilter('all_campuses');
    setDepartmentFilter('all');
    setPulseFilter('all');
    setSearchTerm('');
    setIncludeArchived(false);
  };

  const getResultCount = () => {
    return filteredPeople.length;
  };

  const getFilterSummary = () => {
    const parts = [];
    if (campusFilter && campusFilter !== 'all_campuses') {
      const campus = campuses.find(c => c.id === campusFilter);
      parts.push(campus ? campus.name : campusFilter);
    }
    if (departmentFilter && departmentFilter !== 'all') {
      parts.push(departmentFilter);
    }
    if (pulseFilter && pulseFilter !== 'all') {
      parts.push(pulseFilter.charAt(0).toUpperCase() + pulseFilter.slice(1));
    }
    return parts.length > 0 ? parts.join(' • ') : 'All People';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white">Lists</h1>
          <p className="text-slate-400 mt-1">
            Create and export filtered lists of people from your database
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition flex items-center gap-2"
          >
            <FunnelIcon className="h-5 w-5" />
            {showFilters ? 'Hide Filters' : 'Show Filters'}
          </button>
          <button
            onClick={exportToCSV}
            disabled={exporting || filteredPeople.length === 0}
            className="px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white rounded-lg transition flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ArrowDownTrayIcon className="h-5 w-5" />
            {exporting ? 'Exporting...' : `Export CSV (${getResultCount()})`}
          </button>
        </div>
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="bg-slate-900/60 border border-slate-700/60 rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white">Filters</h2>
            <button
              onClick={clearFilters}
              className="text-sm text-slate-400 hover:text-white flex items-center gap-1"
            >
              <XMarkIcon className="h-4 w-4" />
              Clear All
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Search */}
            <div className="lg:col-span-2">
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Search
              </label>
              <div className="relative">
                <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-slate-400" />
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
            <div>
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

            {/* Department Filter */}
            <div>
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

            {/* Pulse Status Filter */}
            <div>
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

            {/* Include Archived */}
            <div className="flex items-center pt-6">
              <label className="flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeArchived}
                  onChange={(e) => setIncludeArchived(e.target.checked)}
                  className="w-4 h-4 rounded bg-slate-700 border-slate-600 text-blue-500 focus:ring-blue-500 focus:ring-offset-slate-800"
                />
                <span className="ml-2 text-sm text-slate-300">Include Archived</span>
              </label>
            </div>
          </div>
        </div>
      )}

      {/* Results Summary */}
      <div className="bg-slate-900/60 border border-slate-700/60 rounded-2xl p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-white">
              {getFilterSummary()}
            </h3>
            <p className="text-sm text-slate-400 mt-1">
              {getResultCount()} {getResultCount() === 1 ? 'person' : 'people'} found
            </p>
          </div>
        </div>
      </div>

      {/* Results Table */}
      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
          <p className="text-slate-400 mt-4">Loading people...</p>
        </div>
      ) : filteredPeople.length === 0 ? (
        <div className="text-center py-12 bg-slate-900/60 border border-slate-700/60 rounded-2xl">
          <p className="text-slate-400">No people found matching your filters.</p>
          <button
            onClick={clearFilters}
            className="mt-4 text-blue-400 hover:text-blue-300"
          >
            Clear filters
          </button>
        </div>
      ) : (
        <div className="bg-slate-900/60 border border-slate-700/60 rounded-2xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-800/60">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Name</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Email</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Phone</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Campus</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Department</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Connect Group</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Pulse Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50">
                {filteredPeople.slice(0, 100).map((person) => (
                  <tr key={person.id} className="hover:bg-slate-800/30">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-white">{person.full_name}</div>
                      {person.preferred_name && (
                        <div className="text-sm text-slate-400">{person.preferred_name}</div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-300">
                      {person.email || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-300">
                      {person.phone || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-300">
                      {person.campus ? person.campus.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-300">
                      {person.department || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-300">
                      {person.connect_group || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        person.pulse_status === 'green' ? 'bg-green-500/20 text-green-200' :
                        person.pulse_status === 'amber' ? 'bg-amber-500/20 text-amber-200' :
                        'bg-red-500/20 text-red-200'
                      }`}>
                        {person.pulse_status === 'green' ? 'Active' :
                         person.pulse_status === 'amber' ? 'At Risk' : 'Inactive'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {filteredPeople.length > 100 && (
              <div className="px-6 py-4 bg-slate-800/60 text-sm text-slate-400 text-center">
                Showing first 100 of {filteredPeople.length} results. Export CSV to see all.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Lists;

