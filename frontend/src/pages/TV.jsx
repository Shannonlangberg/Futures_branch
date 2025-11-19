import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import SeriesRow from '../components/tv/SeriesRow';
import VideoCard from '../components/tv/VideoCard';

const TV = () => {
  const [series, setSeries] = useState([]);
  const [continueWatching, setContinueWatching] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Fetch all series
      const seriesResponse = await fetch('/api/tv/series', {
        credentials: 'include'
      });
      
      if (seriesResponse.ok) {
        const seriesData = await seriesResponse.json();
        setSeries(seriesData.series || []);
      }
      
      // Fetch continue watching
      const continueResponse = await fetch('/api/tv/continue-watching', {
        credentials: 'include'
      });
      
      if (continueResponse.ok) {
        const continueData = await continueResponse.json();
        setContinueWatching(continueData.episodes || []);
      }
      
      setLoading(false);
    } catch (err) {
      console.error('Error fetching TV data:', err);
      setError('Failed to load content');
      setLoading(false);
    }
  };

  // Group series by category
  const seriesByCategory = {
    foundations: series.filter(s => s.category === 'foundations'),
    leadership: series.filter(s => s.category === 'leadership'),
    parents: series.filter(s => s.category === 'parents'),
    youth: series.filter(s => s.category === 'youth'),
    other: series.filter(s => !['foundations', 'leadership', 'parents', 'youth'].includes(s.category))
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-white text-xl">Loading Pulse TV...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-red-400 text-xl">{error}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Hero Header */}
      <div className="relative bg-gradient-to-r from-purple-600 via-pink-600 to-blue-600 py-16 mb-8">
        <div className="max-w-7xl mx-auto px-6">
          <h1 className="text-5xl font-bold text-white mb-4">Pulse TV</h1>
          <p className="text-xl text-white/90">
            Watch teaching series, discipleship content, and more
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 pb-12">
        {/* Continue Watching */}
        {continueWatching.length > 0 && (
          <SeriesRow
            title="Continue Watching"
            episodes={continueWatching}
          />
        )}

        {/* Foundations Pathway */}
        {seriesByCategory.foundations.length > 0 && (
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-white mb-4">Foundations Pathway</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
              {seriesByCategory.foundations.map((s) => (
                <Link
                  key={s.id}
                  to={`/tv/series/${s.id}`}
                  className="group relative block bg-slate-800 rounded-xl overflow-hidden hover:scale-105 transition-transform duration-300"
                >
                  <div className="relative aspect-video bg-gradient-to-br from-purple-900 to-blue-900">
                    {s.thumbnail_url ? (
                      <img
                        src={s.thumbnail_url}
                        alt={s.title}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <span className="text-white/50 text-4xl">📺</span>
                      </div>
                    )}
                    <div className="absolute inset-0 bg-black/40 group-hover:bg-black/20 transition-colors" />
                  </div>
                  <div className="p-4">
                    <h3 className="text-white font-semibold text-sm line-clamp-2 group-hover:text-purple-300 transition-colors">
                      {s.title}
                    </h3>
                    {s.episode_count > 0 && (
                      <p className="text-xs text-slate-400 mt-1">
                        {s.episode_count} {s.episode_count === 1 ? 'episode' : 'episodes'}
                      </p>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}

        {/* Leadership Track */}
        {seriesByCategory.leadership.length > 0 && (
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-white mb-4">Leadership Track</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
              {seriesByCategory.leadership.map((s) => (
                <Link
                  key={s.id}
                  to={`/tv/series/${s.id}`}
                  className="group relative block bg-slate-800 rounded-xl overflow-hidden hover:scale-105 transition-transform duration-300"
                >
                  <div className="relative aspect-video bg-gradient-to-br from-purple-900 to-blue-900">
                    {s.thumbnail_url ? (
                      <img
                        src={s.thumbnail_url}
                        alt={s.title}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <span className="text-white/50 text-4xl">📺</span>
                      </div>
                    )}
                    <div className="absolute inset-0 bg-black/40 group-hover:bg-black/20 transition-colors" />
                  </div>
                  <div className="p-4">
                    <h3 className="text-white font-semibold text-sm line-clamp-2 group-hover:text-purple-300 transition-colors">
                      {s.title}
                    </h3>
                    {s.episode_count > 0 && (
                      <p className="text-xs text-slate-400 mt-1">
                        {s.episode_count} {s.episode_count === 1 ? 'episode' : 'episodes'}
                      </p>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}

        {/* For Parents */}
        {seriesByCategory.parents.length > 0 && (
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-white mb-4">For Parents</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
              {seriesByCategory.parents.map((s) => (
                <Link
                  key={s.id}
                  to={`/tv/series/${s.id}`}
                  className="group relative block bg-slate-800 rounded-xl overflow-hidden hover:scale-105 transition-transform duration-300"
                >
                  <div className="relative aspect-video bg-gradient-to-br from-purple-900 to-blue-900">
                    {s.thumbnail_url ? (
                      <img
                        src={s.thumbnail_url}
                        alt={s.title}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <span className="text-white/50 text-4xl">📺</span>
                      </div>
                    )}
                    <div className="absolute inset-0 bg-black/40 group-hover:bg-black/20 transition-colors" />
                  </div>
                  <div className="p-4">
                    <h3 className="text-white font-semibold text-sm line-clamp-2 group-hover:text-purple-300 transition-colors">
                      {s.title}
                    </h3>
                    {s.episode_count > 0 && (
                      <p className="text-xs text-slate-400 mt-1">
                        {s.episode_count} {s.episode_count === 1 ? 'episode' : 'episodes'}
                      </p>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}

        {/* Youth */}
        {seriesByCategory.youth.length > 0 && (
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-white mb-4">Youth</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
              {seriesByCategory.youth.map((s) => (
                <Link
                  key={s.id}
                  to={`/tv/series/${s.id}`}
                  className="group relative block bg-slate-800 rounded-xl overflow-hidden hover:scale-105 transition-transform duration-300"
                >
                  <div className="relative aspect-video bg-gradient-to-br from-purple-900 to-blue-900">
                    {s.thumbnail_url ? (
                      <img
                        src={s.thumbnail_url}
                        alt={s.title}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <span className="text-white/50 text-4xl">📺</span>
                      </div>
                    )}
                    <div className="absolute inset-0 bg-black/40 group-hover:bg-black/20 transition-colors" />
                  </div>
                  <div className="p-4">
                    <h3 className="text-white font-semibold text-sm line-clamp-2 group-hover:text-purple-300 transition-colors">
                      {s.title}
                    </h3>
                    {s.episode_count > 0 && (
                      <p className="text-xs text-slate-400 mt-1">
                        {s.episode_count} {s.episode_count === 1 ? 'episode' : 'episodes'}
                      </p>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}

        {/* All Series */}
        {series.length === 0 && (
          <div className="text-center py-16">
            <p className="text-slate-400 text-lg">No series available yet</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default TV;

