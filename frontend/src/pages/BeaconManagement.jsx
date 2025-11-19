import React, { useState, useEffect } from 'react';
import {
  SignalIcon,
  PlusIcon,
  PencilIcon,
  TrashIcon,
  XMarkIcon,
  CheckIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

const BeaconManagement = () => {
  const [beacons, setBeacons] = useState([]);
  const [campuses, setCampuses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingBeacon, setEditingBeacon] = useState(null);
  const [campusFilter, setCampusFilter] = useState('all_campuses');
  const [formData, setFormData] = useState({
    zone_name: '',
    campus: '',
    beacon_uuid: '',
    beacon_major: '',
    beacon_minor: '',
    is_active: true
  });

  useEffect(() => {
    loadCampuses();
    loadBeacons();
  }, [campusFilter]);

  const loadCampuses = async () => {
    try {
      const response = await fetch('/api/campuses/public', {
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

  const loadBeacons = async () => {
    try {
      setLoading(true);
      setError('');
      
      const params = new URLSearchParams();
      if (campusFilter && campusFilter !== 'all_campuses') {
        params.append('campus', campusFilter);
      }
      
      const response = await fetch(`/api/beacons?${params.toString()}`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        setBeacons(data.beacons || []);
      } else {
        setError('Failed to load beacons');
      }
    } catch (err) {
      console.error('Error loading beacons:', err);
      setError('Failed to connect to server');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenModal = (beacon = null) => {
    if (beacon) {
      setEditingBeacon(beacon);
      setFormData({
        zone_name: beacon.zone_name,
        campus: beacon.campus,
        beacon_uuid: beacon.beacon_uuid,
        beacon_major: beacon.beacon_major.toString(),
        beacon_minor: beacon.beacon_minor.toString(),
        is_active: beacon.is_active
      });
    } else {
      setEditingBeacon(null);
      setFormData({
        zone_name: '',
        campus: campuses.length > 0 ? campuses[0].name : '',
        beacon_uuid: '',
        beacon_major: '',
        beacon_minor: '',
        is_active: true
      });
    }
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setEditingBeacon(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validation
    if (!formData.zone_name.trim()) {
      alert('Zone name is required');
      return;
    }
    
    if (!formData.campus || formData.campus === 'all_campuses') {
      alert('Campus is required');
      return;
    }
    
    // Validate UUID format
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    if (!uuidRegex.test(formData.beacon_uuid.trim())) {
      alert('Invalid UUID format. Expected: 00000000-0000-0000-0000-000000000000');
      return;
    }
    
    // Validate major and minor are numbers
    const major = parseInt(formData.beacon_major);
    const minor = parseInt(formData.beacon_minor);
    if (isNaN(major) || isNaN(minor)) {
      alert('Major and Minor must be numbers');
      return;
    }
    
    if (major < 0 || major > 65535 || minor < 0 || minor > 65535) {
      alert('Major and Minor must be between 0 and 65535');
      return;
    }

    try {
      const url = editingBeacon 
        ? `/api/beacons/${editingBeacon.id}`
        : '/api/beacons';
      
      const method = editingBeacon ? 'PUT' : 'POST';
      
      const payload = {
        ...formData,
        beacon_major: major,
        beacon_minor: minor
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
        await loadBeacons();
        handleCloseModal();
        alert(editingBeacon ? 'Beacon updated successfully' : 'Beacon created successfully');
      } else {
        alert(data.error || 'Failed to save beacon');
      }
    } catch (err) {
      console.error('Error saving beacon:', err);
      alert('Failed to save beacon');
    }
  };

  const handleDelete = async (beacon) => {
    if (!confirm(`Are you sure you want to delete "${beacon.zone_name}"?`)) {
      return;
    }

    try {
      const response = await fetch(`/api/beacons/${beacon.id}`, {
        method: 'DELETE',
        credentials: 'include'
      });

      const data = await response.json();

      if (response.ok) {
        await loadBeacons();
        alert('Beacon deleted successfully');
      } else {
        alert(data.error || 'Failed to delete beacon');
      }
    } catch (err) {
      console.error('Error deleting beacon:', err);
      alert('Failed to delete beacon');
    }
  };

  const formatUUID = (uuid) => {
    // Format UUID for display: 00000000-0000-0000-0000-000000000000
    return uuid.toUpperCase();
  };

  if (loading && beacons.length === 0) {
    return (
      <div className="min-h-screen bg-slate-900 p-6 flex items-center justify-center">
        <div className="text-white text-xl">Loading beacons...</div>
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
                <SignalIcon className="w-10 h-10 mr-3 text-blue-500" />
                Beacon Management
              </h1>
              <p className="text-slate-400">Manage Bluetooth beacons and zones for automatic attendance tracking</p>
            </div>
            <button
              onClick={() => handleOpenModal()}
              className="flex items-center px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
            >
              <PlusIcon className="w-5 h-5 mr-2" />
              Add Beacon
            </button>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-500/20 border border-red-500/50 rounded-lg text-red-400">
            {error}
          </div>
        )}

        {/* Info Banner */}
        <div className="mb-6 p-4 bg-blue-500/20 border border-blue-500/50 rounded-lg text-blue-400">
          <div className="flex items-start">
            <ExclamationTriangleIcon className="w-5 h-5 mr-2 mt-0.5 flex-shrink-0" />
            <div className="text-sm">
              <p className="font-semibold mb-1">How it works:</p>
              <ul className="list-disc list-inside space-y-1 text-blue-300">
                <li>When people arrive on Sunday morning, their mobile app detects the beacon</li>
                <li>The app automatically sends attendance data to Heartbeat</li>
                <li>Attendance is recorded in real-time without manual check-in</li>
                <li>Each beacon needs a unique UUID, Major, and Minor value</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="mb-6 bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-4">
          <div className="flex items-center gap-4">
            <label className="text-sm font-medium text-slate-300">Filter by Campus:</label>
            <select
              value={campusFilter}
              onChange={(e) => setCampusFilter(e.target.value)}
              className="px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
            >
              <option value="all_campuses">All Campuses</option>
              {campuses.map(campus => (
                <option key={campus.id} value={campus.name}>
                  {campus.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Beacons Table */}
        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-700/50">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-slate-300">Zone Name</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-slate-300">Campus</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-slate-300">UUID</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-slate-300">Major</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-slate-300">Minor</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-slate-300">Status</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-slate-300">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50">
                {beacons.length === 0 ? (
                  <tr>
                    <td colSpan="7" className="px-6 py-12 text-center text-slate-400">
                      {loading ? 'Loading...' : 'No beacons found. Click "Add Beacon" to create one.'}
                    </td>
                  </tr>
                ) : (
                  beacons.map((beacon) => (
                    <tr 
                      key={beacon.id} 
                      className="hover:bg-slate-700/30 transition-colors"
                    >
                      <td className="px-6 py-4 text-white font-medium">{beacon.zone_name}</td>
                      <td className="px-6 py-4 text-slate-300">{beacon.campus}</td>
                      <td className="px-6 py-4 text-slate-300 font-mono text-xs">
                        {formatUUID(beacon.beacon_uuid)}
                      </td>
                      <td className="px-6 py-4 text-slate-300">{beacon.beacon_major}</td>
                      <td className="px-6 py-4 text-slate-300">{beacon.beacon_minor}</td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex px-3 py-1 rounded-full text-xs font-medium border ${
                          beacon.is_active 
                            ? 'bg-green-500/20 text-green-400 border-green-500/30'
                            : 'bg-slate-500/20 text-slate-400 border-slate-500/30'
                        }`}>
                          {beacon.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => handleOpenModal(beacon)}
                            title="Edit Beacon"
                            className="p-2 text-blue-400 hover:text-blue-300 hover:bg-blue-500/10 rounded-lg transition-colors"
                          >
                            <PencilIcon className="w-5 h-5" />
                          </button>
                          <button
                            onClick={() => handleDelete(beacon)}
                            title="Delete Beacon"
                            className="p-2 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-lg transition-colors"
                          >
                            <TrashIcon className="w-5 h-5" />
                          </button>
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

      {/* Add/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-800 rounded-xl border border-slate-700 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-slate-700 flex items-center justify-between sticky top-0 bg-slate-800 z-10">
              <h2 className="text-2xl font-bold text-white">
                {editingBeacon ? 'Edit Beacon' : 'Add New Beacon'}
              </h2>
              <button
                onClick={handleCloseModal}
                className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
              >
                <XMarkIcon className="w-6 h-6 text-slate-400" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-6">
              {/* Zone Name */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Zone Name <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={formData.zone_name}
                  onChange={(e) => setFormData({ ...formData, zone_name: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                  placeholder="e.g., Main Entrance, Sanctuary, Kids Area"
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
                  onChange={(e) => setFormData({ ...formData, campus: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="">Select Campus</option>
                  {campuses.map(campus => (
                    <option key={campus.id} value={campus.name}>
                      {campus.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* UUID */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Beacon UUID <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={formData.beacon_uuid}
                  onChange={(e) => setFormData({ ...formData, beacon_uuid: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white font-mono text-sm focus:outline-none focus:border-blue-500"
                  placeholder="00000000-0000-0000-0000-000000000000"
                  pattern="[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
                />
                <p className="mt-1 text-xs text-slate-400">
                  Format: 00000000-0000-0000-0000-000000000000
                </p>
              </div>

              {/* Major and Minor */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Major <span className="text-red-400">*</span>
                  </label>
                  <input
                    type="number"
                    required
                    min="0"
                    max="65535"
                    value={formData.beacon_major}
                    onChange={(e) => setFormData({ ...formData, beacon_major: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                    placeholder="0-65535"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Minor <span className="text-red-400">*</span>
                  </label>
                  <input
                    type="number"
                    required
                    min="0"
                    max="65535"
                    value={formData.beacon_minor}
                    onChange={(e) => setFormData({ ...formData, beacon_minor: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                    placeholder="0-65535"
                  />
                </div>
              </div>

              {/* Active Status */}
              <div>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="w-4 h-4 rounded bg-slate-700 border-slate-600 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm font-medium text-slate-300">Active (beacon is currently in use)</span>
                </label>
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
                  {editingBeacon ? 'Update Beacon' : 'Create Beacon'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default BeaconManagement;

