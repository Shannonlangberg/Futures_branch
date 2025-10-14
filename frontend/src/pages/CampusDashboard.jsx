import React, { useState, useEffect } from 'react';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const CampusDashboard = ({ campusId, campusName, isRollup = false, onBackToSelector }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [campusData, setCampusData] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [modalType, setModalType] = useState('');
  const [modalData, setModalData] = useState(null);
  const [dateFilter, setDateFilter] = useState('last_12_months');
  const [customStartDate, setCustomStartDate] = useState('');
  const [customEndDate, setCustomEndDate] = useState('');
  const [showPreviousYear, setShowPreviousYear] = useState(false);
  const [lastRefresh, setLastRefresh] = useState(new Date());
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Debounced effect to prevent rapid API calls when filters change
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      fetchCampusData();
    }, 500); // 500ms debounce

    return () => clearTimeout(timeoutId);
  }, [campusId, dateFilter, customStartDate, customEndDate, showPreviousYear]);

  const fetchCampusData = async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setIsRefreshing(true);
      } else {
        setLoading(true);
      }

      const params = new URLSearchParams({
        campus_id: campusId,
        date_filter: dateFilter,
        custom_start_date: customStartDate,
        custom_end_date: customEndDate,
        show_previous_year: showPreviousYear.toString(),
        _t: Date.now()
      });

      const cacheBuster = `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      const response = await fetch(`/api/dashboard_data_public?campus=${campusId}&date_filter=${dateFilter}&custom_start_date=${customStartDate}&custom_end_date=${customEndDate}&show_previous_year=${showPreviousYear}&_t=${cacheBuster}`);
      const result = await response.json();
      console.log('🔄 Fresh API response received:', result);
      console.log('🔄 Service breakdown in response:', result.service_breakdown);
      setData(result);
      setCampusData(result);
      setLastRefresh(new Date());
    } catch (error) {
      console.error('Error fetching campus data:', error);
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  };

  const handleRefresh = () => {
    // Force clear any cached data
    console.log('🔄 Force refresh triggered');
    setData({});
    setCampusData({});
    
    // Add a small delay to ensure state is cleared
    setTimeout(() => {
      fetchCampusData(true);
    }, 100);
  };

  const openModal = (type, data) => {
    setModalType(type);
    setModalData(data);
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setModalType('');
    setModalData(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-20 h-20 bg-gradient-to-r from-blue-500 to-purple-500 rounded-2xl flex items-center justify-center mx-auto mb-6 animate-pulse">
            <span className="text-4xl">⛪</span>
          </div>
          <div className="text-white text-2xl font-bold mb-2">Loading Campus Dashboard</div>
          <div className="text-white/60 text-lg">Fetching {campusName} data...</div>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-20 h-20 bg-gradient-to-r from-orange-500 to-red-500 rounded-2xl flex items-center justify-center mx-auto mb-6">
            <span className="text-4xl">⚠️</span>
          </div>
          <div className="text-white text-2xl font-bold mb-2">No Data Available</div>
          <div className="text-white/60 text-lg">Unable to load {campusName} data</div>
        </div>
      </div>
    );
  }

  // Determine if we should show averages or totals based on date range
  // For short periods (7 days, 30 days): show totals
  // For longer periods (3 months, 12 months, year, all time): show averages
  const shouldShowAverages = ['last_3_months', 'last_12_months', 'this_year', 'last_year', 'all_time'].includes(dateFilter);
  
  // Calculate percentages and metrics
  const totalPeople = data.stats?.total_people || 0;
  const sundayAttendance = shouldShowAverages 
    ? Math.round(data.stats?.avg_attendance || 0) 
    : (data.stats?.total_attendance || 0); // Average or Total Sunday attendance
  const youthAttendance = shouldShowAverages 
    ? Math.round(data.stats?.avg_youth_attendance || 0) 
    : (data.stats?.youth_attendance || 0); // Average or Total youth attendance
  const totalAttendance = sundayAttendance + youthAttendance; // Weekend = Sunday + Youth
  const attendancePercentage = totalPeople > 0 ? Math.round((totalAttendance / totalPeople) * 100) : 0;
  const connectGroupPercentage = sundayAttendance > 0 ? Math.round((data.stats?.avg_connect_groups || 0) / sundayAttendance * 100) : 0;
  
  // Get service breakdown from the data
  const serviceBreakdown = data.service_breakdown || {};
  console.log('🔍 Service breakdown from API:', serviceBreakdown);
  const services = Object.keys(serviceBreakdown).map(service => ({
    name: service,
    attendance: serviceBreakdown[service]?.average || 0,
    count: serviceBreakdown[service]?.count || 0
  }));
  console.log('🔍 Processed services array:', services);

  return (
    <div key={`campus-dashboard-${campusId}-${lastRefresh.getTime()}`} className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Animated Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-purple-500/10 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-pink-500/5 rounded-full blur-3xl animate-pulse delay-500"></div>
      </div>

      {/* Header */}
      <div className="relative bg-gradient-to-r from-blue-600/90 via-purple-600/90 to-pink-600/90 backdrop-blur-sm border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6">
            <div className="flex-1">
              <div className="flex items-center gap-4 mb-4">
                {onBackToSelector && (
                  <button
                    onClick={onBackToSelector}
                    className="group relative bg-gradient-to-r from-slate-600 to-slate-700 text-white px-6 py-3 rounded-2xl font-semibold hover:scale-105 transition-all duration-300 shadow-lg hover:shadow-slate-500/25 overflow-hidden"
                  >
                    <div className="relative flex items-center gap-3">
                      <span className="text-xl">←</span>
                      <span>Back to Campuses</span>
                    </div>
                  </button>
                )}
                <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                  <span className="text-2xl">⛪</span>
                </div>
                <div>
                  <h1 className="text-4xl lg:text-5xl font-bold text-white tracking-tight">
                    {isRollup ? 'Australia' : campusName}
                  </h1>
                  <p className="text-white/80 text-lg font-medium">
                    {isRollup ? 'National Ministry Overview' : 'Campus Ministry Dashboard'}
                  </p>
                </div>
              </div>
            </div>
            
            <div className="flex flex-col lg:flex-row gap-4">
              {/* Date Range Selector */}
              <div className="flex flex-col sm:flex-row gap-3">
                <select
                  value={dateFilter}
                  onChange={(e) => setDateFilter(e.target.value)}
                  className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl px-4 py-3 text-white font-medium focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400/50 transition-all duration-300"
                >
                  <option value="last_7_days" className="bg-slate-800 text-white">Last 7 Days</option>
                  <option value="last_30_days" className="bg-slate-800 text-white">Last 30 Days</option>
                  <option value="last_3_months" className="bg-slate-800 text-white">Last 3 Months</option>
                  <option value="last_6_months" className="bg-slate-800 text-white">Last 6 Months</option>
                  <option value="last_12_months" className="bg-slate-800 text-white">Last 12 Months</option>
                  <option value="last_2_years" className="bg-slate-800 text-white">Last 2 Years</option>
                  <option value="custom" className="bg-slate-800 text-white">Custom Range</option>
                </select>

                {dateFilter === 'custom' && (
                  <div className="flex flex-col sm:flex-row gap-2">
                    <input
                      type="date"
                      value={customStartDate}
                      onChange={(e) => setCustomStartDate(e.target.value)}
                      className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl px-4 py-3 text-white font-medium focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400/50 transition-all duration-300"
                      placeholder="Start Date"
                    />
                    <input
                      type="date"
                      value={customEndDate}
                      onChange={(e) => setCustomEndDate(e.target.value)}
                      className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl px-4 py-3 text-white font-medium focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400/50 transition-all duration-300"
                      placeholder="End Date"
                    />
                  </div>
                )}

              </div>

              <div className="text-right">
                <div className="text-white/60 text-sm">Last Updated</div>
                <div className="text-white font-medium">
                  {lastRefresh.toLocaleTimeString()}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="relative max-w-7xl mx-auto px-6 py-8">
        {/* Campus Cards Grid */}
        <div className="mb-12">
          <div className="flex items-center gap-4 mb-8">
            <div className="w-1 h-12 bg-gradient-to-b from-blue-400 to-purple-400 rounded-full"></div>
            <div>
              <h2 className="text-3xl font-bold text-white">
                Campus Overview
              </h2>
              <p className="text-white/60 text-lg">
                {isRollup ? 'All campuses combined' : `${campusName} ministry metrics`}
              </p>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {/* Campus Overview */}
            <div 
              className="group relative bg-gradient-to-br from-[#62B4FF]/20 to-[#5D1FEC]/20 backdrop-blur-sm rounded-2xl p-6 border border-[#62B4FF]/20 shadow-2xl hover:shadow-[#62B4FF]/25 transition-all duration-500 hover:scale-105 cursor-pointer"
              onClick={() => openModal('campus-overview', { 
                total: totalPeople,
                dreamTeam: Math.round(data.stats?.avg_dream_team || 0),
                baptisms: data.stats?.baptisms || 0,
                childDedications: data.stats?.child_dedications || 0,
                campus: campusName 
              })}
            >
              <div className="absolute inset-0 bg-gradient-to-br from-[#62B4FF]/10 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="relative">
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 bg-[#62B4FF]/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                    <span className="text-2xl">🏢</span>
                  </div>
                  <div className="text-[#62B4FF] text-sm font-semibold">Overview</div>
                </div>
                <h3 className="text-white/80 text-sm font-medium mb-2">Campus Overview</h3>
                <div className="text-4xl font-bold text-white mb-2">
                  {totalPeople.toLocaleString()}
                </div>
                <p className="text-[#62B4FF]/80 text-sm">
                  Total registered people
                </p>
              </div>
            </div>

            {/* Total Weekend Attendance */}
            <div 
              className="group relative bg-gradient-to-br from-[#AC9B25]/20 to-[#FF8432]/20 backdrop-blur-sm rounded-2xl p-6 border border-[#AC9B25]/20 shadow-2xl hover:shadow-[#AC9B25]/25 transition-all duration-500 hover:scale-105 cursor-pointer"
              onClick={() => openModal('weekend-attendance', { 
                total: totalAttendance,
                sunday: sundayAttendance,
                youth: youthAttendance,
                percentage: attendancePercentage,
                campus: campusName
              })}
            >
              <div className="absolute inset-0 bg-gradient-to-br from-[#AC9B25]/10 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="relative">
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 bg-[#AC9B25]/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                    <span className="text-2xl">📅</span>
                  </div>
                  <div className="text-[#AC9B25] text-sm font-semibold">Weekend</div>
                </div>
                <h3 className="text-white/80 text-sm font-medium mb-2">Total Weekend Attendance</h3>
                <div className="text-4xl font-bold text-white mb-2">
                  {totalAttendance.toLocaleString()}
                </div>
                <p className="text-[#AC9B25]/80 text-sm">
                  {shouldShowAverages ? 'Average weekly' : 'Total this period'}
                </p>
              </div>
            </div>

            {/* Sunday Attendance */}
            <div 
              className="group relative bg-gradient-to-br from-purple-500/20 to-purple-600/20 backdrop-blur-sm rounded-2xl p-6 border border-purple-400/20 shadow-2xl hover:shadow-purple-500/25 transition-all duration-500 hover:scale-105 cursor-pointer"
              onClick={() => {
                console.log('Sunday Attendance clicked - services data:', services);
                console.log('Service breakdown from data:', data.service_breakdown);
                openModal('sunday-attendance', { 
                  total: sundayAttendance, 
                  services: services,
                  campus: campusName,
                  serviceBreakdown: data.service_breakdown
                });
              }}
            >
              <div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="relative">
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 bg-purple-500/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                    <span className="text-2xl">⛪</span>
                  </div>
                  <div className="text-purple-400 text-sm font-semibold">Sunday</div>
                </div>
                <h3 className="text-white/80 text-sm font-medium mb-2">Sunday Attendance</h3>
                <div className="text-4xl font-bold text-white mb-2">
                  {sundayAttendance.toLocaleString()}
                </div>
                <p className="text-purple-200/80 text-sm">
                  {shouldShowAverages ? 'Average weekly' : (services.length > 1 ? `${services.length} services` : 'Total this period')}
                </p>
              </div>
            </div>

            {/* Souls */}
            <div 
              className="group relative bg-gradient-to-br from-red-500/20 to-red-600/20 backdrop-blur-sm rounded-2xl p-6 border border-red-400/20 shadow-2xl hover:shadow-red-500/25 transition-all duration-500 hover:scale-105 cursor-pointer"
              onClick={() => openModal('souls', { 
                total: (data.stats?.first_time_christians || 0) + (data.stats?.youth_salvations || 0) + (data.stats?.new_kids_salvations || 0),
                youth: data.stats?.youth_salvations || 0,
                adults: data.stats?.first_time_christians || 0,
                rededications: data.stats?.rededications || 0,
                kids: data.stats?.new_kids_salvations || 0,
                campus: campusName 
              })}
            >
              <div className="absolute inset-0 bg-gradient-to-br from-red-500/10 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="relative">
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 bg-red-500/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                    <span className="text-2xl">✝️</span>
                  </div>
                  <div className="text-red-400 text-sm font-semibold">Souls</div>
                </div>
                <h3 className="text-white/80 text-sm font-medium mb-2">Souls Saved</h3>
                <div className="text-4xl font-bold text-white mb-2">
                  {((data.stats?.first_time_christians || 0) + (data.stats?.youth_salvations || 0) + (data.stats?.new_kids_salvations || 0)).toLocaleString()}
                </div>
                <p className="text-red-200/80 text-sm">
                  All spiritual decisions
                </p>
              </div>
            </div>

            {/* Just Visiting */}
            <div 
              className="group relative bg-gradient-to-br from-orange-500/20 to-orange-600/20 backdrop-blur-sm rounded-2xl p-6 border border-orange-400/20 shadow-2xl hover:shadow-orange-500/25 transition-all duration-500 hover:scale-105 cursor-pointer"
              onClick={() => openModal('new-people', { 
                total: data.stats?.new_people || 0,
                firstTime: data.stats?.first_time_visitors || 0,
                visiting: data.stats?.visitors || 0,
                infoGathered: data.stats?.information_gathered || 0,
                campus: campusName 
              })}
            >
              <div className="absolute inset-0 bg-gradient-to-br from-orange-500/10 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="relative">
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 bg-orange-500/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                    <span className="text-2xl">🆕</span>
                  </div>
                  <div className="text-orange-400 text-sm font-semibold">Growth</div>
                </div>
                <h3 className="text-white/80 text-sm font-medium mb-2">New People</h3>
                <div className="text-4xl font-bold text-white mb-2">
                  {(data.stats?.new_people || 0).toLocaleString()}
                </div>
                <p className="text-orange-200/80 text-sm">
                  First-time + visiting
                </p>
              </div>
            </div>

            {/* Kids */}
            <div 
              className="group relative bg-gradient-to-br from-pink-500/20 to-pink-600/20 backdrop-blur-sm rounded-2xl p-6 border border-pink-400/20 shadow-2xl hover:shadow-pink-500/25 transition-all duration-500 hover:scale-105 cursor-pointer"
              onClick={() => openModal('kids', { 
                attendance: shouldShowAverages ? Math.round(data.stats?.avg_kids_attendance || 0) : (data.stats?.kids_attendance || 0),
                leaders: Math.round(data.stats?.avg_kids_leaders || 0),
                newKids: data.stats?.new_kids || 0,
                salvations: data.stats?.new_kids_salvations || 0,
                campus: campusName,
                kidsServiceBreakdown: data.service_breakdown?.kids || {}
              })}
            >
              <div className="absolute inset-0 bg-gradient-to-br from-pink-500/10 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="relative">
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 bg-pink-500/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                    <span className="text-2xl">🧒</span>
                  </div>
                  <div className="text-pink-400 text-sm font-semibold">Kids</div>
                </div>
                <h3 className="text-white/80 text-sm font-medium mb-2">Kids Attendance</h3>
                <div className="text-4xl font-bold text-white mb-2">
                  {(shouldShowAverages ? Math.round(data.stats?.avg_kids_attendance || 0) : (data.stats?.kids_attendance || 0)).toLocaleString()}
                </div>
                <p className="text-pink-200/80 text-sm">
                  {Math.round(data.stats?.avg_kids_leaders || 0)} leaders serving
                </p>
              </div>
            </div>

            {/* Youth */}
            <div 
              className="group relative bg-gradient-to-br from-indigo-500/20 to-indigo-600/20 backdrop-blur-sm rounded-2xl p-6 border border-indigo-400/20 shadow-2xl hover:shadow-indigo-500/25 transition-all duration-500 hover:scale-105 cursor-pointer"
              onClick={() => openModal('youth', { 
                attendance: shouldShowAverages ? Math.round(data.stats?.avg_youth_attendance || 0) : (data.stats?.youth_attendance || 0),
                salvations: data.stats?.youth_salvations || 0,
                newPeople: data.stats?.youth_new_people || 0,
                campus: campusName 
              })}
            >
              <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/10 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="relative">
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 bg-indigo-500/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                    <span className="text-2xl">🎯</span>
                  </div>
                  <div className="text-indigo-400 text-sm font-semibold">Youth</div>
                </div>
                <h3 className="text-white/80 text-sm font-medium mb-2">Youth Ministry</h3>
                <div className="text-4xl font-bold text-white mb-2">
                  {(shouldShowAverages ? Math.round(data.stats?.avg_youth_attendance || 0) : (data.stats?.youth_attendance || 0)).toLocaleString()}
                </div>
                <p className="text-indigo-200/80 text-sm">
                  {data.stats?.youth_salvations || 0} salvations
                </p>
              </div>
            </div>

            {/* Giving */}
            <div 
              className="group relative bg-gradient-to-br from-yellow-500/20 to-yellow-600/20 backdrop-blur-sm rounded-2xl p-6 border border-yellow-400/20 shadow-2xl hover:shadow-yellow-500/25 transition-all duration-500 hover:scale-105 cursor-pointer"
              onClick={() => openModal('giving', { 
                total: data.stats?.tithe || 0,
                average: data.stats?.avg_tithe || 0,
                breakdown: data.tithe_breakdown || {general: 0, trust: 0, online: 0, building: 0},
                campus: campusName 
              })}
            >
              <div className="absolute inset-0 bg-gradient-to-br from-yellow-500/10 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="relative">
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 bg-yellow-500/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                    <span className="text-2xl">💰</span>
                  </div>
                  <div className="text-yellow-400 text-sm font-semibold">Finance</div>
                </div>
                <h3 className="text-white/80 text-sm font-medium mb-2">Average Giving</h3>
                <div className="text-4xl font-bold text-white mb-2">
                  ${((data.tithe_breakdown?.general || 0) + (data.tithe_breakdown?.trust || 0) + (data.tithe_breakdown?.online || 0)).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                </div>
                <p className="text-yellow-200/80 text-sm">
                  Financial stewardship
                </p>
              </div>
            </div>

            {/* Connect Groups */}
            <div 
              className="group relative bg-gradient-to-br from-cyan-500/20 to-cyan-600/20 backdrop-blur-sm rounded-2xl p-6 border border-cyan-400/20 shadow-2xl hover:shadow-cyan-500/25 transition-all duration-500 hover:scale-105 cursor-pointer"
              onClick={() => openModal('connect-groups', { 
                total: Math.round(data.stats?.avg_connect_groups || 0),
                percentage: connectGroupPercentage,
                sundayAttendance: sundayAttendance,
                campus: campusName 
              })}
            >
              <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/10 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="relative">
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 bg-cyan-500/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                    <span className="text-2xl">🤝</span>
                  </div>
                  <div className="text-cyan-400 text-sm font-semibold">Community</div>
                </div>
                <h3 className="text-white/80 text-sm font-medium mb-2">Total Connect Group Attendance</h3>
                <div className="text-4xl font-bold text-white mb-2">
                  {Math.round(data.stats?.avg_connect_groups || 0).toLocaleString()}
                </div>
                <p className="text-cyan-200/80 text-sm">
                  {connectGroupPercentage}% of Sunday attendance
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Insights and Charts */}
        <div className="mb-12">
          <div className="flex items-center gap-4 mb-8">
            <div className="w-1 h-12 bg-gradient-to-b from-emerald-400 to-cyan-400 rounded-full"></div>
            <div>
              <h2 className="text-3xl font-bold text-white">
                Campus Insights
              </h2>
              <p className="text-white/60 text-lg">
                Detailed analytics and trends for {campusName}
              </p>
            </div>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Connect Groups Percentage */}
            <div className="group relative bg-white/5 backdrop-blur-sm rounded-2xl p-8 border border-white/10 shadow-2xl hover:shadow-cyan-500/10 transition-all duration-500">
              <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="relative">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-cyan-500/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                      <span className="text-xl">📊</span>
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-white">Connect Groups Engagement</h3>
                      <p className="text-white/60 text-sm">Percentage of Sunday attendance</p>
                    </div>
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-6xl font-bold text-cyan-400 mb-4">
                    {connectGroupPercentage}%
                  </div>
                  <div className="w-full bg-white/10 rounded-full h-4 mb-4">
                    <div 
                      className="bg-gradient-to-r from-cyan-500 to-blue-500 h-4 rounded-full transition-all duration-1000"
                      style={{ width: `${Math.min(connectGroupPercentage, 100)}%` }}
                    ></div>
                  </div>
                  <p className="text-white/60 text-sm">
                    {Math.round(data.stats?.avg_connect_groups || 0)} in groups out of {sundayAttendance} Sunday attendees
                  </p>
                </div>
              </div>
            </div>

            {/* Attendance Trends */}
            <div className="group relative bg-white/5 backdrop-blur-sm rounded-2xl p-8 border border-white/10 shadow-2xl hover:shadow-blue-500/10 transition-all duration-500">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="relative">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-blue-500/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                      <span className="text-xl">📈</span>
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-white">Attendance YTD</h3>
                      <p className="text-white/60 text-sm">Year-to-date attendance trends</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={showPreviousYear}
                        onChange={(e) => setShowPreviousYear(e.target.checked)}
                        className="w-4 h-4 text-blue-500 bg-white/10 border-white/20 rounded focus:ring-blue-500 focus:ring-2"
                      />
                      <span className="text-white/80 text-sm">Show previous year</span>
                    </label>
                  </div>
                </div>
                <div className="h-64">
                  <Line 
                    data={{
                      labels: data.chart_data?.labels || [],
                      datasets: [
                        {
                          label: 'Attendance YTD',
                          data: data.chart_data?.attendance || [],
                          borderColor: '#3b82f6',
                          backgroundColor: 'rgba(59, 130, 246, 0.1)',
                          borderWidth: 3,
                          tension: 0.4,
                          fill: true,
                          pointRadius: 5,
                          pointHoverRadius: 7,
                          pointBackgroundColor: '#3b82f6',
                          pointBorderColor: '#ffffff',
                          pointBorderWidth: 2
                        },
                        ...(showPreviousYear ? [{
                          label: 'Previous Year',
                          data: data.chart_data?.attendance_previous_year || [],
                          borderColor: '#94a3b8',
                          backgroundColor: 'rgba(148, 163, 184, 0.1)',
                          borderWidth: 2,
                          tension: 0.4,
                          fill: false,
                          borderDash: [5, 5],
                          pointRadius: 4,
                          pointHoverRadius: 6,
                          pointBackgroundColor: '#94a3b8',
                          pointBorderColor: '#ffffff',
                          pointBorderWidth: 2
                        }] : [])
                      ]
                    }} 
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          labels: {
                            color: 'rgba(255, 255, 255, 0.8)'
                          }
                        }
                      },
                      scales: {
                        x: {
                          ticks: {
                            color: 'rgba(255, 255, 255, 0.6)'
                          },
                          grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                          }
                        },
                        y: {
                          ticks: {
                            color: 'rgba(255, 255, 255, 0.6)'
                          },
                          grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                          }
                        }
                      }
                    }} 
                  />
                </div>
              </div>
            </div>

            {/* Tithe YTD Chart */}
            <div className="group relative bg-white/5 backdrop-blur-sm rounded-2xl p-8 border border-white/10 shadow-2xl hover:shadow-green-500/10 transition-all duration-500">
              <div className="absolute inset-0 bg-gradient-to-br from-green-500/5 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="relative">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-green-500/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                      <span className="text-xl">💰</span>
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-white">Tithe YTD</h3>
                      <p className="text-white/60 text-sm">Year-to-date giving with comparison</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="flex items-center gap-2 text-sm text-white/80">
                      <input
                        type="checkbox"
                        checked={showPreviousYear}
                        onChange={(e) => setShowPreviousYear(e.target.checked)}
                        className="w-4 h-4 text-green-500 bg-white/10 border-white/20 rounded focus:ring-green-500 focus:ring-2"
                      />
                      Show Previous Year
                    </label>
                  </div>
                </div>
                <div className="h-64">
                  <Line 
                    data={{
                      labels: data.chart_data?.tithe_labels || ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                      datasets: [
                        {
                          label: '2025 YTD',
                          data: data.chart_data?.tithe_ytd || [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                          borderColor: '#10b981',
                          backgroundColor: 'rgba(16, 185, 129, 0.1)',
                          borderWidth: 3,
                          tension: 0.4,
                          fill: true,
                          pointRadius: 5,
                          pointHoverRadius: 7,
                          pointBackgroundColor: '#10b981',
                          pointBorderColor: '#ffffff',
                          pointBorderWidth: 2
                        },
                        ...(showPreviousYear ? [{
                          label: '2024',
                          data: data.chart_data?.tithe_previous_year || [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                          borderColor: '#6b7280',
                          backgroundColor: 'rgba(107, 114, 128, 0.1)',
                          borderWidth: 2,
                          tension: 0.4,
                          fill: false,
                          borderDash: [5, 5],
                          pointRadius: 4,
                          pointHoverRadius: 6,
                          pointBackgroundColor: '#6b7280',
                          pointBorderColor: '#ffffff',
                          pointBorderWidth: 2
                        }] : [])
                      ]
                    }} 
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          labels: {
                            color: 'rgba(255, 255, 255, 0.8)'
                          }
                        }
                      },
                      scales: {
                        x: {
                          ticks: {
                            color: 'rgba(255, 255, 255, 0.6)'
                          },
                          grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                          }
                        },
                        y: {
                          ticks: {
                            color: 'rgba(255, 255, 255, 0.6)',
                            callback: function(value) {
                              return '$' + value.toLocaleString();
                            }
                          },
                          grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                          }
                        }
                      }
                    }} 
                  />
                </div>
                <div className="mt-4 flex justify-between items-center text-sm">
                  <div className="text-white/60">
                    Current YTD: <span className="text-green-400 font-semibold">
                      ${(data.stats?.tithe_ytd || 0).toLocaleString()}
                    </span>
                  </div>
                  {showPreviousYear && (
                    <div className="text-white/60">
                      Previous Year: <span className="text-gray-400 font-semibold">
                        ${(data.stats?.tithe_previous_year || 0).toLocaleString()}
                      </span>
                    </div>
                  )}
                </div>
                {showPreviousYear && (
                  <div className="mt-2 text-center">
                    <div className="text-white/60 text-sm">
                      % Increase YTD: <span className={`font-semibold ${(() => {
                        const current = data.stats?.tithe_ytd || 0;
                        const previous = data.stats?.tithe_previous_year || 0;
                        if (previous === 0) return 'text-gray-400';
                        const increase = ((current - previous) / previous) * 100;
                        return increase >= 0 ? 'text-green-400' : 'text-red-400';
                      })()}`}>
                        {(() => {
                          const current = data.stats?.tithe_ytd || 0;
                          const previous = data.stats?.tithe_previous_year || 0;
                          if (previous === 0) return '0%';
                          const increase = ((current - previous) / previous) * 100;
                          return `${increase >= 0 ? '+' : ''}${increase.toFixed(1)}%`;
                        })()}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Modal for Drill-down Details */}
      {showModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-gradient-to-br from-slate-900/95 to-slate-800/95 backdrop-blur-xl rounded-3xl p-8 max-w-4xl w-full max-h-[90vh] overflow-y-auto border border-white/10 shadow-2xl">
            <div className="flex justify-between items-start mb-8">
              <div>
                <h2 className="text-3xl font-bold text-white">
                  {modalType.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())} Details
                </h2>
                <p className="text-white/60 text-lg mt-1">
                  {campusName} - Detailed Breakdown
                </p>
              </div>
              <button
                onClick={closeModal}
                className="w-10 h-10 bg-white/10 hover:bg-white/20 rounded-xl flex items-center justify-center text-white/60 hover:text-white transition-all duration-300"
              >
                <span className="text-xl">×</span>
              </button>
            </div>

            <div className="space-y-6">
              {modalType === 'campus-overview' && (
                <div className="space-y-6">
                  <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
                    <h3 className="text-xl font-bold text-white mb-4">Campus Overview</h3>
                    <div className="text-4xl font-bold text-[#62B4FF] mb-2">
                      {modalData.total.toLocaleString()}
                    </div>
                    <p className="text-white/60">Total on database in {modalData.campus}</p>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
                      <h3 className="text-xl font-bold text-white mb-4">Dream Team</h3>
                      <div className="text-4xl font-bold text-[#FF8432] mb-2">
                        {modalData.dreamTeam.toLocaleString()}
                      </div>
                      <p className="text-white/60">Average volunteers serving this period</p>
                    </div>
                    <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
                      <h3 className="text-xl font-bold text-white mb-4">Baptisms</h3>
                      <div className="text-4xl font-bold text-[#E43CB9] mb-2">
                        {modalData.baptisms.toLocaleString()}
                      </div>
                      <p className="text-white/60">People baptized this period</p>
                    </div>
                    <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
                      <h3 className="text-xl font-bold text-white mb-4">Child Dedications</h3>
                      <div className="text-4xl font-bold text-[#5D1FEC] mb-2">
                        {modalData.childDedications.toLocaleString()}
                      </div>
                      <p className="text-white/60">Children dedicated this period</p>
                    </div>
                  </div>
                </div>
              )}

              {modalType === 'sunday-attendance' && (
                <div className="space-y-6">
                  <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
                    <h3 className="text-xl font-bold text-white mb-4">Sunday Service Breakdown</h3>
                    <div className="text-4xl font-bold text-purple-400 mb-2">
                      {modalData.total.toLocaleString()}
                    </div>
                    <p className="text-white/60">
                      {isRollup 
                        ? 'Average Sunday attendance across all campuses (excluding youth)' 
                        : 'Total Sunday attendance (excluding youth)'}
                    </p>
                  </div>
                  
                  {!isRollup && (() => {
                    // Only show service breakdown for individual campuses, not rollup views
                    // Get service breakdowns from data
                    const adultBreakdown = data.service_breakdown || {};
                    const kidsBreakdown = data.kids_service_breakdown || {};
                    
                    console.log('Adult breakdown:', adultBreakdown);
                    console.log('Kids breakdown:', kidsBreakdown);
                    
                    // Get all service times from both breakdowns
                    const allServiceTimes = new Set([
                      ...Object.keys(adultBreakdown),
                      ...Object.keys(kidsBreakdown)
                    ]);
                    
                    if (allServiceTimes.size > 0) {
                      return (
                        <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
                          <h3 className="text-xl font-bold text-white mb-4">Service Breakdown</h3>
                          <div className="space-y-4">
                            {Array.from(allServiceTimes).sort().map((serviceTime, index) => {
                              const adultData = adultBreakdown[serviceTime] || { average: 0, count: 0 };
                              const kidsData = kidsBreakdown[serviceTime] || { average: 0, count: 0 };
                              const adultAvg = Math.round(adultData.average || 0);
                              const kidsAvg = Math.round(kidsData.average || 0);
                              const totalAvg = adultAvg + kidsAvg;
                              const serviceCount = Math.max(adultData.count || 0, kidsData.count || 0);
                              
                              return (
                                <div key={index} className="p-4 bg-white/5 rounded-xl">
                                  <div className="flex justify-between items-center mb-3">
                                    <div>
                                      <div className="text-lg font-semibold text-white">{serviceTime}</div>
                                      <div className="text-sm text-white/60">{serviceCount} services</div>
                                    </div>
                                    <div className="text-2xl font-bold text-purple-400">
                                      {totalAvg.toLocaleString()}
                                    </div>
                                  </div>
                                  <div className="grid grid-cols-3 gap-4 mt-3 pt-3 border-t border-white/10">
                                    <div className="text-center">
                                      <div className="text-xs text-white/50 mb-1">Adults</div>
                                      <div className="text-lg font-semibold text-blue-400">{adultAvg.toLocaleString()}</div>
                                    </div>
                                    <div className="text-center">
                                      <div className="text-xs text-white/50 mb-1">Kids</div>
                                      <div className="text-lg font-semibold text-pink-400">{kidsAvg.toLocaleString()}</div>
                                    </div>
                                    <div className="text-center">
                                      <div className="text-xs text-white/50 mb-1">Total</div>
                                      <div className="text-lg font-semibold text-purple-400">{totalAvg.toLocaleString()}</div>
                                    </div>
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      );
                    }
                    return null;
                  })()}
                </div>
              )}

              {modalType === 'weekend-attendance' && (
                <div className="space-y-6">
                  <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
                    <h3 className="text-xl font-bold text-white mb-4">Weekend Attendance Breakdown</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="bg-purple-500/10 rounded-xl p-4 border border-purple-400/20">
                        <h4 className="text-lg font-semibold text-purple-300 mb-2">Sunday Services</h4>
                        <div className="text-3xl font-bold text-purple-400 mb-1">
                          {sundayAttendance.toLocaleString()}
                        </div>
                        <p className="text-purple-200/80 text-sm">Average Sunday attendance</p>
                      </div>
                      <div className="bg-blue-500/10 rounded-xl p-4 border border-blue-400/20">
                        <h4 className="text-lg font-semibold text-blue-300 mb-2">Youth Friday</h4>
                        <div className="text-3xl font-bold text-blue-400 mb-1">
                          {youthAttendance.toLocaleString()}
                        </div>
                        <p className="text-blue-200/80 text-sm">Average youth attendance</p>
                      </div>
                    </div>
                    <div className="mt-6 pt-4 border-t border-white/10">
                      <div className="flex justify-between items-center">
                        <span className="text-lg font-semibold text-white">Average Weekend</span>
                        <div className="text-2xl font-bold text-emerald-400">
                          {totalAttendance.toLocaleString()}
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  {!isRollup && (() => {
                    // Only show service breakdown for individual campuses, not rollup views
                    // Try to get services from modalData or fallback to data
                    let servicesToShow = modalData.services;
                    
                    // If no services in modalData, try to build from serviceBreakdown
                    if (!servicesToShow || servicesToShow.length === 0) {
                      const serviceBreakdown = modalData.serviceBreakdown || data.service_breakdown || {};
                      servicesToShow = Object.keys(serviceBreakdown).map(service => ({
                        name: service,
                        attendance: serviceBreakdown[service]?.average || 0,
                        count: serviceBreakdown[service]?.count || 0
                      }));
                    }
                    
                    if (servicesToShow && servicesToShow.length > 0) {
                      return (
                        <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
                          <h3 className="text-xl font-bold text-white mb-4">Service Breakdown</h3>
                          <div className="space-y-4">
                            {servicesToShow.map((service, index) => (
                              <div key={index} className="flex justify-between items-center p-4 bg-white/5 rounded-xl">
                                <div>
                                  <div className="text-lg font-semibold text-white">{service.name}</div>
                                  <div className="text-sm text-white/60">{service.count} services</div>
                                </div>
                                <div className="text-2xl font-bold text-purple-400">
                                  {Math.round(service.attendance).toLocaleString()}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      );
                    }
                    return null;
                  })()}
                  
                  <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
                    <h3 className="text-xl font-bold text-white mb-4">Engagement Rate</h3>
                    <div className="text-4xl font-bold text-cyan-400 mb-2">
                      {modalData.percentage}%
                    </div>
                    <p className="text-white/60">Attendance/Campus total</p>
                  </div>
                </div>
              )}

              {modalType === 'souls' && (
                <div className="space-y-6">
                  <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
                    <h3 className="text-xl font-bold text-white mb-4">Total Souls</h3>
                    <div className="text-4xl font-bold text-red-400 mb-2">
                      {modalData.total.toLocaleString()}
                    </div>
                    <p className="text-white/60">All spiritual decisions made</p>
                  </div>
                  
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
              <h3 className="text-xl font-bold text-white mb-4">Adult Salvations</h3>
              <div className="text-4xl font-bold text-orange-400 mb-2">
                {modalData.adults.toLocaleString()}
              </div>
              <p className="text-white/60">Adults saved</p>
            </div>
            <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
              <h3 className="text-xl font-bold text-white mb-4">Youth Salvations</h3>
              <div className="text-4xl font-bold text-purple-400 mb-2">
                {modalData.youth.toLocaleString()}
              </div>
              <p className="text-white/60">Young people saved</p>
            </div>
            <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
              <h3 className="text-xl font-bold text-white mb-4">Kids Salvations</h3>
              <div className="text-4xl font-bold text-green-400 mb-2">
                {modalData.kids.toLocaleString()}
              </div>
              <p className="text-white/60">Children saved</p>
            </div>
            <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
              <h3 className="text-xl font-bold text-white mb-4">Rededications</h3>
              <div className="text-4xl font-bold text-blue-400 mb-2">
                {modalData.rededications.toLocaleString()}
              </div>
              <p className="text-white/60">People recommitting</p>
            </div>
          </div>
                </div>
              )}

              {modalType === 'new-people' && (
                <div className="space-y-6">
                  <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
                    <h3 className="text-xl font-bold text-white mb-4">Total New People</h3>
                    <div className="text-4xl font-bold text-orange-400 mb-2">
                      {modalData.total.toLocaleString()}
                    </div>
                    <p className="text-white/60">Total new people this period</p>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
                      <h3 className="text-xl font-bold text-white mb-4">First-Time Visitors</h3>
                      <div className="text-4xl font-bold text-blue-400 mb-2">
                        {modalData.firstTime.toLocaleString()}
                      </div>
                      <p className="text-white/60">First time at church</p>
                    </div>
                    <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
                      <h3 className="text-xl font-bold text-white mb-4">Visitors</h3>
                      <div className="text-4xl font-bold text-purple-400 mb-2">
                        {modalData.visiting.toLocaleString()}
                      </div>
                      <p className="text-white/60">Just visiting</p>
                    </div>
                    <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
                      <h3 className="text-xl font-bold text-white mb-4">Info Gathered</h3>
                      <div className="text-4xl font-bold text-green-400 mb-2">
                        {modalData.infoGathered.toLocaleString()}
                      </div>
                      <p className="text-white/60">Contact information collected</p>
                    </div>
                  </div>
                </div>
              )}

              {modalType === 'kids' && (
                <div className="space-y-6">
                  <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
                    <h3 className="text-xl font-bold text-white mb-4">Kids Ministry Overview</h3>
                    <div className="text-4xl font-bold text-pink-400 mb-2">
                      {modalData.attendance.toLocaleString()}
                    </div>
                    <p className="text-white/60">Average kids attendance this period</p>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
                      <h3 className="text-xl font-bold text-white mb-4">Kids Attendance</h3>
                      <div className="text-4xl font-bold text-pink-400 mb-2">
                        {modalData.attendance.toLocaleString()}
                      </div>
                      <p className="text-white/60">Average children in attendance</p>
                    </div>
                    <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
                      <h3 className="text-xl font-bold text-white mb-4">Kids Leaders</h3>
                      <div className="text-4xl font-bold text-purple-400 mb-2">
                        {modalData.leaders.toLocaleString()}
                      </div>
                      <p className="text-white/60">Average volunteers serving</p>
                    </div>
                    <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
                      <h3 className="text-xl font-bold text-white mb-4">New Kids</h3>
                      <div className="text-4xl font-bold text-orange-400 mb-2">
                        {modalData.newKids.toLocaleString()}
                      </div>
                      <p className="text-white/60">Total new children this period</p>
                    </div>
                    <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
                      <h3 className="text-xl font-bold text-white mb-4">Kids Salvations</h3>
                      <div className="text-4xl font-bold text-green-400 mb-2">
                        {modalData.salvations.toLocaleString()}
                      </div>
                      <p className="text-white/60">Total children saved this period</p>
                    </div>
                  </div>
                  
                  {modalData.kidsServiceBreakdown && Object.keys(modalData.kidsServiceBreakdown).length > 0 && (
                    <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
                      <h3 className="text-xl font-bold text-white mb-4">Kids by Service Time</h3>
                      <div className="space-y-4">
                        {Object.entries(modalData.kidsServiceBreakdown).map(([serviceTime, data]) => (
                          data.count > 0 && (
                            <div key={serviceTime} className="flex justify-between items-center p-4 bg-white/5 rounded-xl">
                              <div>
                                <div className="text-lg font-semibold text-white">{serviceTime}</div>
                                <div className="text-sm text-white/60">{data.count} services</div>
                              </div>
                              <div className="text-2xl font-bold text-pink-400">
                                {Math.round(data.average).toLocaleString()}
                              </div>
                            </div>
                          )
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {modalType === 'youth' && (
                <div className="space-y-6">
                  <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
                    <h3 className="text-xl font-bold text-white mb-4">Youth Ministry Overview</h3>
                    <div className="text-4xl font-bold text-indigo-400 mb-2">
                      {modalData.attendance.toLocaleString()}
                    </div>
                    <p className="text-white/60">Average youth attendance this period</p>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
                      <h3 className="text-xl font-bold text-white mb-4">Youth Attendance</h3>
                      <div className="text-4xl font-bold text-indigo-400 mb-2">
                        {modalData.attendance.toLocaleString()}
                      </div>
                      <p className="text-white/60">Average young people in attendance</p>
                    </div>
                    <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
                      <h3 className="text-xl font-bold text-white mb-4">Youth Salvations</h3>
                      <div className="text-4xl font-bold text-purple-400 mb-2">
                        {modalData.salvations.toLocaleString()}
                      </div>
                      <p className="text-white/60">Total young people saved this period</p>
                    </div>
                    <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
                      <h3 className="text-xl font-bold text-white mb-4">Youth New People</h3>
                      <div className="text-4xl font-bold text-orange-400 mb-2">
                        {modalData.newPeople.toLocaleString()}
                      </div>
                      <p className="text-white/60">Total new youth this period</p>
                    </div>
                  </div>
                </div>
              )}

              {modalType === 'giving' && (
                <div className="space-y-6">
                  <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
                    <h3 className="text-xl font-bold text-white mb-4">Giving Overview</h3>
                    <div className="text-4xl font-bold text-yellow-400 mb-2">
                      ${((modalData.breakdown?.general || 0) + (modalData.breakdown?.trust || 0) + (modalData.breakdown?.online || 0)).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                    </div>
                    <p className="text-white/60">Average weekly giving for this period (excludes Building Fund)</p>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
                      <h3 className="text-xl font-bold text-white mb-4">General</h3>
                      <div className="text-4xl font-bold text-green-400 mb-2">
                        ${(modalData.breakdown?.general || 0).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                      </div>
                      <p className="text-white/60">Regular giving</p>
                    </div>
                    <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
                      <h3 className="text-xl font-bold text-white mb-4">Trust</h3>
                      <div className="text-4xl font-bold text-blue-400 mb-2">
                        ${(modalData.breakdown?.trust || 0).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                      </div>
                      <p className="text-white/60">Trust fund giving</p>
                    </div>
                    <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
                      <h3 className="text-xl font-bold text-white mb-4">Online Giving</h3>
                      <div className="text-4xl font-bold text-purple-400 mb-2">
                        ${(modalData.breakdown?.online || 0).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                      </div>
                      <p className="text-white/60">Online contributions</p>
                    </div>
                    <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
                      <h3 className="text-xl font-bold text-white mb-4">Building Fund</h3>
                      <div className="text-4xl font-bold text-orange-400 mb-2">
                        ${(modalData.breakdown?.building || 0).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                      </div>
                      <p className="text-white/60">Building fund contributions</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Add more modal types as needed */}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CampusDashboard;
