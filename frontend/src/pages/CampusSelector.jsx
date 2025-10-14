import React, { useState, useEffect } from 'react';

const CampusSelector = ({ onCampusSelect, userRole, userCampus }) => {
  const [regions, setRegions] = useState([]);
  const [campuses, setCampuses] = useState([]);
  const [selectedRegion, setSelectedRegion] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showAIModal, setShowAIModal] = useState(false);
  
  // Check if user has full access (admin, senior leader, senior pastor, lead pastor)
  const hasFullAccess = userRole === 'admin' || userRole === 'senior_leader' || userRole === 'senior_pastor' || userRole === 'lead_pastor';
  
  // Filter campuses based on user role and assigned campus
  const getAccessibleCampuses = () => {
    if (hasFullAccess) {
      return campuses; // Show all campuses
    }
    // For campus pastors, only show their assigned campus
    if (userCampus && userCampus !== 'all_campuses') {
      return campuses.filter(c => c.id === userCampus || c.id === userCampus.toLowerCase().replace(' ', '_'));
    }
    return []; // No access
  };

  useEffect(() => {
    fetchRegions();
    fetchCampuses();
  }, []);

  const fetchRegions = async () => {
    try {
      const response = await fetch('/api/v2/regions');
      if (response.ok) {
        const data = await response.json();
        setRegions(data.regions || []);
      }
    } catch (error) {
      console.error('Error fetching regions:', error);
    }
  };

  const fetchCampuses = async () => {
    try {
      const response = await fetch('/api/campuses/public');
      const result = await response.json();
      const campusesList = result.campuses || [];
      
      if (Array.isArray(campusesList)) {
        setCampuses(campusesList.filter(c => c.id !== 'all_campuses'));
      }
    } catch (error) {
      console.error('Error fetching campuses:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-20 h-20 bg-gradient-to-r from-blue-500 to-purple-500 rounded-2xl flex items-center justify-center mx-auto mb-6 animate-pulse">
            <span className="text-4xl">⛪</span>
          </div>
          <div className="text-white text-2xl font-bold mb-2">Loading Campuses</div>
          <div className="text-white/60 text-lg">Fetching campus data...</div>
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

      {/* Header */}
      <div className="relative bg-gradient-to-r from-blue-600/90 via-purple-600/90 to-pink-600/90 backdrop-blur-sm border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4 flex-1 justify-center">
              <div className="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center backdrop-blur-sm">
                <span className="text-4xl">⛪</span>
              </div>
              <div>
                <h1 className="text-5xl font-bold text-white tracking-tight">
                  Futures Church
                </h1>
                <p className="text-white/80 text-xl font-medium">
                  Campus Dashboard Selection
                </p>
              </div>
            </div>
            
            {/* AI Assistant Button - Only for leadership roles */}
            {hasFullAccess && (
              <button
                onClick={() => setShowAIModal(true)}
                className="flex items-center gap-3 bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-600 hover:to-cyan-600 text-white px-6 py-3 rounded-2xl font-semibold transition-all duration-300 hover:scale-105 shadow-lg hover:shadow-emerald-500/25"
              >
                <span className="text-xl">🤖</span>
                <span>AI Assistant</span>
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="relative max-w-7xl mx-auto px-6 py-12">
        {/* Back Button */}
        {selectedRegion && (
          <button
            onClick={() => setSelectedRegion(null)}
            className="mb-8 flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 rounded-xl text-white transition-all"
          >
            <span className="text-xl">←</span>
            <span>Back to Regions</span>
          </button>
        )}

        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-white mb-4">
            {selectedRegion ? `${selectedRegion.display_name} Campuses` : 'Select a Region'}
          </h2>
          <p className="text-white/60 text-lg">
            {selectedRegion 
              ? 'Choose a campus to view detailed ministry analytics' 
              : 'Choose your region to begin'
            }
          </p>
        </div>

        {/* Region Selection */}
        {!selectedRegion && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {regions.map((region) => (
              <div
                key={region.id}
                onClick={() => region.active && setSelectedRegion(region)}
                className={`group relative bg-white/5 backdrop-blur-sm rounded-2xl p-8 border border-white/10 shadow-2xl transition-all duration-500 ${
                  region.active 
                    ? 'hover:shadow-blue-500/25 hover:scale-105 cursor-pointer' 
                    : 'opacity-60 cursor-not-allowed'
                }`}
              >
                <div className={`absolute inset-0 bg-gradient-to-br ${
                  region.active 
                    ? 'from-blue-500/5 to-transparent opacity-0 group-hover:opacity-100' 
                    : 'from-gray-500/5 to-transparent'
                } rounded-2xl transition-opacity duration-500`}></div>
                
                <div className="relative text-center">
                  <div className={`w-20 h-20 ${
                    region.active 
                      ? 'bg-gradient-to-r from-blue-500/20 to-purple-500/20' 
                      : 'bg-gray-500/20'
                  } rounded-2xl flex items-center justify-center mx-auto mb-6 backdrop-blur-sm`}>
                    <span className="text-4xl">
                      {region.code === 'AU' ? '🇦🇺' : 
                       region.code === 'US' ? '🇺🇸' : 
                       region.code === 'BR' ? '🇧🇷' : 
                       region.code === 'ID' ? '🇮🇩' : '🌏'}
                    </span>
                  </div>
                  
                  <h3 className="text-2xl font-bold text-white mb-3">
                    {region.display_name}
                  </h3>
                  
                  {region.coming_soon ? (
                    <div className="space-y-3">
                      <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500/20 rounded-full">
                        <span className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></span>
                        <span className="text-blue-300 font-semibold text-sm">Coming Soon</span>
                      </div>
                      <p className="text-white/40 text-sm">
                        Launching in {region.launch_date || '2026'}
                      </p>
                    </div>
                  ) : (
                    <div>
                      <p className="text-white/60 text-lg mb-6">
                        {getAccessibleCampuses().length} {hasFullAccess ? 'Active' : 'Assigned'} Campus{getAccessibleCampuses().length !== 1 ? 'es' : ''}
                      </p>
                      <div className="flex items-center justify-center gap-2 text-blue-400 font-semibold">
                        <span>View Campuses</span>
                        <span className="text-xl group-hover:translate-x-1 transition-transform duration-300">→</span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Campus Selection (when region is selected) */}
        {selectedRegion && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Australia National Overview for senior leadership */}
            {selectedRegion.code === 'AU' && (userRole === 'senior_leader' || userRole === 'admin' || userRole === 'senior_pastor' || userRole === 'lead_pastor') && (
              <div
                onClick={() => onCampusSelect({ id: 'australia', name: 'Australia', description: 'National Overview', icon: '🇦🇺', isRollup: true })}
                className="group relative bg-white/5 backdrop-blur-sm rounded-2xl p-8 border border-white/10 shadow-2xl hover:shadow-purple-500/25 transition-all duration-500 hover:scale-105 cursor-pointer"
              >
                <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                <div className="relative text-center">
                  <div className="w-20 h-20 bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-2xl flex items-center justify-center mx-auto mb-6 backdrop-blur-sm">
                    <span className="text-4xl">🇦🇺</span>
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-3">
                    Australia
                  </h3>
                  <p className="text-white/60 text-lg mb-6">
                    National Overview
                  </p>
                  <div className="flex items-center justify-center gap-2 text-purple-400 font-semibold">
                    <span>View Dashboard</span>
                    <span className="text-xl group-hover:translate-x-1 transition-transform duration-300">→</span>
                  </div>
                </div>
              </div>
            )}

            {/* Individual Campuses */}
            {getAccessibleCampuses().map((campus) => (
              <div
                key={campus.id}
                onClick={() => onCampusSelect(campus)}
                className="group relative bg-white/5 backdrop-blur-sm rounded-2xl p-8 border border-white/10 shadow-2xl hover:shadow-blue-500/25 transition-all duration-500 hover:scale-105 cursor-pointer"
              >
                <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                <div className="relative text-center">
                  <div className="w-20 h-20 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-2xl flex items-center justify-center mx-auto mb-6 backdrop-blur-sm">
                    <span className="text-4xl">{campus.icon || '⛪'}</span>
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-3">
                    {campus.name}
                  </h3>
                  <p className="text-white/60 text-lg mb-6">
                    {campus.description || 'Campus Ministry Dashboard'}
                  </p>
                  <div className="flex items-center justify-center gap-2 text-blue-400 font-semibold">
                    <span>View Dashboard</span>
                    <span className="text-xl group-hover:translate-x-1 transition-transform duration-300">→</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* User Role Info */}
        <div className="mt-16 text-center">
          <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-8 border border-white/10 shadow-2xl max-w-2xl mx-auto">
            <div className="flex items-center justify-center gap-4 mb-4">
              <div className="w-12 h-12 bg-gradient-to-r from-emerald-500 to-cyan-500 rounded-xl flex items-center justify-center">
                <span className="text-2xl">👤</span>
              </div>
              <div>
                <h3 className="text-2xl font-bold text-white">Your Access Level</h3>
                <p className="text-white/60 text-lg">
                  {userRole === 'senior_leader' || userRole === 'admin' || userRole === 'senior_pastor' || userRole === 'lead_pastor'
                    ? 'Full access to all campus dashboards' 
                    : 'Access to your assigned campus dashboard'
                  }
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* AI Assistant Modal */}
      {showAIModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-3xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto border border-white/10">
            {/* Modal Header */}
            <div className="sticky top-0 bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 px-8 py-6 rounded-t-3xl border-b border-white/10">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                    <span className="text-2xl">🤖</span>
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-white">AI Assistant</h2>
                    <p className="text-white/80 text-sm">Get insights about your campuses and ministry data</p>
                  </div>
                </div>
                <button
                  onClick={() => setShowAIModal(false)}
                  className="text-white/80 hover:text-white text-3xl font-light transition-colors"
                >
                  ×
                </button>
              </div>
            </div>

            {/* Modal Body */}
            <div className="p-8">
              <div className="text-center space-y-6">
                <div className="w-20 h-20 bg-gradient-to-r from-emerald-500/20 to-cyan-500/20 rounded-2xl flex items-center justify-center mx-auto">
                  <span className="text-5xl">🚀</span>
                </div>
                <h3 className="text-2xl font-bold text-white">AI Assistant Available in Campus Dashboards</h3>
                <p className="text-white/60 text-lg max-w-2xl mx-auto">
                  Once you select a campus, you'll have access to the AI Assistant that can:
                </p>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-8">
                  <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/10 text-left">
                    <div className="text-3xl mb-3">📊</div>
                    <h4 className="text-white font-semibold mb-2">Generate Reports</h4>
                    <p className="text-white/60 text-sm">Weekend, monthly, and annual ministry reports</p>
                  </div>
                  
                  <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/10 text-left">
                    <div className="text-3xl mb-3">📈</div>
                    <h4 className="text-white font-semibold mb-2">Analyze Trends</h4>
                    <p className="text-white/60 text-sm">Identify growth patterns and attendance trends</p>
                  </div>
                  
                  <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/10 text-left">
                    <div className="text-3xl mb-3">💡</div>
                    <h4 className="text-white font-semibold mb-2">Get Insights</h4>
                    <p className="text-white/60 text-sm">Ask questions about your ministry data</p>
                  </div>
                  
                  <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/10 text-left">
                    <div className="text-3xl mb-3">🎯</div>
                    <h4 className="text-white font-semibold mb-2">Compare Performance</h4>
                    <p className="text-white/60 text-sm">Benchmark across different time periods</p>
                  </div>
                </div>

                <div className="mt-8 pt-8 border-t border-white/10">
                  <p className="text-white/80 text-lg font-semibold mb-4">
                    👉 Select a campus or region to access the AI Assistant
                  </p>
                  <button
                    onClick={() => setShowAIModal(false)}
                    className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-8 py-4 rounded-2xl font-semibold hover:scale-105 transition-all duration-300 shadow-lg hover:shadow-blue-500/25"
                  >
                    Got it!
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CampusSelector;




