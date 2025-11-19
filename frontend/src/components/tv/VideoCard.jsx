import React from 'react';
import { Link } from 'react-router-dom';
import { PlayIcon, ClockIcon } from '@heroicons/react/24/outline';

const VideoCard = ({ episode, series, showProgress = false, progress = null }) => {
  const thumbnailUrl = series?.thumbnail_url || episode?.thumbnail_url || '/static/logo.png';
  const duration = episode?.duration_formatted || '0:00';
  const progressPercent = progress && episode?.duration_seconds 
    ? (progress.last_position_seconds / episode.duration_seconds) * 100 
    : 0;

  return (
    <Link
      to={`/tv/watch/${episode.id}`}
      className="group relative block bg-slate-800 rounded-xl overflow-hidden hover:scale-105 transition-transform duration-300"
    >
      {/* Thumbnail */}
      <div className="relative aspect-video bg-gradient-to-br from-purple-900 to-blue-900">
        {thumbnailUrl && thumbnailUrl.startsWith('http') ? (
          <img
            src={thumbnailUrl}
            alt={episode.title}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <PlayIcon className="w-16 h-16 text-white/50" />
          </div>
        )}
        
        {/* Progress bar overlay */}
        {showProgress && progress && progressPercent > 0 && (
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-slate-700">
            <div
              className="h-full bg-gradient-to-r from-purple-500 to-blue-500"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        )}
        
        {/* Play overlay */}
        <div className="absolute inset-0 bg-black/40 group-hover:bg-black/20 transition-colors flex items-center justify-center">
          <div className="w-16 h-16 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center group-hover:scale-110 transition-transform">
            <PlayIcon className="w-8 h-8 text-white ml-1" />
          </div>
        </div>
        
        {/* Duration badge */}
        <div className="absolute top-2 right-2 bg-black/70 backdrop-blur-sm px-2 py-1 rounded flex items-center gap-1 text-xs text-white">
          <ClockIcon className="w-3 h-3" />
          {duration}
        </div>
      </div>
      
      {/* Info */}
      <div className="p-4">
        {series && (
          <p className="text-xs text-slate-400 mb-1">{series.title}</p>
        )}
        <h3 className="text-white font-semibold text-sm line-clamp-2 group-hover:text-purple-300 transition-colors">
          {episode.title}
        </h3>
        {episode.description && (
          <p className="text-xs text-slate-400 mt-1 line-clamp-2">
            {episode.description}
          </p>
        )}
      </div>
    </Link>
  );
};

export default VideoCard;

