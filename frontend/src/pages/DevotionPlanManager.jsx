import React, { useState, useEffect } from 'react';
import { 
  PlusIcon, 
  PencilIcon, 
  TrashIcon, 
  EyeIcon,
  BookOpenIcon,
  CalendarDaysIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  CheckIcon,
  XMarkIcon,
  MagnifyingGlassIcon,
  GlobeAltIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';

const DevotionPlanManager = () => {
  const [plans, setPlans] = useState([]);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [selectedDay, setSelectedDay] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showCreatePlan, setShowCreatePlan] = useState(false);
  const [showDayEditor, setShowDayEditor] = useState(false);

  // Plan creation form
  const [newPlan, setNewPlan] = useState({
    name: '',
    description: '',
    total_days: 30,
    category: 'Bible Study',
    author: ''
  });

  // Day editor form
  const [dayContent, setDayContent] = useState({
    day_number: 1,
    title: '',
    scripture_reference: '',
    scripture_text: '',
    content: '',
    prayer_focus: '',
    reflection_questions: [],
    tags: []
  });

  // Bible API integration
  const [bibleVersions] = useState([
    { id: 'NIV', name: 'New International Version', abbreviation: 'NIV' },
    { id: 'ESV', name: 'English Standard Version', abbreviation: 'ESV' },
    { id: 'KJV', name: 'King James Version', abbreviation: 'KJV' },
    { id: 'NKJV', name: 'New King James Version', abbreviation: 'NKJV' },
    { id: 'NLT', name: 'New Living Translation', abbreviation: 'NLT' },
    { id: 'CSB', name: 'Christian Standard Bible', abbreviation: 'CSB' },
    { id: 'NASB', name: 'New American Standard Bible', abbreviation: 'NASB' },
    { id: 'MSG', name: 'The Message', abbreviation: 'MSG' }
  ]);
  const [selectedVersion, setSelectedVersion] = useState('NIV');
  const [isLoadingScripture, setIsLoadingScripture] = useState(false);
  const [scriptureSearchResults, setScriptureSearchResults] = useState([]);
  const [showScriptureSearch, setShowScriptureSearch] = useState(false);

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    try {
      setLoading(true);
      // Mock data for now - in real app would fetch from API
      const mockPlans = [
        {
          id: 'acts-study',
          name: 'Acts Study - Ordinary People, Extraordinary Mission',
          description: 'A 30-day journey through the book of Acts',
          total_days: 30,
          category: 'Bible Study',
          author: 'Pastor Sarah',
          created_at: '2025-01-01',
          days_completed: 15,
          days: generateMockDays(30, 'acts')
        },
        {
          id: 'sabbath-practice',
          name: 'The Sabbath Practice',
          description: 'A 7-day exploration of rest and worship',
          total_days: 7,
          category: 'Spiritual Practice',
          author: 'Pastor John',
          created_at: '2025-01-01',
          days_completed: 7,
          days: generateMockDays(7, 'sabbath')
        }
      ];
      setPlans(mockPlans);
    } catch (error) {
      console.error('Error fetching plans:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateMockDays = (totalDays, theme) => {
    const days = [];
    for (let i = 1; i <= totalDays; i++) {
      if (theme === 'acts') {
        days.push({
          day_number: i,
          title: `Day ${i}: ${getActsTitle(i)}`,
          scripture_reference: `Acts ${i}:1-10`,
          scripture_text: `Sample scripture text for Acts chapter ${i}...`,
          content: `Today we explore Acts chapter ${i} and discover how ordinary people can do extraordinary things through God's power...`,
          prayer_focus: `Lord, help me to be bold like the early church in Acts ${i}...`,
          reflection_questions: [
            `What stands out to you from Acts ${i}?`,
            `How can you apply this passage to your life today?`
          ],
          tags: ['acts', 'early-church', 'mission'],
          is_completed: i <= 15 // First 15 days completed
        });
      } else if (theme === 'sabbath') {
        days.push({
          day_number: i,
          title: `Day ${i}: ${getSabbathTitle(i)}`,
          scripture_reference: getSabbathScripture(i),
          scripture_text: `Sample scripture about rest and worship...`,
          content: `Today we learn about the importance of Sabbath rest...`,
          prayer_focus: `Father, teach me to find true rest in You...`,
          reflection_questions: [
            `How do you currently practice rest?`,
            `What prevents you from truly resting in God?`
          ],
          tags: ['sabbath', 'rest', 'worship'],
          is_completed: true
        });
      }
    }
    return days;
  };

  const getActsTitle = (day) => {
    const titles = [
      'The Promise of the Spirit', 'Pentecost Power', 'Bold Preaching', 'Community Life',
      'Healing and Miracles', 'Persecution Begins', 'Choosing Deacons', 'Stephen\'s Witness',
      'Saul\'s Conversion', 'Peter\'s Vision', 'The Gospel Spreads', 'Prison Break',
      'First Missionary Journey', 'Jerusalem Council', 'Second Journey Begins', 'Lydia\'s Conversion',
      'Philippian Jail', 'Athens Encounter', 'Corinthian Ministry', 'Ephesian Revival',
      'Farewell to Ephesus', 'Journey to Jerusalem', 'Paul\'s Arrest', 'Before the Council',
      'Plot Against Paul', 'Before Felix', 'Before Agrippa', 'Shipwreck', 'Malta Ministry', 'Rome at Last'
    ];
    return titles[day - 1] || `Acts Chapter ${day}`;
  };

  const getSabbathTitle = (day) => {
    const titles = [
      'God\'s Design for Rest', 'Jesus and the Sabbath', 'Rest for the Weary',
      'Worship and Wonder', 'Community and Connection', 'Reflection and Renewal', 'Living Sabbath'
    ];
    return titles[day - 1] || `Sabbath Day ${day}`;
  };

  const getSabbathScripture = (day) => {
    const scriptures = [
      'Genesis 2:2-3', 'Mark 2:27-28', 'Matthew 11:28-30',
      'Psalm 46:10', 'Hebrews 10:24-25', 'Psalm 23:1-3', 'Isaiah 58:13-14'
    ];
    return scriptures[day - 1] || `Psalm ${day}:1`;
  };

  const handleCreatePlan = async () => {
    try {
      // In real app, would call API to create plan
      const newPlanData = {
        ...newPlan,
        id: `plan-${Date.now()}`,
        created_at: new Date().toISOString().split('T')[0],
        days_completed: 0,
        days: Array.from({ length: newPlan.total_days }, (_, i) => ({
          day_number: i + 1,
          title: `Day ${i + 1}`,
          scripture_reference: '',
          scripture_text: '',
          content: '',
          prayer_focus: '',
          reflection_questions: [],
          tags: [],
          is_completed: false
        }))
      };
      
      setPlans([...plans, newPlanData]);
      setShowCreatePlan(false);
      setNewPlan({ name: '', description: '', total_days: 30, category: 'Bible Study', author: '' });
    } catch (error) {
      console.error('Error creating plan:', error);
    }
  };

  const handleEditDay = (plan, day) => {
    setSelectedPlan(plan);
    setSelectedDay(day);
    setDayContent({
      day_number: day.day_number,
      title: day.title,
      scripture_reference: day.scripture_reference,
      scripture_text: day.scripture_text,
      content: day.content,
      prayer_focus: day.prayer_focus,
      reflection_questions: day.reflection_questions || [],
      tags: day.tags || []
    });
    setShowDayEditor(true);
  };

  const handleSaveDay = async () => {
    try {
      // Update the day in the selected plan
      const updatedPlans = plans.map(plan => {
        if (plan.id === selectedPlan.id) {
          const updatedDays = plan.days.map(day => {
            if (day.day_number === selectedDay.day_number) {
              return { ...day, ...dayContent };
            }
            return day;
          });
          return { ...plan, days: updatedDays };
        }
        return plan;
      });
      
      setPlans(updatedPlans);
      setShowDayEditor(false);
      setSelectedDay(null);
      setSelectedPlan(null);
    } catch (error) {
      console.error('Error saving day:', error);
    }
  };

  const addReflectionQuestion = () => {
    setDayContent({
      ...dayContent,
      reflection_questions: [...dayContent.reflection_questions, '']
    });
  };

  const updateReflectionQuestion = (index, value) => {
    const updated = [...dayContent.reflection_questions];
    updated[index] = value;
    setDayContent({ ...dayContent, reflection_questions: updated });
  };

  const removeReflectionQuestion = (index) => {
    setDayContent({
      ...dayContent,
      reflection_questions: dayContent.reflection_questions.filter((_, i) => i !== index)
    });
  };

  // Bible API functions
  const searchScripture = async (reference) => {
    if (!reference.trim()) return;
    
    setIsLoadingScripture(true);
    try {
      // Call our backend Bible API
      const response = await fetch(`/api/bible/search?reference=${encodeURIComponent(reference)}&version=${selectedVersion}`);
      const data = await response.json();
      
      if (data.success) {
        const results = [{
          reference: data.reference,
          text: data.text,
          version: data.version,
          book: data.book,
          chapter: data.chapter,
          verse: data.verse_start
        }];
        
        setScriptureSearchResults(results);
        setShowScriptureSearch(true);
      } else {
        console.error('Bible API error:', data.error);
        // Fallback to mock data for demo purposes
        const mockResults = [
          {
            reference: reference,
            text: `This is a sample scripture text for ${reference} in ${selectedVersion}. In a real implementation, this would fetch the actual text from Bible Gateway or another Bible API.`,
            version: selectedVersion,
            book: reference.split(' ')[0],
            chapter: reference.split(' ')[1]?.split(':')[0] || '1',
            verse: reference.split(' ')[1]?.split(':')[1] || '1'
          }
        ];
        setScriptureSearchResults(mockResults);
        setShowScriptureSearch(true);
      }
    } catch (error) {
      console.error('Error searching scripture:', error);
      // Fallback to mock data
      const mockResults = [
        {
          reference: reference,
          text: `This is a sample scripture text for ${reference} in ${selectedVersion}. In a real implementation, this would fetch the actual text from Bible Gateway or another Bible API.`,
          version: selectedVersion,
          book: reference.split(' ')[0],
          chapter: reference.split(' ')[1]?.split(':')[0] || '1',
          verse: reference.split(' ')[1]?.split(':')[1] || '1'
        }
      ];
      setScriptureSearchResults(mockResults);
      setShowScriptureSearch(true);
    } finally {
      setIsLoadingScripture(false);
    }
  };

  const fetchScriptureFromAPI = async (reference, version) => {
    // In production, this would call a real Bible API
    // Example: Bible Gateway, Bible API, or ESV API
    try {
      // Mock API call - replace with actual API endpoint
      const response = await fetch(`/api/bible/search?reference=${encodeURIComponent(reference)}&version=${version}`);
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error fetching from Bible API:', error);
      return null;
    }
  };

  const insertScriptureText = (scriptureData) => {
    setDayContent({
      ...dayContent,
      scripture_text: scriptureData.text,
      scripture_reference: scriptureData.reference
    });
    setShowScriptureSearch(false);
    setScriptureSearchResults([]);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center min-h-96">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400 mx-auto mb-4"></div>
              <p className="text-slate-300">Loading devotion plans...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2">Devotion Plan Manager</h1>
            <p className="text-slate-300 text-lg">
              Create and manage multi-day devotional plans with daily content
            </p>
            <div className="mt-4 p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
              <h3 className="text-blue-300 font-medium mb-2 flex items-center gap-2">
                <GlobeAltIcon className="h-4 w-4" />
                Bible API Integration
              </h3>
              <p className="text-slate-300 text-sm">
                ✨ <strong>No more copy-pasting!</strong> Enter scripture references (e.g., "John 3:16", "Psalm 23:1-3") 
                and automatically fetch text from multiple Bible versions (NIV, ESV, KJV, NKJV, NLT, CSB, NASB, MSG).
                <br />
                <span className="text-blue-300">💡 Tip:</span> Use the "Fetch" button in the day editor to automatically load scripture text.
              </p>
            </div>
          </div>
          <button
            onClick={() => setShowCreatePlan(true)}
            className="flex items-center gap-2 bg-blue-500 hover:bg-blue-400 text-white font-medium px-4 py-2 rounded-lg transition-colors duration-200"
          >
            <PlusIcon className="h-5 w-5" />
            Create Plan
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-1 mb-6 bg-slate-800/50 rounded-lg p-1 border border-slate-700/50">
          <a
            href="/devotions"
            className={`flex items-center gap-2 px-4 py-2 rounded-md font-medium transition-colors duration-200 ${
              window.location.pathname === '/devotions' 
                ? 'bg-blue-600 text-white' 
                : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
            }`}
          >
            <DocumentTextIcon className="h-4 w-4" />
            Devotions
          </a>
          <a
            href="/devotions/plans/manage"
            className={`flex items-center gap-2 px-4 py-2 rounded-md font-medium transition-colors duration-200 ${
              window.location.pathname === '/devotions/plans/manage' 
                ? 'bg-blue-600 text-white' 
                : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
            }`}
          >
            <BookOpenIcon className="h-4 w-4" />
            Plans
          </a>
        </div>

        {/* Plans Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {plans.map((plan) => (
            <div key={plan.id} className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 overflow-hidden">
              {/* Plan Header */}
              <div className="p-6 border-b border-slate-700/50">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-xl font-semibold text-white mb-2">{plan.name}</h3>
                    <p className="text-slate-400 text-sm">{plan.description}</p>
                  </div>
                  <span className="px-2 py-1 text-xs rounded-full bg-blue-500/20 text-blue-300 border border-blue-500/30">
                    {plan.category}
                  </span>
                </div>
                
                <div className="flex items-center justify-between text-sm text-slate-400">
                  <span>By {plan.author}</span>
                  <span>{plan.total_days} days</span>
                </div>
                
                {/* Progress Bar */}
                <div className="mt-4">
                  <div className="flex justify-between text-sm text-slate-400 mb-2">
                    <span>Progress</span>
                    <span>{plan.days_completed}/{plan.total_days} days</span>
                  </div>
                  <div className="w-full bg-slate-700 rounded-full h-2">
                    <div 
                      className="bg-blue-500 h-2 rounded-full transition-all duration-300" 
                      style={{ width: `${(plan.days_completed / plan.total_days) * 100}%` }}
                    ></div>
                  </div>
                </div>
              </div>

              {/* Days Grid */}
              <div className="p-6">
                <h4 className="text-white font-medium mb-4 flex items-center gap-2">
                  <CalendarDaysIcon className="h-4 w-4" />
                  Daily Content
                </h4>
                
                <div className="grid grid-cols-7 gap-2 mb-4">
                  {plan.days.slice(0, 28).map((day) => (
                    <button
                      key={day.day_number}
                      onClick={() => handleEditDay(plan, day)}
                      className={`
                        w-8 h-8 rounded-lg text-xs font-medium transition-all duration-200
                        ${day.is_completed 
                          ? 'bg-green-500 text-white' 
                          : day.title && day.content 
                            ? 'bg-blue-500 text-white' 
                            : 'bg-slate-700 text-slate-400 hover:bg-slate-600'
                        }
                      `}
                      title={`Day ${day.day_number}: ${day.title || 'Not configured'}`}
                    >
                      {day.day_number}
                    </button>
                  ))}
                </div>
                
                {plan.total_days > 28 && (
                  <div className="text-center">
                    <button
                      onClick={() => handleEditDay(plan, plan.days[0])}
                      className="text-blue-400 hover:text-blue-300 text-sm"
                    >
                      View all {plan.total_days} days →
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Create Plan Modal */}
        {showCreatePlan && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 max-w-md w-full">
              <h3 className="text-lg font-semibold text-white mb-4">Create New Devotion Plan</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Plan Name</label>
                  <input
                    type="text"
                    value={newPlan.name}
                    onChange={(e) => setNewPlan({...newPlan, name: e.target.value})}
                    className="w-full bg-slate-700/50 border border-slate-600 rounded-lg px-3 py-2 text-white"
                    placeholder="e.g., 30-Day Prayer Journey"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Description</label>
                  <textarea
                    value={newPlan.description}
                    onChange={(e) => setNewPlan({...newPlan, description: e.target.value})}
                    rows={3}
                    className="w-full bg-slate-700/50 border border-slate-600 rounded-lg px-3 py-2 text-white"
                    placeholder="Brief description of the plan"
                  />
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">Total Days</label>
                    <input
                      type="number"
                      min="1"
                      max="365"
                      value={newPlan.total_days}
                      onChange={(e) => setNewPlan({...newPlan, total_days: parseInt(e.target.value)})}
                      className="w-full bg-slate-700/50 border border-slate-600 rounded-lg px-3 py-2 text-white"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">Category</label>
                    <select
                      value={newPlan.category}
                      onChange={(e) => setNewPlan({...newPlan, category: e.target.value})}
                      className="w-full bg-slate-700/50 border border-slate-600 rounded-lg px-3 py-2 text-white"
                    >
                      <option value="Bible Study">Bible Study</option>
                      <option value="Prayer">Prayer</option>
                      <option value="Spiritual Practice">Spiritual Practice</option>
                      <option value="Worship">Worship</option>
                      <option value="Daily Reading">Daily Reading</option>
                    </select>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Author</label>
                  <input
                    type="text"
                    value={newPlan.author}
                    onChange={(e) => setNewPlan({...newPlan, author: e.target.value})}
                    className="w-full bg-slate-700/50 border border-slate-600 rounded-lg px-3 py-2 text-white"
                    placeholder="Your name"
                  />
                </div>
              </div>
              
              <div className="flex justify-end gap-3 mt-6">
                <button
                  onClick={() => setShowCreatePlan(false)}
                  className="px-4 py-2 text-slate-400 hover:text-white transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreatePlan}
                  className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors"
                >
                  Create Plan
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Day Editor Modal */}
        {showDayEditor && selectedDay && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-slate-800 border border-slate-700 rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              {/* Header */}
              <div className="flex items-center justify-between p-6 border-b border-slate-700">
                <div>
                  <h2 className="text-2xl font-bold text-white">
                    Edit Day {selectedDay.day_number}
                  </h2>
                  <p className="text-slate-400 mt-1">
                    {selectedPlan.name}
                  </p>
                </div>
                <button
                  onClick={() => setShowDayEditor(false)}
                  className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>

              {/* Form */}
              <div className="p-6 space-y-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Left Column */}
                  <div className="space-y-6">
                    {/* Title */}
                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-2">
                        Day Title
                      </label>
                      <input
                        type="text"
                        value={dayContent.title}
                        onChange={(e) => setDayContent({...dayContent, title: e.target.value})}
                        className="w-full bg-slate-700/50 border border-slate-600 rounded-lg px-3 py-2 text-white"
                        placeholder="e.g., The Promise of the Spirit"
                      />
                    </div>

                    {/* Scripture */}
                    <div>
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold text-white">Scripture</h3>
                        <div className="flex items-center gap-2">
                          <GlobeAltIcon className="h-4 w-4 text-slate-400" />
                          <select
                            value={selectedVersion}
                            onChange={(e) => setSelectedVersion(e.target.value)}
                            className="bg-slate-700/50 border border-slate-600 rounded-lg px-2 py-1 text-sm text-white"
                          >
                            {bibleVersions.map(version => (
                              <option key={version.id} value={version.id}>
                                {version.abbreviation}
                              </option>
                            ))}
                          </select>
                        </div>
                      </div>
                      
                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-slate-300 mb-2">
                            Scripture Reference
                          </label>
                          <div className="flex gap-2">
                            <input
                              type="text"
                              value={dayContent.scripture_reference}
                              onChange={(e) => setDayContent({...dayContent, scripture_reference: e.target.value})}
                              className="flex-1 bg-slate-700/50 border border-slate-600 rounded-lg px-3 py-2 text-white"
                              placeholder="e.g., Acts 1:1-11"
                            />
                            <button
                              onClick={() => searchScripture(dayContent.scripture_reference)}
                              disabled={!dayContent.scripture_reference.trim() || isLoadingScripture}
                              className="flex items-center gap-2 bg-blue-500 hover:bg-blue-600 disabled:bg-slate-600 disabled:cursor-not-allowed text-white px-3 py-2 rounded-lg transition-colors"
                            >
                              {isLoadingScripture ? (
                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                              ) : (
                                <MagnifyingGlassIcon className="h-4 w-4" />
                              )}
                              Fetch
                            </button>
                          </div>
                          <p className="text-xs text-slate-400 mt-1">
                            Enter a reference (e.g., John 3:16, Psalm 23:1-3) and click Fetch to automatically get the text
                          </p>
                        </div>

                        {/* Scripture Search Results */}
                        {showScriptureSearch && scriptureSearchResults.length > 0 && (
                          <div className="bg-slate-700/50 border border-slate-600 rounded-lg p-4">
                            <h4 className="text-sm font-medium text-white mb-3">Scripture Found:</h4>
                            {scriptureSearchResults.map((result, index) => (
                              <div key={index} className="bg-slate-800/50 rounded-lg p-3 mb-3 border border-slate-600">
                                <div className="flex items-start justify-between mb-2">
                                  <div className="flex items-center gap-2">
                                    <DocumentTextIcon className="h-4 w-4 text-blue-400" />
                                    <span className="text-sm font-medium text-white">{result.reference}</span>
                                    <span className="text-xs text-slate-400">({result.version})</span>
                                  </div>
                                  <button
                                    onClick={() => insertScriptureText(result)}
                                    className="text-blue-400 hover:text-blue-300 text-sm font-medium"
                                  >
                                    Use This Text
                                  </button>
                                </div>
                                <p className="text-sm text-slate-300 leading-relaxed">
                                  {result.text.substring(0, 200)}...
                                </p>
                              </div>
                            ))}
                          </div>
                        )}

                        <div>
                          <label className="block text-sm font-medium text-slate-300 mb-2">
                            Scripture Text
                          </label>
                          <textarea
                            value={dayContent.scripture_text}
                            onChange={(e) => setDayContent({...dayContent, scripture_text: e.target.value})}
                            rows={6}
                            className="w-full bg-slate-700/50 border border-slate-600 rounded-lg px-3 py-2 text-white"
                            placeholder="Scripture text will appear here after fetching, or you can type/paste manually"
                          />
                          <p className="text-xs text-slate-400 mt-1">
                            {dayContent.scripture_text ? 
                              `Text loaded from ${selectedVersion} - you can edit if needed` : 
                              'Click "Fetch" above to automatically load scripture text'
                            }
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Right Column */}
                  <div className="space-y-6">
                    {/* Content */}
                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-2">
                        Devotional Content
                      </label>
                      <textarea
                        value={dayContent.content}
                        onChange={(e) => setDayContent({...dayContent, content: e.target.value})}
                        rows={8}
                        className="w-full bg-slate-700/50 border border-slate-600 rounded-lg px-3 py-2 text-white"
                        placeholder="Write the main devotional content for this day..."
                      />
                    </div>

                    {/* Prayer Focus */}
                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-2">
                        Prayer Focus
                      </label>
                      <textarea
                        value={dayContent.prayer_focus}
                        onChange={(e) => setDayContent({...dayContent, prayer_focus: e.target.value})}
                        rows={3}
                        className="w-full bg-slate-700/50 border border-slate-600 rounded-lg px-3 py-2 text-white"
                        placeholder="Prayer points or focus for this day"
                      />
                    </div>
                  </div>
                </div>

                {/* Reflection Questions */}
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-white">Reflection Questions</h3>
                    <button
                      onClick={addReflectionQuestion}
                      className="flex items-center gap-2 text-blue-400 hover:text-blue-300 text-sm"
                    >
                      <PlusIcon className="h-4 w-4" />
                      Add Question
                    </button>
                  </div>
                  
                  <div className="space-y-3">
                    {dayContent.reflection_questions.map((question, index) => (
                      <div key={index} className="flex gap-3">
                        <input
                          type="text"
                          value={question}
                          onChange={(e) => updateReflectionQuestion(index, e.target.value)}
                          className="flex-1 bg-slate-700/50 border border-slate-600 rounded-lg px-3 py-2 text-white"
                          placeholder="Enter reflection question"
                        />
                        <button
                          onClick={() => removeReflectionQuestion(index)}
                          className="p-2 text-slate-400 hover:text-red-400 transition-colors"
                        >
                          <TrashIcon className="h-4 w-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Form Actions */}
                <div className="flex justify-end gap-3 pt-6 border-t border-slate-700">
                  <button
                    onClick={() => setShowDayEditor(false)}
                    className="px-6 py-2 text-slate-400 hover:text-white transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSaveDay}
                    className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-lg transition-colors flex items-center gap-2"
                  >
                    <CheckIcon className="h-4 w-4" />
                    Save Day
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DevotionPlanManager;
