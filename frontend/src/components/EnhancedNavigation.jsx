import React, { useState, useMemo } from 'react';
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
  AcademicCapIcon,
  PlayIcon,
  ListBulletIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  Squares2X2Icon,
  UsersIcon,
  HandRaisedIcon,
  SparklesIcon,
  UserPlusIcon,
  StarIcon
} from '@heroicons/react/24/outline';

// Navigation groups for better organization
const NAVIGATION_GROUPS = {
  core: {
    name: 'Core',
    icon: Squares2X2Icon,
    items: [
      { name: 'Home', href: '/', icon: HomeIcon, roles: ['admin', 'senior_leadership', 'senior_leader', 'senior_pastor', 'lead_pastor', 'campus_pastor', 'pastor', 'user'], featureKey: 'home' },
      { name: 'Dashboard', href: '/dashboard', icon: DocumentChartBarIcon, roles: ['admin', 'senior_leadership', 'senior_leader', 'senior_pastor', 'lead_pastor', 'campus_pastor', 'pastor', 'user'], featureKey: 'dashboard' },
      { name: 'Input', href: '/stats', icon: ClipboardIcon, roles: ['admin', 'senior_leadership', 'senior_leader', 'senior_pastor', 'lead_pastor', 'campus_pastor', 'pastor', 'user'], featureKey: 'input' },
    ]
  },
  engagement: {
    name: 'Engagement',
    icon: HeartIcon,
    items: [
      { 
        name: 'People', 
        href: '/people', 
        icon: UserGroupIcon, 
        roles: ['admin', 'senior_leadership', 'senior_leader', 'senior_pastor', 'lead_pastor', 'campus_pastor', 'staff'], 
        featureKey: 'people',
        subItems: [
          { name: 'People', href: '/people', icon: UserGroupIcon },
          { name: 'Families', href: '/people/families', icon: UsersIcon },
          { name: 'Heartbeat', href: '/people/heartbeat', icon: HeartIcon },
          { name: 'Pastoral Care', href: '/people/pastoral-care', icon: HandRaisedIcon },
          { name: 'New People', href: '/people/new-people', icon: UserPlusIcon },
          { name: 'New Christians', href: '/people/new-christians', icon: SparklesIcon },
          { name: 'Attendance', href: '/people/attendance', icon: CalendarIcon },
          { name: 'Groups', href: '/connect-groups', icon: UserGroupIcon }
        ]
      },
      { name: 'Heartbeat', href: '/heartbeat', icon: HeartIcon, roles: ['admin', 'senior_leadership', 'senior_leader', 'senior_pastor', 'lead_pastor', 'campus_pastor', 'staff'], featureKey: 'heartbeat' },
      { name: 'Connect Groups', href: '/connect-groups', icon: UserGroupIcon, roles: ['admin', 'senior_leadership', 'senior_leader', 'senior_pastor', 'lead_pastor', 'campus_pastor', 'staff', 'connect_group_leader'], featureKey: 'connect_groups' },
      { name: 'Prayer & Praise', href: '/prayer', icon: HeartIcon, roles: ['admin', 'senior_leadership', 'senior_leader', 'senior_pastor', 'lead_pastor', 'campus_pastor', 'pastor', 'staff'], featureKey: 'prayer' },
      { name: 'Serving', href: '/serving', icon: UserGroupIcon, roles: ['admin', 'senior_leadership', 'senior_leader', 'senior_pastor', 'lead_pastor', 'campus_pastor', 'pastor', 'staff'], featureKey: 'serving' },
    ]
  },
  content: {
    name: 'Content',
    icon: PlayIcon,
    items: [
      { name: 'Pulse TV', href: '/tv', icon: PlayIcon, roles: ['admin', 'senior_leadership', 'senior_leader', 'senior_pastor', 'lead_pastor', 'campus_pastor', 'pastor', 'user', 'staff', 'finance'], featureKey: 'pulse_tv' },
      { name: 'Events', href: '/events', icon: CalendarIcon, roles: ['admin', 'senior_leadership', 'senior_leader', 'senior_pastor', 'lead_pastor', 'campus_pastor', 'pastor', 'user', 'staff'], featureKey: 'events' },
      { name: 'Resources', href: '/resources', icon: BookOpenIcon, roles: ['admin', 'senior_leadership', 'senior_leader', 'senior_pastor', 'lead_pastor'], featureKey: 'resources' },
      { name: 'Devotions', href: '/devotions', icon: BookOpenIcon, roles: ['admin', 'senior_leadership', 'senior_leader', 'senior_pastor', 'lead_pastor', 'campus_pastor', 'pastor', 'user', 'staff'], featureKey: 'devotions' },
    ]
  },
  finance: {
    name: 'Finance',
    icon: CurrencyDollarIcon,
    items: [
      { name: 'Finance', href: '/finance', icon: CurrencyDollarIcon, roles: ['admin', 'finance', 'senior_leadership', 'senior_leader', 'senior_pastor', 'lead_pastor'], featureKey: 'finance' },
      { name: 'Giving', href: '/giving-analytics', icon: ChartBarIcon, roles: ['admin', 'finance', 'senior_leadership', 'senior_leader', 'senior_pastor', 'lead_pastor'], featureKey: 'giving' },
    ]
  },
  communications: {
    name: 'Communications',
    icon: EnvelopeIcon,
    items: [
      { name: 'Communications', href: '/communication', icon: EnvelopeIcon, roles: ['admin', 'senior_leadership', 'senior_leader', 'senior_pastor', 'lead_pastor', 'campus_pastor'], featureKey: 'communication' },
    ]
  }
};

const EnhancedNavigation = ({ 
  userRole, 
  customPermissions, 
  userName, 
  onLogout,
  sidebarOpen,
  setSidebarOpen,
  settingsOpen,
  setSettingsOpen
}) => {
  const location = useLocation();
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedGroups, setExpandedGroups] = useState({});
  const [expandedItems, setExpandedItems] = useState({});
  const [viewMode, setViewMode] = useState('grouped'); // 'grouped' or 'flat'

  // Filter and get navigation items
  const getFilteredItems = () => {
    const allItems = [];
    
    Object.values(NAVIGATION_GROUPS).forEach(group => {
      const filteredGroupItems = group.items.filter(item => {
        // Pulse TV is visible to all authenticated users (unless explicitly denied)
        if (item.name === 'Pulse TV') {
          if (item.featureKey && customPermissions[item.featureKey] === false) {
            return false;
          }
          return true;
        }
        
        // Check custom permissions first (overrides role defaults)
        if (item.featureKey && customPermissions.hasOwnProperty(item.featureKey)) {
          return customPermissions[item.featureKey] === true;
        }
        
        // Then check role permission
        if (!item.roles.includes(userRole)) {
          return false;
        }
        
        return true;
      });
      
      if (filteredGroupItems.length > 0) {
        allItems.push(...filteredGroupItems.map(item => ({ ...item, group: group.name })));
      }
    });
    
    return allItems;
  };

  const allItems = useMemo(() => getFilteredItems(), [userRole, customPermissions]);

  // Filter by search term
  const filteredItems = useMemo(() => {
    if (!searchTerm) return allItems;
    const search = searchTerm.toLowerCase();
    return allItems.filter(item => 
      item.name.toLowerCase().includes(search) ||
      item.group?.toLowerCase().includes(search)
    );
  }, [allItems, searchTerm]);

  // Group items for grouped view
  const groupedItems = useMemo(() => {
    if (viewMode === 'flat') return { 'All': filteredItems };
    
    const grouped = {};
    filteredItems.forEach(item => {
      const groupName = item.group || 'Other';
      if (!grouped[groupName]) {
        grouped[groupName] = [];
      }
      grouped[groupName].push(item);
    });
    return grouped;
  }, [filteredItems, viewMode]);

  const toggleGroup = (groupName) => {
    setExpandedGroups(prev => ({
      ...prev,
      [groupName]: !prev[groupName]
    }));
  };

  const toggleItem = (itemName) => {
    setExpandedItems(prev => ({
      ...prev,
      [itemName]: !prev[itemName]
    }));
  };

  // Settings menu items
  const getSettingsItems = () => {
    const items = [
      { name: 'My Profile', href: '/profile', icon: UserCircleIcon, show: true, featureKey: null }
    ];

    const adminItems = [
      { name: 'Data Export', href: '/export', icon: DocumentChartBarIcon, featureKey: 'data_export' },
      { name: 'Users', href: '/users', icon: UserGroupIcon, featureKey: 'user_management' },
      { name: 'Role Manager', href: '/role-manager', icon: ShieldCheckIcon, featureKey: 'user_management' },
      { name: 'Campuses', href: '/campuses', icon: BuildingOfficeIcon, featureKey: 'campus_management' },
      { name: 'Beacon Management', href: '/beacons', icon: SignalIcon, featureKey: 'beacon_management' },
      { name: 'Journey Manager', href: '/journeys', icon: AcademicCapIcon, featureKey: 'pathway_manager' },
      { name: 'Resource Manager', href: '/resources/manage', icon: BookOpenIcon, featureKey: 'resource_manager' },
      { name: 'TV Manager', href: '/tv/manage', icon: PlayIcon, featureKey: 'tv_manager' },
      { name: 'Events Manager', href: '/events/manage', icon: CalendarIcon, featureKey: 'events_manager' },
      { name: 'Push Notifications', href: '/notifications', icon: BellIcon, featureKey: 'notifications' }
    ];

    adminItems.forEach(item => {
      let show = false;
      if (userRole === 'admin' || userRole === 'senior_leadership' || userRole === 'senior_leader' || userRole === 'senior_pastor' || userRole === 'lead_pastor') {
        if (item.featureKey && customPermissions.hasOwnProperty(item.featureKey)) {
          show = customPermissions[item.featureKey] === true;
        } else {
          show = true;
        }
      }
      items.push({ ...item, show });
    });

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

  const settingsItems = getSettingsItems();

  return (
    <>
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
            <Link to="/" className="flex items-center space-x-3 hover:opacity-80 transition-opacity">
              <img 
                src="/static/logo.png?v=3" 
                alt="Futures PULSE Logo" 
                className="h-8 w-auto object-contain"
              />
              <span className="text-white font-semibold text-lg">Futures PULSE</span>
            </Link>
            <button
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden p-1 rounded-md text-slate-400 hover:text-white hover:bg-slate-800"
            >
              <XMarkIcon className="h-5 w-5" />
            </button>
          </div>

          {/* Search Bar */}
          <div className="px-4 py-4 border-b border-slate-700/50 flex-shrink-0">
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-slate-400" />
              <input
                type="text"
                placeholder="Search navigation..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-white text-sm placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
              />
              {searchTerm && (
                <button
                  onClick={() => setSearchTerm('')}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-slate-400 hover:text-white"
                >
                  <XMarkIcon className="h-4 w-4" />
                </button>
              )}
            </div>
            
            {/* View Mode Toggle */}
            <div className="mt-2 flex gap-2">
              <button
                onClick={() => setViewMode('grouped')}
                className={`flex-1 px-2 py-1.5 text-xs rounded-md transition-all ${
                  viewMode === 'grouped'
                    ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                    : 'bg-slate-800/50 text-slate-400 border border-slate-700/50 hover:bg-slate-800'
                }`}
                title="Grouped view"
              >
                <FunnelIcon className="h-3 w-3 inline mr-1" />
                Grouped
              </button>
              <button
                onClick={() => setViewMode('flat')}
                className={`flex-1 px-2 py-1.5 text-xs rounded-md transition-all ${
                  viewMode === 'flat'
                    ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                    : 'bg-slate-800/50 text-slate-400 border border-slate-700/50 hover:bg-slate-800'
                }`}
                title="Flat view"
              >
                <ListBulletIcon className="h-3 w-3 inline mr-1" />
                Flat
              </button>
            </div>
          </div>

          {/* Navigation - Scrollable */}
          <nav className="flex-1 px-4 py-4 space-y-2 overflow-y-auto min-h-0 pb-4 scrollbar-thin scrollbar-thumb-slate-600 scrollbar-track-transparent">
            {viewMode === 'grouped' ? (
              // Grouped View
              Object.entries(groupedItems).map(([groupName, items]) => {
                const groupInfo = Object.values(NAVIGATION_GROUPS).find(g => g.name === groupName);
                const isExpanded = expandedGroups[groupName] !== false; // Default to expanded
                const GroupIcon = groupInfo?.icon || Squares2X2Icon;
                
                return (
                  <div key={groupName} className="mb-2">
                    <button
                      onClick={() => toggleGroup(groupName)}
                      className="w-full flex items-center justify-between px-3 py-2 text-xs font-semibold text-slate-400 hover:text-slate-300 transition-colors uppercase tracking-wider"
                    >
                      <div className="flex items-center gap-2">
                        <GroupIcon className="h-4 w-4" />
                        <span>{groupName}</span>
                        <span className="text-slate-600">({items.length})</span>
                      </div>
                      <ChevronDownIcon className={`h-4 w-4 transition-transform ${isExpanded ? '' : '-rotate-90'}`} />
                    </button>
                    
                    {isExpanded && (
                      <div className="mt-1 space-y-1">
                        {items.map((item) => {
                          const hasSubItems = item.subItems && item.subItems.length > 0;
                          const isItemExpanded = expandedItems[item.name] !== false; // Default to expanded
                          const isActive = location.pathname === item.href || (hasSubItems && item.subItems.some(sub => location.pathname === sub.href || location.pathname.startsWith(sub.href + '/')));
                          
                          if (hasSubItems) {
                            return (
                              <div key={item.name}>
                                <button
                                  onClick={() => toggleItem(item.name)}
                                  className={`
                                    w-full flex items-center justify-between px-4 py-2.5 text-sm font-medium rounded-lg transition-all duration-200
                                    ${isActive 
                                      ? 'bg-gradient-to-r from-blue-600/20 to-purple-600/20 text-white border border-blue-500/30' 
                                      : 'text-slate-300 hover:text-white hover:bg-slate-800/50'
                                    }
                                  `}
                                >
                                  <div className="flex items-center">
                                    <item.icon className={`mr-3 h-5 w-5 ${isActive ? 'text-blue-400' : 'text-slate-400'}`} />
                                    {item.name}
                                  </div>
                                  <ChevronDownIcon className={`h-4 w-4 transition-transform ${isItemExpanded ? '' : '-rotate-90'}`} />
                                </button>
                                
                                {isItemExpanded && (
                                  <div className="mt-1 ml-4 space-y-1 border-l border-slate-700/50 pl-2">
                                    {item.subItems.map((subItem) => {
                                      const isSubActive = location.pathname === subItem.href || location.pathname.startsWith(subItem.href + '/');
                                      return (
                                        <Link
                                          key={subItem.name}
                                          to={subItem.href}
                                          className={`
                                            flex items-center px-3 py-2 text-sm rounded-lg transition-all duration-200
                                            ${isSubActive 
                                              ? 'bg-gradient-to-r from-blue-600/20 to-purple-600/20 text-white border border-blue-500/30' 
                                              : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                                            }
                                          `}
                                          onClick={() => setSidebarOpen(false)}
                                        >
                                          <subItem.icon className={`mr-2 h-4 w-4 ${isSubActive ? 'text-blue-400' : 'text-slate-500'}`} />
                                          {subItem.name}
                                        </Link>
                                      );
                                    })}
                                  </div>
                                )}
                              </div>
                            );
                          }
                          
                          // Regular item without sub-items
                          return (
                            <Link
                              key={item.name}
                              to={item.href}
                              className={`
                                flex items-center px-4 py-2.5 text-sm font-medium rounded-lg transition-all duration-200
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
                      </div>
                    )}
                  </div>
                );
              })
            ) : (
              // Flat View
              <>
                {filteredItems.map((item) => {
                  const hasSubItems = item.subItems && item.subItems.length > 0;
                  const isItemExpanded = expandedItems[item.name] !== false;
                  const isActive = location.pathname === item.href || (hasSubItems && item.subItems.some(sub => location.pathname === sub.href || location.pathname.startsWith(sub.href + '/')));
                  
                  if (hasSubItems) {
                    return (
                      <div key={item.name}>
                        <button
                          onClick={() => toggleItem(item.name)}
                          className={`
                            w-full flex items-center justify-between px-4 py-2.5 text-sm font-medium rounded-lg transition-all duration-200
                            ${isActive 
                              ? 'bg-gradient-to-r from-blue-600/20 to-purple-600/20 text-white border border-blue-500/30' 
                              : 'text-slate-300 hover:text-white hover:bg-slate-800/50'
                            }
                          `}
                        >
                          <div className="flex items-center">
                            <item.icon className={`mr-3 h-5 w-5 ${isActive ? 'text-blue-400' : 'text-slate-400'}`} />
                            {item.name}
                          </div>
                          <ChevronDownIcon className={`h-4 w-4 transition-transform ${isItemExpanded ? '' : '-rotate-90'}`} />
                        </button>
                        
                        {isItemExpanded && (
                          <div className="mt-1 ml-4 space-y-1">
                            {item.subItems.map((subItem) => {
                              const isSubActive = location.pathname === subItem.href || location.pathname.startsWith(subItem.href + '/');
                              return (
                                <Link
                                  key={subItem.name}
                                  to={subItem.href}
                                  className={`
                                    flex items-center px-4 py-2.5 pl-8 text-sm font-medium rounded-lg transition-all duration-200
                                    ${isSubActive 
                                      ? 'bg-gradient-to-r from-blue-600/20 to-purple-600/20 text-white border border-blue-500/30 shadow-lg shadow-blue-500/20' 
                                      : 'text-slate-300 hover:text-white hover:bg-slate-800/50'
                                    }
                                  `}
                                  onClick={() => setSidebarOpen(false)}
                                >
                                  <subItem.icon className={`mr-3 h-5 w-5 ${isSubActive ? 'text-blue-400' : 'text-slate-400'}`} />
                                  {subItem.name}
                                </Link>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    );
                  }
                  
                  // Regular item without sub-items
                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      className={`
                        flex items-center px-4 py-2.5 text-sm font-medium rounded-lg transition-all duration-200
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
              </>
            )}

            {/* Settings Dropdown */}
            {settingsItems.length > 0 && (
              <div className="relative mt-4 pt-4 border-t border-slate-700/50">
                <button
                  onClick={() => setSettingsOpen(!settingsOpen)}
                  className={`
                    w-full flex items-center justify-between px-4 py-2.5 text-sm font-medium rounded-lg transition-all duration-200
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

                {settingsOpen && (
                  <div className="mt-1 space-y-1">
                    {settingsItems.map((item) => {
                      const isActive = location.pathname === item.href;
                      return (
                        <Link
                          key={item.name}
                          to={item.href}
                          className={`
                            flex items-center px-4 py-2.5 text-sm font-medium rounded-lg transition-all duration-200
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
                          {item.name}
                        </Link>
                      );
                    })}
                  </div>
                )}
              </div>
            )}
          </nav>

          {/* Footer with User Info and Logout */}
          <div className="p-4 border-t border-slate-700/50 space-y-3 flex-shrink-0 bg-slate-900">
            <div className="px-4 py-2 bg-slate-800/50 rounded-lg">
              <div className="text-sm text-slate-300 font-medium truncate">{userName}</div>
              <div className="text-xs text-slate-500">{getRoleDisplayName(userRole)}</div>
            </div>
            
            <button
              onClick={onLogout}
              className="w-full flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-all duration-200 text-red-300 hover:text-red-200 hover:bg-red-900/20"
            >
              <ArrowRightOnRectangleIcon className="mr-3 h-5 w-5" />
              Logout
            </button>
          </div>
        </div>
      </div>
    </>
  );
};

export default EnhancedNavigation;

