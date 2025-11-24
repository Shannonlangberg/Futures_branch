import React, { useState, useEffect } from 'react';
import {
  DevicePhoneMobileIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  PlusIcon,
  XMarkIcon,
  ClockIcon,
  PaperAirplaneIcon
} from '@heroicons/react/24/outline';

const SMSCampaignCreator = ({ onSave, onCancel, existingCampaign }) => {
  const [formData, setFormData] = useState({
    name: '',
    to: [],
    from: 'FUTURES',
    message: '',
    trackLink: false,
    template: 'New Template',
    schedule: false,
    scheduledAt: ''
  });
  const [senderIds, setSenderIds] = useState([]);
  const [contactLists, setContactLists] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [showSenderDropdown, setShowSenderDropdown] = useState(false);
  const [showContactDropdown, setShowContactDropdown] = useState(false);
  const [charCount, setCharCount] = useState(0);
  const [smsCount, setSmsCount] = useState(1);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchSenderIds();
    fetchContactLists();
    if (existingCampaign) {
      setFormData({
        name: existingCampaign.name || '',
        to: existingCampaign.target_criteria?.to || [],
        from: existingCampaign.target_criteria?.sender_id || 'FUTURES',
        message: existingCampaign.content || '',
        trackLink: existingCampaign.target_criteria?.track_link || false,
        template: existingCampaign.template || 'New Template',
        schedule: !!existingCampaign.scheduled_at,
        scheduledAt: existingCampaign.scheduled_at ? new Date(existingCampaign.scheduled_at).toISOString().slice(0, 16) : ''
      });
    }
  }, [existingCampaign]);

  useEffect(() => {
    const count = formData.message.length;
    setCharCount(count);
    // SMS messages are typically 160 characters per segment
    setSmsCount(Math.ceil(count / 160));
  }, [formData.message]);

  const fetchSenderIds = async () => {
    try {
      const response = await fetch('/api/communication/sms/sender-ids', {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setSenderIds(Object.entries(data.sender_ids || {}).map(([key, value]) => ({ key, value })));
      }
    } catch (error) {
      console.error('Error fetching sender IDs:', error);
    }
  };

  const fetchContactLists = async () => {
    try {
      // This would fetch from your contact lists API
      // For now, using sample data
      setContactLists([
        { id: '1', name: 'All Members', count: 1250 },
        { id: '2', name: 'Paradise Campus', count: 450 },
        { id: '3', name: 'South Campus', count: 320 },
        { id: '4', name: 'Youth Group', count: 180 },
        { id: '5', name: 'Kids Ministry', count: 95 }
      ]);
    } catch (error) {
      console.error('Error fetching contact lists:', error);
    }
  };

  const handleMessageChange = (e) => {
    setFormData(prev => ({ ...prev, message: e.target.value }));
  };

  const handlePersonalization = (variable) => {
    setFormData(prev => ({
      ...prev,
      message: prev.message + variable
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const campaignData = {
        name: formData.name,
        campaign_type: 'sms',
        content: formData.message,
        target_criteria: {
          to: formData.to,
          sender_id: formData.from,
          track_link: formData.trackLink
        },
        scheduled_at: formData.schedule && formData.scheduledAt ? new Date(formData.scheduledAt).toISOString() : undefined
      };

      const response = await fetch('/api/communication/campaigns', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(campaignData)
      });

      const data = await response.json();
      if (data.success) {
        onSave(data.campaign);
      } else {
        alert('Error: ' + (data.error || 'Failed to create campaign'));
      }
    } catch (error) {
      console.error('Error creating SMS campaign:', error);
      alert('Error creating campaign');
    } finally {
      setLoading(false);
    }
  };

  const filteredContactLists = contactLists.filter(list =>
    list.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 p-6">
      {/* Left: Form */}
      <div className="space-y-6">
        {/* To Field */}
        <div>
          <label className="block text-white/80 text-sm font-semibold mb-2">
            To*
          </label>
          <div className="relative">
            <div className="flex items-center gap-2">
              <div className="flex-1 relative">
                <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-white/40" />
                <input
                  type="text"
                  placeholder="Search Contact Lists"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  onFocus={() => setShowContactDropdown(true)}
                  className="w-full pl-10 pr-10 py-3 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white/10 transition-all"
                />
                <FunnelIcon className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-white/40 cursor-pointer" />
              </div>
            </div>
            {showContactDropdown && (
              <div className="absolute z-10 w-full mt-2 bg-slate-800 border border-white/10 rounded-xl shadow-xl max-h-60 overflow-y-auto">
                {filteredContactLists.map(list => (
                  <div
                    key={list.id}
                    onClick={() => {
                      if (!formData.to.includes(list.id)) {
                        setFormData(prev => ({
                          ...prev,
                          to: [...prev.to, list.id]
                        }));
                      }
                      setShowContactDropdown(false);
                      setSearchTerm('');
                    }}
                    className="px-4 py-3 hover:bg-white/10 cursor-pointer border-b border-white/5 last:border-b-0"
                  >
                    <div className="text-white font-medium">{list.name}</div>
                    <div className="text-white/50 text-sm">{list.count} contacts</div>
                  </div>
                ))}
              </div>
            )}
            {formData.to.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {formData.to.map(id => {
                  const list = contactLists.find(l => l.id === id);
                  return list ? (
                    <span
                      key={id}
                      className="inline-flex items-center gap-1 px-3 py-1 bg-blue-500/20 text-blue-300 rounded-full text-sm"
                    >
                      {list.name}
                      <button
                        onClick={() => setFormData(prev => ({
                          ...prev,
                          to: prev.to.filter(t => t !== id)
                        }))}
                        className="hover:text-blue-100"
                      >
                        <XMarkIcon className="w-4 h-4" />
                      </button>
                    </span>
                  ) : null;
                })}
              </div>
            )}
          </div>
        </div>

        {/* From Field */}
        <div>
          <label className="block text-white/80 text-sm font-semibold mb-2">
            From*
          </label>
          <div className="flex items-center gap-2">
            <div className="flex-1 relative">
              <input
                type="text"
                value={formData.from}
                onChange={(e) => setFormData(prev => ({ ...prev, from: e.target.value }))}
                onFocus={() => setShowSenderDropdown(true)}
                placeholder="Search Senders"
                className="w-full px-4 py-3 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white/10 transition-all"
              />
              {showSenderDropdown && (
                <div className="absolute z-10 w-full mt-2 bg-slate-800 border border-white/10 rounded-xl shadow-xl max-h-60 overflow-y-auto">
                  {senderIds.map(sender => (
                    <div
                      key={sender.key}
                      onClick={() => {
                        setFormData(prev => ({ ...prev, from: sender.value }));
                        setShowSenderDropdown(false);
                      }}
                      className="px-4 py-3 hover:bg-white/10 cursor-pointer border-b border-white/5 last:border-b-0"
                    >
                      <div className="text-white font-medium">{sender.value}</div>
                      <div className="text-white/50 text-sm">{sender.key}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <button
              type="button"
              className="px-4 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-xl font-semibold transition-colors"
            >
              Add sender
            </button>
            <button
              type="button"
              className="px-4 py-3 bg-white/5 hover:bg-white/10 text-white rounded-xl font-semibold transition-colors"
            >
              Reply options
            </button>
          </div>
        </div>

        {/* Message Field */}
        <div>
          <label className="block text-white/80 text-sm font-semibold mb-2">
            Message*
          </label>
          <div className="mb-2">
            <span className="text-white/60 text-sm">Personalisation: </span>
            <button
              type="button"
              onClick={() => handlePersonalization('[Firstname]')}
              className="text-blue-400 hover:text-blue-300 text-sm mx-1"
            >
              [Firstname]
            </button>
            <button
              type="button"
              onClick={() => handlePersonalization('[Lastname]')}
              className="text-blue-400 hover:text-blue-300 text-sm mx-1"
            >
              [Lastname]
            </button>
            <button
              type="button"
              onClick={() => handlePersonalization('[Mobile]')}
              className="text-blue-400 hover:text-blue-300 text-sm mx-1"
            >
              [Mobile]
            </button>
          </div>
          <div className="relative">
            <textarea
              value={formData.message}
              onChange={handleMessageChange}
              placeholder="Opt-out reply STOP"
              rows="8"
              className="w-full px-4 py-3 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white/10 transition-all resize-none"
            />
            <div className="absolute bottom-3 left-4 flex items-center gap-2">
              <span className="text-white/40 text-sm">😊</span>
            </div>
            <div className="absolute bottom-3 right-4 flex items-center gap-2">
              <span className="text-white/60 text-sm">{charCount}/612</span>
              <span className="px-2 py-1 bg-white/10 text-white/60 text-xs rounded-full">
                {smsCount} SMS
              </span>
            </div>
          </div>
        </div>

        {/* Track Link */}
        <div className="flex items-center justify-between">
          <label className="text-white/80 text-sm font-semibold">Track link</label>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={formData.trackLink}
              onChange={(e) => setFormData(prev => ({ ...prev, trackLink: e.target.checked }))}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-white/20 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-blue-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-500"></div>
          </label>
        </div>

        {/* Templates */}
        <div>
          <label className="block text-white/80 text-sm font-semibold mb-2">Templates</label>
          <div className="flex items-center gap-2">
            <select
              value={formData.template}
              onChange={(e) => setFormData(prev => ({ ...prev, template: e.target.value }))}
              className="flex-1 px-4 py-3 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="New Template" className="bg-slate-800">New Template</option>
              <option value="Welcome" className="bg-slate-800">Welcome</option>
              <option value="Reminder" className="bg-slate-800">Reminder</option>
              <option value="Event" className="bg-slate-800">Event</option>
            </select>
            <button
              type="button"
              className="px-4 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-xl font-semibold transition-colors"
            >
              Save
            </button>
          </div>
        </div>

        {/* Schedule Campaign */}
        <div className="flex items-center justify-between">
          <label className="text-white/80 text-sm font-semibold">Schedule campaign</label>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={formData.schedule}
              onChange={(e) => setFormData(prev => ({ ...prev, schedule: e.target.checked }))}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-white/20 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-blue-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-500"></div>
          </label>
        </div>

        {formData.schedule && (
          <div>
            <input
              type="datetime-local"
              value={formData.scheduledAt}
              onChange={(e) => setFormData(prev => ({ ...prev, scheduledAt: e.target.value }))}
              className="w-full px-4 py-3 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        )}

        {/* Test Message */}
        <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-4">
          <label className="block text-white/80 text-sm font-semibold mb-2">Test Message</label>
          <input
            type="text"
            placeholder="Enter phone number to test"
            className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end gap-3 pt-4">
          <button
            type="button"
            onClick={onCancel}
            className="px-6 py-3 bg-white/5 hover:bg-white/10 text-white rounded-xl font-semibold transition-all"
          >
            Cancel
          </button>
          <button
            type="submit"
            onClick={handleSubmit}
            disabled={loading || !formData.name || !formData.message || formData.to.length === 0}
            className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-xl font-semibold hover:scale-105 transition-all duration-300 shadow-lg hover:shadow-blue-500/50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Saving...' : 'Send Campaign'}
          </button>
        </div>
      </div>

      {/* Right: Preview */}
      <div className="lg:sticky lg:top-6 h-fit">
        <div className="bg-slate-800 rounded-2xl p-6 border border-white/10">
          <h3 className="text-white font-semibold mb-4">Preview</h3>
          <div className="bg-slate-900 rounded-xl p-4 border border-white/10">
            {/* Phone Mockup */}
            <div className="bg-slate-700 rounded-lg p-4 max-w-xs mx-auto">
              {/* Phone Header */}
              <div className="flex items-center justify-between mb-4 pb-2 border-b border-white/10">
                <div className="flex items-center gap-2">
                  <div className="w-1 h-1 bg-white/40 rounded-full"></div>
                  <div className="w-1 h-1 bg-white/40 rounded-full"></div>
                  <div className="w-1 h-1 bg-white/40 rounded-full"></div>
                </div>
                <div className="text-white/60 text-xs">9:41 AM</div>
                <div className="flex items-center gap-1">
                  <div className="w-6 h-3 border border-white/40 rounded-sm">
                    <div className="w-4 h-2 bg-green-400 rounded-sm m-0.5"></div>
                  </div>
                </div>
              </div>

              {/* Message Preview */}
              <div className="space-y-2">
                <div className="text-white/60 text-xs mb-2">Message</div>
                <div className="bg-slate-600 rounded-lg p-3 text-white text-sm">
                  {formData.message || 'Your message will appear here...'}
                </div>
                <div className="text-white/40 text-xs">Sun, 23 Nov, 5:48 PM</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SMSCampaignCreator;


