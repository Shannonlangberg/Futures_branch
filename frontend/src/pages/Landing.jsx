import React, { useEffect, useMemo, useState } from 'react';
import {
  ArrowTopRightOnSquareIcon,
  ClipboardDocumentListIcon,
  DocumentChartBarIcon,
  LifebuoyIcon,
  MegaphoneIcon,
  PlayCircleIcon,
  SparklesIcon,
  UserGroupIcon
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

  const quickActions = useMemo(() => ([
    {
      name: 'View Dashboards',
      description: 'Explore ministry metrics and weekend pulse data visualisations.',
      href: '/dashboard',
      icon: DocumentChartBarIcon,
      highlight: true
    },
    {
      name: 'Weekend Pulse Input',
      description: 'Submit the latest weekend figures and service insights.',
      href: '/stats',
      icon: ClipboardDocumentListIcon
    },
    {
      name: 'Team Resources',
      description: 'Find templates, playbooks, and media to support your teams.',
      href: '/resources',
      icon: PlayCircleIcon,
      highlight: true
    },
    {
      name: 'People & Campuses',
      description: 'Manage campuses, teams, and user access (admins only).',
      href: '/campuses',
      icon: UserGroupIcon
    }
  ]), []);

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
  const displayName = session?.full_name || session?.username || 'team';

  return (
    <div className={`min-h-screen ${gradientBackground} text-white`}>
      <div className="relative">
        <div className="fixed inset-0 pointer-events-none overflow-hidden">
          <div className="absolute -top-40 -left-20 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse" />
          <div className="absolute bottom-0 right-0 w-[28rem] h-[28rem] bg-purple-500/10 rounded-full blur-3xl animate-pulse delay-700" />
          <div className="absolute top-1/3 left-1/3 w-80 h-80 bg-teal-500/10 rounded-full blur-3xl animate-pulse delay-[1200ms]" />
        </div>

        <div className="relative max-w-7xl mx-auto px-6 py-10 space-y-12">
          <header className="bg-white/5 border border-white/10 rounded-3xl p-8 md:p-12 backdrop-blur-md shadow-xl shadow-blue-500/10">
            <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-8">
              <div className="space-y-4">
                <div className="inline-flex items-center gap-2 text-blue-300 text-sm font-medium bg-blue-500/10 border border-blue-400/40 rounded-full px-3 py-1">
                  <SparklesIcon className="h-4 w-4" />
                  {sessionLoading ? 'Loading profile...' : 'Welcome to Futures PULSE'}
                </div>
                <div className="space-y-2">
                  <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">
                    {sessionLoading ? 'Loading...' : `${greeting}, ${displayName}.`}
                  </h1>
                  <p className="text-white/70 text-base sm:text-lg max-w-2xl leading-relaxed">
                    Your launchpad for the week ahead—track key metrics, share weekend stories, and access the resources your teams rely on.
                  </p>
                </div>
              </div>
              <div className="bg-gradient-to-br from-blue-600/20 to-purple-600/20 border border-white/10 rounded-2xl p-6 w-full max-w-sm">
                <div className="flex items-center gap-3 text-white/80 text-sm">
                  <MegaphoneIcon className="h-6 w-6 text-blue-300" />
                  Platform updates land here—check back regularly for new drops.
                </div>
                <div className="mt-4 space-y-3">
                  {announcements.map((item) => (
                    <a
                      key={item.title}
                      href={item.href}
                      className="block bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl px-4 py-3 transition-all duration-200 group"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <div>
                          <p className="text-sm font-semibold text-white group-hover:text-blue-200">{item.title}</p>
                          <p className="text-xs text-white/50">{item.description}</p>
                        </div>
                        <ArrowTopRightOnSquareIcon className="h-4 w-4 text-white/40 group-hover:text-blue-200" />
                      </div>
                    </a>
                  ))}
                </div>
              </div>
            </div>
          </header>

          <section className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <h2 className="text-2xl font-semibold">Get moving</h2>
                <p className="text-white/60 text-sm">Jump straight into the actions that matter most today.</p>
              </div>
              <span className="text-xs uppercase tracking-[0.2em] text-white/40">Quick links</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
              {quickActions.map((action) => (
                <a
                  key={action.name}
                  href={action.href}
                  className={`
                    group rounded-2xl border border-white/10 p-6 transition-transform duration-200
                    bg-white/5 hover:bg-white/10 hover:-translate-y-1
                    ${action.highlight ? 'shadow-lg shadow-blue-500/10' : 'shadow-sm shadow-black/10'}
                  `}
                >
                  <div className="flex items-center justify-between gap-4">
                    <div className="w-12 h-12 rounded-xl bg-blue-500/15 flex items-center justify-center text-blue-200">
                      <action.icon className="h-6 w-6" />
                    </div>
                    <ArrowTopRightOnSquareIcon className="h-4 w-4 text-white/30 group-hover:text-blue-200" />
                  </div>
                  <div className="mt-5 space-y-2">
                    <h3 className="text-lg font-semibold leading-snug">{action.name}</h3>
                    <p className="text-sm text-white/60 leading-relaxed">
                      {action.description}
                    </p>
                  </div>
                </a>
              ))}
            </div>
          </section>

          <section className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <h2 className="text-2xl font-semibold">Resource spotlight</h2>
                <p className="text-white/60 text-sm">
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
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {categoriesLoading && (
                <div className="col-span-full bg-white/5 border border-white/10 rounded-2xl p-6 text-white/60">
                  Loading featured folders...
                </div>
              )}
              {!categoriesLoading && featuredCategories.length === 0 && (
                <div className="col-span-full bg-white/5 border border-white/10 rounded-2xl p-6 text-white/60">
                  No shared folders yet—check back soon or reach out to the Ops team.
                </div>
              )}
              {featuredCategories.map((category) => (
                <a
                  key={category.id}
                  href="/resources"
                  className="group bg-gradient-to-br from-slate-900/60 to-slate-900/30 border border-white/10 rounded-2xl p-6 transition-all duration-200 hover:border-blue-400/40 hover:-translate-y-1"
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

          <section className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <h2 className="text-2xl font-semibold">Support & feedback</h2>
                <p className="text-white/60 text-sm">
                  We’re here to help keep things moving smoothly for your campus.
                </p>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {supportItems.map((item) => (
                <div
                  key={item.title}
                  className="bg-white/5 border border-white/10 rounded-2xl p-6 space-y-3"
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
        </div>
      </div>
    </div>
  );
};

export default Landing;

