import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeftIcon,
  PaperAirplaneIcon,
  EyeIcon,
  PhotoIcon,
  VideoCameraIcon,
  LinkIcon,
  XMarkIcon,
  PlusIcon,
  CheckCircleIcon,
  UserGroupIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline';
import RichEmailEditor from '../components/communication/RichEmailEditor';
import BlockEmailEditor from '../components/communication/BlockEmailEditor';
import Vision6EmailEditor from '../components/communication/Vision6EmailEditor';
import DesignSettingsPanel from '../components/communication/DesignSettingsPanel';

const EmailEditor = () => {
  const navigate = useNavigate();
  const { campaignId } = useParams();
  const [formData, setFormData] = useState({
    name: '',
    subject_line: '',
    content: '',
    content_text: '',
    from_email: '',
    from_name: 'Futures Church'
  });
  const [campuses, setCampuses] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [customLists, setCustomLists] = useState([]);
  const [selectedTargets, setSelectedTargets] = useState({
    campuses: [],
    departments: [],
    customLists: [],
    csvList: null
  });
  const [showPreview, setShowPreview] = useState(false);
  const [showTestEmail, setShowTestEmail] = useState(false);
  const [testEmail, setTestEmail] = useState('');
  const [sendingTest, setSendingTest] = useState(false);
  const [showCustomListModal, setShowCustomListModal] = useState(false);
  const [newListName, setNewListName] = useState('');
  const [newListDescription, setNewListDescription] = useState('');
  const [csvFile, setCsvFile] = useState(null);
  const [csvData, setCsvData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [useBlockEditor, setUseBlockEditor] = useState(true);
  const [useVision6Editor, setUseVision6Editor] = useState(true);
  const [designSettings, setDesignSettings] = useState({
    emailWidth: 567,
    evenColumns: true,
    fullWidthMobile: false,
    gridWidth: 25,
    useGrid: false,
    borderColor: '#FFFFFF',
    borderWidth: 0,
    backgroundColor: '#E8E6E6',
    fullHeightBackground: false,
    backgroundImage: null,
    bodyTextColor: '#2A2A2A',
    bodyFont: 'Arial',
    bodyFontSize: 12,
    lineHeight: 1.5,
    linkColor: null,
    linkBold: false,
    linkItalic: false,
    linkUnderline: false
  });

  useEffect(() => {
    fetchCampuses();
    fetchDepartments();
    fetchCustomLists();
    if (campaignId) {
      fetchCampaign();
    }
  }, [campaignId]);

  const fetchCampaign = async () => {
    try {
      const response = await fetch(`/api/communication/campaigns/${campaignId}`, {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        if (data.campaign) {
          setFormData({
            name: data.campaign.name || '',
            subject_line: data.campaign.subject_line || '',
            content: data.campaign.content || '',
            content_text: data.campaign.content_text || '',
            from_email: data.campaign.target_criteria?.from_email || '',
            from_name: data.campaign.target_criteria?.from_name || 'Futures Church'
          });
          setSelectedTargets({
            campuses: data.campaign.target_criteria?.campus || [],
            departments: data.campaign.target_criteria?.department || [],
            customLists: data.campaign.target_criteria?.custom_lists || [],
            csvList: null
          });
        }
      }
    } catch (error) {
      console.error('Error fetching campaign:', error);
    }
  };

  const fetchCampuses = async () => {
    try {
      const response = await fetch('/api/communication/campuses', {
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

  const fetchDepartments = async () => {
    try {
      const response = await fetch('/api/communication/departments', {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setDepartments(data.departments || []);
      }
    } catch (error) {
      console.error('Error fetching departments:', error);
      setDepartments(['Kids', 'Youth', 'Young Adults', 'Families', 'Adults', 'Seniors']);
    }
  };

  const fetchCustomLists = async () => {
    try {
      const response = await fetch('/api/communication/email-lists', {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setCustomLists(data.lists || []);
      }
    } catch (error) {
      console.error('Error fetching custom lists:', error);
    }
  };

  const handleSave = async (sendNow = false) => {
    setSaving(true);
    try {
      const campaignData = {
        name: formData.name,
        campaign_type: 'email',
        subject_line: formData.subject_line,
        content: formData.content,
        content_text: formData.content_text,
        target_criteria: {
          campus: selectedTargets.campuses,
          department: selectedTargets.departments,
          custom_lists: selectedTargets.customLists,
          from_email: formData.from_email,
          from_name: formData.from_name
        }
      };

      let response;
      if (campaignId) {
        response = await fetch(`/api/communication/campaigns/${campaignId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify(campaignData)
        });
      } else {
        response = await fetch('/api/communication/campaigns', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify(campaignData)
        });
      }

      const data = await response.json();
      if (data.success) {
        if (sendNow) {
          const sendResponse = await fetch(`/api/communication/campaigns/${data.campaign_id || campaignId}/send`, {
            method: 'POST',
            credentials: 'include'
          });
          const sendData = await sendResponse.json();
          if (sendData.success) {
            alert('Campaign sent successfully!');
            navigate('/communication');
          } else {
            alert('Campaign saved but failed to send: ' + (sendData.error || 'Unknown error'));
          }
        } else {
          alert('Campaign saved successfully!');
          if (!campaignId) {
            navigate(`/communication/email-editor/${data.campaign_id}`);
          }
        }
      } else {
        alert('Error: ' + (data.error || 'Failed to save campaign'));
      }
    } catch (error) {
      console.error('Error saving campaign:', error);
      alert('Error saving campaign');
    } finally {
      setSaving(false);
    }
  };

  const handleSendTestEmail = async () => {
    if (!testEmail) {
      alert('Please enter a test email address');
      return;
    }

    setSendingTest(true);
    try {
      const response = await fetch('/api/communication/email/send-test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          to_email: testEmail,
          subject: formData.subject_line || 'Test Email',
          html_content: formData.content,
          text_content: formData.content_text
        })
      });

      const data = await response.json();
      if (data.success) {
        alert('Test email sent successfully!');
        setShowTestEmail(false);
        setTestEmail('');
      } else {
        alert('Error: ' + (data.error || 'Failed to send test email'));
      }
    } catch (error) {
      console.error('Error sending test email:', error);
      alert('Error sending test email');
    } finally {
      setSendingTest(false);
    }
  };

  const handleCreateCustomList = async () => {
    if (!newListName) {
      alert('Please enter a list name');
      return;
    }

    try {
      const response = await fetch('/api/communication/email-lists', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          name: newListName,
          description: newListDescription,
          list_type: 'custom',
          members: []
        })
      });

      const data = await response.json();
      if (data.success) {
        setShowCustomListModal(false);
        setNewListName('');
        setNewListDescription('');
        fetchCustomLists();
        alert('Custom list created! You can now add members to it.');
      } else {
        alert('Error: ' + (data.error || 'Failed to create list'));
      }
    } catch (error) {
      console.error('Error creating custom list:', error);
      alert('Error creating custom list');
    }
  };

  const handleCSVUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setCsvFile(file);
    const reader = new FileReader();
    reader.onload = (event) => {
      const text = event.target.result;
      const lines = text.split('\n');
      const headers = lines[0].split(',').map(h => h.trim());
      const rows = lines.slice(1).map(line => {
        const values = line.split(',').map(v => v.trim());
        const row = {};
        headers.forEach((header, index) => {
          row[header] = values[index] || '';
        });
        return row;
      }).filter(row => Object.values(row).some(v => v));

      setCsvData(rows);
      // Auto-create a list from CSV
      const listName = file.name.replace('.csv', '');
      setNewListName(listName);
      setShowCustomListModal(true);
    };
    reader.readAsText(file);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <div className="bg-white/5 backdrop-blur-sm border-b border-white/10 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/communication')}
                className="p-2 hover:bg-white/10 rounded-xl transition-colors"
              >
                <ArrowLeftIcon className="w-6 h-6 text-white" />
              </button>
              <div>
                <h1 className="text-2xl font-bold text-white">
                  {campaignId ? 'Edit Email Campaign' : 'New Email'}
                </h1>
                <p className="text-white/60 text-sm">Design and send beautiful emails to your church</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1 bg-white/5 rounded-lg p-1">
                <button className="px-3 py-1 bg-blue-500 text-white rounded text-sm font-semibold">
                  Designer
                </button>
                <button className="px-3 py-1 text-white/60 hover:text-white rounded text-sm">
                  Accessibility
                </button>
                <button className="px-3 py-1 text-white/60 hover:text-white rounded text-sm">
                  Social
                </button>
              </div>
              <button
                onClick={() => setShowPreview(!showPreview)}
                className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 text-white rounded-xl transition-colors"
              >
                <EyeIcon className="w-5 h-5" />
                Preview
              </button>
              <button
                onClick={() => setShowTestEmail(true)}
                className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 text-white rounded-xl transition-colors"
              >
                <PaperAirplaneIcon className="w-5 h-5" />
                Test
              </button>
              <button
                onClick={() => handleSave(true)}
                disabled={saving || !formData.name || !formData.subject_line || !formData.content}
                className="flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-xl font-semibold transition-colors disabled:opacity-50"
              >
                <PaperAirplaneIcon className="w-5 h-5" />
                Send
              </button>
              <div className="relative">
                <button
                  onClick={() => handleSave(false)}
                  disabled={saving}
                  className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-semibold transition-colors disabled:opacity-50"
                >
                  Save
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: Editor */}
          <div className="lg:col-span-2 space-y-6">
            {/* Campaign Name */}
            <div className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-white/10">
              <label className="block text-white/80 text-sm font-semibold mb-2">
                Campaign Name *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                placeholder="e.g., Weekly Newsletter"
                className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Subject Line */}
            <div className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-white/10">
              <label className="block text-white/80 text-sm font-semibold mb-2">
                Subject Line *
              </label>
              <input
                type="text"
                value={formData.subject_line}
                onChange={(e) => setFormData(prev => ({ ...prev, subject_line: e.target.value }))}
                placeholder="Email subject line"
                className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Email Editor */}
            <div className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 overflow-hidden" style={{ minHeight: '600px', height: 'auto' }}>
              {useVision6Editor ? (
                <div className="flex flex-col md:flex-row h-full">
                  <div className="flex-1 min-h-[400px]">
                    <Vision6EmailEditor
                      value={formData.content}
                      onChange={(html) => setFormData(prev => ({ ...prev, content: html }))}
                      designSettings={designSettings}
                      onDesignSettingsChange={setDesignSettings}
                    />
                  </div>
                  <div className="hidden md:block">
                    <DesignSettingsPanel
                      settings={designSettings}
                      onChange={setDesignSettings}
                    />
                  </div>
                </div>
              ) : (
                <div className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <label className="block text-white/80 text-sm font-semibold">
                      Email Content *
                    </label>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setUseVision6Editor(true)}
                        className="px-3 py-1 bg-blue-500 hover:bg-blue-600 text-white text-sm rounded-lg transition-colors"
                      >
                        Use Vision 6 Editor
                      </button>
                    </div>
                  </div>
                  {useBlockEditor ? (
                    <BlockEmailEditor
                      value={formData.content}
                      onChange={(html) => setFormData(prev => ({ ...prev, content: html }))}
                    />
                  ) : (
                    <RichEmailEditor
                      value={formData.content}
                      onChange={(html) => setFormData(prev => ({ ...prev, content: html }))}
                    />
                  )}
                </div>
              )}
            </div>

            {/* Plain Text Version */}
            <div className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-white/10">
              <label className="block text-white/80 text-sm font-semibold mb-2">
                Plain Text Version (Optional)
              </label>
              <textarea
                value={formData.content_text}
                onChange={(e) => setFormData(prev => ({ ...prev, content_text: e.target.value }))}
                rows="6"
                placeholder="Plain text version for email clients that don't support HTML"
                className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Right: Settings & Targeting */}
          <div className="space-y-6">
            {/* From Settings */}
            <div className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-white/10">
              <h3 className="text-white font-semibold mb-4">From Settings</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-white/60 text-sm mb-2">From Name</label>
                  <input
                    type="text"
                    value={formData.from_name}
                    onChange={(e) => setFormData(prev => ({ ...prev, from_name: e.target.value }))}
                    className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-white/60 text-sm mb-2">From Email</label>
                  <input
                    type="email"
                    value={formData.from_email}
                    onChange={(e) => setFormData(prev => ({ ...prev, from_email: e.target.value }))}
                    placeholder="noreply@futures.church"
                    className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
            </div>

            {/* Target Audience */}
            <div className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-white/10">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-white font-semibold">Target Audience</h3>
                <button
                  onClick={() => setShowCustomListModal(true)}
                  className="flex items-center gap-1 px-3 py-1 bg-blue-500/20 hover:bg-blue-500/30 text-blue-300 rounded-lg text-sm transition-colors"
                >
                  <PlusIcon className="w-4 h-4" />
                  New List
                </button>
              </div>

              {/* Custom Lists */}
              <div className="mb-4">
                <label className="block text-white/60 text-sm mb-2">Custom Lists</label>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {customLists.map(list => (
                    <label key={list.id} className="flex items-center gap-2 px-3 py-2 bg-white/5 rounded-lg cursor-pointer hover:bg-white/10 transition-colors">
                      <input
                        type="checkbox"
                        checked={selectedTargets.customLists.includes(list.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedTargets(prev => ({
                              ...prev,
                              customLists: [...prev.customLists, list.id]
                            }));
                          } else {
                            setSelectedTargets(prev => ({
                              ...prev,
                              customLists: prev.customLists.filter(id => id !== list.id)
                            }));
                          }
                        }}
                        className="w-4 h-4 text-blue-500 bg-white/10 border-white/20 rounded focus:ring-blue-500"
                      />
                      <span className="text-white text-sm flex-1">{list.name}</span>
                      <span className="text-white/40 text-xs">({list.member_count})</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* CSV Upload */}
              <div className="mb-4">
                <label className="block text-white/60 text-sm mb-2">Upload CSV</label>
                <label className="flex items-center gap-2 px-4 py-3 bg-white/5 border border-white/10 rounded-lg cursor-pointer hover:bg-white/10 transition-colors">
                  <PhotoIcon className="w-5 h-5 text-white/60" />
                  <span className="text-white text-sm">Choose CSV File</span>
                  <input
                    type="file"
                    accept=".csv"
                    onChange={handleCSVUpload}
                    className="hidden"
                  />
                </label>
                {csvFile && (
                  <div className="mt-2 text-white/60 text-sm">
                    Selected: {csvFile.name}
                  </div>
                )}
              </div>

              {/* Campuses */}
              <div className="mb-4">
                <label className="block text-white/60 text-sm mb-2">Campuses</label>
                <div className="space-y-2 max-h-32 overflow-y-auto">
                  {campuses.map(campus => (
                    <label key={campus} className="flex items-center gap-2 px-3 py-2 bg-white/5 rounded-lg cursor-pointer hover:bg-white/10 transition-colors">
                      <input
                        type="checkbox"
                        checked={selectedTargets.campuses.includes(campus)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedTargets(prev => ({
                              ...prev,
                              campuses: [...prev.campuses, campus]
                            }));
                          } else {
                            setSelectedTargets(prev => ({
                              ...prev,
                              campuses: prev.campuses.filter(c => c !== campus)
                            }));
                          }
                        }}
                        className="w-4 h-4 text-blue-500 bg-white/10 border-white/20 rounded focus:ring-blue-500"
                      />
                      <span className="text-white text-sm">{campus}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Departments */}
              <div>
                <label className="block text-white/60 text-sm mb-2">Departments</label>
                <div className="space-y-2 max-h-32 overflow-y-auto">
                  {departments.map(dept => (
                    <label key={dept} className="flex items-center gap-2 px-3 py-2 bg-white/5 rounded-lg cursor-pointer hover:bg-white/10 transition-colors">
                      <input
                        type="checkbox"
                        checked={selectedTargets.departments.includes(dept)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedTargets(prev => ({
                              ...prev,
                              departments: [...prev.departments, dept]
                            }));
                          } else {
                            setSelectedTargets(prev => ({
                              ...prev,
                              departments: prev.departments.filter(d => d !== dept)
                            }));
                          }
                        }}
                        className="w-4 h-4 text-blue-500 bg-white/10 border-white/20 rounded focus:ring-blue-500"
                      />
                      <span className="text-white text-sm">{dept}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Test Email Modal */}
      {showTestEmail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-slate-800 rounded-xl p-6 border border-white/10 max-w-md w-full">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-white">Send Test Email</h3>
              <button
                onClick={() => setShowTestEmail(false)}
                className="p-2 hover:bg-white/10 rounded transition-colors"
              >
                <XMarkIcon className="w-5 h-5 text-white" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-white/80 text-sm font-semibold mb-2">Test Email Address</label>
                <input
                  type="email"
                  value={testEmail}
                  onChange={(e) => setTestEmail(e.target.value)}
                  placeholder="your@email.com"
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex items-center justify-end gap-3">
                <button
                  onClick={() => setShowTestEmail(false)}
                  className="px-4 py-2 bg-white/5 hover:bg-white/10 text-white rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSendTestEmail}
                  disabled={sendingTest || !testEmail}
                  className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors disabled:opacity-50"
                >
                  {sendingTest ? 'Sending...' : 'Send Test'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Custom List Modal */}
      {showCustomListModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-slate-800 rounded-xl p-6 border border-white/10 max-w-md w-full">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-white">Create Custom List</h3>
              <button
                onClick={() => {
                  setShowCustomListModal(false);
                  setNewListName('');
                  setNewListDescription('');
                  setCsvFile(null);
                  setCsvData([]);
                }}
                className="p-2 hover:bg-white/10 rounded transition-colors"
              >
                <XMarkIcon className="w-5 h-5 text-white" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-white/80 text-sm font-semibold mb-2">List Name *</label>
                <input
                  type="text"
                  value={newListName}
                  onChange={(e) => setNewListName(e.target.value)}
                  placeholder="e.g., Business People, New People"
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-white/80 text-sm font-semibold mb-2">Description</label>
                <textarea
                  value={newListDescription}
                  onChange={(e) => setNewListDescription(e.target.value)}
                  rows="3"
                  placeholder="Optional description"
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              {csvData.length > 0 && (
                <div className="bg-blue-500/20 border border-blue-500/40 rounded-lg p-3 text-blue-200 text-sm">
                  CSV file loaded: {csvData.length} rows ready to import
                </div>
              )}
              <div className="flex items-center justify-end gap-3">
                <button
                  onClick={() => {
                    setShowCustomListModal(false);
                    setNewListName('');
                    setNewListDescription('');
                    setCsvFile(null);
                    setCsvData([]);
                  }}
                  className="px-4 py-2 bg-white/5 hover:bg-white/10 text-white rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateCustomList}
                  disabled={!newListName}
                  className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors disabled:opacity-50"
                >
                  Create List
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Preview Modal */}
      {showPreview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-gray-900">Email Preview</h3>
              <button
                onClick={() => setShowPreview(false)}
                className="p-2 hover:bg-gray-100 rounded transition-colors"
              >
                <XMarkIcon className="w-5 h-5 text-gray-600" />
              </button>
            </div>
            <div className="border border-gray-200 rounded-lg p-4">
              <div className="mb-4 pb-4 border-b border-gray-200">
                <div className="text-sm text-gray-600 mb-1">From: {formData.from_name} &lt;{formData.from_email || 'noreply@futures.church'}&gt;</div>
                <div className="text-sm text-gray-600 mb-1">To: [Recipient Email]</div>
                <div className="font-semibold text-gray-900">{formData.subject_line || 'Email Subject'}</div>
              </div>
              <div dangerouslySetInnerHTML={{ __html: formData.content || '<p>No content yet</p>' }} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EmailEditor;


