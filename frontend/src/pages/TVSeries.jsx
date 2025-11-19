import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeftIcon } from '@heroicons/react/24/outline';
import VideoCard from '../components/tv/VideoCard';

const TVSeries = () => {
  const { id } = useParams();
  const [series, setSeries] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchSeries();
  }, [id]);

  const fetchSeries = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/tv/series/${id}`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        setSeries(data.series);
      } else {
        setError('Series not found');
      }
      setLoading(false);
    } catch (err) {
      console.error('Error fetching series:', err);
      setError('Failed to load series');
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  if (error || !series) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-red-400 text-xl">{error || 'Series not found'}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Header */}
      <div className="relative bg-gradient-to-r from-purple-600 via-pink-600 to-blue-600 py-16 mb-8">
        <div className="max-w-7xl mx-auto px-6">
          <Link
            to="/tv"
            className="inline-flex items-center gap-2 text-white/80 hover:text-white mb-4 transition-colors"
          >
            <ArrowLeftIcon className="w-5 h-5" />
            <span>Back to Pulse TV</span>
          </Link>
          
          {series.thumbnail_url && (
            <div className="mb-4">
              <img
                src={series.thumbnail_url}
                alt={series.title}
                className="w-32 h-32 rounded-xl object-cover"
              />
            </div>
          )}
          
          <h1 className="text-4xl font-bold text-white mb-2">{series.title}</h1>
          {series.description && (
            <p className="text-lg text-white/90 max-w-3xl">{series.description}</p>
          )}
        </div>
      </div>

      {/* Episodes */}
      <div className="max-w-7xl mx-auto px-6 pb-12">
        <h2 className="text-2xl font-bold text-white mb-6">
          Episodes ({series.episodes?.length || 0})
        </h2>
        
        {series.episodes && series.episodes.length > 0 ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
            {series.episodes.map((episode) => (
              <VideoCard
                key={episode.id}
                episode={episode}
                series={series}
                showProgress={true}
                progress={episode.progress}
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-16">
            <p className="text-slate-400 text-lg">No episodes available</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default TVSeries;

