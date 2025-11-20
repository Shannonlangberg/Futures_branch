import React, { useState, useEffect } from 'react';
import { 
  CalendarIcon, 
  MapPinIcon, 
  ClockIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  ChevronDownIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';

const Events = () => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [campusFilter, setCampusFilter] = useState('all_campuses');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [campuses, setCampuses] = useState([]);
  const [categories, setCategories] = useState([]);
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    fetchCampuses();
    fetchEvents();
  }, [campusFilter, categoryFilter]);

  const fetchCampuses = async () => {
    try {
      const response = await fetch('/api/campuses', {
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

  const fetchEvents = async () => {
    try {
      setLoading(true);
      let url = `/api/events?upcoming=true`;
      if (campusFilter !== 'all_campuses') {
        url += `&campus=${campusFilter}`;
      }
      if (categoryFilter !== 'all') {
        url += `&category=${categoryFilter}`;
      }

      const response = await fetch(url, {
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        setEvents(data.events || []);
      }
    } catch (error) {
      console.error('Error fetching events:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return {
      weekday: date.toLocaleDateString('en-US', { weekday: 'long' }),
      month: date.toLocaleDateString('en-US', { month: 'short' }),
      day: date.getDate(),
      year: date.getFullYear(),
      time: date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
    };
  };

  const filteredEvents = events.filter(event => {
    const matchesSearch = searchTerm === '' || 
      event.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      event.description?.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesSearch;
  });

  // Extract unique categories from events
  useEffect(() => {
    const uniqueCategories = [...new Set(events.map(e => e.category?.name).filter(Boolean))];
    setCategories(uniqueCategories);
  }, [events]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600/90 via-purple-600/90 to-pink-600/90 backdrop-blur-sm border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2">Events</h1>
              <p className="text-white/80">Upcoming church events and gatherings</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Filters & Search */}
        <div className="bg-slate-800/50 rounded-2xl p-6 mb-8 border border-white/10">
          <div className="flex flex-col md:flex-row gap-4">
            {/* Search */}
            <div className="flex-1 relative">
              <MagnifyingGlassIcon className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-slate-400" />
              <input
                type="text"
                placeholder="Search events..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-12 pr-4 py-3 bg-slate-700/50 border border-white/10 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Campus Filter */}
            <div className="relative">
              <select
                value={campusFilter}
                onChange={(e) => setCampusFilter(e.target.value)}
                className="appearance-none bg-slate-700/50 border border-white/10 rounded-xl px-4 py-3 pr-10 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer"
              >
                <option value="all_campuses">All Campuses</option>
                {campuses
                  .filter(c => c.id !== 'all_campuses')
                  .map(campus => (
                    <option key={campus.id} value={campus.id}>
                      {campus.name}
                    </option>
                  ))}
              </select>
              <ChevronDownIcon className="absolute right-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-slate-400 pointer-events-none" />
            </div>

            {/* Category Filter */}
            {categories.length > 0 && (
              <div className="relative">
                <select
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                  className="appearance-none bg-slate-700/50 border border-white/10 rounded-xl px-4 py-3 pr-10 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer"
                >
                  <option value="all">All Categories</option>
                  {categories.map(cat => (
                    <option key={cat} value={cat}>
                      {cat}
                    </option>
                  ))}
                </select>
                <ChevronDownIcon className="absolute right-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-slate-400 pointer-events-none" />
              </div>
            )}
          </div>
        </div>

        {/* Events Grid */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-white text-xl">Loading events...</div>
          </div>
        ) : filteredEvents.length === 0 ? (
          <div className="text-center py-20">
            <CalendarIcon className="h-20 w-20 text-slate-600 mx-auto mb-4" />
            <h3 className="text-2xl font-semibold text-white mb-2">No Events Found</h3>
            <p className="text-slate-400">No upcoming events match your filters.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredEvents.map((event) => {
              const dateInfo = formatDate(event.start_datetime || event.start_time);
              return (
                <div
                  key={event.id}
                  className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 rounded-2xl p-6 border border-white/10 hover:border-blue-500/50 transition-all duration-300 hover:shadow-xl hover:shadow-blue-500/20"
                >
                  {/* Date Badge */}
                  <div className="flex items-start justify-between mb-4">
                    <div className="bg-blue-500/20 rounded-xl px-4 py-2 border border-blue-500/30">
                      <div className="text-blue-400 font-bold text-sm uppercase">{dateInfo.weekday}</div>
                      <div className="text-white text-2xl font-bold">{dateInfo.day}</div>
                      <div className="text-slate-400 text-xs uppercase">{dateInfo.month} {dateInfo.year}</div>
                    </div>
                    {event.requires_payment && event.price && (
                      <div className="bg-green-500/20 rounded-lg px-3 py-1 border border-green-500/30">
                        <span className="text-green-400 font-semibold text-sm">
                          ${parseFloat(event.price).toFixed(2)}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Event Title */}
                  <h3 className="text-xl font-bold text-white mb-2 line-clamp-2">
                    {event.title}
                  </h3>

                  {/* Event Details */}
                  <div className="space-y-2 mb-4">
                    {(event.start_datetime || event.start_time) && (
                      <div className="flex items-center text-slate-400 text-sm">
                        <ClockIcon className="h-4 w-4 mr-2" />
                        {dateInfo.time}
                      </div>
                    )}
                    {event.location && (
                      <div className="flex items-center text-slate-400 text-sm">
                        <MapPinIcon className="h-4 w-4 mr-2" />
                        {event.location}
                      </div>
                    )}
                    {event.campus && event.campus !== 'all_campuses' && (
                      <div className="flex items-center text-slate-400 text-sm">
                        <span className="text-xs bg-slate-700/50 rounded px-2 py-1">
                          {campuses.find(c => c.id === event.campus)?.name || event.campus}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Description */}
                  {event.description && (
                    <p className="text-slate-300 text-sm mb-4 line-clamp-3">
                      {event.description}
                    </p>
                  )}

                  {/* RSVP Button */}
                  <button
                    className="w-full bg-gradient-to-r from-blue-500 to-purple-500 text-white py-3 rounded-xl font-semibold hover:scale-105 transition-transform duration-200"
                  >
                    View Details
                  </button>
                </div>
              );
            })}
          </div>
        )}

        {/* Summary */}
        {!loading && filteredEvents.length > 0 && (
          <div className="mt-8 text-center text-slate-400">
            Showing {filteredEvents.length} of {events.length} upcoming events
          </div>
        )}
      </div>
    </div>
  );
};

export default Events;

