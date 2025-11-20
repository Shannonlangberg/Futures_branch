import React, { useState, useEffect } from 'react';
import {
  ArrowDownTrayIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';

const Lists = () => {
  const [allPeople, setAllPeople] = useState([]);
  const [filteredPeople, setFilteredPeople] = useState([]);
  const [loading, setLoading] = useState(true);
  const [campuses, setCampuses] = useState([]);
  
  // Multiple selections - arrays for multi-select
  const [selectedCampuses, setSelectedCampuses] = useState([]);
  const [selectedDepartments, setSelectedDepartments] = useState([]);
  const [selectedHeartbeat, setSelectedHeartbeat] = useState([]);
  
  // Export state
  const [exporting, setExporting] = useState(false);

  const departments = [
    { id: 'Kids', label: 'Kids' },
    { id: 'Youth', label: 'Youth' },
    { id: 'Young Adults', label: 'Young Adults' },
    { id: 'Families', label: 'Families' },
    { id: 'Adults', label: 'Adults' },
    { id: 'Seniors', label: 'Seniors' }
  ];

  const heartbeatOptions = [
    { id: 'green', label: 'Active', color: 'bg-green-500' },
    { id: 'amber', label: 'At Risk', color: 'bg-amber-500' },
    { id: 'red', label: 'Inactive', color: 'bg-red-500' }
  ];

  useEffect(() => {
    loadCampuses();
    loadAllPeople();
  }, []);

  // Filter people whenever selections change
  useEffect(() => {
    filterPeople();
  }, [allPeople, selectedCampuses, selectedDepartments, selectedHeartbeat]);

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

  const loadAllPeople = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/persons?include_archived=true', {
        credentials: 'include',
        cache: 'no-store'
      });
      
      if (response.ok) {
        const data = await response.json();
        setAllPeople(data.people || []);
      } else {
        console.error('Failed to load people');
        setAllPeople([]);
      }
      setLoading(false);
    } catch (err) {
      console.error('Error loading people:', err);
      setAllPeople([]);
      setLoading(false);
    }
  };

  const filterPeople = () => {
    let filtered = [...allPeople];

    // Filter by campus
    if (selectedCampuses.length > 0) {
      filtered = filtered.filter(person => 
        selectedCampuses.includes(person.campus)
      );
    }

    // Filter by department
    if (selectedDepartments.length > 0) {
      filtered = filtered.filter(person => {
        const personDept = person.department || '';
        return selectedDepartments.includes(personDept);
      });
    }

    // Filter by heartbeat status
    if (selectedHeartbeat.length > 0) {
      filtered = filtered.filter(person => {
        const pulseStatus = person.pulse_status || 'red';
        return selectedHeartbeat.includes(pulseStatus);
      });
    }

    setFilteredPeople(filtered);
  };

  const toggleCampus = (campusId) => {
    setSelectedCampuses(prev => 
      prev.includes(campusId) 
        ? prev.filter(id => id !== campusId)
        : [...prev, campusId]
    );
  };

  const toggleDepartment = (deptId) => {
    setSelectedDepartments(prev => 
      prev.includes(deptId) 
        ? prev.filter(id => id !== deptId)
        : [...prev, deptId]
    );
  };

  const toggleHeartbeat = (statusId) => {
    setSelectedHeartbeat(prev => 
      prev.includes(statusId) 
        ? prev.filter(id => id !== statusId)
        : [...prev, statusId]
    );
  };

  const escapeCSV = (value) => {
    if (value === null || value === undefined) return '';
    const str = String(value);
    if (str.includes(',') || str.includes('"') || str.includes('\n')) {
      return `"${str.replace(/"/g, '""')}"`;
    }
    return str;
  };

  const exportToCSV = async () => {
    try {
      setExporting(true);
      
      const csvRows = [];
      
      // Header row with all columns
      csvRows.push([
        'Name',
        'Preferred Name',
        'Email',
        'Phone',
        'Campus',
        'Department',
        'Connect Group',
        'Dream Team Roles',
        'Birthday',
        'Tags',
        'Pulse Status',
        'Last Seen',
        'Attendance Frequency',
        'Serving Frequency',
        'Overall Engagement',
        'DNA Completed',
        'Baptised On',
        'Filled Holy Spirit',
        'RISE Attended',
        'First Served On',
        'Pastoral Notes',
        'Is Active',
        'ID',
        'Created At',
        'Updated At'
      ].join(','));

      // Data rows
      filteredPeople.forEach(person => {
        // Parse JSON fields if they exist
        let dreamTeamRoles = '';
        let tags = '';
        
        try {
          if (person.dream_team_roles) {
            const roles = typeof person.dream_team_roles === 'string' 
              ? JSON.parse(person.dream_team_roles) 
              : person.dream_team_roles;
            dreamTeamRoles = Array.isArray(roles) ? roles.join(', ') : roles;
          }
        } catch (e) {
          dreamTeamRoles = person.dream_team_roles || '';
        }

        try {
          if (person.tags) {
            const tagList = typeof person.tags === 'string' 
              ? JSON.parse(person.tags) 
              : person.tags;
            tags = Array.isArray(tagList) ? tagList.join(', ') : tagList;
          }
        } catch (e) {
          tags = person.tags || '';
        }

        // Format dates
        const formatDate = (date) => {
          if (!date) return '';
          if (typeof date === 'string') return date.split('T')[0];
          if (date.toISOString) return date.toISOString().split('T')[0];
          return date;
        };

        csvRows.push([
          escapeCSV(person.full_name || ''),
          escapeCSV(person.preferred_name || ''),
          escapeCSV(person.email || ''),
          escapeCSV(person.phone || ''),
          escapeCSV(person.campus || ''),
          escapeCSV(person.department || ''),
          escapeCSV(person.connect_group || ''),
          escapeCSV(dreamTeamRoles),
          escapeCSV(formatDate(person.birthday)),
          escapeCSV(tags),
          escapeCSV(person.pulse_status || 'red'),
          escapeCSV(formatDate(person.last_seen)),
          escapeCSV(person.attendance_frequency || 0),
          escapeCSV(person.serving_frequency || 0),
          escapeCSV(person.overall_engagement || 0),
          escapeCSV(formatDate(person.dna_completed)),
          escapeCSV(formatDate(person.baptised_on)),
          escapeCSV(formatDate(person.filled_holy_spirit)),
          escapeCSV(formatDate(person.rise_attended)),
          escapeCSV(formatDate(person.first_served_on)),
          escapeCSV(person.pastoral_notes || ''),
          escapeCSV(person.is_active ? 'Yes' : 'No'),
          escapeCSV(person.id || ''),
          escapeCSV(formatDate(person.created_at)),
          escapeCSV(formatDate(person.updated_at))
        ].join(','));
      });
      
      // Create blob and download
      const csvContent = csvRows.join('\n');
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      
      // Generate filename
      const filenameParts = ['people-export'];
      if (selectedCampuses.length > 0 && selectedCampuses.length < campuses.length) {
        filenameParts.push(`${selectedCampuses.length}-campuses`);
      }
      if (selectedDepartments.length > 0 && selectedDepartments.length < departments.length) {
        filenameParts.push(`${selectedDepartments.length}-departments`);
      }
      if (selectedHeartbeat.length > 0 && selectedHeartbeat.length < heartbeatOptions.length) {
        filenameParts.push(`${selectedHeartbeat.length}-statuses`);
      }
      const filename = `${filenameParts.join('-')}-${new Date().toISOString().split('T')[0]}.csv`;
      
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      setExporting(false);
    } catch (err) {
      console.error('Error exporting CSV:', err);
      alert('Error exporting CSV. Please try again.');
      setExporting(false);
    }
  };

  const clearAll = () => {
    setSelectedCampuses([]);
    setSelectedDepartments([]);
    setSelectedHeartbeat([]);
  };

  const resultCount = filteredPeople.length;
  const hasSelections = selectedCampuses.length > 0 || selectedDepartments.length > 0 || selectedHeartbeat.length > 0;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-4xl font-bold text-white">LISTS</h1>
          <p className="text-slate-400 mt-1">
            Select campuses, departments, and heartbeat status, then export to CSV
          </p>
        </div>
        <div className="flex gap-3">
          {hasSelections && (
            <button
              onClick={clearAll}
              className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition"
            >
              Clear All
            </button>
          )}
          <button
            onClick={exportToCSV}
            disabled={exporting || resultCount === 0}
            className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white rounded-lg transition flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed font-semibold"
          >
            <ArrowDownTrayIcon className="h-5 w-5" />
            {exporting ? 'Exporting...' : `EXPORT (${resultCount} people)`}
          </button>
        </div>
      </div>

      {/* CAMPUS Section */}
      <div className="bg-slate-900/60 border border-slate-700/60 rounded-2xl p-6">
        <h2 className="text-xl font-semibold text-white mb-4">CAMPUS</h2>
        <div className="flex flex-wrap gap-3">
          {campuses.map(campus => {
            const isSelected = selectedCampuses.includes(campus.id);
            return (
              <button
                key={campus.id}
                onClick={() => toggleCampus(campus.id)}
                className={`
                  px-6 py-3 rounded-lg font-medium transition-all duration-200
                  flex items-center gap-2
                  ${isSelected
                    ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/30 border-2 border-blue-400'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600 border-2 border-transparent'
                  }
                `}
              >
                {isSelected && <CheckCircleIcon className="h-5 w-5" />}
                {campus.name}
              </button>
            );
          })}
        </div>
      </div>

      {/* DEPARTMENT Section */}
      <div className="bg-slate-900/60 border border-slate-700/60 rounded-2xl p-6">
        <h2 className="text-xl font-semibold text-white mb-4">DEPARTMENT</h2>
        <div className="flex flex-wrap gap-3">
          {departments.map(dept => {
            const isSelected = selectedDepartments.includes(dept.id);
            return (
              <button
                key={dept.id}
                onClick={() => toggleDepartment(dept.id)}
                className={`
                  px-6 py-3 rounded-lg font-medium transition-all duration-200
                  flex items-center gap-2
                  ${isSelected
                    ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/30 border-2 border-blue-400'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600 border-2 border-transparent'
                  }
                `}
              >
                {isSelected && <CheckCircleIcon className="h-5 w-5" />}
                {dept.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* HEARTBEAT Section */}
      <div className="bg-slate-900/60 border border-slate-700/60 rounded-2xl p-6">
        <h2 className="text-xl font-semibold text-white mb-4">HEARTBEAT</h2>
        <div className="flex flex-wrap gap-3">
          {heartbeatOptions.map(option => {
            const isSelected = selectedHeartbeat.includes(option.id);
            return (
              <button
                key={option.id}
                onClick={() => toggleHeartbeat(option.id)}
                className={`
                  px-6 py-3 rounded-lg font-medium transition-all duration-200
                  flex items-center gap-2
                  ${isSelected
                    ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/30 border-2 border-blue-400'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600 border-2 border-transparent'
                  }
                `}
              >
                {isSelected && <CheckCircleIcon className="h-5 w-5" />}
                <span className={`w-3 h-3 rounded-full ${option.color}`}></span>
                {option.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Results Summary */}
      {hasSelections && (
        <div className="bg-slate-900/60 border border-slate-700/60 rounded-2xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-white">Results</h3>
              <p className="text-sm text-slate-400 mt-1">
                {loading ? 'Loading...' : `${resultCount} ${resultCount === 1 ? 'person' : 'people'} will be exported`}
              </p>
            </div>
            {loading && (
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white"></div>
            )}
          </div>
        </div>
      )}

      {!hasSelections && !loading && (
        <div className="bg-slate-900/60 border border-slate-700/60 rounded-2xl p-6 text-center">
          <p className="text-slate-400">Select campuses, departments, or heartbeat status to filter and export</p>
        </div>
      )}
    </div>
  );
};

export default Lists;
