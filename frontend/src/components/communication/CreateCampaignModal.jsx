import React, { useState, useEffect } from 'react';
import { XMarkIcon, EnvelopeIcon, DevicePhoneMobileIcon } from '@heroicons/react/24/outline';

const CreateCampaignModal = ({ campaignType, onClose, onSuccess, existingCampaign }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    subject_line: '',
    content: '',
    content_text: '',
    target_criteria: {
      campus: [],
      department: [],
      tags: []
    },
    scheduled_at: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [campuses, setCampuses] = useState([]);
  const [departments] = useState(['Kids', 'Youth', 'Young Adults', 'Families', 'Adults', 'Seniors']);
  const [sendNow, setSendNow] = useState(false);

  useEffect(() => {
    fetchCampuses();
    if (existingCampaign) {
      setFormData({
        name: existingCampaign.name || '',
        description: existingCampaign.description || '',
        subject_line: existingCampaign.subject_line || '',
        content: existingCampaign.content || '',
        content_text: existingCampaign.content_text || '',
        target_criteria: existingCampaign.target_criteria || { campus: [], department: [], tags: [] },
        scheduled_at: existingCampaign.scheduled_at ? new Date(existingCampaign.scheduled_at).toISOString().slice(0, 16) : ''
      });
    }
  }, [existingCampaign]);

  const fetchCampuses = async () => {
    try {
      const response = await fetch('/api/campuses', {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setCampuses(data.campuses || []);
      }
    } catch (error) {
      console.error('Error fetching campuses:', error);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleTargetChange = (type, value, checked) => {
    setFormData(prev => {
      const criteria = { ...prev.target_criteria };
      if (!criteria[type]) criteria[type] = [];
      
      if (checked) {
        criteria[type] = [...criteria[type], value];
      } else {
        criteria[type] = criteria[type].filter(item => item !== value);
      }
      
      return {
        ...prev,
        target_criteria: criteria
      };
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const payload = {
        name: formData.name,
        description: formData.description,
        campaign_type: campaignType,
        subject_line: campaignType === 'email' ? formData.subject_line : undefined,
        content: formData.content,
        content_text: campaignType === 'email' ? formData.content_text : undefined,
        target_criteria: formData.target_criteria,
        scheduled_at: formData.scheduled_at ? new Date(formData.scheduled_at).toISOString() : undefined
      };

      let response;
      if (existingCampaign) {
        // Update existing campaign
        response = await fetch(`/api/communication/campaigns/${existingCampaign.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify(payload)
        });
      } else {
        // Create new campaign
        response = await fetch('/api/communication/campaigns', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify(payload)
        });
      }

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.error || 'Failed to save campaign');
      }

      // Send immediately if requested
      if (sendNow && data.campaign?.id) {
        const sendResponse = await fetch(`/api/communication/campaigns/${data.campaign.id}/send`, {
          method: 'POST',
          credentials: 'include'
        });

        const sendData = await sendResponse.json();
        if (!sendResponse.ok || !sendData.success) {
          alert(`Campaign created but failed to send: ${sendData.error || 'Unknown error'}`);
        }
      }

      onSuccess();
    } catch (err) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-2xl shadow-2xl border border-white/10 max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-white/10">
          <div className="flex items-center gap-3">
            {campaignType === 'email' ? (
              <EnvelopeIcon className="w-6 h-6 text-blue-400" />
            ) : (
              <DevicePhoneMobileIcon className="w-6 h-6 text-green-400" />
            )}
            <h2 className="text-2xl font-bold text-white">
              {existingCampaign ? 'Edit' : 'Create'} {campaignType === 'email' ? 'Email' : 'SMS'} Campaign
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/10 rounded-xl transition-colors"
          >
            <XMarkIcon className="w-6 h-6 text-white/60" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {error && (
            <div className="bg-red-500/20 border border-red-500/40 text-red-200 rounded-xl p-4">
              {error}
            </div>
          )}

          {/* Campaign Name */}
          <div>
            <label className="block text-white/80 text-sm font-semibold mb-2">
              Campaign Name *
            </label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
              className="w-full px-4 py-3 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white/10 transition-all"
              placeholder="e.g., Weekly Newsletter"
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-white/80 text-sm font-semibold mb-2">
              Description
            </label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleChange}
              rows="2"
              className="w-full px-4 py-3 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white/10 transition-all"
              placeholder="Brief description of this campaign"
            />
          </div>

          {/* Subject Line (Email only) */}
          {campaignType === 'email' && (
            <div>
              <label className="block text-white/80 text-sm font-semibold mb-2">
                Subject Line *
              </label>
              <input
                type="text"
                name="subject_line"
                value={formData.subject_line}
                onChange={handleChange}
                required
                className="w-full px-4 py-3 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white/10 transition-all"
                placeholder="Email subject line"
              />
            </div>
          )}

          {/* Content */}
          <div>
            <label className="block text-white/80 text-sm font-semibold mb-2">
              {campaignType === 'email' ? 'Email Content (HTML)' : 'SMS Message'} *
            </label>
            {campaignType === 'email' ? (
              <textarea
                name="content"
                value={formData.content}
                onChange={handleChange}
                required
                rows="10"
                className="w-full px-4 py-3 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white/10 transition-all font-mono text-sm"
                placeholder="<html>...</html>"
              />
            ) : (
              <textarea
                name="content"
                value={formData.content}
                onChange={handleChange}
                required
                rows="6"
                maxLength={1600}
                className="w-full px-4 py-3 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white/10 transition-all"
                placeholder="SMS message (160 characters recommended for single message)"
              />
            )}
            {campaignType === 'sms' && (
              <div className="text-white/50 text-sm mt-1">
                {formData.content.length} / 160 characters
              </div>
            )}
          </div>

          {/* Plain Text Content (Email only) */}
          {campaignType === 'email' && (
            <div>
              <label className="block text-white/80 text-sm font-semibold mb-2">
                Plain Text Version
              </label>
              <textarea
                name="content_text"
                value={formData.content_text}
                onChange={handleChange}
                rows="6"
                className="w-full px-4 py-3 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white/10 transition-all"
                placeholder="Plain text version for email clients that don't support HTML"
              />
            </div>
          )}

          {/* Targeting */}
          <div>
            <label className="block text-white/80 text-sm font-semibold mb-3">
              Target Audience
            </label>
            
            {/* Campus Selection */}
            <div className="mb-4">
              <div className="text-white/60 text-sm mb-2">Campuses</div>
              <div className="flex flex-wrap gap-2">
                {campuses.map((campus) => (
                  <label key={campus.id} className="flex items-center gap-2 px-3 py-2 bg-white/5 rounded-lg cursor-pointer hover:bg-white/10 transition-colors">
                    <input
                      type="checkbox"
                      checked={formData.target_criteria.campus?.includes(campus.name)}
                      onChange={(e) => handleTargetChange('campus', campus.name, e.target.checked)}
                      className="w-4 h-4 text-blue-500 bg-white/10 border-white/20 rounded focus:ring-blue-500"
                    />
                    <span className="text-white text-sm">{campus.name}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Department Selection */}
            <div className="mb-4">
              <div className="text-white/60 text-sm mb-2">Departments</div>
              <div className="flex flex-wrap gap-2">
                {departments.map((dept) => (
                  <label key={dept} className="flex items-center gap-2 px-3 py-2 bg-white/5 rounded-lg cursor-pointer hover:bg-white/10 transition-colors">
                    <input
                      type="checkbox"
                      checked={formData.target_criteria.department?.includes(dept)}
                      onChange={(e) => handleTargetChange('department', dept, e.target.checked)}
                      className="w-4 h-4 text-blue-500 bg-white/10 border-white/20 rounded focus:ring-blue-500"
                    />
                    <span className="text-white text-sm">{dept}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* Schedule */}
          <div>
            <label className="block text-white/80 text-sm font-semibold mb-2">
              Schedule (Optional)
            </label>
            <input
              type="datetime-local"
              name="scheduled_at"
              value={formData.scheduled_at}
              onChange={handleChange}
              className="w-full px-4 py-3 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white/10 transition-all"
            />
            {!formData.scheduled_at && (
              <label className="flex items-center gap-2 mt-2 text-white/60 text-sm cursor-pointer">
                <input
                  type="checkbox"
                  checked={sendNow}
                  onChange={(e) => setSendNow(e.target.checked)}
                  className="w-4 h-4 text-blue-500 bg-white/10 border-white/20 rounded focus:ring-blue-500"
                />
                <span>Send immediately after creating</span>
              </label>
            )}
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-white/10">
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-3 bg-white/5 hover:bg-white/10 text-white rounded-xl font-semibold transition-all duration-300"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-xl font-semibold hover:scale-105 transition-all duration-300 shadow-lg hover:shadow-blue-500/50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Saving...' : existingCampaign ? 'Update Campaign' : 'Create Campaign'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateCampaignModal;

