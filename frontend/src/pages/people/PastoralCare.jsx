import React, { useState, useEffect } from 'react';
import { 
  UserCircleIcon, 
  ExclamationTriangleIcon, 
  ClockIcon,
  PlusIcon,
  PencilIcon,
  XMarkIcon,
  CheckCircleIcon,
  UserGroupIcon,
  HeartIcon,
  FunnelIcon,
  BuildingOfficeIcon,
  CalendarIcon,
  HandRaisedIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline';
// Removed CampusSelector import - using inline selector instead

const PastoralCare = () => {
  // Debug: Log that component is rendering
  console.log('🔵 PastoralCare component is rendering!');
  
  const [careCases, setCareCases] = useState([]);
  const [prayerRequests, setPrayerRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showAssignModal, setShowAssignModal] = useState(null);
  const [selectedTab, setSelectedTab] = useState('cases'); // 'cases', 'prayer', 'all'
  const [statusFilter, setStatusFilter] = useState('all'); // 'open', 'resolved', 'all' - Start with 'all' to show everything
  const [priorityFilter, setPriorityFilter] = useState('all'); // 'all', 'high', 'medium', 'low'
  const [searchTerm, setSearchTerm] = useState('');
  const [userRole, setUserRole] = useState('');
  const [userCampus, setUserCampus] = useState('');
  const [selectedCampus, setSelectedCampus] = useState(null);
  const [campuses, setCampuses] = useState([]);
  const [showCampusSelector, setShowCampusSelector] = useState(false);
  const [pastors, setPastors] = useState([]);
  
  const [formData, setFormData] = useState({
    person_id: '',
    person_name: '',
    priority: 'medium',
    notes: '',
    assigned_leader: '',
    follow_up_date: '',
    ai_summary: ''
  });

  useEffect(() => {
    fetchUserSession();
    loadCampuses();
    loadPastors();
  }, []);

  useEffect(() => {
    if (userRole) { // Only load when we have user role
      loadCareCases();
      if (selectedTab === 'prayer' || selectedTab === 'all') {
        loadPrayerRequests();
      }
    }
  }, [selectedTab, statusFilter, priorityFilter, selectedCampus, userRole, searchTerm]);

  const fetchUserSession = async () => {
    try {
      const response = await fetch('/api/session', {
        credentials: 'include',
        cache: 'no-store'
      });
      const data = await response.json();
      if (data.authenticated) {
        setUserRole(data.role || 'user');
        setUserCampus(data.campus || 'all_campuses');
        
        // Show campus selector for senior leadership - DISABLED for now to avoid dashboard selector
        const hasFullAccess = ['admin', 'senior_leadership', 'senior_pastor', 'lead_pastor'].includes(data.role);
        setShowCampusSelector(false); // Temporarily disabled - will show simple dropdown instead
        
        // Auto-select campus for campus pastors
        if (data.role === 'campus_pastor' && data.campus && data.campus !== 'all_campuses') {
          const normalizedCampus = data.campus.toLowerCase().trim().replace(/\s+/g, '_');
          // Will be set when campuses load
        }
      }
    } catch (error) {
      console.error('Error fetching user session:', error);
    }
  };

  const loadCampuses = async () => {
    try {
      const response = await fetch('/api/campuses/public');
      if (response.ok) {
        const data = await response.json();
        const campusesList = data.campuses || [];
        setCampuses(campusesList);
        
        // Auto-select campus for campus pastors
        if (userRole === 'campus_pastor' && userCampus && userCampus !== 'all_campuses') {
          const normalizedCampus = userCampus.toLowerCase().trim().replace(/\s+/g, '_');
          const foundCampus = campusesList.find(c => {
            const campusId = (c.id || '').toLowerCase().trim();
            return campusId === normalizedCampus || campusId === userCampus.toLowerCase().trim();
          });
          if (foundCampus) {
            setSelectedCampus({ id: foundCampus.id, name: foundCampus.name || foundCampus.display_name });
          }
        } else if (campusesList.length > 0 && !selectedCampus) {
          // Default to all campuses for admins
          setSelectedCampus({ id: 'all_campuses', name: 'All Campuses' });
        }
      }
    } catch (error) {
      console.error('Error loading campuses:', error);
    }
  };

  const loadPastors = async () => {
    try {
      const response = await fetch('/api/users', {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        const users = data.users || [];
        // Filter to pastors/leaders
        const pastorRoles = ['admin', 'senior_leadership', 'senior_pastor', 'lead_pastor', 'campus_pastor', 'pastor', 'staff'];
        const pastorList = users
          .filter(u => pastorRoles.includes(u.role))
          .map(u => ({ id: u.id, name: u.full_name || u.username, role: u.role }));
        setPastors(pastorList);
      }
    } catch (error) {
      console.error('Error loading pastors:', error);
    }
  };

  const loadCareCases = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      
      if (statusFilter !== 'all') {
        params.append('status', statusFilter);
      }
      if (priorityFilter !== 'all') {
        params.append('priority', priorityFilter);
      }
      
      const response = await fetch(`/api/pastoral-care/cases?${params.toString()}`, {
        credentials: 'include',
        cache: 'no-store'
      });
      
      if (response.ok) {
        const data = await response.json();
        let cases = data.cases || [];
        
        console.log('Loaded care cases:', cases.length, cases);
        
        // Apply campus filter - simplified to avoid blocking
        if (selectedCampus && selectedCampus.id !== 'all_campuses') {
          // For now, just filter if we have campus info in the case itself
          // We'll improve this later with proper person lookup
          cases = cases.filter(c => {
            // If case has campus info, use it; otherwise include it (will be filtered later)
            if (c.campus) {
              const caseCampus = (c.campus || '').toLowerCase().trim().replace(/\s+/g, '_');
              const selectedCampusId = (selectedCampus.id || '').toLowerCase().trim();
              return caseCampus === selectedCampusId;
            }
            // Include cases without campus info for now (we can improve this)
            return true;
          });
        }
        
        // Apply search filter
        if (searchTerm) {
          cases = cases.filter(c => 
            (c.person_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
            (c.notes || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
            (c.assigned_leader || '').toLowerCase().includes(searchTerm.toLowerCase())
          );
        }
        
        console.log('Filtered care cases:', cases.length);
        setCareCases(cases);
      } else {
        console.error('Failed to load care cases:', response.status, response.statusText);
        setCareCases([]);
      }
    } catch (err) {
      console.error('Error loading care cases:', err);
      setCareCases([]);
    } finally {
      setLoading(false);
    }
  };

  const loadPrayerRequests = async () => {
    try {
      const response = await fetch('/api/prayer/submissions', {
        credentials: 'include',
        cache: 'no-store'
      });
      
      if (response.ok) {
        const data = await response.json();
        let requests = data.submissions || [];
        
        // Filter to only prayer requests (not praise reports) and open status
        requests = requests.filter(r => 
          r.type === 'prayer_request' && 
          (r.status === 'open' || r.status === 'in_progress')
        );
        
        // Apply campus filter
        if (selectedCampus && selectedCampus.id !== 'all_campuses') {
          requests = requests.filter(r => {
            const requestCampus = (r.campus || '').toLowerCase().trim().replace(/\s+/g, '_');
            const selectedCampusId = (selectedCampus.id || '').toLowerCase().trim();
            return requestCampus === selectedCampusId;
          });
        }
        
        // Apply search filter
        if (searchTerm) {
          requests = requests.filter(r => 
            (r.person_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
            (r.summary || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
            (r.details || '').toLowerCase().includes(searchTerm.toLowerCase())
          );
        }
        
        setPrayerRequests(requests);
      }
    } catch (err) {
      console.error('Error loading prayer requests:', err);
      setPrayerRequests([]);
    }
  };

  const handleCreateCase = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/pastoral-care/cases', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          person_id: formData.person_id,
          priority: formData.priority,
          notes: formData.notes,
          assigned_leader: formData.assigned_leader || null,
          follow_up_date: formData.follow_up_date || null,
          status: 'open'
        })
      });
      
      if (response.ok) {
        setShowCreateModal(false);
        setFormData({
          person_id: '',
          person_name: '',
          priority: 'medium',
          notes: '',
          assigned_leader: '',
          follow_up_date: '',
          ai_summary: ''
        });
        loadCareCases();
      } else {
        const error = await response.json();
        alert(`Error: ${error.error || 'Failed to create case'}`);
      }
    } catch (err) {
      console.error('Error creating case:', err);
      alert('Failed to create case');
    }
  };

  const handleAssignLeader = async (caseId, leaderName) => {
    try {
      const response = await fetch(`/api/pastoral-care/cases/${caseId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          assigned_leader: leaderName
        })
      });
      
      if (response.ok) {
        setShowAssignModal(null);
        loadCareCases();
      }
    } catch (err) {
      console.error('Error assigning leader:', err);
      alert('Failed to assign leader');
    }
  };

  const handleResolveCase = async (caseId) => {
    if (!window.confirm('Mark this case as resolved?')) return;
    
    try {
      const response = await fetch(`/api/pastoral-care/cases/${caseId}/resolve`, {
        method: 'POST',
        credentials: 'include'
      });
      
      if (response.ok) {
        loadCareCases();
      }
    } catch (err) {
      console.error('Error resolving case:', err);
      alert('Failed to resolve case');
    }
  };

  const handleCreateCaseFromPrayer = async (prayerRequest) => {
    setFormData({
      person_id: prayerRequest.person_id || '',
      person_name: prayerRequest.person_name || '',
      priority: 'medium',
      notes: `Prayer Request: ${prayerRequest.summary || prayerRequest.details || ''}`,
      assigned_leader: '',
      follow_up_date: '',
      ai_summary: ''
    });
    setShowCreateModal(true);
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high':
        return 'bg-red-500/20 text-red-400 border-red-500/50';
      case 'medium':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50';
      case 'low':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/50';
      default:
        return 'bg-slate-500/20 text-slate-400 border-slate-500/50';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'open':
        return 'bg-orange-500/20 text-orange-400 border-orange-500/50';
      case 'resolved':
        return 'bg-green-500/20 text-green-400 border-green-500/50';
      case 'closed':
        return 'bg-slate-500/20 text-slate-400 border-slate-500/50';
      default:
        return 'bg-slate-500/20 text-slate-400 border-slate-500/50';
    }
  };

  const canCreateCase = ['admin', 'senior_leadership', 'senior_pastor', 'lead_pastor', 'campus_pastor', 'pastor', 'staff'].includes(userRole);

  const filteredCases = careCases;
  const filteredPrayerRequests = prayerRequests;

  // Debug: Log current state
  useEffect(() => {
    console.log('PastoralCare State:', {
      loading,
      careCasesCount: careCases.length,
      prayerRequestsCount: prayerRequests.length,
      selectedTab,
      statusFilter,
      priorityFilter,
      selectedCampus,
      userRole
    });
  }, [loading, careCases.length, prayerRequests.length, selectedTab, statusFilter, priorityFilter, selectedCampus, userRole]);

  // Ensure we always render the Pastoral Care UI, never CampusSelector
  console.log('🔵 PastoralCare component rendering - URL:', window.location.pathname);
  console.log('🔵 showCampusSelector:', showCampusSelector, 'campuses:', campuses.length);
  
  // CRITICAL: Never render CampusSelector - this component should ONLY show Pastoral Care UI
  return (
    <div className="h-full bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6 overflow-y-auto" data-page="pastoral-care">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-3xl font-bold text-white mb-2">Pastoral Care</h2>
            <p className="text-white/60">Care engine for tracking and managing pastoral needs</p>
            <p className="text-red-400 text-xs mt-1">⚠️ If you see "Campus Dashboard Selection" below, the frontend needs to be rebuilt!</p>
          </div>
          {canCreateCase && (
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors"
            >
              <PlusIcon className="h-5 w-5" />
              Create Case
            </button>
          )}
        </div>

        {/* Campus Selector - Simple Dropdown */}
        {showCampusSelector && campuses.length > 0 && (
          <div className="mb-4">
            <label className="block text-white/80 mb-2 text-sm font-medium">Filter by Campus</label>
            <select
              value={selectedCampus?.id || 'all_campuses'}
              onChange={(e) => {
                const campusId = e.target.value;
                if (campusId === 'all_campuses') {
                  setSelectedCampus({ id: 'all_campuses', name: 'All Campuses' });
                } else {
                  const campus = campuses.find(c => c.id === campusId || c.campus_id === campusId);
                  if (campus) {
                    setSelectedCampus({ 
                      id: campus.id || campus.campus_id, 
                      name: campus.name || campus.display_name || campusId 
                    });
                  }
                }
                loadCareCases();
                if (selectedTab === 'prayer' || selectedTab === 'all') {
                  loadPrayerRequests();
                }
              }}
              className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-purple-500 min-w-[200px]"
            >
              <option value="all_campuses">All Campuses</option>
              {campuses.map(campus => (
                <option key={campus.id || campus.campus_id} value={campus.id || campus.campus_id}>
                  {campus.name || campus.display_name || campus.id || campus.campus_id}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-2 mb-4 border-b border-white/10">
          <button
            onClick={() => setSelectedTab('cases')}
            className={`px-4 py-2 font-medium transition-colors ${
              selectedTab === 'cases'
                ? 'text-purple-400 border-b-2 border-purple-400'
                : 'text-white/60 hover:text-white'
            }`}
          >
            Care Cases ({filteredCases.length})
          </button>
          <button
            onClick={() => setSelectedTab('prayer')}
            className={`px-4 py-2 font-medium transition-colors ${
              selectedTab === 'prayer'
                ? 'text-purple-400 border-b-2 border-purple-400'
                : 'text-white/60 hover:text-white'
            }`}
          >
            Prayer Requests ({filteredPrayerRequests.length})
          </button>
          <button
            onClick={() => setSelectedTab('all')}
            className={`px-4 py-2 font-medium transition-colors ${
              selectedTab === 'all'
                ? 'text-purple-400 border-b-2 border-purple-400'
                : 'text-white/60 hover:text-white'
            }`}
          >
            All ({filteredCases.length + filteredPrayerRequests.length})
          </button>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-4 mb-4">
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-white/40" />
              <input
                type="text"
                placeholder="Search cases or requests..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-white/40 focus:outline-none focus:border-purple-500"
              />
            </div>
          </div>
          
          {(selectedTab === 'cases' || selectedTab === 'all') && (
            <>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-purple-500"
              >
                <option value="open">Open</option>
                <option value="resolved">Resolved</option>
                <option value="all">All Status</option>
              </select>
              
              <select
                value={priorityFilter}
                onChange={(e) => setPriorityFilter(e.target.value)}
                className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-purple-500"
              >
                <option value="all">All Priorities</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </>
          )}
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <div className="text-center py-12 text-white/60">Loading...</div>
      ) : (
        <div className="space-y-4">
          {/* Care Cases */}
          {(selectedTab === 'cases' || selectedTab === 'all') && filteredCases.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold text-white mb-3">Care Cases</h3>
              {filteredCases.map((case_) => (
                <div
                  key={case_.id}
                  className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-6 mb-4 hover:border-purple-500/50 transition-colors"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2 flex-wrap">
                        <h3 className="text-xl font-semibold text-white">
                          {case_.person_name || 'Unnamed Case'}
                        </h3>
                        <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getPriorityColor(case_.priority)}`}>
                          {case_.priority || 'medium'} priority
                        </span>
                        <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(case_.status)}`}>
                          {case_.status || 'open'}
                        </span>
                      </div>
                      <div className="text-white/60 text-sm mb-4">{case_.notes}</div>
                    </div>
                    <div className="flex gap-2">
                      {canCreateCase && case_.status === 'open' && (
                        <>
                          <button
                            onClick={() => setShowAssignModal(case_.id)}
                            className="p-2 text-white/60 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
                            title="Assign Leader"
                          >
                            <UserGroupIcon className="h-5 w-5" />
                          </button>
                          <button
                            onClick={() => handleResolveCase(case_.id)}
                            className="p-2 text-white/60 hover:text-green-400 hover:bg-white/10 rounded-lg transition-colors"
                            title="Resolve Case"
                          >
                            <CheckCircleIcon className="h-5 w-5" />
                          </button>
                        </>
                      )}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-white/5 rounded-lg p-4">
                      <div className="text-white/60 text-sm mb-1">Assigned Leader</div>
                      <div className="text-white font-medium">{case_.assigned_leader || 'Unassigned'}</div>
                    </div>
                    <div className="bg-white/5 rounded-lg p-4">
                      <div className="text-white/60 text-sm mb-1">Follow-up Timeline</div>
                      <div className="text-white font-medium">
                        {case_.follow_up_date ? new Date(case_.follow_up_date).toLocaleDateString() : 'No date set'}
                      </div>
                    </div>
                    <div className="bg-white/5 rounded-lg p-4">
                      <div className="text-white/60 text-sm mb-1">Created</div>
                      <div className="text-white font-medium">
                        {case_.created_at ? new Date(case_.created_at).toLocaleDateString() : 'Unknown'}
                      </div>
                    </div>
                  </div>

                  {case_.ai_summary && (
                    <div className="mt-4 bg-purple-500/10 border border-purple-500/30 rounded-lg p-4">
                      <div className="text-purple-400 font-semibold mb-2">AI Care Summary</div>
                      <div className="text-white/80">{case_.ai_summary}</div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Prayer Requests */}
          {(selectedTab === 'prayer' || selectedTab === 'all') && filteredPrayerRequests.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold text-white mb-3">Prayer Requests</h3>
              {filteredPrayerRequests.map((request) => (
                <div
                  key={request.id}
                  className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-6 mb-4 hover:border-purple-500/50 transition-colors"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <HeartIcon className="h-5 w-5 text-pink-400" />
                        <h3 className="text-xl font-semibold text-white">
                          {request.person_name || 'Anonymous'}
                        </h3>
                        {request.campus && (
                          <span className="px-2 py-1 bg-blue-500/20 text-blue-400 text-xs rounded">
                            {request.campus}
                          </span>
                        )}
                      </div>
                      <div className="text-white/60 text-sm mb-4">{request.summary || request.details || 'No details'}</div>
                    </div>
                    {canCreateCase && (
                      <button
                        onClick={() => handleCreateCaseFromPrayer(request)}
                        className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-medium transition-colors"
                      >
                        Create Case
                      </button>
                    )}
                  </div>
                  <div className="text-white/40 text-xs">
                    {request.created_at ? new Date(request.created_at).toLocaleString() : 'Unknown date'}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Empty State */}
          {((selectedTab === 'cases' && filteredCases.length === 0) ||
            (selectedTab === 'prayer' && filteredPrayerRequests.length === 0) ||
            (selectedTab === 'all' && filteredCases.length === 0 && filteredPrayerRequests.length === 0)) && (
            <div className="text-center py-12 text-white/60">
              <HandRaisedIcon className="h-16 w-16 mx-auto mb-4 text-white/20" />
              <p className="text-lg mb-2">No {selectedTab === 'all' ? 'items' : selectedTab === 'cases' ? 'care cases' : 'prayer requests'} found</p>
              {canCreateCase && selectedTab !== 'prayer' && (
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="mt-4 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors"
                >
                  Create Your First Case
                </button>
              )}
            </div>
          )}
        </div>
      )}

      {/* Create Case Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 rounded-2xl p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-2xl font-bold text-white">Create Care Case</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-white/60 hover:text-white"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>
            
            <form onSubmit={handleCreateCase} className="space-y-4">
              <div>
                <label className="block text-white/80 mb-2">Person Name/ID</label>
                <input
                  type="text"
                  value={formData.person_name || formData.person_id}
                  onChange={(e) => {
                    setFormData({ ...formData, person_name: e.target.value, person_id: e.target.value });
                  }}
                  placeholder="Enter person name or ID"
                  className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-purple-500"
                  required
                />
              </div>
              
              <div>
                <label className="block text-white/80 mb-2">Priority</label>
                <select
                  value={formData.priority}
                  onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                  className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-purple-500"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>
              
              <div>
                <label className="block text-white/80 mb-2">Notes</label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  placeholder="Describe the care need..."
                  rows={4}
                  className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-purple-500"
                  required
                />
              </div>
              
              <div>
                <label className="block text-white/80 mb-2">Assign Leader</label>
                <select
                  value={formData.assigned_leader}
                  onChange={(e) => setFormData({ ...formData, assigned_leader: e.target.value })}
                  className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-purple-500"
                >
                  <option value="">Unassigned</option>
                  {pastors.map(p => (
                    <option key={p.id} value={p.name}>{p.name}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-white/80 mb-2">Follow-up Date</label>
                <input
                  type="date"
                  value={formData.follow_up_date}
                  onChange={(e) => setFormData({ ...formData, follow_up_date: e.target.value })}
                  className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-purple-500"
                />
              </div>
              
              <div className="flex gap-3 pt-4">
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors"
                >
                  Create Case
                </button>
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 bg-white/5 hover:bg-white/10 text-white rounded-lg font-medium transition-colors"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Assign Leader Modal */}
      {showAssignModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 rounded-2xl p-6 max-w-md w-full">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-white">Assign Leader</h3>
              <button
                onClick={() => setShowAssignModal(null)}
                className="text-white/60 hover:text-white"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>
            
            <div className="space-y-3">
              {pastors.map(pastor => (
                <button
                  key={pastor.id}
                  onClick={() => handleAssignLeader(showAssignModal, pastor.name)}
                  className="w-full text-left px-4 py-3 bg-white/5 hover:bg-white/10 rounded-lg text-white transition-colors"
                >
                  {pastor.name} <span className="text-white/40 text-sm">({pastor.role})</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PastoralCare;
