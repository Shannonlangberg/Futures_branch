import React, { useState, useEffect } from 'react';
import {
  ArrowDownTrayIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';

const Lists = () => {
  const [people, setPeople] = useState([]);
  const [loading, setLoading] = useState(true);
  const [campuses, setCampuses] = useState([]);
  
  // Multiple selections - arrays for multi-select
  const [selectedCampuses, setSelectedCampuses] = useState([]);
  const [selectedDepartments, setSelectedDepartments] = useState([]);
  const [selectedHeartbeat, setSelectedHeartbeat] = useState([]);
  
  // Export state
  const [exporting, setExporting] = useState(false);
  const [resultCount, setResultCount] = useState(0);

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
  }, []);

  useEffect(() => {
    loadPersons();
  }, [selectedCampuses, selectedDepartments, selectedHeartbeat]);

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
      // Build query - we'll get all people and filter client-side for now
      // Or we could make multiple API calls and combine
      const allPeople = [];
      
      // If campuses selected, query each one
      if (selectedCampuses.length > 0) {
        for (const campusId of selectedCampuses) {
          const params = new URLSearchParams();
          params.append('campus', campusId);
          
          // Add department filters if any selected
          if (selectedDepartments.length > 0) {
            // We'll need to handle multiple departments - query each
            for (const dept of selectedDepartments) {
              const deptParams = new URLSearchParams(params);
              deptParams.append('department', dept);
              
              const response = await fetch(`/api/persons?${deptParams.toString()}`, {
                credentials: 'include',
                cache: 'no-store'
              });
              
              if (response.ok) {
                const data = await response.json();
                // Merge results, avoiding duplicates
                const newPeople = (data.people || []).filter(p => 
                  !allPeople.find(existing => existing.id === p.id)
                );
                allPeople.push(...newPeople);
              }
            }
          } else {
            // No department filter, just get all from this campus
            const response = await fetch(`/api/persons?${params.toString()}`, {
              credentials: 'include',
              cache: 'no-store'
            });
            
            if (response.ok) {
              const data = await response.json();
              const newPeople = (data.people || []).filter(p => 
                !allPeople.find(existing => existing.id === p.id)
              );
              allPeople.push(...newPeople);
            }
          }
        }
      } else {
        // No campuses selected, get all people
        const params = new URLSearchParams();
        if (selectedDepartments.length > 0) {
          // Still need to filter by department
          for (const dept of selectedDepartments) {
            const deptParams = new URLSearchParams();
            deptParams.append('department', dept);
            
            const response = await fetch(`/api/persons?${deptParams.toString()}`, {
              credentials: 'include',
              cache: 'no-store'
            });
            
            if (response.ok) {
              const data = await response.json();
              const newPeople = (data.people || []).filter(p => 
                !allPeople.find(existing => existing.id === p.id)
              );
              allPeople.push(...newPeople);
            }
          }
        } else {
          // Get all people
          const response = await fetch(`/api/persons?${params.toString()}`, {
            credentials: 'include',
            cache: 'no-store'
          });
          
          if (response.ok) {
            const data = await response.json();
            allPeople.push(...(data.people || []));
          }
        }
      }
      
      // Filter by heartbeat status if selected
      let filtered = allPeople;
      if (selectedHeartbeat.length > 0) {
        filtered = allPeople.filter(p => 
          selectedHeartbeat.includes(p.pulse_status || 'red')
        );
      }
      
      setPeople(filtered);
      setResultCount(filtered.length);
      setLoading(false);
    } catch (err) {
      console.error('Error loading people:', err);
      setLoading(false);
    }
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

  const exportToCSV = async () => {
    try {
      setExporting(true);
      
      // Build export parameters for multiple selections
      // We'll export each combination and combine, or modify backend to accept arrays
      const params = new URLSearchParams();
      
      // For now, export what we have loaded
      // In a better implementation, we'd pass arrays to the backend
      if (selectedCampuses.length === 1) {
        params.append('campus', selectedCampuses[0]);
      }
      if (selectedDepartments.length === 1) {
        params.append('department', selectedDepartments[0]);
      }
      if (selectedHeartbeat.length === 1) {
        params.append('pulse_status', selectedHeartbeat[0]);
      }
      
      // If multiple selections, we'll need to handle differently
      // For now, let's create a CSV from the current filtered results
      const csvRows = [];
      
      // Header
      csvRows.push([
        'ID', 'Full Name', 'Preferred Name', 'Email', 'Phone',
        'Campus', 'Department', 'Connect Group', 'Dream Team Roles',
        'Birthday', 'Tags', 'Pulse Status', 'Last Seen',
        'Attendance Frequency', 'Serving Frequency', 'Overall Engagement',
        'DNA Completed', 'Baptised On', 'Filled Holy Spirit',
        'RISE Attended', 'First Served On', 'Pastoral Notes',
        'Is Active', 'Created At', 'Updated At'
      ].join(','));
      
      // Data rows
      people.forEach(person => {
        const dreamTeamRoles = Array.isArray(person.dream_team_roles) 
          ? person.dream_team_roles.join(', ') 
          : (person.dream_team_roles || '');
        const tags = Array.isArray(person.tags) 
          ? person.tags.join(', ') 
          : (person.tags || '');
        
        csvRows.push([
          person.id || '',
          `"${(person.full_name || '').replace(/"/g, '""')}"`,
          `"${(person.preferred_name || '').replace(/"/g, '""')}"`,
          person.email || '',
          person.phone || '',
          person.campus || '',
          person.department || '',
          person.connect_group || '',
          `"${dreamTeamRoles.replace(/"/g, '""')}"`,
          person.birthday || '',
          `"${tags.replace(/"/g, '""')}"`,
          person.pulse_status || 'red',
          person.last_seen || '',
          person.attendance_frequency || 0,
          person.serving_frequency || 0,
          person.overall_engagement || 0,
          person.dna_completed || '',
          person.baptised_on || '',
          person.filled_holy_spirit || '',
          person.rise_attended || '',
          person.first_served_on || '',
          `"${(person.pastoral_notes || '').replace(/"/g, '""')}"`,
          person.is_active ? 'Yes' : 'No',
          person.created_at || '',
          person.updated_at || ''
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
      if (selectedCampuses.length > 0) {
        filenameParts.push(`${selectedCampuses.length}-campuses`);
      }
      if (selectedDepartments.length > 0) {
        filenameParts.push(`${selectedDepartments.length}-departments`);
      }
      if (selectedHeartbeat.length > 0) {
        filenameParts.push(selectedHeartbeat.join('-'));
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
          {(selectedCampuses.length > 0 || selectedDepartments.length > 0 || selectedHeartbeat.length > 0) && (
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
      {(selectedCampuses.length > 0 || selectedDepartments.length > 0 || selectedHeartbeat.length > 0) && (
        <div className="bg-slate-900/60 border border-slate-700/60 rounded-2xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-white">Results</h3>
              <p className="text-sm text-slate-400 mt-1">
                {resultCount} {resultCount === 1 ? 'person' : 'people'} will be exported
              </p>
            </div>
            {loading && (
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white"></div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Lists;
