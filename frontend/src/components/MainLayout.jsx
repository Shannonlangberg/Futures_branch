import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  HomeIcon,
  ClipboardIcon,
  HeartIcon,
  UserCircleIcon,
  Cog6ToothIcon,
  MapPinIcon,
  Bars3Icon,
  XMarkIcon,
  ArrowRightOnRectangleIcon,
  ChevronDownIcon,
  UserGroupIcon,
  BuildingOfficeIcon,
  BellIcon,
  ShieldCheckIcon,
  ChartBarIcon,
  CurrencyDollarIcon,
  EnvelopeIcon,
  BookOpenIcon,
  SignalIcon,
  DocumentChartBarIcon,
  CalendarIcon,
  AcademicCapIcon
} from '@heroicons/react/24/outline';

const MainLayout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [dropdownPosition, setDropdownPosition] = useState('bottom');
  const [userRole, setUserRole] = useState('user');
  const [userName, setUserName] = useState('');
  const [currentUser, setCurrentUser] = useState(null);
  const location = useLocation();

  // Fetch user session data on component mount
  useEffect(() => {
    const fetchSessionData = async () => {
      try {
        const response = await fetch('/api/session');
        const data = await response.json();
        if (data.authenticated) {
          setUserRole(data.role || 'user');
          setUserName(data.full_name || 'User');
          setCurrentUser({
            id: data.id || 'unknown',
            username: data.username || 'User',
            full_name: data.full_name || 'User',
            role: data.role || 'user',
            campus: data.campus || 'all_campuses'
          });
        }
      } catch (error) {
        console.error('Error fetching session data:', error);
      }
    };

    fetchSessionData();
  }, []);

  // Reset dropdown position when settings close
  useEffect(() => {
    if (!settingsOpen) {
      setDropdownPosition('bottom');
    }
  }, [settingsOpen]);


  // Determine dropdown position to avoid cutoff
  const handleSettingsToggle = () => {
    if (!settingsOpen) {
      // Calculate if dropdown should appear above or below
      const settingsButton = document.querySelector('[data-settings-button]');
      if (settingsButton) {
        const rect = settingsButton.getBoundingClientRect();
        const viewportHeight = window.innerHeight;
        const sidebarHeight = window.innerHeight; // Sidebar height is full viewport height
        const dropdownHeight = Math.min(getSettingsItems().length * 48 + 16, 256); // 48px per item + padding
        
        // Check if dropdown would extend beyond the sidebar
        if (rect.bottom + dropdownHeight > sidebarHeight && rect.top > dropdownHeight) {
          setDropdownPosition('top');
        } else {
          setDropdownPosition('bottom');
        }
      }
    }
    setSettingsOpen(!settingsOpen);
  };

  // Filter navigation items based on user role and permissions
  const getNavigationItems = () => {
    const allItems = [
      // Core navigation - simplified to only show essential items
      { name: 'Home', href: '/', icon: HomeIcon, roles: ['admin', 'senior_leadership', 'senior_leader', 'senior_pastor', 'lead_pastor', 'campus_pastor', 'pastor', 'user'] },
      { name: 'Dashboard', href: '/dashboard', icon: DocumentChartBarIcon, roles: ['admin', 'senior_leadership', 'senior_leader', 'senior_pastor', 'lead_pastor', 'campus_pastor', 'pastor', 'user'] },
      { name: 'Input', href: '/stats', icon: ClipboardIcon, roles: ['admin', 'senior_leadership', 'senior_leader', 'senior_pastor', 'lead_pastor', 'campus_pastor', 'pastor', 'user'] },
      { name: 'Finance', href: '/finance', icon: CurrencyDollarIcon, roles: ['admin', 'finance', 'senior_leadership', 'senior_leader', 'senior_pastor', 'lead_pastor'] },
      { name: 'Giving Analytics', href: '/giving-analytics', icon: ChartBarIcon, roles: ['admin', 'finance', 'senior_leadership', 'senior_leader', 'senior_pastor', 'lead_pastor'] },
      { name: 'People', href: '/people', icon: UserGroupIcon, roles: ['admin', 'senior_leadership', 'senior_leader', 'senior_pastor', 'lead_pastor', 'campus_pastor', 'staff'] },
      { name: 'Heartbeat', href: '/heartbeat', icon: HeartIcon, roles: ['admin', 'senior_leadership', 'senior_leader', 'senior_pastor', 'lead_pastor', 'campus_pastor', 'staff'] },
      { name: 'Connect Groups', href: '/connect-groups', icon: UserGroupIcon, roles: ['admin', 'senior_leadership', 'senior_leader', 'senior_pastor', 'lead_pastor', 'campus_pastor', 'staff', 'connect_group_leader'] },
      { name: 'Resources', href: '/resources', icon: BookOpenIcon, roles: ['admin', 'senior_leadership', 'senior_leader', 'senior_pastor', 'lead_pastor'] },
      
      // Hidden items - commented out for now
      // { name: 'Heartbeat', href: '/heartbeat', icon: HeartIcon, roles: ['admin', 'senior_leadership', 'campus_pastor', 'finance'] },
      // { name: 'Devotions Admin', href: '/devotions/admin', icon: BookOpenIcon, roles: ['admin', 'senior_leadership', 'campus_pastor', 'staff'], featureFlag: 'DEVOTIONS_ADMIN_ENABLED' },
      // { name: 'Connect Groups', href: '/groups', icon: UserGroupIcon, roles: ['admin', 'senior_leadership', 'campus_pastor', 'staff'], featureFlag: 'GROUPS_FOR_STAFF_ENABLED' },
      // { name: 'Beacon Management', href: '/beacons', icon: SignalIcon, roles: ['admin'], featureFlag: 'BEACON_MGMT_ENABLED' },
      // { name: 'Passport', href: '/journey', icon: UserCircleIcon, roles: ['admin', 'senior_leadership', 'campus_pastor', 'finance'] },
      // { name: 'Communications', href: '/communications', icon: EnvelopeIcon, roles: ['admin', 'senior_leadership', 'campus_pastor'] },
      // { name: 'Devotions', href: '/devotions', icon: BookOpenIcon, roles: ['admin', 'senior_leadership', 'campus_pastor'] },
      // { name: 'Prayer Requests', href: '/prayer-requests', icon: HeartIcon, roles: ['admin', 'senior_leadership', 'campus_pastor'] },
      // { name: 'Events', href: '/events', icon: CalendarIcon, roles: ['admin', 'senior_leadership', 'campus_pastor', 'pastor', 'user'] },
      // { name: 'Event Management', href: '/events-admin', icon: Cog6ToothIcon, roles: ['admin', 'senior_leadership', 'campus_pastor'] },
      // { name: 'Serving', href: '/serving', icon: UserGroupIcon, roles: ['admin', 'senior_leadership', 'campus_pastor', 'pastor', 'team_leader'] },
      // { name: 'Finance Dashboard', href: '/finance', icon: CurrencyDollarIcon, roles: ['admin', 'finance'] },
    ];

    // Filter items based on user role and feature flags
    const filteredItems = allItems.filter(item => {
      // Check role permission
      if (!item.roles.includes(userRole)) {
        return false;
      }
      
      // Check feature flag if specified
      if (item.featureFlag) {
        // For now, we'll assume all feature flags are enabled
        // In a real implementation, you'd fetch this from the API
      }
      
      return true;
    });
    
    return filteredItems;
  };

  const navigation = getNavigationItems();

  // Settings menu items based on user role
  const getSettingsItems = () => {
    const items = [];

    // My Profile - available to all users
    items.push(
      { name: 'My Profile', href: '/profile', icon: UserCircleIcon, show: true }
    );

    // Admin-only items - only show fully functional pages
    if (userRole === 'admin' || userRole === 'senior_leadership' || userRole === 'senior_leader' || userRole === 'senior_pastor' || userRole === 'lead_pastor') {
      items.push(
        { name: 'Data Export', href: '/export', icon: DocumentChartBarIcon, show: true },
        { name: 'Users', href: '/users', icon: UserGroupIcon, show: true },
        { name: 'Campuses', href: '/campuses', icon: BuildingOfficeIcon, show: true },
        { name: 'Beacon Management', href: '/beacons', icon: SignalIcon, show: true },
        { name: 'Pathway Manager', href: '/pathways', icon: AcademicCapIcon, show: true },
        { name: 'Resource Manager', href: '/resources/manage', icon: BookOpenIcon, show: true }
      );
    }

    return items.filter(item => item.show);
  };

  const getRoleDisplayName = (role) => {
    const names = {
      'admin': 'Administrator',
      'senior_leadership': 'Senior Leadership',
      'senior_leader': 'Senior Leader',
      'senior_pastor': 'Senior Pastor',
      'lead_pastor': 'Lead Pastor',
      'campus_pastor': 'Campus Pastor',
      'pastor': 'Pastor',
      'finance': 'Finance'
    };
    return names[role] || role;
  };

  const handleLogout = async () => {
    try {
      await fetch('/api/logout', {
        method: 'POST',
        credentials: 'include',
      });
      window.location.href = '/login';
    } catch (error) {
      console.error('Logout error:', error);
      // Force logout on client side even if server fails
      window.location.href = '/login';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-40 bg-black bg-opacity-50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed inset-y-0 left-0 z-50 w-64 transform transition-transform duration-300 ease-in-out
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        bg-slate-900 border-r border-slate-700/50 flex flex-col
      `}>
        <div className="flex h-full flex-col min-h-0">
          {/* Logo/Brand */}
          <div className="flex h-16 items-center justify-between px-6 border-b border-slate-700/50 flex-shrink-0">
            <div className="flex items-center space-x-3">
              <img 
                src="/static/logo.png" 
                alt="Futures PULSE Logo" 
                className="h-8 w-auto object-contain"
              />
              <span className="text-white font-semibold text-lg">Futures PULSE</span>
            </div>
            <button
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden p-1 rounded-md text-slate-400 hover:text-white hover:bg-slate-800"
            >
              <XMarkIcon className="h-5 w-5" />
            </button>
          </div>

          {/* Navigation - Make it scrollable */}
          <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto min-h-0 pb-4 scrollbar-thin scrollbar-thumb-slate-600 scrollbar-track-transparent">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`
                    flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-all duration-200
                    ${isActive 
                      ? 'bg-gradient-to-r from-blue-600/20 to-purple-600/20 text-white border border-blue-500/30 shadow-lg shadow-blue-500/20' 
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/50'
                    }
                  `}
                  onClick={() => setSidebarOpen(false)}
                >
                  <item.icon className={`mr-3 h-5 w-5 ${isActive ? 'text-blue-400' : 'text-slate-400'}`} />
                  {item.name}
                </Link>
              );
            })}

            {/* Settings Dropdown - Only show if user has access */}
            {getSettingsItems().length > 0 && (
              <div className="relative">
                <button
                  data-settings-button
                  onClick={handleSettingsToggle}
                  className={`
                    w-full flex items-center justify-between px-4 py-3 text-sm font-medium rounded-lg transition-all duration-200
                    ${settingsOpen 
                      ? 'bg-gradient-to-r from-blue-600/20 to-purple-600/20 text-white border border-blue-500/30 shadow-lg shadow-blue-500/20' 
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/50'
                    }
                  `}
                >
                  <div className="flex items-center">
                    <Cog6ToothIcon className={`mr-3 h-5 w-5 ${settingsOpen ? 'text-blue-400' : 'text-slate-400'}`} />
                    Settings
                  </div>
                  <ChevronDownIcon className={`h-4 w-4 transition-transform duration-200 ${settingsOpen ? 'rotate-180' : ''}`} />
                </button>

                {/* Settings Dropdown Menu */}
                {settingsOpen && (
                  <div className={`
                    absolute left-0 right-0 bg-slate-800 border border-slate-700 rounded-lg shadow-lg z-10 
                    settings-dropdown
                    ${dropdownPosition === 'top' 
                      ? 'bottom-full mb-1' 
                      : 'top-full mt-1'
                    }
                  `}>
                    {getSettingsItems().map((item) => {
                      const isActive = location.pathname === item.href;
                      return (
                        <Link
                          key={item.name}
                          to={item.href}
                          className={`
                            flex items-center px-4 py-3 text-sm font-medium transition-all duration-200
                            ${isActive 
                              ? 'bg-blue-600/20 text-blue-400' 
                              : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
                            }
                          `}
                          onClick={() => {
                            setSettingsOpen(false);
                            setSidebarOpen(false);
                          }}
                        >
                          <item.icon className={`mr-3 h-5 w-5 ${isActive ? 'text-blue-400' : 'text-slate-400'}`} />
                          <span className="truncate">{item.name}</span>
                        </Link>
                      );
                    })}
                  </div>
                )}
              </div>
            )}
          </nav>

          {/* Footer with User Info and Logout - Make it non-scrollable */}
          <div className="p-4 border-t border-slate-700/50 space-y-3 flex-shrink-0 bg-slate-900">
            {/* User Info */}
            <div className="px-4 py-2 bg-slate-800/50 rounded-lg">
              <div className="text-sm text-slate-300 font-medium">{userName}</div>
              <div className="text-xs text-slate-500">{getRoleDisplayName(userRole)}</div>
            </div>
            
            <button
              onClick={handleLogout}
              className="w-full flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-all duration-200 text-red-300 hover:text-red-200 hover:bg-red-900/20"
            >
              <ArrowRightOnRectangleIcon className="mr-3 h-5 w-5" />
              Logout
            </button>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Mobile header */}
        <div className="lg:hidden flex items-center justify-between p-4 border-b border-slate-700/50">
          <button
            onClick={() => setSidebarOpen(true)}
            className="p-2 rounded-md text-slate-400 hover:text-white hover:bg-slate-800"
          >
            <Bars3Icon className="h-6 w-6" />
          </button>
          <div className="flex items-center space-x-2">
            <img 
              src="/static/logo.png" 
              alt="Futures PULSE Logo" 
              className="h-6 w-auto object-contain"
            />
            <span className="text-white font-semibold">Futures PULSE</span>
          </div>
          <button
            onClick={handleLogout}
            className="p-2 rounded-md text-red-400 hover:text-red-300 hover:bg-red-900/20"
          >
            <ArrowRightOnRectangleIcon className="h-5 w-5" />
          </button>
        </div>

        {/* Page content */}
        <main className="p-6">
          {children}
        </main>
      </div>
    </div>
  );
};

export default MainLayout; 