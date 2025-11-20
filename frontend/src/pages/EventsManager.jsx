import React, { useState, useEffect } from 'react';
import {
  CalendarIcon,
  PlusIcon,
  PencilIcon,
  TrashIcon,
  ClockIcon,
  MapPinIcon,
  XMarkIcon,
  CurrencyDollarIcon
} from '@heroicons/react/24/outline';

const EventsManager = () => {
  const [events, setEvents] = useState([]);
  const [categories, setCategories] = useState([]);
  const [campuses, setCampuses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingEvent, setEditingEvent] = useState(null);
  const [campusFilter, setCampusFilter] = useState('all_campuses');
  const [statusFilter, setStatusFilter] = useState('all'); // all, upcoming, past

  const [formData, setFormData] = useState({
    title: '',
    description: '',
    short_description: '',
    category_id: '',
    campus: 'all_campuses',
    location: '',
    start_datetime: '',
    end_datetime: '',
    price: '',
    requires_payment: false,
    stripe_price_id: '',
    max_capacity: '',
    contact_person: '',
    contact_email: '',
    contact_phone: '',
    image_url: '',
    additional_info: ''
  });

  useEffect(() => {
    fetchEvents();
    fetchCategories();
    fetchCampuses();
  }, [campusFilter, statusFilter]);

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

  const fetchCategories = async () => {
    try {
      const response = await fetch('/api/events/categories', {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setCategories(data.categories || []);
      }
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  const fetchEvents = async () => {
    try {
      setLoading(true);
      let url = '/api/events?upcoming=all';
      if (campusFilter !== 'all_campuses') {
        url += `&campus=${campusFilter}`;
      }

      const response = await fetch(url, {
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        let filtered = data.events || [];
        
        // Filter by status
        const now = new Date();
        if (statusFilter === 'upcoming') {
          filtered = filtered.filter(e => new Date(e.start_datetime || e.start_time) > now);
        } else if (statusFilter === 'past') {
          filtered = filtered.filter(e => new Date(e.start_datetime || e.start_time) < now);
        }
        
        setEvents(filtered);
      }
    } catch (error) {
      console.error('Error fetching events:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const openCreateModal = () => {
    setEditingEvent(null);
    setFormData({
      title: '',
      description: '',
      short_description: '',
      category_id: '',
      campus: 'all_campuses',
      location: '',
      start_datetime: '',
      end_datetime: '',
      price: '',
      requires_payment: false,
      stripe_price_id: '',
      max_capacity: '',
      contact_person: '',
      contact_email: '',
      contact_phone: '',
      image_url: '',
      additional_info: ''
    });
    setShowModal(true);
  };

  const openEditModal = (event) => {
    setEditingEvent(event);
    const startTime = event.start_datetime || event.start_time;
    const endTime = event.end_datetime || event.end_time;
    
    // Format datetime for input field (YYYY-MM-DDTHH:mm)
    const formatForInput = (isoString) => {
      if (!isoString) return '';
      const date = new Date(isoString);
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      const hours = String(date.getHours()).padStart(2, '0');
      const minutes = String(date.getMinutes()).padStart(2, '0');
      return `${year}-${month}-${day}T${hours}:${minutes}`;
    };
    
    setFormData({
      title: event.title || '',
      description: event.description || '',
      short_description: event.short_description || '',
      category_id: event.category_id || event.category?.id || '',
      campus: event.campus || 'all_campuses',
      location: event.location || '',
      start_datetime: formatForInput(startTime),
      end_datetime: formatForInput(endTime),
      price: event.price || '',
      requires_payment: event.requires_payment || false,
      stripe_price_id: event.stripe_price_id || '',
      max_capacity: event.max_capacity || '',
      contact_person: event.contact_person || '',
      contact_email: event.contact_email || '',
      contact_phone: event.contact_phone || '',
      image_url: event.image_url || '',
      additional_info: event.additional_info || ''
    });
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const url = editingEvent 
        ? `/api/events/${editingEvent.id}`
        : '/api/events';
      
      const method = editingEvent ? 'PUT' : 'POST';
      
      // Convert datetime to ISO format
      const payload = {
        ...formData,
        start_datetime: formData.start_datetime ? new Date(formData.start_datetime).toISOString() : null,
        end_datetime: formData.end_datetime ? new Date(formData.end_datetime).toISOString() : null,
        price: formData.price ? parseFloat(formData.price) : null,
        max_capacity: formData.max_capacity ? parseInt(formData.max_capacity) : null,
        category_id: parseInt(formData.category_id) || null
      };

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        setShowModal(false);
        fetchEvents();
      } else {
        const error = await response.json();
        alert(error.error || 'Failed to save event');
      }
    } catch (error) {
      console.error('Error saving event:', error);
      alert('Failed to save event');
    }
  };

  const handleDelete = async (event) => {
    if (!confirm(`Are you sure you want to delete "${event.title}"?`)) {
      return;
    }

    try {
      const response = await fetch(`/api/events/${event.id}`, {
        method: 'DELETE',
        credentials: 'include',
      });

      if (response.ok) {
        fetchEvents();
      } else {
        const error = await response.json();
        alert(error.error || 'Failed to delete event');
      }
    } catch (error) {
      console.error('Error deleting event:', error);
      alert('Failed to delete event');
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return {
      date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
      time: date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
    };
  };

  const filteredEvents = events;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900/20 to-slate-900 p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2">Events Manager</h1>
            <p className="text-white/60">Manage church events - synced with Futures App</p>
          </div>
          <button
            onClick={openCreateModal}
            className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl font-semibold hover:shadow-lg hover:shadow-purple-500/50 transition-all"
          >
            <PlusIcon className="w-5 h-5" />
            New Event
          </button>
        </div>

        {/* Filters */}
        <div className="mt-6 flex gap-3 flex-wrap">
          <select
            value={campusFilter}
            onChange={(e) => setCampusFilter(e.target.value)}
            className="px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-purple-500"
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

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-purple-500"
          >
            <option value="all">All Events</option>
            <option value="upcoming">Upcoming</option>
            <option value="past">Past</option>
          </select>
        </div>
      </div>

      {/* Events List */}
      <div className="max-w-7xl mx-auto">
        {loading ? (
          <div className="text-center text-white/60 py-20">Loading events...</div>
        ) : filteredEvents.length === 0 ? (
          <div className="text-center text-white/60 py-20">
            No events found. Click "New Event" to create one.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredEvents.map((event) => {
              const dateInfo = formatDate(event.start_datetime || event.start_time);
              return (
                <div
                  key={event.id}
                  className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6 hover:bg-white/10 transition-all"
                >
                  {/* Event Header */}
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex items-start gap-3 flex-1">
                      <div className="p-3 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-xl">
                        <CalendarIcon className="w-6 h-6 text-blue-400" />
                      </div>
                      <div className="flex-1">
                        <h3 className="text-xl font-bold text-white mb-1 line-clamp-2">
                          {event.title}
                        </h3>
                        {event.category && (
                          <p className="text-sm text-white/60">{event.category.name}</p>
                        )}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => openEditModal(event)}
                        className="p-2 bg-white/10 hover:bg-white/20 rounded-lg transition-all"
                      >
                        <PencilIcon className="w-4 h-4 text-white/80" />
                      </button>
                      <button
                        onClick={() => handleDelete(event)}
                        className="p-2 bg-red-500/20 hover:bg-red-500/30 rounded-lg transition-all"
                      >
                        <TrashIcon className="w-4 h-4 text-red-400" />
                      </button>
                    </div>
                  </div>

                  {/* Event Details */}
                  <div className="space-y-2 mb-4">
                    <div className="flex items-center gap-2 text-white/70 text-sm">
                      <ClockIcon className="w-4 h-4 text-yellow-400" />
                      <span>{dateInfo.date} at {dateInfo.time}</span>
                    </div>
                    
                    {event.location && (
                      <div className="flex items-center gap-2 text-white/70 text-sm">
                        <MapPinIcon className="w-4 h-4 text-green-400" />
                        <span>{event.location}</span>
                      </div>
                    )}

                    {event.campus && event.campus !== 'all_campuses' && (
                      <div className="flex items-center gap-2 text-white/70 text-sm">
                        <span className="text-xs bg-white/10 px-2 py-1 rounded">
                          {campuses.find(c => c.id === event.campus)?.name || event.campus}
                        </span>
                      </div>
                    )}

                    {event.requires_payment && event.price && (
                      <div className="flex items-center gap-2 text-white/70 text-sm">
                        <CurrencyDollarIcon className="w-4 h-4 text-green-400" />
                        <span className="font-semibold">${parseFloat(event.price).toFixed(2)}</span>
                      </div>
                    )}
                  </div>

                  {/* Description */}
                  {event.description && (
                    <p className="text-slate-300 text-sm mb-4 line-clamp-3">
                      {event.description}
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Create/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-800 rounded-2xl p-6 max-w-3xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-white">
                {editingEvent ? 'Edit Event' : 'Create New Event'}
              </h2>
              <button
                onClick={() => setShowModal(false)}
                className="p-2 hover:bg-white/10 rounded-lg transition-all"
              >
                <XMarkIcon className="w-6 h-6 text-white/60" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Basic Info */}
              <div>
                <label className="block text-sm font-medium text-white/80 mb-2">
                  Event Title *
                </label>
                <input
                  type="text"
                  name="title"
                  value={formData.title}
                  onChange={handleInputChange}
                  required
                  className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-purple-500"
                  placeholder="Leadership Summit 2026"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-white/80 mb-2">
                    Category *
                  </label>
                  <select
                    name="category_id"
                    value={formData.category_id}
                    onChange={handleInputChange}
                    required
                    className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-purple-500"
                  >
                    <option value="">Select category</option>
                    {categories.map(cat => (
                      <option key={cat.id} value={cat.id} className="bg-slate-800">
                        {cat.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-white/80 mb-2">
                    Campus
                  </label>
                  <select
                    name="campus"
                    value={formData.campus}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-purple-500"
                  >
                    <option value="all_campuses">All Campuses</option>
                    {campuses
                      .filter(c => c.id !== 'all_campuses')
                      .map(campus => (
                        <option key={campus.id} value={campus.id} className="bg-slate-800">
                          {campus.name}
                        </option>
                      ))}
                  </select>
                </div>
              </div>

              {/* Date & Time */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-white/80 mb-2">
                    Start Date & Time *
                  </label>
                  <input
                    type="datetime-local"
                    name="start_datetime"
                    value={formData.start_datetime}
                    onChange={handleInputChange}
                    required
                    className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-purple-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-white/80 mb-2">
                    End Date & Time
                  </label>
                  <input
                    type="datetime-local"
                    name="end_datetime"
                    value={formData.end_datetime}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-purple-500"
                  />
                </div>
              </div>

              {/* Location */}
              <div>
                <label className="block text-sm font-medium text-white/80 mb-2">
                  Location
                </label>
                <input
                  type="text"
                  name="location"
                  value={formData.location}
                  onChange={handleInputChange}
                  className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-purple-500"
                  placeholder="Main Auditorium, 123 Main St"
                />
              </div>

              {/* Payment Fields */}
              <div className="border-t border-white/10 pt-4">
                <h3 className="text-lg font-semibold text-white mb-4">Payment Settings</h3>
                
                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      name="requires_payment"
                      checked={formData.requires_payment}
                      onChange={handleInputChange}
                      className="w-5 h-5 rounded border-white/20 bg-white/5 text-purple-500 focus:ring-purple-500"
                    />
                    <label className="text-white/80">This event requires payment</label>
                  </div>

                  {formData.requires_payment && (
                    <>
                      <div>
                        <label className="block text-sm font-medium text-white/80 mb-2">
                          Price ($)
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          name="price"
                          value={formData.price}
                          onChange={handleInputChange}
                          className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-purple-500"
                          placeholder="25.00"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-white/80 mb-2">
                          Stripe Price ID (optional)
                        </label>
                        <input
                          type="text"
                          name="stripe_price_id"
                          value={formData.stripe_price_id}
                          onChange={handleInputChange}
                          className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-purple-500"
                          placeholder="price_xxxxx"
                        />
                      </div>
                    </>
                  )}
                </div>
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-white/80 mb-2">
                  Description
                </label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  rows={4}
                  className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-purple-500"
                  placeholder="Event description..."
                />
              </div>

              {/* Additional Info */}
              <div>
                <label className="block text-sm font-medium text-white/80 mb-2">
                  Additional Info
                </label>
                <textarea
                  name="additional_info"
                  value={formData.additional_info}
                  onChange={handleInputChange}
                  rows={3}
                  className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-purple-500"
                  placeholder="What to bring, parking info, etc..."
                />
              </div>

              {/* Contact Info */}
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-white/80 mb-2">
                    Contact Person
                  </label>
                  <input
                    type="text"
                    name="contact_person"
                    value={formData.contact_person}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-purple-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-white/80 mb-2">
                    Contact Email
                  </label>
                  <input
                    type="email"
                    name="contact_email"
                    value={formData.contact_email}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-purple-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-white/80 mb-2">
                    Contact Phone
                  </label>
                  <input
                    type="tel"
                    name="contact_phone"
                    value={formData.contact_phone}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-purple-500"
                  />
                </div>
              </div>

              {/* Max Capacity */}
              <div>
                <label className="block text-sm font-medium text-white/80 mb-2">
                  Max Capacity
                </label>
                <input
                  type="number"
                  name="max_capacity"
                  value={formData.max_capacity}
                  onChange={handleInputChange}
                  className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-purple-500"
                  placeholder="100"
                />
              </div>

              {/* Submit Buttons */}
              <div className="flex gap-3 pt-4 border-t border-white/10">
                <button
                  type="submit"
                  className="flex-1 px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl font-semibold hover:shadow-lg hover:shadow-purple-500/50 transition-all"
                >
                  {editingEvent ? 'Update Event' : 'Create Event'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-6 py-3 bg-white/10 text-white rounded-xl font-semibold hover:bg-white/20 transition-all"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default EventsManager;

