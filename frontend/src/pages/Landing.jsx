import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowTopRightOnSquareIcon,
  ClipboardDocumentListIcon,
  DocumentChartBarIcon,
  LifebuoyIcon,
  MegaphoneIcon,
  PlayCircleIcon,
  SparklesIcon,
  CurrencyDollarIcon,
  BookOpenIcon,
  Cog6ToothIcon,
  UserGroupIcon,
  ShieldCheckIcon,
  ChartBarIcon,
  BuildingOfficeIcon,
  UserCircleIcon,
  HeartIcon,
  ArrowsRightLeftIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';

const gradientBackground = 'bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950';

const getTimeOfDayGreeting = () => {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 18) return 'Good afternoon';
  return 'Good evening';
};

const Landing = () => {
  const [session, setSession] = useState(null);
  const [sessionLoading, setSessionLoading] = useState(true);
  const [categories, setCategories] = useState([]);
  const [categoriesLoading, setCategoriesLoading] = useState(true);
  const [previewRole, setPreviewRole] = useState(null);
  const [showRoleSwitcher, setShowRoleSwitcher] = useState(false);

  useEffect(() => {
    const fetchSession = async () => {
      setSessionLoading(true);
      try {
        const response = await fetch('/api/session', { credentials: 'include' });
        if (!response.ok) {
          throw new Error('Session fetch failed');
        }
        const data = await response.json();
        setSession(data || {});
      } catch (error) {
        console.error('Unable to load session data:', error);
        setSession(null);
      } finally {
        setSessionLoading(false);
      }
    };

    const fetchCategoryPreview = async () => {
      setCategoriesLoading(true);
      try {
        const response = await fetch('/api/resources/categories', { credentials: 'include' });
        if (!response.ok) {
          if (response.status === 403) {
            setCategories([]);
            return;
          }
          throw new Error('Categories fetch failed');
        }
        const data = await response.json();
        const categoryList = Array.isArray(data.categories) ? data.categories : [];
        setCategories(categoryList.slice(0, 3));
      } catch (error) {
        console.error('Unable to load resource categories:', error);
        setCategories([]);
      } finally {
        setCategoriesLoading(false);
      }
    };

    fetchSession();
    fetchCategoryPreview();
  }, []);

  const navigate = useNavigate();

  // Extract first name from full name
  const getFirstName = (fullName) => {
    if (!fullName) return 'team';
    return fullName.split(' ')[0];
  };

  // Get role-specific quick actions
  const getQuickActions = () => {
    // Use preview role if set (for beta role switcher), otherwise use actual role
    const userRole = previewRole || session?.role || 'user';
    const userCampus = session?.campus || 'all_campuses';
    const isCampusPastor = userRole === 'campus_pastor';
    
    const baseActions = [
      {
        name: 'Dashboard',
        description: 'Explore ministry metrics and weekend pulse data visualisations.',
        href: '/dashboard',
        icon: DocumentChartBarIcon,
        highlight: true
      },
      {
        name: 'Input',
        description: 'Submit the latest weekend figures and service insights.',
        href: '/stats',
        icon: ClipboardDocumentListIcon
      },
      {
        name: isCampusPastor ? 'Campus Heartbeat' : 'Heartbeat',
        description: isCampusPastor 
          ? 'Monitor your campus health and engagement metrics.'
          : 'Track health and engagement across your ministry.',
        href: '/heartbeat',
        icon: HeartIcon,
        highlight: true,
        hotRodRed: true
      },
      {
        name: 'Settings',
        description: 'Manage your profile and account settings.',
        href: '/profile',
        icon: Cog6ToothIcon
      },
    ];

    // Admin-specific actions
    if (userRole === 'admin') {
      return [
        ...baseActions,
        {
          name: 'User Management',
          description: 'Manage users, roles, and permissions across the platform.',
          href: '/users',
          icon: UserGroupIcon,
          highlight: true,
          adminOnly: true
        },
        {
          name: 'Campus Management',
          description: 'Configure campuses and their settings.',
          href: '/campuses',
          icon: BuildingOfficeIcon,
          adminOnly: true
        },
        {
          name: 'Resources',
          description: 'Manage and organize resource categories and files.',
          href: '/resources',
          icon: BookOpenIcon,
          highlight: true,
          adminOnly: true
        },
        {
          name: 'Finance',
          description: 'View and manage financial data across all campuses.',
          href: '/finance',
          icon: CurrencyDollarIcon,
          adminOnly: true
        },
        {
          name: 'People',
          description: 'Access the complete people database and health reports.',
          href: '/people',
          icon: UserCircleIcon,
          adminOnly: true
        },
        {
          name: 'Data Export',
          description: 'Export data for analysis and reporting.',
          href: '/export',
          icon: ChartBarIcon,
          adminOnly: true
        },
      ];
    }

    // Campus Pastor - special handling
    if (isCampusPastor) {
      return [
        ...baseActions,
        {
          name: 'Resources',
          description: 'Find templates, playbooks, and media to support your teams.',
          href: '/resources',
          icon: BookOpenIcon,
          highlight: true
        },
        {
          name: 'Finance',
          description: 'Submit tithe data and view financial reports.',
          href: '/finance',
          icon: CurrencyDollarIcon
        },
        {
          name: 'People',
          description: 'View people database and health reports.',
          href: '/people',
          icon: UserGroupIcon
        },
      ];
    }

    // Leadership roles
    if (['senior_leadership', 'senior_leader', 'senior_pastor', 'lead_pastor'].includes(userRole)) {
      return [
        ...baseActions,
        {
          name: 'Resources',
          description: 'Find templates, playbooks, and media to support your teams.',
          href: '/resources',
          icon: BookOpenIcon,
          highlight: true
        },
        {
          name: 'Finance',
          description: 'Submit tithe data and view financial reports.',
          href: '/finance',
          icon: CurrencyDollarIcon
        },
        {
          name: 'People',
          description: 'View people database and health reports.',
          href: '/people',
          icon: UserGroupIcon
        },
      ];
    }

    // Default actions for other roles
    return [
      ...baseActions,
      {
        name: 'Finance',
        description: 'Submit tithe data and view financial reports.',
        href: '/finance',
        icon: CurrencyDollarIcon
      },
    ];
  };

  const quickActions = useMemo(() => getQuickActions(), [session?.role, session?.campus, previewRole]);

  const featuredCategories = categories.filter(Boolean);

  const announcements = [
    {
      title: 'New volunteer onboarding kit',
      description: 'Download the refreshed onboarding guide for campus teams.',
      href: '/resources',
      type: 'update'
    },
    {
      title: 'Weekend pulse refresher',
      description: 'Watch the 5-minute walkthrough on capturing post-service highlights.',
      href: '/resources',
      type: 'training'
    }
  ];

  const supportItems = [
    {
      title: 'Need help?',
      description: 'Email the Ops team for assistance with access or data questions.',
      action: 'ops@futures.church'
    },
    {
      title: 'Share feedback',
      description: 'Suggest new resources or features to keep PULSE moving forward.',
      action: 'feedback@futures.church'
    }
  ];

  const greeting = getTimeOfDayGreeting();
  const firstName = getFirstName(session?.full_name) || session?.username || 'team';
  const actualRole = session?.role || 'user';
  const displayRole = previewRole || actualRole;
  const isAdmin = actualRole === 'admin';
  const isDisplayingAdmin = displayRole === 'admin';
  // Beta mode - always show role switcher for admins
  const isBetaMode = true; // Always enabled for admins to preview roles

  return (
    <div className={`min-h-screen ${gradientBackground} text-white`}>
      <div className="relative">
        <div className="fixed inset-0 pointer-events-none overflow-hidden">
          <div className="absolute -top-40 -left-20 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse" />
          <div className="absolute bottom-0 right-0 w-[28rem] h-[28rem] bg-purple-500/10 rounded-full blur-3xl animate-pulse delay-700" />
          <div className="absolute top-1/3 left-1/3 w-80 h-80 bg-teal-500/10 rounded-full blur-3xl animate-pulse delay-[1200ms]" />
          <div className="absolute top-2/3 right-1/4 w-72 h-72 bg-red-600/15 rounded-full blur-3xl animate-pulse delay-[800ms]" />
        </div>

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 py-8 sm:py-10 space-y-10 sm:space-y-12">
          <header className="bg-gradient-to-br from-white/5 via-white/5 to-white/5 border border-white/10 rounded-3xl p-6 sm:p-8 md:p-12 backdrop-blur-md shadow-xl shadow-blue-500/10 relative overflow-hidden">
            {isDisplayingAdmin && (
              <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-purple-500/20 to-blue-500/20 rounded-full blur-3xl -mr-32 -mt-32 animate-pulse" />
            )}
            <div className="absolute top-0 left-0 w-32 h-1 bg-gradient-to-r from-red-600 via-red-500 to-transparent rounded-tl-3xl" />
            <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-6 lg:gap-8 relative z-10">
              <div className="space-y-3 sm:space-y-4">
                <div className="inline-flex items-center gap-2 text-blue-300 text-sm font-medium bg-blue-500/10 border border-blue-400/40 rounded-full px-3 py-1">
                  <SparklesIcon className="h-4 w-4" />
                  {sessionLoading ? 'Loading profile...' : (previewRole ? `Preview: ${previewRole.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}` : (isAdmin ? 'Admin Dashboard - Futures PULSE' : 'Welcome to Futures PULSE'))}
                </div>
                <div className="space-y-2 sm:space-y-3">
                  <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold tracking-tight bg-gradient-to-r from-white via-blue-100 to-white bg-clip-text text-transparent">
                    {sessionLoading ? 'Loading...' : `${greeting}, ${firstName}!`}
                  </h1>
                  <p className="text-white/70 text-sm sm:text-base lg:text-lg max-w-2xl leading-relaxed">
                    {previewRole 
                      ? `Previewing view as ${previewRole.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}`
                      : (isDisplayingAdmin 
                        ? 'Your command center for managing Futures PULSE—oversee users, campuses, resources, and data across the entire platform.'
                        : 'Your launchpad for the week ahead—track key metrics, share weekend stories, and access the resources your teams rely on.'
                      )
                    }
                  </p>
                  {previewRole && (
                    <div className="flex items-center gap-2 mt-3">
                      <div className="flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-yellow-500/20 to-orange-500/20 border border-yellow-400/40 rounded-lg">
                        <ArrowsRightLeftIcon className="h-4 w-4 text-yellow-300" />
                        <span className="text-xs font-medium text-yellow-200">Role Preview Mode</span>
                      </div>
                    </div>
                  )}
                  {isAdmin && !previewRole && (
                    <div className="flex items-center gap-2 mt-3">
                      <div className="flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-purple-500/20 to-blue-500/20 border border-purple-400/40 rounded-lg">
                        <ShieldCheckIcon className="h-4 w-4 text-purple-300" />
                        <span className="text-xs font-medium text-purple-200">Administrator Access</span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
              <div className="bg-gradient-to-br from-blue-600/20 to-purple-600/20 border border-white/10 rounded-2xl p-5 sm:p-6 w-full max-w-full sm:max-w-sm">
                <div className="flex items-center gap-3 text-white/80 text-sm">
                  <MegaphoneIcon className="h-6 w-6 text-blue-300" />
                  Platform updates land here—check back regularly for new drops.
                </div>
                <div className="mt-4 space-y-3">
                  {announcements.map((item) => (
                    <a
                      key={item.title}
                      href={item.href}
                      className="block bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl px-3 sm:px-4 py-3 transition-all duration-200 group"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <div>
                          <p className="text-sm font-semibold text-white group-hover:text-blue-200">{item.title}</p>
                          <p className="text-xs text-white/50 leading-snug">{item.description}</p>
                        </div>
                        <ArrowTopRightOnSquareIcon className="h-4 w-4 text-white/40 group-hover:text-blue-200" />
                      </div>
                    </a>
                  ))}
                </div>
              </div>
            </div>
          </header>

          <section className="space-y-5 sm:space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-4">
              <div>
                <h2 className="text-xl sm:text-2xl font-semibold">Get moving</h2>
                <p className="text-white/60 text-sm sm:text-base">Jump straight into the actions that matter most today.</p>
              </div>
              <span className="text-xs uppercase tracking-[0.2em] text-white/40">Quick links</span>
            </div>
            <div className={`grid grid-cols-1 md:grid-cols-2 ${isDisplayingAdmin ? 'xl:grid-cols-3' : 'xl:grid-cols-5'} gap-4 sm:gap-6`}>
              {quickActions.map((action, index) => (
                <button
                  key={action.name}
                  onClick={() => navigate(action.href)}
                  className={`
                    group rounded-2xl border p-5 sm:p-6 transition-all duration-300 text-left
                    ${action.hotRodRed
                      ? 'border-red-500/50 bg-gradient-to-br from-red-600/15 to-red-500/10 hover:from-red-600/25 hover:to-red-500/20 shadow-lg shadow-red-500/30'
                      : action.highlight 
                        ? 'border-blue-400/40 bg-gradient-to-br from-blue-500/10 to-purple-500/10 hover:from-blue-500/20 hover:to-purple-500/20 shadow-lg shadow-blue-500/20' 
                        : 'border-white/10 bg-white/5 hover:bg-white/10 shadow-sm shadow-black/10'
                    }
                    hover:-translate-y-2 hover:scale-[1.02] hover:shadow-xl
                    ${action.adminOnly ? 'ring-2 ring-purple-500/30' : ''}
                  `}
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  <div className="flex items-center justify-between gap-4">
                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center transition-transform duration-300 group-hover:scale-110 ${
                      action.hotRodRed
                        ? 'bg-gradient-to-br from-red-600/40 to-red-500/30 text-red-200'
                        : action.highlight 
                          ? 'bg-gradient-to-br from-blue-500/30 to-purple-500/30 text-blue-200' 
                          : 'bg-blue-500/15 text-blue-200'
                    }`}>
                      <action.icon className="h-6 w-6" />
                    </div>
                    <ArrowTopRightOnSquareIcon className={`h-4 w-4 text-white/30 group-hover:translate-x-1 group-hover:-translate-y-1 transition-all duration-300 ${
                      action.hotRodRed 
                        ? 'group-hover:text-red-300' 
                        : 'group-hover:text-blue-200'
                    }`} />
                  </div>
                  <div className="mt-4 sm:mt-5 space-y-2">
                    <div className="flex items-center gap-2">
                      <h3 className={`text-base sm:text-lg font-semibold leading-snug transition-colors ${
                        action.hotRodRed 
                          ? 'group-hover:text-red-300' 
                          : 'group-hover:text-blue-200'
                      }`}>{action.name}</h3>
                      {action.adminOnly && (
                        <span className="text-xs px-2 py-0.5 bg-purple-500/20 text-purple-300 rounded-full border border-purple-400/40">
                          Admin
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-white/60 leading-relaxed group-hover:text-white/80 transition-colors">
                      {action.description}
                    </p>
                  </div>
                </button>
              ))}
            </div>
          </section>

          {!isDisplayingAdmin && (
          <section className="space-y-5 sm:space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-4">
              <div>
                <h2 className="text-xl sm:text-2xl font-semibold">Resource spotlight</h2>
                <p className="text-white/60 text-sm sm:text-base">
                  Recently added folders from the Futures resource library.
                </p>
              </div>
              <a
                href="/resources"
                className="inline-flex items-center gap-2 text-sm text-blue-200 hover:text-blue-100 transition-colors duration-200"
              >
                Browse full library
                <ArrowTopRightOnSquareIcon className="h-4 w-4" />
              </a>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-6">
              {categoriesLoading && (
                <div className="col-span-full bg-white/5 border border-white/10 rounded-2xl p-5 sm:p-6 text-white/60">
                  Loading featured folders...
                </div>
              )}
              {!categoriesLoading && featuredCategories.length === 0 && (
                <div className="col-span-full bg-white/5 border border-white/10 rounded-2xl p-5 sm:p-6 text-white/60">
                  No shared folders yet—check back soon or reach out to the Ops team.
                </div>
              )}
              {featuredCategories.map((category) => (
                <a
                  key={category.id}
                  href="/resources"
                  className="group bg-gradient-to-br from-slate-900/60 to-slate-900/30 border border-white/10 rounded-2xl p-5 sm:p-6 transition-all duration-200 hover:border-blue-400/40 hover:-translate-y-1"
                >
                  <div className="flex items-center justify-between gap-4">
                    <div className="w-12 h-12 rounded-xl bg-blue-500/15 flex items-center justify-center text-2xl">
                      📁
                    </div>
                    <ArrowTopRightOnSquareIcon className="h-4 w-4 text-white/30 group-hover:text-blue-200" />
                  </div>
                  <div className="mt-5 space-y-2">
                    <h3 className="text-lg font-semibold text-white group-hover:text-blue-200 transition-colors duration-200">
                      {category.name}
                    </h3>
                    {category.description && (
                      <p className="text-sm text-white/60 leading-relaxed line-clamp-3">
                        {category.description}
                      </p>
                    )}
                  </div>
                </a>
              ))}
            </div>
          </section>
          )}

          {isDisplayingAdmin && (
          <section className="space-y-5 sm:space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-4">
              <div>
                <h2 className="text-xl sm:text-2xl font-semibold flex items-center gap-2">
                  <ShieldCheckIcon className="h-6 w-6 text-purple-400" />
                  Admin Quick Stats
                </h2>
                <p className="text-white/60 text-sm sm:text-base">
                  Key metrics and system overview at a glance.
                </p>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-6">
              <div className="bg-gradient-to-br from-blue-500/10 to-purple-500/10 border border-blue-400/30 rounded-2xl p-6 hover:scale-105 transition-transform duration-300">
                <div className="flex items-center justify-between mb-4">
                  <UserGroupIcon className="h-8 w-8 text-blue-300" />
                  <span className="text-2xl font-bold text-blue-200">—</span>
                </div>
                <h3 className="text-lg font-semibold text-white mb-1">User Management</h3>
                <p className="text-sm text-white/60">Manage all users and permissions</p>
                <button
                  onClick={() => navigate('/users')}
                  className="mt-4 text-sm text-blue-300 hover:text-blue-200 flex items-center gap-1 group"
                >
                  Go to Users
                  <ArrowTopRightOnSquareIcon className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
                </button>
              </div>
              <div className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 border border-purple-400/30 rounded-2xl p-6 hover:scale-105 transition-transform duration-300">
                <div className="flex items-center justify-between mb-4">
                  <BuildingOfficeIcon className="h-8 w-8 text-purple-300" />
                  <span className="text-2xl font-bold text-purple-200">—</span>
                </div>
                <h3 className="text-lg font-semibold text-white mb-1">Campus Management</h3>
                <p className="text-sm text-white/60">Configure campus settings</p>
                <button
                  onClick={() => navigate('/campuses')}
                  className="mt-4 text-sm text-purple-300 hover:text-purple-200 flex items-center gap-1 group"
                >
                  Go to Campuses
                  <ArrowTopRightOnSquareIcon className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
                </button>
              </div>
              <div className="bg-gradient-to-br from-teal-500/10 to-cyan-500/10 border border-teal-400/30 rounded-2xl p-6 hover:scale-105 transition-transform duration-300">
                <div className="flex items-center justify-between mb-4">
                  <BookOpenIcon className="h-8 w-8 text-teal-300" />
                  <span className="text-2xl font-bold text-teal-200">—</span>
                </div>
                <h3 className="text-lg font-semibold text-white mb-1">Resource Manager</h3>
                <p className="text-sm text-white/60">Organize and manage resources</p>
                <button
                  onClick={() => navigate('/resources/manage')}
                  className="mt-4 text-sm text-teal-300 hover:text-teal-200 flex items-center gap-1 group"
                >
                  Manage Resources
                  <ArrowTopRightOnSquareIcon className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
                </button>
              </div>
            </div>
          </section>
          )}

          <section className="space-y-5 sm:space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-4">
              <div>
                <h2 className="text-xl sm:text-2xl font-semibold">Support & feedback</h2>
                <p className="text-white/60 text-sm sm:text-base">
                  We’re here to help keep things moving smoothly for your campus.
                </p>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
              {supportItems.map((item) => (
                <div
                  key={item.title}
                  className="bg-white/5 border border-white/10 rounded-2xl p-5 sm:p-6 space-y-3"
                >
                  <div className="flex items-center gap-3">
                    <LifebuoyIcon className="h-6 w-6 text-blue-300" />
                    <h3 className="text-lg font-semibold">{item.title}</h3>
                  </div>
                  <p className="text-sm text-white/60 leading-relaxed">
                    {item.description}
                  </p>
                  <a
                    href={`mailto:${item.action}`}
                    className="inline-flex items-center gap-2 text-sm text-blue-200 hover:text-blue-100 transition-colors duration-200"
                  >
                    {item.action}
                    <ArrowTopRightOnSquareIcon className="h-4 w-4" />
                  </a>
                </div>
              ))}
            </div>
          </section>

          {/* Beta Role Switcher - Only visible to admins */}
          {isAdmin && isBetaMode && (
            <div className="fixed bottom-6 right-6 z-[9999]">
              {!showRoleSwitcher ? (
                <button
                  onClick={() => setShowRoleSwitcher(true)}
                  className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white px-5 py-3 rounded-xl shadow-2xl hover:shadow-purple-500/50 transition-all duration-300 flex items-center gap-2 font-semibold text-sm border-2 border-purple-400/60 hover:scale-105"
                >
                  <ArrowsRightLeftIcon className="h-5 w-5" />
                  <span>Preview Roles</span>
                </button>
              ) : (
                <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 border border-white/20 rounded-2xl p-4 shadow-2xl backdrop-blur-md min-w-[280px]">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-white font-semibold text-sm flex items-center gap-2">
                      <ArrowsRightLeftIcon className="h-4 w-4 text-purple-300" />
                      Role Preview
                    </h3>
                    <button
                      onClick={() => {
                        setShowRoleSwitcher(false);
                        setPreviewRole(null);
                      }}
                      className="text-white/60 hover:text-white transition-colors"
                    >
                      <XMarkIcon className="h-5 w-5" />
                    </button>
                  </div>
                  <div className="space-y-2">
                    <button
                      onClick={() => setPreviewRole(null)}
                      className={`w-full text-left px-3 py-2 rounded-lg transition-all duration-200 ${
                        !previewRole
                          ? 'bg-gradient-to-r from-purple-500/30 to-blue-500/30 border border-purple-400/50 text-white'
                          : 'bg-white/5 hover:bg-white/10 text-white/70 hover:text-white border border-white/10'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">Your Role ({actualRole})</span>
                        {!previewRole && <span className="text-xs text-purple-300">Active</span>}
                      </div>
                    </button>
                    {['admin', 'campus_pastor', 'senior_leadership', 'senior_pastor', 'lead_pastor', 'staff', 'user'].map((role) => (
                      <button
                        key={role}
                        onClick={() => setPreviewRole(role === actualRole ? null : role)}
                        className={`w-full text-left px-3 py-2 rounded-lg transition-all duration-200 ${
                          previewRole === role
                            ? 'bg-gradient-to-r from-yellow-500/30 to-orange-500/30 border border-yellow-400/50 text-white'
                            : 'bg-white/5 hover:bg-white/10 text-white/70 hover:text-white border border-white/10'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium capitalize">{role.replace('_', ' ')}</span>
                          {previewRole === role && <span className="text-xs text-yellow-300">Previewing</span>}
                        </div>
                      </button>
                    ))}
                  </div>
                  {previewRole && (
                    <div className="mt-3 pt-3 border-t border-white/10">
                      <button
                        onClick={() => setPreviewRole(null)}
                        className="w-full px-3 py-2 bg-red-500/20 hover:bg-red-500/30 border border-red-400/50 text-red-200 rounded-lg text-sm font-medium transition-all duration-200"
                      >
                        Clear Preview
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Landing;

