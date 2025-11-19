import React, { useState, useEffect } from 'react';
import { PlusIcon, PencilIcon, TrashIcon, EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline';

const TVManager = () => {
  const [series, setSeries] = useState([]);
  const [selectedSeries, setSelectedSeries] = useState(null);
  const [showSeriesModal, setShowSeriesModal] = useState(false);
  const [showEpisodeModal, setShowEpisodeModal] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchSeries();
  }, []);

  const fetchSeries = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/tv/admin/series/all', {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        setSeries(data.series || []);
      } else {
        setError('Failed to load series');
      }
      setLoading(false);
    } catch (err) {
      console.error('Error fetching series:', err);
      setError('Failed to load series');
      setLoading(false);
    }
  };

  const handleCreateSeries = () => {
    setSelectedSeries(null);
    setShowSeriesModal(true);
  };

  const handleEditSeries = (series) => {
    setSelectedSeries(series);
    setShowSeriesModal(true);
  };

  const handleDeleteSeries = async (seriesId) => {
    if (!window.confirm('Are you sure you want to delete this series? This will also delete all episodes.')) {
      return;
    }

    try {
      const response = await fetch(`/api/tv/admin/series/${seriesId}`, {
        method: 'DELETE',
        credentials: 'include'
      });

      if (response.ok) {
        fetchSeries();
      } else {
        alert('Failed to delete series');
      }
    } catch (err) {
      console.error('Error deleting series:', err);
      alert('Failed to delete series');
    }
  };

  const handleTogglePublish = async (seriesId, currentStatus) => {
    try {
      const response = await fetch(`/api/tv/admin/series/${seriesId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({
          is_published: !currentStatus
        })
      });

      if (response.ok) {
        fetchSeries();
      } else {
        alert('Failed to update series');
      }
    } catch (err) {
      console.error('Error updating series:', err);
      alert('Failed to update series');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2">Pulse TV Manager</h1>
            <p className="text-slate-400">Manage TV series and episodes</p>
          </div>
          <button
            onClick={handleCreateSeries}
            className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:from-purple-700 hover:to-blue-700 transition-colors"
          >
            <PlusIcon className="w-5 h-5" />
            <span>New Series</span>
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-900/30 border border-red-500/40 text-red-200 rounded-xl px-4 py-3 mb-6">
            {error}
          </div>
        )}

        {/* Series List */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {series.map((s) => (
            <div
              key={s.id}
              className="bg-slate-800 rounded-xl p-6 hover:bg-slate-700/50 transition-colors"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-xl font-semibold text-white mb-2">{s.title}</h3>
                  {s.description && (
                    <p className="text-sm text-slate-400 line-clamp-2">{s.description}</p>
                  )}
                  <div className="flex items-center gap-2 mt-2">
                    {s.category && (
                      <span className="text-xs px-2 py-1 bg-purple-600/20 text-purple-300 rounded">
                        {s.category}
                      </span>
                    )}
                    {s.audience && (
                      <span className="text-xs px-2 py-1 bg-blue-600/20 text-blue-300 rounded">
                        {s.audience}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between mt-4 pt-4 border-t border-slate-700">
                <div className="text-sm text-slate-400">
                  {s.episodes?.length || 0} {s.episodes?.length === 1 ? 'episode' : 'episodes'}
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleTogglePublish(s.id, s.is_published)}
                    className="p-2 rounded-lg hover:bg-slate-700 transition-colors"
                    title={s.is_published ? 'Unpublish' : 'Publish'}
                  >
                    {s.is_published ? (
                      <EyeIcon className="w-5 h-5 text-green-400" />
                    ) : (
                      <EyeSlashIcon className="w-5 h-5 text-slate-400" />
                    )}
                  </button>
                  <button
                    onClick={() => handleEditSeries(s)}
                    className="p-2 rounded-lg hover:bg-slate-700 transition-colors"
                    title="Edit"
                  >
                    <PencilIcon className="w-5 h-5 text-blue-400" />
                  </button>
                  <button
                    onClick={() => handleDeleteSeries(s.id)}
                    className="p-2 rounded-lg hover:bg-slate-700 transition-colors"
                    title="Delete"
                  >
                    <TrashIcon className="w-5 h-5 text-red-400" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {series.length === 0 && (
          <div className="text-center py-16">
            <p className="text-slate-400 text-lg">No series yet. Create your first series!</p>
          </div>
        )}
      </div>

      {/* Series Modal */}
      {showSeriesModal && (
        <SeriesModal
          series={selectedSeries}
          onClose={() => {
            setShowSeriesModal(false);
            setSelectedSeries(null);
          }}
          onSave={() => {
            setShowSeriesModal(false);
            setSelectedSeries(null);
            fetchSeries();
          }}
        />
      )}
    </div>
  );
};

// Series Modal Component
const SeriesModal = ({ series, onClose, onSave }) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    category: '',
    audience: 'all',
    thumbnail_url: '',
    is_published: false,
    tags: []
  });
  const [tagInput, setTagInput] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (series) {
      setFormData({
        title: series.title || '',
        description: series.description || '',
        category: series.category || '',
        audience: series.audience || 'all',
        thumbnail_url: series.thumbnail_url || '',
        is_published: series.is_published || false,
        tags: series.tags?.map(t => t.name) || []
      });
    }
  }, [series]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const url = series
        ? `/api/tv/admin/series/${series.id}`
        : '/api/tv/admin/series';
      
      const method = series ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        onSave();
      } else {
        const data = await response.json();
        alert(data.error || 'Failed to save series');
      }
    } catch (err) {
      console.error('Error saving series:', err);
      alert('Failed to save series');
    } finally {
      setLoading(false);
    }
  };

  const handleAddTag = () => {
    if (tagInput.trim() && !formData.tags.includes(tagInput.trim())) {
      setFormData({
        ...formData,
        tags: [...formData.tags, tagInput.trim()]
      });
      setTagInput('');
    }
  };

  const handleRemoveTag = (tag) => {
    setFormData({
      ...formData,
      tags: formData.tags.filter(t => t !== tag)
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <div className="bg-slate-800 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <h2 className="text-2xl font-bold text-white mb-6">
            {series ? 'Edit Series' : 'Create Series'}
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Title *
              </label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="w-full px-4 py-2 bg-slate-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={4}
                className="w-full px-4 py-2 bg-slate-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Category
                </label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="">Select category</option>
                  <option value="foundations">Foundations</option>
                  <option value="leadership">Leadership</option>
                  <option value="parents">Parents</option>
                  <option value="youth">Youth</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Audience
                </label>
                <select
                  value={formData.audience}
                  onChange={(e) => setFormData({ ...formData, audience: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="all">All</option>
                  <option value="adults">Adults</option>
                  <option value="youth">Youth</option>
                  <option value="kids">Kids</option>
                  <option value="parents">Parents</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Thumbnail URL
              </label>
              <input
                type="url"
                value={formData.thumbnail_url}
                onChange={(e) => setFormData({ ...formData, thumbnail_url: e.target.value })}
                className="w-full px-4 py-2 bg-slate-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                placeholder="https://..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Tags
              </label>
              <div className="flex gap-2 mb-2">
                <input
                  type="text"
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddTag())}
                  className="flex-1 px-4 py-2 bg-slate-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="Add tag..."
                />
                <button
                  type="button"
                  onClick={handleAddTag}
                  className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                >
                  Add
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                {formData.tags.map((tag) => (
                  <span
                    key={tag}
                    className="inline-flex items-center gap-1 px-3 py-1 bg-purple-600/20 text-purple-300 rounded-lg text-sm"
                  >
                    {tag}
                    <button
                      type="button"
                      onClick={() => handleRemoveTag(tag)}
                      className="hover:text-red-400"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="is_published"
                checked={formData.is_published}
                onChange={(e) => setFormData({ ...formData, is_published: e.target.checked })}
                className="w-4 h-4 rounded bg-slate-700 text-purple-600 focus:ring-purple-500"
              />
              <label htmlFor="is_published" className="text-sm text-slate-300">
                Publish immediately
              </label>
            </div>

            <div className="flex items-center justify-end gap-4 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="px-6 py-2 text-slate-300 hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-6 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:from-purple-700 hover:to-blue-700 transition-colors disabled:opacity-50"
              >
                {loading ? 'Saving...' : 'Save'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default TVManager;

