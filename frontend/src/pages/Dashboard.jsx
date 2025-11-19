import React, { useState, useEffect } from 'react';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import CampusSelector from './CampusSelector';
import CampusDashboard from './CampusDashboard';
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

const Dashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [campus, setCampus] = useState('');
  const [campuses, setCampuses] = useState([
    { id: 'all_campuses', name: 'All Campuses' },
    { id: 'paradise', name: 'Paradise Campus' },
    { id: 'adelaide_city', name: 'Adelaide City Campus' },
    { id: 'salisbury', name: 'Salisbury Campus' },
    { id: 'south', name: 'South Campus' },
    { id: 'mt_barker', name: 'Mt Barker Campus' },
    { id: 'clare_valley', name: 'Clare Valley Campus' },
    { id: 'victor_harbour', name: 'Victor Harbor Campus' },
    { id: 'copper_coast', name: 'Copper Coast Campus' }
  ]);
  const [showPreviousYear, setShowPreviousYear] = useState(true);
  const [dateFilter, setDateFilter] = useState('last_12_months');
  const [customStartDate, setCustomStartDate] = useState('');
  const [customEndDate, setCustomEndDate] = useState('');
  const [currentUser, setCurrentUser] = useState(null);
  const [userRole, setUserRole] = useState('');
  const [userCampus, setUserCampus] = useState('');
  const [showAIModal, setShowAIModal] = useState(false);
  const [aiQuery, setAiQuery] = useState('');
  const [aiResponse, setAiResponse] = useState('');
  const [aiLoading, setAiLoading] = useState(false);
  const [lastRefresh, setLastRefresh] = useState(new Date());
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [selectedCampus, setSelectedCampus] = useState(null);
  const [showCampusSelector, setShowCampusSelector] = useState(false);

  useEffect(() => {
    fetchUserSession();
  }, []);

  useEffect(() => {
    // Show campus selector for senior leadership or if no campus is selected
    if (userRole && (userRole === 'senior_leader' || userRole === 'admin' || userRole === 'senior_pastor' || userRole === 'lead_pastor')) {
      setShowCampusSelector(true);
    } else if (userRole && userCampus && userCampus !== 'all_campuses') {
      // Auto-select campus for campus pastors
      setSelectedCampus({
        id: userCampus,
        name: (Array.isArray(campuses) ? campuses.find(c => c.id === userCampus)?.name : userCampus) || userCampus,
        isRollup: false
      });
    }
  }, [userRole, userCampus, campuses]);

  useEffect(() => {
    if (campus) {
      fetchData();
    }
  }, [campus, dateFilter, customStartDate, customEndDate, showPreviousYear]);

  // Auto-refresh every 5 minutes
  useEffect(() => {
    const interval = setInterval(() => {
      if (campus && !isRefreshing) {
        fetchData(true);
      }
    }, 5 * 60 * 1000); // 5 minutes

    return () => clearInterval(interval);
  }, [campus, isRefreshing]);

  const fetchUserSession = async () => {
    try {
      const response = await fetch('/api/session');
      const data = await response.json();
      if (data.authenticated) {
        setCurrentUser({
          id: data.id || 'unknown',
          username: data.username || 'User',
          full_name: data.full_name || 'User',
          role: data.role || 'user',
          campus: data.campus || 'all_campuses'
        });
        setUserRole(data.role || 'user');
        setUserCampus(data.campus || 'all_campuses');
        
        if (data.role === 'campus_pastor' && data.campus && data.campus !== 'all_campuses') {
          setCampus(data.campus);
        }
      }
    } catch (error) {
      console.error('Error fetching user session:', error);
    }
  };

  const fetchCampuses = async () => {
    try {
      const response = await fetch('/api/campuses/public');
      const result = await response.json();
      const campusesList = result.campuses || [];
      
      if (Array.isArray(campusesList)) {
        if (userRole === 'campus_pastor' && userCampus && userCampus !== 'all_campuses') {
          const userCampusData = campusesList.find(c => c.id === userCampus);
          if (userCampusData) {
            setCampuses([userCampusData]);
            setCampus(userCampus);
          }
        } else {
          setCampuses(campusesList);
          if (!campus && campusesList.length > 0) {
            const defaultCampus = campusesList.find(c => c.id === 'all_campuses') || campusesList[0];
            setCampus(defaultCampus.id);
          }
        }
      }
    } catch (error) {
      console.error('Error fetching campuses:', error);
      if (!campus) {
        setCampus('all_campuses');
      }
    }
  };

  const fetchData = async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setIsRefreshing(true);
      } else {
      setLoading(true);
      }
      
      const params = new URLSearchParams({
        campus: campus,
        date_filter: dateFilter,
        _t: Date.now()
      });
      
      if (dateFilter === 'custom' && customStartDate && customEndDate) {
        params.append('custom_start_date', customStartDate);
        params.append('custom_end_date', customEndDate);
      }
      
      if (showPreviousYear) {
        params.append('show_previous_year', 'true');
      }
      
      const response = await fetch(`/api/dashboard_data_public?${params}`);
      const result = await response.json();
      setData(result);
      setLastRefresh(new Date());
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  };

  const handleRefresh = () => {
    fetchData(true);
  };

  const handleCampusSelect = (campus) => {
    setSelectedCampus(campus);
    setShowCampusSelector(false);
  };

  const handleBackToSelector = () => {
    setSelectedCampus(null);
    setShowCampusSelector(true);
  };

  useEffect(() => {
    if (userRole) {
      fetchCampuses();
    }
  }, [userRole, userCampus]);

  // AI Functions
  const generateWeekendReport = async () => {
    try {
      setAiLoading(true);
      const selectedCampus = campus === 'all_campuses' ? 'all_campuses' : campus;
      const response = await fetch(`/api/dashboard_data_public?campus=${selectedCampus}&date_filter=last_7_days`);
      const data = await response.json();
      
      const campusName = campus === 'all_campuses' ? 'All Campuses' : (Array.isArray(campuses) ? campuses.find(c => c.id === campus)?.name : 'Selected Campus') || 'Selected Campus';
      
      const report = `# Weekend Report (Last 7 Days) - ${campusName}

**📊 Attendance Overview**
- Total Attendance: ${data.stats?.total_attendance?.toLocaleString() || 'N/A'}
- Average per Service: ${Math.round(data.stats?.avg_attendance || 0)}
- Services Count: ${data.stats?.entry_count || 'N/A'}

**🎯 Key Metrics**
- New People: ${data.stats?.new_people || 'N/A'} (Avg: ${Math.round(data.stats?.avg_new_people || 0)} per service)
- New Christians: ${data.stats?.new_christians || 'N/A'} (Avg: ${Math.round(data.stats?.avg_new_christians || 0)} per service)
- Youth Attendance: ${data.stats?.youth_attendance || 'N/A'} (Avg: ${Math.round(data.stats?.avg_youth_attendance || 0)} per service)
- Kids Attendance: ${data.stats?.kids_attendance || 'N/A'} (Avg: ${Math.round(data.stats?.avg_kids_attendance || 0)} per service)
- Connect Groups: ${data.stats?.connect_groups || 'N/A'} (Avg: ${Math.round(data.stats?.avg_connect_groups || 0)} per service)
- Volunteers: ${data.stats?.volunteers || 'N/A'} (Avg: ${Math.round(data.stats?.avg_volunteers || 0)} per service)

**📈 Campus-Specific Insights**
- Campus Focus: ${campusName}
- Data Period: Last 7 Days
- Report Type: Weekend Performance Analysis`;
      
      setAiResponse(report);
    } catch (error) {
      setAiResponse('Error generating weekend report. Please try again.');
    } finally {
      setAiLoading(false);
    }
  };

  const generateGrowthAnalysis = async () => {
    try {
      setAiLoading(true);
      const selectedCampus = campus === 'all_campuses' ? 'all_campuses' : campus;
      const response = await fetch(`/api/dashboard_data_public?campus=${selectedCampus}&date_filter=last_12_months`);

      const data = await response.json();
      
      const campusName = campus === 'all_campuses' ? 'All Campuses' : (Array.isArray(campuses) ? campuses.find(c => c.id === campus)?.name : 'Selected Campus') || 'Selected Campus';
      
      const report = `# Growth Analysis Report (Last 12 Months) - ${campusName}

**📈 Growth Trends**
- Attendance Growth: ${data.stats?.total_attendance ? '📈 Growing' : '📊 Stable'}
- New People Trend: ${data.stats?.new_people > 0 ? '🆕 Consistent new people' : '🔄 Focus on outreach needed'}
- Salvation Impact: ${data.stats?.new_christians > 0 ? '✝️ Lives being changed' : '🙏 Pray for salvation opportunities'}

**🎯 Key Performance Indicators**
- Total Attendance: ${data.stats?.total_attendance?.toLocaleString() || 'N/A'} (Avg: ${Math.round(data.stats?.avg_attendance || 0)} per service)
- New People: ${data.stats?.new_people || 'N/A'} (Avg: ${Math.round(data.stats?.avg_new_people || 0)} per service)
- New Christians: ${data.stats?.new_christians || 'N/A'} (Avg: ${Math.round(data.stats?.avg_new_christians || 0)} per service)
- Youth Engagement: ${data.stats?.youth_attendance || 'N/A'} (Avg: ${Math.round(data.stats?.avg_youth_attendance || 0)} per service)
- Kids Ministry: ${data.stats?.kids_attendance || 'N/A'} (Avg: ${Math.round(data.stats?.avg_kids_attendance || 0)} per service)
- Connect Groups: ${data.stats?.connect_groups || 'N/A'} (Avg: ${Math.round(data.stats?.avg_connect_groups || 0)} per service)
- Volunteer Team: ${data.stats?.volunteers || 'N/A'} (Avg: ${Math.round(data.stats?.avg_volunteers || 0)} per service)

**🚀 Strategic Insights**
- Ministry Health: ${data.stats?.total_attendance > 1000 ? 'Excellent' : data.stats?.total_attendance > 500 ? 'Good' : 'Growing'}
- Outreach Effectiveness: ${data.stats?.new_people > 50 ? 'Strong' : data.stats?.new_people > 20 ? 'Moderate' : 'Needs improvement'}
- Discipleship Pipeline: ${data.stats?.new_christians > 10 ? 'Active' : 'Developing'}

**📈 Campus-Specific Insights**
- Campus Focus: ${campusName}
- Data Period: Last 12 Months
- Report Type: Growth & Trend Analysis`;
      
      setAiResponse(report);
    } catch (error) {
      setAiResponse('Error generating growth analysis. Please try again.');
    } finally {
      setAiLoading(false);
    }
  };

  const generateInsightsReport = async () => {
    try {
      setAiLoading(true);
      const selectedCampus = campus === 'all_campuses' ? 'all_campuses' : campus;
      const response = await fetch(`/api/dashboard_data_public?campus=${selectedCampus}&date_filter=last_30_days`);

      const data = await response.json();
      
      const campusName = campus === 'all_campuses' ? 'All Campuses' : (Array.isArray(campuses) ? campuses.find(c => c.id === campus)?.name : 'Selected Campus') || 'Selected Campus';
      
      const report = `# AI Insights Report (Last 30 Days) - ${campusName}

**🧠 AI-Powered Analysis**
- Campus Performance: ${data.stats?.total_attendance > 500 ? '🌟 Exceptional' : data.stats?.total_attendance > 300 ? '⭐ Strong' : '📈 Growing'}
- Growth Trajectory: ${data.stats?.new_people > 20 ? '🚀 Accelerating' : data.stats?.new_people > 10 ? '📈 Steady' : '🔄 Stable'}
- Ministry Health: ${data.stats?.new_christians > 5 ? '💪 Very Healthy' : data.stats?.new_christians > 2 ? '👍 Healthy' : '🌱 Developing'}

**🎯 Key Insights**
- Attendance Pattern: ${data.stats?.avg_attendance > 200 ? 'Consistent large gatherings' : data.stats?.avg_attendance > 100 ? 'Steady growth' : 'Building momentum'}
- New People Flow: ${data.stats?.new_people > 0 ? 'Active outreach working' : 'Focus on visitor engagement needed'}
- Salvation Impact: ${data.stats?.new_christians > 0 ? 'Gospel is bearing fruit' : 'Pray for harvest opportunities'}

**📊 Performance Metrics**
- Total Attendance: ${data.stats?.total_attendance?.toLocaleString() || 'N/A'} (Avg: ${Math.round(data.stats?.avg_attendance || 0)} per service)
- New People: ${data.stats?.new_people || 'N/A'} (Avg: ${Math.round(data.stats?.avg_new_people || 0)} per service)
- New Christians: ${data.stats?.new_christians || 'N/A'} (Avg: ${Math.round(data.stats?.avg_new_christians || 0)} per service)
- Youth Ministry: ${data.stats?.youth_attendance || 'N/A'} (Avg: ${Math.round(data.stats?.avg_youth_attendance || 0)} per service)
- Kids Ministry: ${data.stats?.kids_attendance || 'N/A'} (Avg: ${Math.round(data.stats?.avg_kids_attendance || 0)} per service)
- Connect Groups: ${data.stats?.connect_groups || 'N/A'} (Avg: ${Math.round(data.stats?.avg_connect_groups || 0)} per service)

**💡 Strategic Recommendations**
- ${data.stats?.new_people > 20 ? 'Maintain strong outreach momentum' : 'Increase visitor follow-up systems'}
- ${data.stats?.new_christians > 5 ? 'Celebrate and disciple new believers' : 'Focus on gospel presentation'}
- ${data.stats?.youth_attendance > 50 ? 'Youth ministry is thriving' : 'Develop youth engagement strategies'}

**📈 Campus-Specific Insights**
- Campus Focus: ${campusName}
- Data Period: Last 30 Days
- Report Type: AI-Powered Strategic Insights`;
      
      setAiResponse(report);
    } catch (error) {
      setAiResponse('Error generating insights report. Please try again.');
    } finally {
      setAiLoading(false);
    }
  };

  const generateAnnualReport = async () => {
    try {
      setAiLoading(true);
      const selectedCampus = campus === 'all_campuses' ? 'all_campuses' : campus;
      const response = await fetch(`/api/dashboard_data_public?campus=${selectedCampus}&date_filter=year_to_date`);
      const data = await response.json();
      
      const campusName = campus === 'all_campuses' ? 'All Campuses' : (Array.isArray(campuses) ? campuses.find(c => c.id === campus)?.name : 'Selected Campus') || 'Selected Campus';
      
      const report = `# Annual Report (Year to Date) - ${campusName}

**📊 Annual Overview**
- Total Attendance: ${data.stats?.total_attendance?.toLocaleString() || 'N/A'} (Avg: ${Math.round(data.stats?.avg_attendance || 0)} per service)
- Total New People: ${data.stats?.new_people?.toLocaleString() || 'N/A'} (Avg: ${Math.round(data.stats?.avg_new_people || 0)} per service)
- Total New Christians: ${data.stats?.new_christians?.toLocaleString() || 'N/A'} (Avg: ${Math.round(data.stats?.avg_new_christians || 0)} per service)

**🎯 Ministry Growth**
- Youth Ministry: ${data.stats?.youth_attendance?.toLocaleString() || 'N/A'} total (Avg: ${Math.round(data.stats?.avg_youth_attendance || 0)} per service)
- Kids Ministry: ${data.stats?.kids_attendance?.toLocaleString() || 'N/A'} total (Avg: ${Math.round(data.stats?.avg_kids_attendance || 0)} per service)
- Volunteer Team: ${data.stats?.volunteers?.toLocaleString() || 'N/A'} total (Avg: ${Math.round(data.stats?.avg_volunteers || 0)} per service)
- Connect Groups: ${data.stats?.connect_groups?.toLocaleString() || 'N/A'} total (Avg: ${Math.round(data.stats?.avg_connect_groups || 0)} per service)

**📈 Campus-Specific Insights**
- Campus Focus: ${campusName}
- Data Period: Year to Date
- Report Type: Annual Performance Analysis`;
      
      setAiResponse(report);
    } catch (error) {
      setAiResponse('Error generating annual report. Please try again.');
    } finally {
      setAiLoading(false);
    }
  };

  const handleAIQuery = async () => {
    if (!aiQuery.trim()) return;
    
    setAiLoading(true);
    setAiResponse('');
    
    const query = aiQuery.toLowerCase();
    
    if (query.includes('weekend') || query.includes('weekly') || query.includes('7 days')) {
      await generateWeekendReport();
    } else if (query.includes('annual') || query.includes('year') || query.includes('yearly')) {
      await generateAnnualReport();
    } else if (query.includes('growth') || query.includes('trend') || query.includes('12 months')) {
      await generateGrowthAnalysis();
    } else if (query.includes('insight') || query.includes('analysis') || query.includes('30 days')) {
      await generateInsightsReport();
    } else if (query.includes('campus') || query.includes('location')) {
      // Generate a campus overview report
      const campusName = campus === 'all_campuses' ? 'All Campuses' : (Array.isArray(campuses) ? campuses.find(c => c.id === campus)?.name : 'Selected Campus') || 'Selected Campus';
      setAiResponse(`# Campus Overview - ${campusName}

**📍 Campus Information**
- Selected Campus: ${campusName}
- Campus ID: ${campus}
- Available Data: Weekend, Annual, Growth, and Insights reports

**📊 Quick Report Options**
- Type "weekend" for last 7 days performance
- Type "annual" for year-to-date overview  
- Type "growth" for 12-month trend analysis
- Type "insights" for AI-powered strategic analysis

**🎯 Campus-Specific Features**
- All reports automatically filter to selected campus
- Switch campuses to see different data views
- Compare performance across locations`);
    } else {
      // Default to weekend report
      await generateWeekendReport();
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-20 h-20 bg-gradient-to-r from-blue-500 to-purple-500 rounded-2xl flex items-center justify-center mx-auto mb-6 animate-pulse">
            <span className="text-4xl">⛪</span>
          </div>
          <div className="text-white text-2xl font-bold mb-2">Loading Dashboard</div>
          <div className="text-white/60 text-lg">Fetching ministry data...</div>
          <div className="mt-6 w-64 bg-white/10 rounded-full h-2 mx-auto">
            <div className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full animate-pulse"></div>
          </div>
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
          <div className="text-white/60 text-lg">Unable to load ministry data at this time</div>
          <button 
            onClick={() => window.location.reload()} 
            className="mt-6 bg-gradient-to-r from-blue-500 to-purple-500 text-white px-8 py-3 rounded-2xl font-semibold hover:scale-105 transition-all duration-300 shadow-lg hover:shadow-blue-500/25"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  const attendanceChartData = {
    labels: data.chart_data?.labels || [],
    datasets: [
      {
        label: 'Current Year',
        data: data.chart_data?.attendance || [],
        borderColor: '#62b4ff',
        backgroundColor: 'rgba(98, 180, 255, 0.1)',
        borderWidth: 3,
        tension: 0.4,
      },
      ...(showPreviousYear ? [{
        label: 'Previous Year',
        data: data.previous_year_data?.attendance || [],
        borderColor: '#e444b9',
        backgroundColor: 'rgba(228, 68, 185, 0.1)',
        borderWidth: 3,
        borderDash: [5, 5],
        tension: 0.4,
      }] : [])
    ]
  };

  const newPeopleChartData = {
    labels: data.chart_data?.labels || [],
    datasets: [
      {
        label: 'New People',
        data: data.chart_data?.new_people || [],
        borderColor: '#ffff5f',
        backgroundColor: 'rgba(255, 255, 95, 0.1)',
        borderWidth: 3,
        tension: 0.4,
      },
      {
        label: 'New Christians',
        data: data.chart_data?.new_christians || [],
        borderColor: '#ff8432',
        backgroundColor: 'rgba(255, 132, 50, 0.1)',
        borderWidth: 3,
        tension: 0.4,
      }
    ]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    plugins: {
      legend: {
        labels: {
          color: 'rgba(255, 255, 255, 0.8)',
          font: { size: 12 },
          padding: 20
        }
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: 'rgba(255, 255, 255, 0.9)',
        bodyColor: 'rgba(255, 255, 255, 0.8)',
        borderColor: 'rgba(255, 255, 255, 0.2)',
        borderWidth: 1,
        cornerRadius: 8,
        displayColors: true,
        callbacks: {
          title: function(context) {
            return context[0].label;
          },
          label: function(context) {
            const label = context.dataset.label || '';
            const value = context.parsed.y;
            return `${label}: ${value.toLocaleString()}`;
          }
        }
      }
    },
    scales: {
      x: {
        ticks: {
          color: 'rgba(255, 255, 255, 0.6)',
          font: { size: 11 }
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.1)',
          drawBorder: false
        }
      },
      y: {
        ticks: {
          color: 'rgba(255, 255, 255, 0.6)',
          font: { size: 11 },
          callback: function(value) {
            return value.toLocaleString();
          }
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.1)',
          drawBorder: false
        }
      }
    },
    elements: {
      point: {
        radius: 4,
        hoverRadius: 6,
        borderWidth: 2
      },
      line: {
        tension: 0.4
      }
    }
  };

  // Show campus selector if needed
  if (showCampusSelector) {
    return <CampusSelector onCampusSelect={handleCampusSelect} userRole={userRole} userCampus={userCampus} />;
  }

  // Show campus dashboard if campus is selected
  if (selectedCampus) {
  return (
      <CampusDashboard 
        campusId={selectedCampus.id} 
        campusName={selectedCampus.name} 
        isRollup={selectedCampus.isRollup}
        onBackToSelector={handleBackToSelector}
      />
    );
  }

  // Show loading while determining what to show
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-20 h-20 bg-gradient-to-r from-blue-500 to-purple-500 rounded-2xl flex items-center justify-center mx-auto mb-6 animate-pulse">
            <span className="text-4xl">⛪</span>
          </div>
          <div className="text-white text-2xl font-bold mb-2">Loading Dashboard</div>
          <div className="text-white/60 text-lg">Determining your access level...</div>
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
          <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6">
            <div className="flex-1">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                  <span className="text-2xl">⛪</span>
                </div>
            <div>
                  <h1 className="text-4xl lg:text-5xl font-bold text-white tracking-tight">
                    Futures Church
                  </h1>
                  <p className="text-white/80 text-lg font-medium">
                    Ministry Analytics Dashboard
                  </p>
                </div>
              </div>
              
                {campus && campus !== 'all_campuses' && (
                <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm rounded-full px-4 py-2 border border-white/20">
                  <span className="text-lg">📍</span>
                  <span className="text-white font-semibold">
                    {(Array.isArray(campuses) ? campuses.find(c => c.id === campus)?.name : 'Selected Campus') || 'Selected Campus'}
                  </span>
                </div>
                )}
            </div>
            
            <div className="flex flex-col sm:flex-row gap-4">
              <button
                onClick={handleRefresh}
                disabled={isRefreshing}
                className="group relative bg-gradient-to-r from-blue-600 to-cyan-600 text-white px-6 py-4 rounded-2xl font-semibold hover:scale-105 disabled:opacity-50 disabled:scale-100 transition-all duration-300 shadow-2xl hover:shadow-blue-500/25 overflow-hidden"
              >
                <div className="relative flex items-center gap-3">
                  <span className={`text-xl ${isRefreshing ? 'animate-spin' : ''}`}>
                    {isRefreshing ? '🔄' : '↻'}
                  </span>
                  <span>{isRefreshing ? 'Refreshing...' : 'Refresh'}</span>
                </div>
              </button>
            
            <button
              onClick={() => setShowAIModal(true)}
                className="group relative bg-gradient-to-r from-purple-600 to-pink-600 text-white px-8 py-4 rounded-2xl font-semibold hover:scale-105 transition-all duration-300 shadow-2xl hover:shadow-purple-500/25 overflow-hidden"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-purple-600 to-pink-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                <div className="relative flex items-center gap-3">
                  <span className="text-xl">🤖</span>
                  <span>AI Assistant</span>
                </div>
            </button>
              
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
        {/* Controls */}
        <div className="mb-8 bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/10 shadow-2xl">
          <div className="flex flex-col xl:flex-row gap-6 items-start xl:items-end">
            <div className="flex-1">
              <label className="block text-white/80 text-sm font-semibold mb-3 flex items-center gap-2">
                <span className="text-lg">🏢</span>
                Campus Selection
              </label>
              <select
                value={campus}
                onChange={(e) => setCampus(e.target.value)}
                className="w-full bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl px-4 py-3 text-white placeholder-white/60 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:bg-white/15 transition-all duration-300"
              >
                {campuses.map((c) => (
                  <option key={c.id} value={c.id} className="bg-slate-800 text-white">{c.name}</option>
                ))}
              </select>
            </div>
            
            <div className="flex-1">
              <label className="block text-white/80 text-sm font-semibold mb-3 flex items-center gap-2">
                <span className="text-lg">📅</span>
                Date Range
              </label>
              <select
                value={dateFilter}
                onChange={(e) => setDateFilter(e.target.value)}
                className="w-full bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl px-4 py-3 text-white placeholder-white/60 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:bg-white/15 transition-all duration-300"
              >
                <option value="last_7_days" className="bg-slate-800 text-white">Last 7 Days</option>
                <option value="last_30_days" className="bg-slate-800 text-white">Last 30 Days</option>
                <option value="last_3_months" className="bg-slate-800 text-white">Last 3 Months</option>
                <option value="last_6_months" className="bg-slate-800 text-white">Last 6 Months</option>
                <option value="last_12_months" className="bg-slate-800 text-white">Last 12 Months</option>
                <option value="year_to_date" className="bg-slate-800 text-white">Year to Date</option>
                <option value="custom" className="bg-slate-800 text-white">Custom Range</option>
              </select>
            </div>

            {dateFilter === 'custom' && (
              <>
                <div>
                  <label className="block text-white/80 text-sm font-semibold mb-3">Start Date</label>
                  <input
                    type="date"
                    value={customStartDate}
                    onChange={(e) => setCustomStartDate(e.target.value)}
                    className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl px-4 py-3 text-white placeholder-white/60 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:bg-white/15 transition-all duration-300"
                  />
                </div>
                <div>
                  <label className="block text-white/80 text-sm font-semibold mb-3">End Date</label>
                  <input
                    type="date"
                    value={customEndDate}
                    onChange={(e) => setCustomEndDate(e.target.value)}
                    className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl px-4 py-3 text-white placeholder-white/60 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:bg-white/15 transition-all duration-300"
                  />
                </div>
              </>
            )}

            <div className="flex items-center gap-3 bg-white/5 backdrop-blur-sm rounded-xl px-4 py-3 border border-white/10">
              <input
                type="checkbox"
                id="showPreviousYear"
                checked={showPreviousYear}
                onChange={(e) => setShowPreviousYear(e.target.checked)}
                className="w-5 h-5 rounded border-white/20 text-blue-500 focus:ring-blue-400 bg-white/10"
              />
              <label htmlFor="showPreviousYear" className="text-white/80 text-sm font-medium flex items-center gap-2">
                <span className="text-lg">📊</span>
                Show Previous Year
              </label>
            </div>
          </div>
        </div>

        {/* Key Stats - Hero Cards */}
        <div className="mb-12">
          <div className="flex items-center gap-4 mb-8">
            <div className="w-1 h-12 bg-gradient-to-b from-blue-400 to-purple-400 rounded-full"></div>
            <div>
              <h2 className="text-3xl font-bold text-white">
                Ministry Overview
              </h2>
              <p className="text-white/60 text-lg">
                {campus === 'all_campuses' ? 'All Campuses' : (Array.isArray(campuses) ? campuses.find(c => c.id === campus)?.name : 'Selected Campus') || 'Selected Campus'}
              </p>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
            {/* Total Attendance Card */}
            <div className="group relative bg-gradient-to-br from-blue-500/20 to-blue-600/20 backdrop-blur-sm rounded-2xl p-6 border border-blue-400/20 shadow-2xl hover:shadow-blue-500/25 transition-all duration-500 hover:scale-105">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="relative">
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 bg-blue-500/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                    <span className="text-2xl">👥</span>
                  </div>
                  <div className="text-blue-400 text-sm font-semibold">Total</div>
                </div>
                <h3 className="text-white/80 text-sm font-medium mb-2">Total Attendance</h3>
              <div className="text-4xl font-bold text-white mb-2">
                {data.stats?.total_attendance?.toLocaleString() || 'N/A'}
              </div>
                <p className="text-blue-200/80 text-sm">
                  Avg: {Math.round(data.stats?.avg_attendance || 0)} per service
              </p>
              </div>
            </div>

            {/* New People Card */}
            <div className="group relative bg-gradient-to-br from-emerald-500/20 to-emerald-600/20 backdrop-blur-sm rounded-2xl p-6 border border-emerald-400/20 shadow-2xl hover:shadow-emerald-500/25 transition-all duration-500 hover:scale-105">
              <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/10 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="relative">
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 bg-emerald-500/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                    <span className="text-2xl">🆕</span>
                  </div>
                  <div className="text-emerald-400 text-sm font-semibold">Growth</div>
                </div>
                <h3 className="text-white/80 text-sm font-medium mb-2">New People</h3>
              <div className="text-4xl font-bold text-white mb-2">
                  {data.stats?.new_people?.toLocaleString() || 'N/A'}
              </div>
                <p className="text-emerald-200/80 text-sm">
                  Christians: {data.stats?.new_christians?.toLocaleString() || 'N/A'}
              </p>
              </div>
            </div>

            {/* Youth Card */}
            <div className="group relative bg-gradient-to-br from-purple-500/20 to-purple-600/20 backdrop-blur-sm rounded-2xl p-6 border border-purple-400/20 shadow-2xl hover:shadow-purple-500/25 transition-all duration-500 hover:scale-105">
              <div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="relative">
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 bg-purple-500/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                    <span className="text-2xl">🎯</span>
                  </div>
                  <div className="text-purple-400 text-sm font-semibold">Youth</div>
                </div>
                <h3 className="text-white/80 text-sm font-medium mb-2">Youth Attendance</h3>
              <div className="text-4xl font-bold text-white mb-2">
                  {data.stats?.youth_attendance?.toLocaleString() || 'N/A'}
              </div>
                <p className="text-purple-200/80 text-sm">
                  Leaders: {data.stats?.youth_leaders || 'N/A'} | Salvations: {data.stats?.youth_salvations || 'N/A'}
              </p>
              </div>
            </div>

            {/* Kids Card */}
            <div className="group relative bg-gradient-to-br from-pink-500/20 to-pink-600/20 backdrop-blur-sm rounded-2xl p-6 border border-pink-400/20 shadow-2xl hover:shadow-pink-500/25 transition-all duration-500 hover:scale-105">
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
                  {data.stats?.kids_attendance?.toLocaleString() || 'N/A'}
              </div>
                <p className="text-pink-200/80 text-sm">
                  Leaders: {data.stats?.kids_leaders || 'N/A'}
              </p>
              </div>
            </div>
          </div>

          {/* Secondary Stats Row */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
            <div className="group relative bg-gradient-to-br from-orange-500/20 to-orange-600/20 backdrop-blur-sm rounded-2xl p-6 border border-orange-400/20 shadow-2xl hover:shadow-orange-500/25 transition-all duration-500 hover:scale-105">
              <div className="absolute inset-0 bg-gradient-to-br from-orange-500/10 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="relative">
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 bg-orange-500/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                    <span className="text-2xl">💰</span>
                  </div>
                  <div className="text-orange-400 text-sm font-semibold">Finance</div>
                </div>
                <h3 className="text-white/80 text-sm font-medium mb-2">Tithe Amount</h3>
              <div className="text-3xl font-bold text-white mb-2">
                {data.stats?.tithe ? `$${data.stats.tithe.toLocaleString()}` : 'N/A'}
              </div>
                <p className="text-orange-200/80 text-sm">
                  Financial giving
              </p>
              </div>
            </div>

            <div className="group relative bg-gradient-to-br from-cyan-500/20 to-cyan-600/20 backdrop-blur-sm rounded-2xl p-6 border border-cyan-400/20 shadow-2xl hover:shadow-cyan-500/25 transition-all duration-500 hover:scale-105">
              <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/10 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="relative">
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 bg-cyan-500/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                    <span className="text-2xl">🤝</span>
                  </div>
                  <div className="text-cyan-400 text-sm font-semibold">Community</div>
                </div>
                <h3 className="text-white/80 text-sm font-medium mb-2">Connect Groups</h3>
              <div className="text-3xl font-bold text-white mb-2">
                {data.stats?.connect_groups?.toLocaleString() || 'N/A'}
              </div>
                <p className="text-cyan-200/80 text-sm">
                  Avg: {Math.round(data.stats?.avg_connect_groups || 0)} per service
              </p>
              </div>
            </div>

            <div className="group relative bg-gradient-to-br from-indigo-500/20 to-indigo-600/20 backdrop-blur-sm rounded-2xl p-6 border border-indigo-400/20 shadow-2xl hover:shadow-indigo-500/25 transition-all duration-500 hover:scale-105">
              <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/10 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="relative">
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 bg-indigo-500/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                    <span className="text-2xl">🙋</span>
                  </div>
                  <div className="text-indigo-400 text-sm font-semibold">Service</div>
                </div>
                <h3 className="text-white/80 text-sm font-medium mb-2">Volunteers</h3>
              <div className="text-3xl font-bold text-white mb-2">
                {data.stats?.volunteers?.toLocaleString() || 'N/A'}
              </div>
                <p className="text-indigo-200/80 text-sm">
                Serving in ministry
              </p>
              </div>
            </div>
          </div>
        </div>

        {/* Key Insights - Analytics Cards */}
        <div className="mb-12">
          <div className="flex items-center gap-4 mb-8">
            <div className="w-1 h-12 bg-gradient-to-b from-emerald-400 to-cyan-400 rounded-full"></div>
            <div>
              <h2 className="text-3xl font-bold text-white">
                Ministry Analytics
              </h2>
              <p className="text-white/60 text-lg">
                Key performance indicators and engagement metrics
              </p>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
            {/* Conversion Rate Card */}
            <div className="group relative bg-gradient-to-br from-emerald-500/20 to-emerald-600/20 backdrop-blur-sm rounded-2xl p-6 border border-emerald-400/20 shadow-2xl hover:shadow-emerald-500/25 transition-all duration-500 hover:scale-105">
              <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/10 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="relative">
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 bg-emerald-500/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                    <span className="text-2xl">📈</span>
                  </div>
                  <div className="text-emerald-400 text-sm font-semibold">Conversion</div>
                </div>
                <h3 className="text-white/80 text-sm font-medium mb-2">Conversion Rate</h3>
                <div className="text-4xl font-bold text-white mb-2">
                {data.stats?.new_people > 0 && data.stats?.new_christians > 0 
                  ? `${Math.round((data.stats.new_christians / data.stats.new_people) * 100)}%`
                  : 'N/A%'
                }
              </div>
                <p className="text-emerald-200/80 text-sm">
                {data.stats?.new_people > 0 && data.stats?.new_christians > 0
                    ? `${data.stats.new_christians} Christians / ${data.stats.new_people} people`
                    : 'No data available'
                }
              </p>
              </div>
            </div>

            {/* Youth Engagement Card */}
            <div className="group relative bg-gradient-to-br from-purple-500/20 to-purple-600/20 backdrop-blur-sm rounded-2xl p-6 border border-purple-400/20 shadow-2xl hover:shadow-purple-500/25 transition-all duration-500 hover:scale-105">
              <div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="relative">
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 bg-purple-500/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                    <span className="text-2xl">🎯</span>
                  </div>
                  <div className="text-purple-400 text-sm font-semibold">Youth</div>
                </div>
                <h3 className="text-white/80 text-sm font-medium mb-2">Youth Engagement</h3>
                <div className="text-4xl font-bold text-white mb-2">
                {data.stats?.total_attendance > 0 && data.stats?.youth_attendance > 0
                  ? `${Math.round((data.stats.youth_attendance / data.stats.total_attendance) * 100)}%`
                  : 'N/A%'
                }
              </div>
                <p className="text-purple-200/80 text-sm">
                {data.stats?.youth_attendance > 0
                  ? `${data.stats.youth_attendance} youth / ${data.stats.total_attendance} total`
                    : 'No youth data'
                }
              </p>
              </div>
            </div>

            {/* Children's Engagement Card */}
            <div className="group relative bg-gradient-to-br from-pink-500/20 to-pink-600/20 backdrop-blur-sm rounded-2xl p-6 border border-pink-400/20 shadow-2xl hover:shadow-pink-500/25 transition-all duration-500 hover:scale-105">
              <div className="absolute inset-0 bg-gradient-to-br from-pink-500/10 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="relative">
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 bg-pink-500/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                    <span className="text-2xl">🧒</span>
                  </div>
                  <div className="text-pink-400 text-sm font-semibold">Kids</div>
                </div>
                <h3 className="text-white/80 text-sm font-medium mb-2">Children's Engagement</h3>
                <div className="text-4xl font-bold text-white mb-2">
                {data.stats?.total_attendance > 0 && data.stats?.kids_attendance > 0
                  ? `${Math.round((data.stats.kids_attendance / data.stats.total_attendance) * 100)}%`
                  : 'N/A%'
                }
              </div>
                <p className="text-pink-200/80 text-sm">
                  {data.stats?.kids_attendance > 0
                  ? `${data.stats.kids_attendance} kids / ${data.stats.total_attendance} total`
                    : 'No children data'
                }
              </p>
              </div>
            </div>

            {/* Volunteer Rate Card */}
            <div className="group relative bg-gradient-to-br from-indigo-500/20 to-indigo-600/20 backdrop-blur-sm rounded-2xl p-6 border border-indigo-400/20 shadow-2xl hover:shadow-indigo-500/25 transition-all duration-500 hover:scale-105">
              <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/10 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="relative">
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 bg-indigo-500/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                    <span className="text-2xl">🙋</span>
                  </div>
                  <div className="text-indigo-400 text-sm font-semibold">Service</div>
                </div>
                <h3 className="text-white/80 text-sm font-medium mb-2">Volunteer Rate</h3>
                <div className="text-4xl font-bold text-white mb-2">
                {data.stats?.total_attendance > 0 && data.stats?.volunteers > 0
                  ? `${Math.round((data.stats.volunteers / data.stats.total_attendance) * 100)}%`
                  : 'N/A%'
                }
              </div>
                <p className="text-indigo-200/80 text-sm">
                {data.stats?.volunteers > 0
                  ? `${data.stats.volunteers} volunteers serving`
                    : 'No volunteer data'
                }
              </p>
              </div>
            </div>
          </div>
        </div>

        {/* Charts Section */}
        <div className="mb-12">
          <div className="flex items-center gap-4 mb-8">
            <div className="w-1 h-12 bg-gradient-to-b from-cyan-400 to-blue-400 rounded-full"></div>
            <div>
              <h2 className="text-3xl font-bold text-white">
                Data Visualization
              </h2>
              <p className="text-white/60 text-lg">
                Interactive charts and trend analysis
              </p>
            </div>
          </div>
          
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
            {/* Attendance Trends Chart */}
            <div className="group relative bg-white/5 backdrop-blur-sm rounded-2xl p-8 border border-white/10 shadow-2xl hover:shadow-blue-500/10 transition-all duration-500">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="relative">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-blue-500/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                      <span className="text-xl">📈</span>
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-white">Attendance Trends</h3>
                      <p className="text-white/60 text-sm">Weekly attendance patterns</p>
                    </div>
                  </div>
                </div>
                <div className="h-64">
              <Line data={attendanceChartData} options={chartOptions} />
                </div>
            </div>
          </div>

            {/* New People & Christians Chart */}
            <div className="group relative bg-white/5 backdrop-blur-sm rounded-2xl p-8 border border-white/10 shadow-2xl hover:shadow-emerald-500/10 transition-all duration-500">
              <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="relative">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-emerald-500/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                      <span className="text-xl">👥</span>
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-white">Growth Metrics</h3>
                      <p className="text-white/60 text-sm">New people and Christians</p>
                    </div>
                  </div>
                </div>
                <div className="h-64">
              <Line data={newPeopleChartData} options={chartOptions} />
                </div>
            </div>
          </div>
        </div>

          {/* Additional Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mt-8">
            {/* Ministry Breakdown Doughnut Chart */}
            <div className="group relative bg-white/5 backdrop-blur-sm rounded-2xl p-8 border border-white/10 shadow-2xl hover:shadow-purple-500/10 transition-all duration-500">
              <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="relative">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-purple-500/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                      <span className="text-xl">🥧</span>
                    </div>
                    <div>
                      <h3 className="text-lg font-bold text-white">Ministry Breakdown</h3>
                      <p className="text-white/60 text-sm">Attendance distribution</p>
                    </div>
                  </div>
                </div>
                <div className="h-48">
                  <Doughnut 
                    data={{
                      labels: ['Youth', 'Kids', 'Adults'],
                      datasets: [{
                        data: [
                          data.stats?.youth_attendance || 0,
                          data.stats?.kids_attendance || 0,
                          (data.stats?.total_attendance || 0) - (data.stats?.youth_attendance || 0) - (data.stats?.kids_attendance || 0)
                        ],
                        backgroundColor: [
                          'rgba(168, 85, 247, 0.8)',
                          'rgba(236, 72, 153, 0.8)',
                          'rgba(59, 130, 246, 0.8)'
                        ],
                        borderWidth: 0
                      }]
                    }} 
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          labels: {
                            color: 'rgba(255, 255, 255, 0.8)',
                            padding: 20
                          }
                        }
                      }
                    }} 
                  />
                </div>
              </div>
            </div>

            {/* Monthly Comparison Bar Chart */}
            <div className="group relative bg-white/5 backdrop-blur-sm rounded-2xl p-8 border border-white/10 shadow-2xl hover:shadow-orange-500/10 transition-all duration-500">
              <div className="absolute inset-0 bg-gradient-to-br from-orange-500/5 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="relative">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-orange-500/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                      <span className="text-xl">📊</span>
                </div>
                    <div>
                      <h3 className="text-lg font-bold text-white">Monthly Comparison</h3>
                      <p className="text-white/60 text-sm">Key metrics overview</p>
                </div>
                </div>
                </div>
                <div className="h-48">
                  <Bar 
                    data={{
                      labels: ['Attendance', 'New People', 'New Christians', 'Youth', 'Kids'],
                      datasets: [{
                        label: 'Current Period',
                        data: [
                          data.stats?.total_attendance || 0,
                          data.stats?.new_people || 0,
                          data.stats?.new_christians || 0,
                          data.stats?.youth_attendance || 0,
                          data.stats?.kids_attendance || 0
                        ],
                        backgroundColor: [
                          'rgba(59, 130, 246, 0.8)',
                          'rgba(16, 185, 129, 0.8)',
                          'rgba(245, 158, 11, 0.8)',
                          'rgba(168, 85, 247, 0.8)',
                          'rgba(236, 72, 153, 0.8)'
                        ],
                        borderRadius: 8
                      }]
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

            {/* Growth Rate Card */}
            <div className="group relative bg-white/5 backdrop-blur-sm rounded-2xl p-8 border border-white/10 shadow-2xl hover:shadow-cyan-500/10 transition-all duration-500">
              <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="relative">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-cyan-500/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                      <span className="text-xl">🚀</span>
                </div>
                    <div>
                      <h3 className="text-lg font-bold text-white">Growth Insights</h3>
                      <p className="text-white/60 text-sm">Key performance indicators</p>
                </div>
                </div>
                </div>
                <div className="space-y-4">
                  <div className="flex justify-between items-center p-4 bg-white/5 rounded-xl">
                    <span className="text-white/80 text-sm">Conversion Rate</span>
                    <span className="text-2xl font-bold text-emerald-400">
                      {data.stats?.new_people > 0 && data.stats?.new_christians > 0 
                        ? `${Math.round((data.stats.new_christians / data.stats.new_people) * 100)}%`
                        : 'N/A'
                      }
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-4 bg-white/5 rounded-xl">
                    <span className="text-white/80 text-sm">Youth Engagement</span>
                    <span className="text-2xl font-bold text-purple-400">
                      {data.stats?.total_attendance > 0 && data.stats?.youth_attendance > 0
                        ? `${Math.round((data.stats.youth_attendance / data.stats.total_attendance) * 100)}%`
                        : 'N/A'
                      }
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-4 bg-white/5 rounded-xl">
                    <span className="text-white/80 text-sm">Kids Engagement</span>
                    <span className="text-2xl font-bold text-pink-400">
                      {data.stats?.total_attendance > 0 && data.stats?.kids_attendance > 0
                        ? `${Math.round((data.stats.kids_attendance / data.stats.total_attendance) * 100)}%`
                        : 'N/A'
                      }
                    </span>
                  </div>
                </div>
              </div>
            </div>
              </div>
            </div>

        {/* Detailed Statistics */}
        <div className="mb-12">
          <div className="flex items-center gap-4 mb-8">
            <div className="w-1 h-12 bg-gradient-to-b from-orange-400 to-red-400 rounded-full"></div>
            <div>
              <h2 className="text-3xl font-bold text-white">
                Detailed Statistics
              </h2>
              <p className="text-white/60 text-lg">
                Comprehensive ministry breakdown and metrics
              </p>
                </div>
                </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Youth Ministry Card */}
            <div className="group relative bg-white/5 backdrop-blur-sm rounded-2xl p-8 border border-white/10 shadow-2xl hover:shadow-purple-500/10 transition-all duration-500">
              <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="relative">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-12 h-12 bg-purple-500/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                    <span className="text-2xl">🎯</span>
                </div>
                  <div>
                    <h3 className="text-xl font-bold text-white">Youth Ministry</h3>
                    <p className="text-white/60 text-sm">Young people engagement</p>
                  </div>
                </div>
                <div className="space-y-4">
                  <div className="flex justify-between items-center p-4 bg-white/5 rounded-xl">
                    <span className="text-white/80 text-sm">Total Attendance</span>
                    <span className="text-xl font-bold text-purple-400">
                      {data.stats?.youth_attendance?.toLocaleString() || 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-4 bg-white/5 rounded-xl">
                    <span className="text-white/80 text-sm">Salvations</span>
                    <span className="text-xl font-bold text-emerald-400">
                      {data.stats?.youth_salvations || 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-4 bg-white/5 rounded-xl">
                    <span className="text-white/80 text-sm">New People</span>
                    <span className="text-xl font-bold text-blue-400">
                      {data.stats?.youth_new_people || 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-4 bg-white/5 rounded-xl">
                    <span className="text-white/80 text-sm">Avg per Service</span>
                    <span className="text-xl font-bold text-cyan-400">
                      {Math.round(data.stats?.avg_youth_attendance || 0)}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Kids Ministry Card */}
            <div className="group relative bg-white/5 backdrop-blur-sm rounded-2xl p-8 border border-white/10 shadow-2xl hover:shadow-pink-500/10 transition-all duration-500">
              <div className="absolute inset-0 bg-gradient-to-br from-pink-500/5 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="relative">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-12 h-12 bg-pink-500/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                    <span className="text-2xl">🧒</span>
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-white">Kids Ministry</h3>
                    <p className="text-white/60 text-sm">Children's programs</p>
                  </div>
                </div>
                <div className="space-y-4">
                  <div className="flex justify-between items-center p-4 bg-white/5 rounded-xl">
                    <span className="text-white/80 text-sm">Total Attendance</span>
                    <span className="text-xl font-bold text-pink-400">
                      {data.stats?.kids_attendance?.toLocaleString() || 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-4 bg-white/5 rounded-xl">
                    <span className="text-white/80 text-sm">Leaders</span>
                    <span className="text-xl font-bold text-orange-400">
                      {data.stats?.kids_leaders || 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-4 bg-white/5 rounded-xl">
                    <span className="text-white/80 text-sm">New Kids</span>
                    <span className="text-xl font-bold text-emerald-400">
                      {data.stats?.new_kids || 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-4 bg-white/5 rounded-xl">
                    <span className="text-white/80 text-sm">Avg per Service</span>
                    <span className="text-xl font-bold text-cyan-400">
                      {Math.round(data.stats?.avg_kids_attendance || 0)}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Connect Groups Card */}
            <div className="group relative bg-white/5 backdrop-blur-sm rounded-2xl p-8 border border-white/10 shadow-2xl hover:shadow-cyan-500/10 transition-all duration-500">
              <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="relative">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-12 h-12 bg-cyan-500/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                    <span className="text-2xl">🤝</span>
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-white">Connect Groups</h3>
                    <p className="text-white/60 text-sm">Small group ministry</p>
                  </div>
                </div>
                <div className="space-y-4">
                  <div className="flex justify-between items-center p-4 bg-white/5 rounded-xl">
                    <span className="text-white/80 text-sm">Total Attendance</span>
                    <span className="text-xl font-bold text-cyan-400">
                      {data.stats?.connect_groups?.toLocaleString() || 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-4 bg-white/5 rounded-xl">
                    <span className="text-white/80 text-sm">Avg per Service</span>
                    <span className="text-xl font-bold text-blue-400">
                      {Math.round(data.stats?.avg_connect_groups || 0)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-4 bg-white/5 rounded-xl">
                    <span className="text-white/80 text-sm">Services</span>
                    <span className="text-xl font-bold text-purple-400">
                      {data.stats?.entry_count || 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-4 bg-white/5 rounded-xl">
                    <span className="text-white/80 text-sm">Status</span>
                    <span className="text-xl font-bold text-emerald-400">
                    {data.stats?.avg_connect_groups > 0 ? '📈 Active' : '📊 Growing'}
                  </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-16 text-center">
          <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-8 border border-white/10 shadow-2xl">
            <div className="flex items-center justify-center gap-4 mb-4">
              <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-500 rounded-xl flex items-center justify-center">
                <span className="text-2xl">⛪</span>
              </div>
              <div>
                <h3 className="text-2xl font-bold text-white">Futures Church</h3>
                <p className="text-white/60">Ministry Analytics Dashboard</p>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm text-white/60">
              <div>
                <p className="font-semibold text-white mb-2">📊 Data Source</p>
                <p>Real-time Google Sheets Integration</p>
              </div>
              <div>
                <p className="font-semibold text-white mb-2">🎯 Analytics</p>
                <p>Comprehensive Ministry Metrics</p>
              </div>
              <div>
                <p className="font-semibold text-white mb-2">🕒 Last Updated</p>
                <p>{lastRefresh.toLocaleDateString()} at {lastRefresh.toLocaleTimeString()}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* AI Assistant Modal */}
      {showAIModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-gradient-to-br from-slate-900/95 to-slate-800/95 backdrop-blur-xl rounded-3xl p-8 max-w-5xl w-full max-h-[90vh] overflow-y-auto border border-white/10 shadow-2xl">
            <div className="flex justify-between items-start mb-8">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-2xl flex items-center justify-center">
                  <span className="text-3xl">🤖</span>
                </div>
              <div>
                  <h2 className="text-3xl font-bold text-white">AI Ministry Assistant</h2>
                  <p className="text-white/60 text-lg mt-1">
                  📍 Campus: {campus === 'all_campuses' ? 'All Campuses' : (Array.isArray(campuses) ? campuses.find(c => c.id === campus)?.name : 'Selected Campus') || 'Selected Campus'}
                </p>
                </div>
              </div>
              <button
                onClick={() => setShowAIModal(false)}
                className="w-10 h-10 bg-white/10 hover:bg-white/20 rounded-xl flex items-center justify-center text-white/60 hover:text-white transition-all duration-300"
              >
                <span className="text-xl">×</span>
              </button>
            </div>

            <div className="mb-8">
              <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-3">
                <span className="text-2xl">⚡</span>
                Quick Actions
              </h3>
              <p className="text-white/70 text-sm mb-6">
                🎯 All reports automatically filter to your selected campus: <span className="text-white font-semibold">
                  {campus === 'all_campuses' ? 'All Campuses' : (Array.isArray(campuses) ? campuses.find(c => c.id === campus)?.name : 'Selected Campus') || 'Selected Campus'}
                </span>
              </p>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <button
                  onClick={generateWeekendReport}
                  disabled={aiLoading}
                  className="group relative bg-gradient-to-r from-purple-600/20 to-pink-600/20 backdrop-blur-sm border border-purple-400/20 text-white px-6 py-4 rounded-2xl font-semibold hover:scale-105 disabled:opacity-50 disabled:scale-100 transition-all duration-300 shadow-lg hover:shadow-purple-500/25"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xl">📅</span>
                    <span>Weekend Report</span>
                  </div>
                </button>
                <button
                  onClick={generateAnnualReport}
                  disabled={aiLoading}
                  className="group relative bg-gradient-to-r from-blue-600/20 to-purple-600/20 backdrop-blur-sm border border-blue-400/20 text-white px-6 py-4 rounded-2xl font-semibold hover:scale-105 disabled:opacity-50 disabled:scale-100 transition-all duration-300 shadow-lg hover:shadow-blue-500/25"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xl">📊</span>
                    <span>Annual Report</span>
                  </div>
                </button>
                <button
                  onClick={generateGrowthAnalysis}
                  disabled={aiLoading}
                  className="group relative bg-gradient-to-r from-pink-600/20 to-blue-600/20 backdrop-blur-sm border border-pink-400/20 text-white px-6 py-4 rounded-2xl font-semibold hover:scale-105 disabled:opacity-50 disabled:scale-100 transition-all duration-300 shadow-lg hover:shadow-pink-500/25"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xl">📈</span>
                    <span>Growth Analysis</span>
                  </div>
                </button>
                <button
                  onClick={generateInsightsReport}
                  disabled={aiLoading}
                  className="group relative bg-gradient-to-r from-emerald-500/20 to-blue-600/20 backdrop-blur-sm border border-emerald-400/20 text-white px-6 py-4 rounded-2xl font-semibold hover:scale-105 disabled:opacity-50 disabled:scale-100 transition-all duration-300 shadow-lg hover:shadow-emerald-500/25"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xl">🧠</span>
                    <span>AI Insights</span>
                  </div>
                </button>
              </div>
            </div>

            <div className="mb-8">
              <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-3">
                <span className="text-2xl">💬</span>
                Ask a Custom Question
              </h3>
              <div className="flex gap-4">
                <input
                  type="text"
                  value={aiQuery}
                  onChange={(e) => setAiQuery(e.target.value)}
                  placeholder="e.g., 'Show me youth ministry trends' or 'Compare campus performance'"
                  className="flex-1 bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl px-6 py-4 text-white placeholder-white/60 focus:outline-none focus:ring-2 focus:ring-purple-400 focus:bg-white/15 transition-all duration-300"
                />
                <button
                  onClick={handleAIQuery}
                  disabled={aiLoading || !aiQuery.trim()}
                  className="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-8 py-4 rounded-2xl font-semibold hover:scale-105 disabled:opacity-50 disabled:scale-100 transition-all duration-300 shadow-lg hover:shadow-purple-500/25"
                >
                  {aiLoading ? 'Analyzing...' : 'Ask AI'}
                </button>
              </div>
            </div>

            {aiResponse && (
              <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/10 shadow-2xl">
                <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-3">
                  <span className="text-2xl">📋</span>
                  AI Response
                </h3>
                <div className="prose prose-invert max-w-none">
                  <pre className="whitespace-pre-wrap text-white/90 text-sm bg-white/5 p-6 rounded-xl overflow-x-auto border border-white/10">
                    {aiResponse}
                  </pre>
                </div>
              </div>
            )}

            {aiLoading && (
              <div className="text-center py-12">
                <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-2xl flex items-center justify-center mx-auto mb-4 animate-pulse">
                  <span className="text-3xl">🤖</span>
                </div>
                <div className="text-white text-xl font-semibold mb-2">AI is analyzing your data...</div>
                <div className="text-white/60 text-sm">This may take a few moments</div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
