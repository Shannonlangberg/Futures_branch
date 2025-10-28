import React, { useState, useEffect } from 'react';
import { PlusIcon, CalendarIcon, XMarkIcon } from '@heroicons/react/24/outline';
import DynamicBackground from '../components/DynamicBackground';

const LogStats = () => {
  const [selectedCampus, setSelectedCampus] = useState('');
  const [campuses, setCampuses] = useState([]);
  const [showQuickInput, setShowQuickInput] = useState(false);
  const [quickInputDate, setQuickInputDate] = useState('');
  const [quickInputStats, setQuickInputStats] = useState({
    'Total People in Campus': '',
    '9:00 AM': '',
    '10:00 AM': '',
    '11:00 AM': '',
    '5:00 PM': '',
    '5:30 PM': '',
    'Kids 9:00 AM': '',
    'Kids 10:00 AM': '',
    'Kids 11:00 AM': '',
    'Kids 5:00 PM': '',
    'Kids 5:30 PM': '',
    'Kids Leaders': '',
    'New Kids': '',
    'Kids Salvations': '',
    'First Time': '',
    'Visitors': '',
    'Info Gathered': '',
    'First Time Decision': '',
    'Rededication': '',
    'Youth Total': '',
    'Youth NP': '',
    'Youth Salvations': '',
    'Connect Groups': '',
    'Dream Team': '',
    'Baptisms': '',
    'Child Dedications': ''
  });
  const [isSubmittingQuickInput, setIsSubmittingQuickInput] = useState(false);
  const [sessionStats, setSessionStats] = useState([]);

  // Calculate total attendance from service times
  const calculateTotalAttendance = () => {
    const serviceTimes = ['9:00 AM', '10:00 AM', '11:00 AM', '5:00 PM', '5:30 PM'];
    return serviceTimes.reduce((total, serviceTime) => {
      const value = parseInt(quickInputStats[serviceTime]) || 0;
      return total + value;
    }, 0);
  };

  // Calculate total kids attendance from service times
  const calculateTotalKidsAttendance = () => {
    const kidsServiceTimes = ['Kids 9:00 AM', 'Kids 10:00 AM', 'Kids 11:00 AM', 'Kids 5:00 PM', 'Kids 5:30 PM'];
    return kidsServiceTimes.reduce((total, serviceTime) => {
      const value = parseInt(quickInputStats[serviceTime]) || 0;
      return total + value;
    }, 0);
  };

  const totalAttendance = calculateTotalAttendance();
  const totalKidsAttendance = calculateTotalKidsAttendance();

  useEffect(() => {
    // Load campuses
    fetch('/api/campuses', {
      credentials: 'include'
    })
      .then(res => res.json())
      .then(data => {
        if (data.campuses) {
          setCampuses(data.campuses);
          // Set the default campus from the API response
          if (data.default) {
            setSelectedCampus(data.default);
          } else if (data.campuses.length > 0) {
            setSelectedCampus(data.campuses[0].id);
          }
        }
      })
      .catch(err => console.error('Error loading campuses:', err));

    // Set default date to today
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    setQuickInputDate(`${year}-${month}-${day}`);
  }, []);

  const handleQuickInputSubmit = async () => {
    if (!selectedCampus || !quickInputDate) {
      alert('Please select a campus and date');
      return;
    }

    setIsSubmittingQuickInput(true);
    
    try {
      // Filter out empty values
      const nonEmptyStats = Object.fromEntries(
        Object.entries(quickInputStats).filter(([_, value]) => value.trim() !== '')
      );

      if (Object.keys(nonEmptyStats).length === 0) {
        alert('Please enter at least one stat value');
        return;
      }

      // Map frontend field names to backend field names
      const fieldMapping = {
        'Total People in Campus': 'Total People in Campus',
        '9:00 AM': '9:00 AM',
        '10:00 AM': '10:00 AM',
        '11:00 AM': '11:00 AM',
        '5:00 PM': '5:00 PM',
        '5:30 PM': '5:30 PM',
        'Kids 9:00 AM': 'Kids 9:00 AM',
        'Kids 10:00 AM': 'Kids 10:00 AM',
        'Kids 11:00 AM': 'Kids 11:00 AM',
        'Kids 5:00 PM': 'Kids 5:00 PM',
        'Kids 5:30 PM': 'Kids 5:30 PM',
        'Kids Leaders': 'Kids Leaders',
        'New Kids': 'New Kids',
        'Kids Salvations': 'New Kids Salvations',
        'First Time': 'First Time Visitors',
        'Visitors': 'Visitors',
        'Info Gathered': 'Cards Back',
        'First Time Decision': 'First Time Christians',
        'Rededication': 'Rededications',
        'Youth Total': 'Youth Attendance',
        'Youth NP': 'Youth New People',
        'Youth Salvations': 'Youth Salvations',
        'Connect Groups': 'Connect Groups',
        'Dream Team': 'Dream Team',
        'Baptisms': 'Baptisms',
        'Child Dedications': 'Child Dedications'
      };

      // Convert stats to backend format
      const backendStats = {};
      Object.entries(nonEmptyStats).forEach(([key, value]) => {
        const backendKey = fieldMapping[key] || key;
        backendStats[backendKey] = parseInt(value) || 0;
      });

      // Note: Total Attendance and Kids Attendance are NOT sent to backend
      // The backend calculates these from the individual service time columns

      const response = await fetch('/api/quick_input', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          campus: selectedCampus,
          date: quickInputDate,
          stats: backendStats
        })
      });

      if (response.ok) {
        const result = await response.json();
        
        // Add to session stats
        const campusName = campuses.find(c => c.id === selectedCampus)?.name || selectedCampus;
        setSessionStats(prev => [{
          campus: campusName,
          text: `Quick input: ${Object.keys(nonEmptyStats).join(', ')}`,
          timestamp: new Date().toISOString()
        }, ...prev.slice(0, 9)]); // Keep last 10 entries

        // Reset form
        setQuickInputStats({
          'Total People in Campus': '',
          '9:00 AM': '',
          '10:00 AM': '',
          '11:00 AM': '',
          '5:00 PM': '',
          '5:30 PM': '',
          'Kids 9:00 AM': '',
          'Kids 10:00 AM': '',
          'Kids 11:00 AM': '',
          'Kids 5:00 PM': '',
          'Kids 5:30 PM': '',
          'Kids Leaders': '',
          'New Kids': '',
          'Kids Salvations': '',
          'First Time': '',
          'Visitors': '',
          'Info Gathered': '',
          'First Time Decision': '',
          'Rededication': '',
          'Youth Total': '',
          'Youth NP': '',
          'Youth Salvations': '',
          'Connect Groups': '',
          'Dream Team': '',
          'Baptisms': '',
          'Child Dedications': ''
        });
        setShowQuickInput(false);
        alert('Stats logged successfully!');
      } else {
        const errorData = await response.json();
        alert(`Error: ${errorData.error || 'Failed to log stats'}`);
      }
    } catch (error) {
      console.error('Error submitting quick input:', error);
      alert('Error submitting stats. Please try again.');
    } finally {
      setIsSubmittingQuickInput(false);
    }
  };

  return (
    <div className="relative">
      <DynamicBackground />
      
      {/* Header */}
      <div className="text-center mb-8">
          <div className="w-20 h-20 bg-gradient-to-r from-blue-500 to-purple-500 rounded-2xl flex items-center justify-center mx-auto mb-6 animate-pulse">
            <span className="text-4xl">📊</span>
          </div>
          <h1 className="text-4xl font-bold text-white mb-3">Stats Input</h1>
          <p className="text-slate-400 text-lg">Input church statistics and attendance data</p>
        </div>

        {/* Main Card */}
        <div className="max-w-6xl mx-auto">
          <div className="bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-sm rounded-3xl p-8 border border-white/20 shadow-2xl">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-8 space-y-4 sm:space-y-0">
              <div>
                <h2 className="text-2xl font-bold text-white mb-2">Quick Stats Entry</h2>
                <p className="text-slate-300 text-base">Enter your church statistics quickly and efficiently</p>
              </div>
              <div className="flex flex-col sm:flex-row items-center space-y-3 sm:space-y-0 sm:space-x-4">
                <div className="flex flex-col sm:flex-row sm:items-center space-y-2 sm:space-y-0 sm:space-x-3">
                  <span className="text-sm text-slate-300 font-medium">Campus:</span>
                  <select
                    value={selectedCampus}
                    onChange={(e) => setSelectedCampus(e.target.value)}
                    className="bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent backdrop-blur-sm"
                  >
                    {campuses.map(campus => (
                      <option key={campus.id} value={campus.id}>
                        {campus.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
            
            {/* Quick Input Section */}
            <div className="text-center">
              <button
                onClick={() => setShowQuickInput(true)}
                className="relative bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white px-12 py-5 rounded-2xl text-xl font-bold transition-all duration-300 shadow-2xl hover:shadow-purple-500/50 transform hover:scale-105 overflow-hidden group"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-purple-600 to-blue-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                <span className="relative z-10">Start Input</span>
              </button>
            </div>
          </div>
        </div>

        {/* Session Stats */}
        <div className="max-w-6xl mx-auto mt-8">
          <div className="bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-sm rounded-3xl p-8 border border-white/20 shadow-2xl">
            <h3 className="text-2xl font-bold text-white mb-6">Recent Entries</h3>
            {sessionStats.length > 0 ? (
              <div className="space-y-4">
                {sessionStats.map((stat, index) => (
                  <div key={index} className="bg-gradient-to-r from-white/10 to-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/20 shadow-lg hover:shadow-xl transition-all duration-300">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm text-blue-400 font-semibold mb-2">{stat.campus}</div>
                        <div className="text-white text-base font-medium">{stat.text}</div>
                      </div>
                      <div className="text-xs text-slate-400 bg-white/10 rounded-lg px-3 py-1">
                        {new Date(stat.timestamp).toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="w-16 h-16 bg-gradient-to-r from-slate-500 to-slate-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl">📝</span>
                </div>
                <div className="text-slate-300 text-lg font-semibold mb-2">No stats logged yet</div>
                <p className="text-slate-400 text-sm">Start by using quick input above</p>
              </div>
            )}
          </div>
        </div>

        {/* Quick Input Modal */}
        {showQuickInput && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-gradient-to-br from-slate-800/90 to-slate-900/90 backdrop-blur-xl border border-white/20 rounded-3xl p-8 max-w-5xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
              <div className="flex justify-between items-start mb-8">
                <div>
                  <h3 className="text-3xl font-bold text-white mb-2">Quick Stats Input</h3>
                  <p className="text-slate-300">Enter your church statistics in organized sections</p>
                </div>
                <button
                  onClick={() => setShowQuickInput(false)}
                  className="text-slate-400 hover:text-white transition-colors duration-200 p-2 hover:bg-white/10 rounded-xl"
                >
                  <XMarkIcon className="w-6 h-6" />
                </button>
              </div>
              
              {/* Campus & Date Selection */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                <div className="bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
                  <label className="block text-sm font-semibold text-white mb-3">
                    Campus
                  </label>
                  <select
                    value={selectedCampus}
                    onChange={(e) => setSelectedCampus(e.target.value)}
                    className="bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white w-full focus:ring-2 focus:ring-blue-500 focus:border-transparent backdrop-blur-sm"
                  >
                    {campuses.map(campus => (
                      <option key={campus.id} value={campus.id}>
                        {campus.name}
                      </option>
                    ))}
                  </select>
                </div>
                
                <div className="bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
                  <label className="block text-sm font-semibold text-white mb-3">
                    Service Date
                  </label>
                  <div className="flex items-center space-x-3">
                    <CalendarIcon className="w-5 h-5 text-blue-400" />
                    <input
                      type="date"
                      value={quickInputDate}
                      onChange={(e) => setQuickInputDate(e.target.value)}
                      className="bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white w-full focus:ring-2 focus:ring-blue-500 focus:border-transparent backdrop-blur-sm"
                    />
                  </div>
                </div>
              </div>
              
              {/* Stats Form */}
              <div className="space-y-8">
                {/* Campus Information */}
                <div className="bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/20 shadow-lg">
                  <div className="flex items-center mb-6">
                    <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-500 rounded-xl flex items-center justify-center mr-4">
                      <span className="text-xl">🏢</span>
                    </div>
                    <h4 className="text-xl font-bold text-white">Campus Information</h4>
                  </div>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <label className="text-white font-semibold min-w-[200px]">
                        Total People in Campus:
                      </label>
                      <input
                        type="text"
                        inputMode="numeric"
                        value={quickInputStats['Total People in Campus']}
                        onChange={(e) => setQuickInputStats(prev => ({
                          ...prev,
                          'Total People in Campus': e.target.value
                        }))}
                        placeholder="0"
                        className="bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white text-right w-full sm:w-40 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none focus:ring-2 focus:ring-blue-500 focus:border-transparent backdrop-blur-sm"
                      />
                    </div>
                  </div>
                </div>

                {/* Service Attendance Breakdown */}
                <div className="bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/20 shadow-lg">
                  <div className="flex items-center mb-6">
                    <div className="w-10 h-10 bg-gradient-to-r from-green-500 to-emerald-500 rounded-xl flex items-center justify-center mr-4">
                      <span className="text-xl">⛪</span>
                    </div>
                    <h4 className="text-xl font-bold text-white">Service Attendance</h4>
                  </div>
                  <div className="space-y-3 sm:space-y-4">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                      <label className="text-white font-semibold text-sm sm:text-base sm:min-w-[150px]">
                        9:00 AM:
                      </label>
                      <input
                        type="text"
                        inputMode="numeric"
                        value={quickInputStats['9:00 AM']}
                        onChange={(e) => setQuickInputStats(prev => ({
                          ...prev,
                          '9:00 AM': e.target.value
                        }))}
                        placeholder="0"
                        className="bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white text-right w-full sm:w-40 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none focus:ring-2 focus:ring-blue-500 focus:border-transparent backdrop-blur-sm"
                      />
                    </div>
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                      <label className="text-white font-semibold text-sm sm:text-base sm:min-w-[150px]">
                        10:00 AM:
                      </label>
                      <input
                        type="text"
                        inputMode="numeric"
                        value={quickInputStats['10:00 AM']}
                        onChange={(e) => setQuickInputStats(prev => ({
                          ...prev,
                          '10:00 AM': e.target.value
                        }))}
                        placeholder="0"
                        className="bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white text-right w-full sm:w-40 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none focus:ring-2 focus:ring-blue-500 focus:border-transparent backdrop-blur-sm"
                      />
                    </div>
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                      <label className="text-white font-semibold text-sm sm:text-base sm:min-w-[150px]">
                        11:00 AM:
                      </label>
                      <input
                        type="text"
                        inputMode="numeric"
                        value={quickInputStats['11:00 AM']}
                        onChange={(e) => setQuickInputStats(prev => ({
                          ...prev,
                          '11:00 AM': e.target.value
                        }))}
                        placeholder="0"
                        className="bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white text-right w-full sm:w-40 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none focus:ring-2 focus:ring-blue-500 focus:border-transparent backdrop-blur-sm"
                      />
                    </div>
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                      <label className="text-white font-semibold text-sm sm:text-base sm:min-w-[150px]">
                        5:00 PM:
                      </label>
                      <input
                        type="text"
                        inputMode="numeric"
                        value={quickInputStats['5:00 PM']}
                        onChange={(e) => setQuickInputStats(prev => ({
                          ...prev,
                          '5:00 PM': e.target.value
                        }))}
                        placeholder="0"
                        className="bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white text-right w-full sm:w-40 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none focus:ring-2 focus:ring-blue-500 focus:border-transparent backdrop-blur-sm"
                      />
                    </div>
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                      <label className="text-white font-semibold text-sm sm:text-base sm:min-w-[150px]">
                        5:30 PM:
                      </label>
                      <input
                        type="text"
                        inputMode="numeric"
                        value={quickInputStats['5:30 PM']}
                        onChange={(e) => setQuickInputStats(prev => ({
                          ...prev,
                          '5:30 PM': e.target.value
                        }))}
                        placeholder="0"
                        className="bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white text-right w-full sm:w-40 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none focus:ring-2 focus:ring-blue-500 focus:border-transparent backdrop-blur-sm"
                      />
                    </div>

                    <div className="flex items-center justify-between border-t border-slate-600 pt-3">
                      <label className="text-white font-semibold min-w-[150px]">
                        Total Attendance:
                      </label>
                      <div className="text-white font-semibold text-right w-32">
                        {totalAttendance}
                      </div>
                    </div>
                  </div>
                </div>

                {/* New People */}
                <div className="bg-slate-700/30 rounded-lg p-4">
                  <h4 className="text-white font-semibold mb-3">New People</h4>
                  <div className="space-y-3">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                      <label className="text-white font-semibold text-sm sm:text-base sm:min-w-[150px]">
                        First Time Visitors:
                      </label>
                      <input
                        type="text"
                        inputMode="numeric"
                        value={quickInputStats['First Time']}
                        onChange={(e) => setQuickInputStats(prev => ({
                          ...prev,
                          'First Time': e.target.value
                        }))}
                        placeholder="0"
                        className="bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white text-right w-full sm:w-40 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none focus:ring-2 focus:ring-blue-500 focus:border-transparent backdrop-blur-sm"
                      />
                    </div>
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                      <label className="text-white font-semibold text-sm sm:text-base sm:min-w-[150px]">
                        Visitors:
                      </label>
                      <input
                        type="text"
                        inputMode="numeric"
                        value={quickInputStats['Visitors']}
                        onChange={(e) => setQuickInputStats(prev => ({
                          ...prev,
                          'Visitors': e.target.value
                        }))}
                        placeholder="0"
                        className="bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white text-right w-full sm:w-40 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none focus:ring-2 focus:ring-blue-500 focus:border-transparent backdrop-blur-sm"
                      />
                    </div>
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                      <label className="text-white font-semibold text-sm sm:text-base sm:min-w-[150px]">
                        Cards Back:
                      </label>
                      <input
                        type="text"
                        inputMode="numeric"
                        value={quickInputStats['Info Gathered']}
                        onChange={(e) => setQuickInputStats(prev => ({
                          ...prev,
                          'Info Gathered': e.target.value
                        }))}
                        placeholder="0"
                        className="bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white text-right w-full sm:w-40 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none focus:ring-2 focus:ring-blue-500 focus:border-transparent backdrop-blur-sm"
                      />
                    </div>
                  </div>
                </div>

                {/* Salvations */}
                <div className="bg-slate-700/30 rounded-lg p-4">
                  <h4 className="text-white font-semibold mb-3">Salvations</h4>
                  <div className="space-y-3">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                      <label className="text-white font-semibold text-sm sm:text-base sm:min-w-[150px]">
                        First Time Decision:
                      </label>
                      <input
                        type="text"
                        inputMode="numeric"
                        value={quickInputStats['First Time Decision']}
                        onChange={(e) => setQuickInputStats(prev => ({
                          ...prev,
                          'First Time Decision': e.target.value
                        }))}
                        placeholder="0"
                        className="bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white text-right w-full sm:w-40 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none focus:ring-2 focus:ring-blue-500 focus:border-transparent backdrop-blur-sm"
                      />
                    </div>
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                      <label className="text-white font-semibold text-sm sm:text-base sm:min-w-[150px]">
                        Rededication:
                      </label>
                      <input
                        type="text"
                        inputMode="numeric"
                        value={quickInputStats['Rededication']}
                        onChange={(e) => setQuickInputStats(prev => ({
                          ...prev,
                          'Rededication': e.target.value
                        }))}
                        placeholder="0"
                        className="bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white text-right w-full sm:w-40 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none focus:ring-2 focus:ring-blue-500 focus:border-transparent backdrop-blur-sm"
                      />
                    </div>
                  </div>
                </div>

                {/* Kids */}
                <div className="bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/20 shadow-lg">
                  <div className="flex items-center mb-6">
                    <div className="w-10 h-10 bg-gradient-to-r from-pink-500 to-rose-500 rounded-xl flex items-center justify-center mr-4">
                      <span className="text-xl">👶</span>
                    </div>
                    <h4 className="text-xl font-bold text-white">Kids</h4>
                  </div>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <label className="text-white font-semibold min-w-[150px]">
                        Kids 9:00 AM:
                      </label>
                      <input
                        type="text"
                        inputMode="numeric"
                        value={quickInputStats['Kids 9:00 AM']}
                        onChange={(e) => setQuickInputStats(prev => ({
                          ...prev,
                          'Kids 9:00 AM': e.target.value
                        }))}
                        placeholder="0"
                        className="bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white text-right w-full sm:w-40 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none focus:ring-2 focus:ring-blue-500 focus:border-transparent backdrop-blur-sm"
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <label className="text-white font-semibold min-w-[150px]">
                        Kids 10:00 AM:
                      </label>
                      <input
                        type="text"
                        inputMode="numeric"
                        value={quickInputStats['Kids 10:00 AM']}
                        onChange={(e) => setQuickInputStats(prev => ({
                          ...prev,
                          'Kids 10:00 AM': e.target.value
                        }))}
                        placeholder="0"
                        className="bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white text-right w-full sm:w-40 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none focus:ring-2 focus:ring-blue-500 focus:border-transparent backdrop-blur-sm"
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <label className="text-white font-semibold min-w-[150px]">
                        Kids 11:00 AM:
                      </label>
                      <input
                        type="text"
                        inputMode="numeric"
                        value={quickInputStats['Kids 11:00 AM']}
                        onChange={(e) => setQuickInputStats(prev => ({
                          ...prev,
                          'Kids 11:00 AM': e.target.value
                        }))}
                        placeholder="0"
                        className="bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white text-right w-full sm:w-40 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none focus:ring-2 focus:ring-blue-500 focus:border-transparent backdrop-blur-sm"
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <label className="text-white font-semibold min-w-[150px]">
                        Kids 5:00 PM:
                      </label>
                      <input
                        type="text"
                        inputMode="numeric"
                        value={quickInputStats['Kids 5:00 PM']}
                        onChange={(e) => setQuickInputStats(prev => ({
                          ...prev,
                          'Kids 5:00 PM': e.target.value
                        }))}
                        placeholder="0"
                        className="bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white text-right w-full sm:w-40 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none focus:ring-2 focus:ring-blue-500 focus:border-transparent backdrop-blur-sm"
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <label className="text-white font-semibold min-w-[150px]">
                        Kids 5:30 PM:
                      </label>
                      <input
                        type="text"
                        inputMode="numeric"
                        value={quickInputStats['Kids 5:30 PM']}
                        onChange={(e) => setQuickInputStats(prev => ({
                          ...prev,
                          'Kids 5:30 PM': e.target.value
                        }))}
                        placeholder="0"
                        className="bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white text-right w-full sm:w-40 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none focus:ring-2 focus:ring-blue-500 focus:border-transparent backdrop-blur-sm"
                      />
                    </div>
                    {totalKidsAttendance > 0 && (
                      <div className="flex items-center justify-between border-t border-white/20 pt-4 mt-2">
                        <span className="text-pink-300 font-bold text-lg">Total Kids:</span>
                        <span className="text-pink-300 font-bold text-2xl">{totalKidsAttendance}</span>
                      </div>
                    )}
                    <div className="border-t border-white/20 pt-4 mt-4">
                      <div className="flex items-center justify-between">
                        <label className="text-white font-semibold min-w-[150px]">
                          Kids Leaders:
                        </label>
                        <input
                          type="text"
                          inputMode="numeric"
                          value={quickInputStats['Kids Leaders']}
                          onChange={(e) => setQuickInputStats(prev => ({
                            ...prev,
                            'Kids Leaders': e.target.value
                          }))}
                          placeholder="0"
                          className="bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white text-right w-full sm:w-40 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none focus:ring-2 focus:ring-blue-500 focus:border-transparent backdrop-blur-sm"
                        />
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <label className="text-white font-semibold min-w-[150px]">
                        New Kids:
                      </label>
                      <input
                        type="text"
                        inputMode="numeric"
                        value={quickInputStats['New Kids']}
                        onChange={(e) => setQuickInputStats(prev => ({
                          ...prev,
                          'New Kids': e.target.value
                        }))}
                        placeholder="0"
                        className="bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white text-right w-full sm:w-40 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none focus:ring-2 focus:ring-blue-500 focus:border-transparent backdrop-blur-sm"
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <label className="text-white font-semibold min-w-[150px]">
                        Kids Salvations:
                      </label>
                      <input
                        type="text"
                        inputMode="numeric"
                        value={quickInputStats['Kids Salvations']}
                        onChange={(e) => setQuickInputStats(prev => ({
                          ...prev,
                          'Kids Salvations': e.target.value
                        }))}
                        placeholder="0"
                        className="bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white text-right w-full sm:w-40 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none focus:ring-2 focus:ring-blue-500 focus:border-transparent backdrop-blur-sm"
                      />
                    </div>
                  </div>
                </div>

                {/* Youth */}
                <div className="bg-slate-700/30 rounded-lg p-4">
                  <h4 className="text-white font-semibold mb-3">Youth</h4>
                  <div className="space-y-3">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                      <label className="text-white font-semibold text-sm sm:text-base sm:min-w-[150px]">
                        Youth Attendance:
                      </label>
                      <input
                        type="text"
                        inputMode="numeric"
                        value={quickInputStats['Youth Total']}
                        onChange={(e) => setQuickInputStats(prev => ({
                          ...prev,
                          'Youth Total': e.target.value
                        }))}
                        placeholder="0"
                        className="bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white text-right w-full sm:w-40 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none focus:ring-2 focus:ring-blue-500 focus:border-transparent backdrop-blur-sm"
                      />
                    </div>
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                      <label className="text-white font-semibold text-sm sm:text-base sm:min-w-[150px]">
                        Youth New People:
                      </label>
                      <input
                        type="text"
                        inputMode="numeric"
                        value={quickInputStats['Youth NP']}
                        onChange={(e) => setQuickInputStats(prev => ({
                          ...prev,
                          'Youth NP': e.target.value
                        }))}
                        placeholder="0"
                        className="bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white text-right w-full sm:w-40 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none focus:ring-2 focus:ring-blue-500 focus:border-transparent backdrop-blur-sm"
                      />
                    </div>
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                      <label className="text-white font-semibold text-sm sm:text-base sm:min-w-[150px]">
                        Youth Salvations:
                      </label>
                      <input
                        type="text"
                        inputMode="numeric"
                        value={quickInputStats['Youth Salvations']}
                        onChange={(e) => setQuickInputStats(prev => ({
                          ...prev,
                          'Youth Salvations': e.target.value
                        }))}
                        placeholder="0"
                        className="bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white text-right w-full sm:w-40 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none focus:ring-2 focus:ring-blue-500 focus:border-transparent backdrop-blur-sm"
                      />
                    </div>
                  </div>
                </div>

                {/* Connect Groups & Ministry */}
                <div className="bg-slate-700/30 rounded-lg p-4">
                  <h4 className="text-white font-semibold mb-3">Connect Groups & Ministry</h4>
                  <div className="space-y-3">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                      <label className="text-white font-semibold text-sm sm:text-base sm:min-w-[150px]">
                        Connect Groups:
                      </label>
                      <input
                        type="text"
                        inputMode="numeric"
                        value={quickInputStats['Connect Groups']}
                        onChange={(e) => setQuickInputStats(prev => ({
                          ...prev,
                          'Connect Groups': e.target.value
                        }))}
                        placeholder="0"
                        className="bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white text-right w-full sm:w-40 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none focus:ring-2 focus:ring-blue-500 focus:border-transparent backdrop-blur-sm"
                      />
                    </div>
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                      <label className="text-white font-semibold text-sm sm:text-base sm:min-w-[150px]">
                        Dream Team:
                      </label>
                      <input
                        type="text"
                        inputMode="numeric"
                        value={quickInputStats['Dream Team']}
                        onChange={(e) => setQuickInputStats(prev => ({
                          ...prev,
                          'Dream Team': e.target.value
                        }))}
                        placeholder="0"
                        className="bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white text-right w-full sm:w-40 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none focus:ring-2 focus:ring-blue-500 focus:border-transparent backdrop-blur-sm"
                      />
                    </div>
                  </div>
                </div>

                {/* Special Events */}
                <div className="bg-slate-700/30 rounded-lg p-4">
                  <h4 className="text-white font-semibold mb-3">Special Events</h4>
                  <div className="space-y-3">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                      <label className="text-white font-semibold text-sm sm:text-base sm:min-w-[150px]">
                        Baptisms:
                      </label>
                      <input
                        type="text"
                        inputMode="numeric"
                        value={quickInputStats['Baptisms']}
                        onChange={(e) => setQuickInputStats(prev => ({
                          ...prev,
                          'Baptisms': e.target.value
                        }))}
                        placeholder="0"
                        className="bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white text-right w-full sm:w-40 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none focus:ring-2 focus:ring-blue-500 focus:border-transparent backdrop-blur-sm"
                      />
                    </div>
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                      <label className="text-white font-semibold text-sm sm:text-base sm:min-w-[150px]">
                        Child Dedications:
                      </label>
                      <input
                        type="text"
                        inputMode="numeric"
                        value={quickInputStats['Child Dedications']}
                        onChange={(e) => setQuickInputStats(prev => ({
                          ...prev,
                          'Child Dedications': e.target.value
                        }))}
                        placeholder="0"
                        className="bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white text-right w-full sm:w-40 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none focus:ring-2 focus:ring-blue-500 focus:border-transparent backdrop-blur-sm"
                      />
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Validation Hint */}
              <div className="mt-6 p-3 bg-slate-700/30 rounded-lg">
                <p className="text-sm text-slate-400">
                  Your number should not have commas or currency symbols
                </p>
              </div>
              
              {/* Submit Button */}
              <div className="flex justify-end mt-8">
                <button
                  onClick={handleQuickInputSubmit}
                  disabled={isSubmittingQuickInput}
                  className="bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 disabled:from-slate-600 disabled:to-slate-700 disabled:cursor-not-allowed text-white px-8 py-4 rounded-2xl flex items-center space-x-3 transition-all duration-300 shadow-lg hover:shadow-xl text-lg font-semibold transform hover:scale-105 disabled:transform-none"
                >
                  {isSubmittingQuickInput ? (
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  ) : (
                    <PlusIcon className="w-5 h-5" />
                  )}
                  <span>{isSubmittingQuickInput ? 'Submitting...' : 'Submit Stats'}</span>
                </button>
              </div>
            </div>
          </div>
        )}
    </div>
  );
};

export default LogStats; 