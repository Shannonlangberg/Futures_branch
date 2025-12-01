import React, { useState, useEffect } from 'react';
import { PlusIcon, PencilIcon, EyeIcon, CheckIcon, BookOpenIcon } from '@heroicons/react/24/outline';
import { Link } from 'react-router-dom';

const DevotionsAdmin = () => {
  const [plans, setPlans] = useState([]);
  const [campuses, setCampuses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingPlan, setEditingPlan] = useState(null);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    campus: '', // Empty = All Campuses
    total_days: 30, // Add custom length
    start_date: '',
    end_date: '',
    status: 'draft'
  });

  useEffect(() => {
    fetchCampuses();
    fetchPlans();
  }, []);

  const fetchCampuses = async () => {
    try {
      const response = await fetch('/api/campuses/public');
      if (response.ok) {
        const data = await response.json();
        // Filter out "all_campuses" and sort by name
        const filteredCampuses = (data.campuses || [])
          .filter(campus => campus.id !== 'all_campuses')
          .sort((a, b) => {
            const nameA = (a.name || a.display_name || '').toLowerCase();
            const nameB = (b.name || b.display_name || '').toLowerCase();
            return nameA.localeCompare(nameB);
          });
        setCampuses(filteredCampuses);
      }
    } catch (err) {
      console.error('Error fetching campuses:', err);
    }
  };

  const fetchPlans = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/devotions/admin/plans');
      if (response.ok) {
        const data = await response.json();
        setPlans(data.plans || []);
      } else {
        setError('Failed to fetch devotion plans');
      }
    } catch (err) {
      setError('Error fetching devotion plans');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const url = editingPlan 
        ? `/api/devotions/admin/plans/${editingPlan.id}`
        : '/api/devotions/admin/plans';
      
      const method = editingPlan ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        await fetchPlans();
        resetForm();
        setShowCreateForm(false);
        setEditingPlan(null);
        setSuccess(editingPlan ? 'Plan updated successfully!' : 'Plan created successfully!');
        setError(null);
        // Clear success message after 3 seconds
        setTimeout(() => setSuccess(null), 3000);
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to save plan');
        setSuccess(null);
      }
    } catch (err) {
      setError('Error saving devotion plan');
      console.error(err);
    }
  };

  const handlePublish = async (planId) => {
    try {
      const response = await fetch(`/api/devotions/admin/plans/${planId}/publish`, {
        method: 'POST',
      });

      if (response.ok) {
        await fetchPlans();
        setSuccess('Plan published successfully!');
        setError(null);
        setTimeout(() => setSuccess(null), 3000);
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to publish plan');
        setSuccess(null);
      }
    } catch (err) {
      setError('Error publishing devotion plan');
      console.error(err);
    }
  };

  const resetForm = () => {
    setFormData({
      title: '',
      description: '',
      campus: '', // Empty = All Campuses
      total_days: 30,
      start_date: '',
      end_date: '',
      status: 'draft'
    });
  };

  const handleEdit = (plan) => {
    setEditingPlan(plan);
    setFormData({
      title: plan.title,
      description: plan.description || '',
      campus: plan.campus || '', // Empty/null = All Campuses
      total_days: plan.total_days || 30,
      start_date: plan.start_date ? plan.start_date.split('T')[0] : '',
      end_date: plan.end_date ? plan.end_date.split('T')[0] : '',
      status: plan.status
    });
    setShowCreateForm(true);
  };

  const handleCancel = () => {
    setShowCreateForm(false);
    setEditingPlan(null);
    resetForm();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-20 h-20 bg-gradient-to-r from-blue-500 to-purple-500 rounded-2xl flex items-center justify-center mx-auto mb-6 animate-pulse">
            <BookOpenIcon className="h-10 w-10 text-white" />
          </div>
          <div className="text-white text-2xl font-bold mb-2">Loading Devotions</div>
          <div className="text-white/60 text-lg">Fetching plans...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Animated Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-purple-500/10 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-pink-500/5 rounded-full blur-3xl animate-pulse delay-500"></div>
      </div>

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-3 mb-2">
            <BookOpenIcon className="h-8 w-8 sm:h-10 sm:w-10 text-blue-400" />
            <h1 className="text-3xl sm:text-4xl font-bold text-white">Devotions</h1>
          </div>
          <p className="text-base sm:text-lg text-white/60">
            Create and manage devotional plans for your community
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 bg-red-500/10 border border-red-500/20 rounded-xl p-4 backdrop-blur-sm animate-fade-in">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-red-400 font-medium">Error</div>
                <div className="text-red-300 text-sm mt-1">{error}</div>
              </div>
              <button
                onClick={() => setError(null)}
                className="text-red-400 hover:text-red-300 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        )}

        {/* Success Message */}
        {success && (
          <div className="mb-6 bg-green-500/10 border border-green-500/20 rounded-xl p-4 backdrop-blur-sm animate-fade-in">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <CheckIcon className="h-5 w-5 text-green-400" />
                <div className="text-green-400 font-medium">{success}</div>
              </div>
              <button
                onClick={() => setSuccess(null)}
                className="text-green-400 hover:text-green-300 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        )}

        {/* Action Bar */}
        <div className="mb-6 flex justify-between items-center flex-wrap gap-4">
          <div className="flex space-x-3">
            <button
              onClick={() => setShowCreateForm(true)}
              className="inline-flex items-center px-4 sm:px-6 py-2 sm:py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold rounded-xl shadow-lg hover:shadow-blue-500/25 hover:scale-105 transition-all duration-300 text-sm sm:text-base"
            >
              <PlusIcon className="-ml-1 mr-2 h-4 w-4 sm:h-5 sm:w-5" />
              <span className="hidden sm:inline">Create New Plan</span>
              <span className="sm:hidden">New Plan</span>
            </button>
          </div>
        </div>

        {/* Create/Edit Form */}
        {showCreateForm && (
          <div className="mb-8 glass-effect rounded-xl p-6 backdrop-blur-sm border border-slate-700/50">
            <h2 className="text-xl font-bold text-white mb-4">
              {editingPlan ? 'Edit Devotion Plan' : 'Create New Devotion Plan'}
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-sm font-medium text-white/80 mb-2">Title</label>
                  <input
                    type="text"
                    required
                    value={formData.title}
                    onChange={(e) => setFormData({...formData, title: e.target.value})}
                    className="w-full bg-slate-800/50 border border-slate-700/50 rounded-lg px-4 py-2 text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Enter plan title"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-white/80 mb-2">Total Days</label>
                  <input
                    type="number"
                    min="1"
                    max="365"
                    required
                    value={formData.total_days}
                    onChange={(e) => setFormData({...formData, total_days: parseInt(e.target.value) || 30})}
                    className="w-full bg-slate-800/50 border border-slate-700/50 rounded-lg px-4 py-2 text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="30"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-white/80 mb-2">Campus</label>
                  <select
                    value={formData.campus || ''}
                    onChange={(e) => setFormData({...formData, campus: e.target.value || ''})}
                    className="w-full bg-slate-800/50 border border-slate-700/50 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">All Campuses</option>
                    {campuses.map((campus) => (
                      <option key={campus.id} value={campus.id || campus.name}>
                        {campus.name || campus.display_name || campus.id}
                      </option>
                    ))}
                  </select>
                  <p className="text-xs text-white/50 mt-1">
                    {formData.campus ? 'Only visible to people from this campus' : 'Visible to all campuses'}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-white/80 mb-2">Status</label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({...formData, status: e.target.value})}
                    className="w-full bg-slate-800/50 border border-slate-700/50 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="draft">Draft</option>
                    <option value="published">Published</option>
                    <option value="archived">Archived</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-white/80 mb-2">Start Date</label>
                  <input
                    type="date"
                    value={formData.start_date}
                    onChange={(e) => setFormData({...formData, start_date: e.target.value})}
                    className="w-full bg-slate-800/50 border border-slate-700/50 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-white/80 mb-2">End Date</label>
                  <input
                    type="date"
                    value={formData.end_date}
                    onChange={(e) => setFormData({...formData, end_date: e.target.value})}
                    className="w-full bg-slate-800/50 border border-slate-700/50 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-white/80 mb-2">Description</label>
                <textarea
                  rows={3}
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  className="w-full bg-slate-800/50 border border-slate-700/50 rounded-lg px-4 py-2 text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Describe your devotion plan..."
                />
              </div>
              <div className="flex justify-end space-x-3 pt-4 border-t border-slate-700/50">
                <button
                  type="button"
                  onClick={handleCancel}
                  className="px-6 py-2 bg-slate-700/50 hover:bg-slate-700 text-white font-medium rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-6 py-2 bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold rounded-lg shadow-lg hover:shadow-blue-500/25 hover:scale-105 transition-all duration-300"
                >
                  {editingPlan ? 'Update Plan' : 'Create Plan'}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Plans List */}
        {plans.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {plans.map((plan) => (
              <div
                key={plan.id}
                className="glass-effect rounded-xl p-6 backdrop-blur-sm border border-slate-700/50 hover:border-blue-500/50 transition-all duration-300 hover:scale-105"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <h3 className="text-xl font-bold text-white truncate">
                        {plan.title}
                      </h3>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        plan.status === 'published' ? 'bg-green-500/20 text-green-400 border border-green-500/30' :
                        plan.status === 'draft' ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30' :
                        'bg-gray-500/20 text-gray-400 border border-gray-500/30'
                      }`}>
                        {plan.status}
                      </span>
                    </div>
                    {plan.description && (
                      <p className="text-sm text-white/60 mb-3 line-clamp-2">{plan.description}</p>
                    )}
                    <div className="flex flex-wrap gap-2 text-xs text-white/50">
                      <span>
                        {plan.campus 
                          ? (campuses.find(c => (c.id || c.name) === plan.campus)?.name || campuses.find(c => (c.id || c.name) === plan.campus)?.display_name || plan.campus)
                          : 'All Campuses'}
                      </span>
                      <span>•</span>
                      <span>{plan.content_count || 0} / {plan.total_days || 30} days</span>
                      <span>•</span>
                      <span>{new Date(plan.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center justify-between pt-4 border-t border-slate-700/50">
                  <Link
                    to={`/devotions/plans/${plan.id}`}
                    className="text-blue-400 hover:text-blue-300 text-sm font-medium flex items-center transition-colors"
                  >
                    Manage Days <PencilIcon className="ml-1 h-4 w-4" />
                  </Link>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleEdit(plan)}
                      className="p-2 text-white/60 hover:text-white hover:bg-slate-700/50 rounded-lg transition-colors"
                      title="Edit Plan"
                    >
                      <PencilIcon className="h-4 w-4" />
                    </button>
                    {plan.status === 'draft' && (
                      <button
                        onClick={() => handlePublish(plan.id)}
                        className="p-2 text-green-400 hover:text-green-300 hover:bg-green-500/10 rounded-lg transition-colors"
                        title="Publish Plan"
                      >
                        <CheckIcon className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="glass-effect rounded-xl p-12 text-center backdrop-blur-sm border border-slate-700/50">
            <div className="max-w-md mx-auto">
              <div className="w-24 h-24 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <BookOpenIcon className="h-12 w-12 text-white/40" />
              </div>
              <h3 className="text-white text-xl font-semibold mb-2">No devotion plans found</h3>
              <p className="text-white/60 text-sm mb-6">Create your first devotion plan to get started. You can add daily readings, scripture, and prayer focuses.</p>
              <button
                onClick={() => setShowCreateForm(true)}
                className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold rounded-xl shadow-lg hover:shadow-blue-500/25 hover:scale-105 transition-all duration-300"
              >
                <PlusIcon className="mr-2 h-5 w-5" />
                Create Your First Plan
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DevotionsAdmin;
