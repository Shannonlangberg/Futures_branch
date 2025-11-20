import React, { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { PlayIcon, InformationCircleIcon } from '@heroicons/react/24/solid';

const SeriesCard = ({ series, isLarge = false }) => {
  const [isHovered, setIsHovered] = useState(false);
  const [previewPosition, setPreviewPosition] = useState('bottom');
  const cardRef = useRef(null);
  const previewRef = useRef(null);

  useEffect(() => {
    if (isHovered && cardRef.current) {
      const cardRect = cardRef.current.getBoundingClientRect();
      const previewHeight = 320; // Approximate preview height
      const viewportHeight = window.innerHeight;
      const spaceBelow = viewportHeight - cardRect.bottom;
      const spaceAbove = cardRect.top;

      // Position preview above if not enough space below, but enough above
      if (spaceBelow < previewHeight && spaceAbove > previewHeight) {
        setPreviewPosition('top');
      } else {
        setPreviewPosition('bottom');
      }
    }
  }, [isHovered]);

  const cardWidth = isLarge ? 'w-64' : 'w-48';
  const cardHeight = isLarge ? 'h-40' : 'aspect-video';

  return (
    <div
      ref={cardRef}
      className="relative"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{ zIndex: isHovered ? 100 : 'auto' }}
    >
      {/* Original Card */}
      <Link
        to={`/tv/series/${series.id}`}
        className={`group flex-shrink-0 ${cardWidth} ${cardHeight} rounded-lg overflow-hidden transition-transform duration-200 relative`}
      >
        <div className="relative w-full h-full bg-gradient-to-br from-purple-900/40 via-blue-900/40 to-pink-900/40">
          {series.thumbnail_url ? (
            <img
              src={series.thumbnail_url}
              alt={series.title}
              className="w-full h-full object-cover"
              onError={(e) => {
                e.target.style.display = 'none';
              }}
            />
          ) : null}
          <div className="absolute inset-0 bg-black/40 group-hover:bg-black/20 transition-colors" />
          {/* Badges */}
          {series.is_published && (
            <div className="absolute top-2 right-2 px-2 py-1 bg-red-600/90 text-white text-xs font-semibold rounded">
              NEW
            </div>
          )}
        </div>
        {!isLarge && (
          <div className="mt-2">
            <h3 className="text-white font-medium text-sm line-clamp-2 group-hover:text-transparent group-hover:bg-gradient-to-r group-hover:from-purple-400 group-hover:via-blue-400 group-hover:to-pink-400 group-hover:bg-clip-text transition-all">
              {series.title}
            </h3>
            {series.episode_count > 0 && (
              <p className="text-xs text-gray-400 mt-1">{series.episode_count} episodes</p>
            )}
          </div>
        )}
      </Link>

      {/* Hover Preview - Netflix Style */}
      {isHovered && cardRef.current && (
        <div
          ref={previewRef}
          className="fixed z-[9999] w-80 bg-slate-900 rounded-lg shadow-2xl border border-slate-700 overflow-hidden pointer-events-auto"
          style={{
            top: previewPosition === 'top' 
              ? `${cardRef.current.getBoundingClientRect().top - 320}px`
              : `${cardRef.current.getBoundingClientRect().bottom + 8}px`,
            left: `${Math.max(16, Math.min(
              window.innerWidth - 336,
              (cardRef.current.getBoundingClientRect().left + cardRef.current.getBoundingClientRect().right) / 2 - 160
            ))}px`,
            animation: 'fadeIn 0.2s ease-out'
          }}
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
        >
          {/* Preview Image */}
          <div className="relative w-full h-44 bg-gradient-to-br from-purple-900/40 via-blue-900/40 to-pink-900/40">
            {series.thumbnail_url ? (
              <img
                src={series.thumbnail_url}
                alt={series.title}
                className="w-full h-full object-cover"
                onError={(e) => {
                  e.target.style.display = 'none';
                }}
              />
            ) : null}
            <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-slate-900/50 to-transparent" />
          </div>

          {/* Preview Content */}
          <div className="p-4 bg-slate-900">
            {/* Action Buttons */}
            <div className="flex items-center gap-2 mb-3">
              <Link
                to={`/tv/series/${series.id}`}
                className="flex items-center justify-center w-8 h-8 rounded-full bg-white hover:bg-gray-200 transition-colors"
                onClick={(e) => e.stopPropagation()}
              >
                <PlayIcon className="w-5 h-5 text-black" />
              </Link>
              <Link
                to={`/tv/series/${series.id}`}
                className="flex items-center justify-center w-8 h-8 rounded-full border-2 border-gray-400 hover:border-white transition-colors"
                onClick={(e) => e.stopPropagation()}
              >
                <InformationCircleIcon className="w-5 h-5 text-white" />
              </Link>
            </div>

            {/* Title */}
            <h3 className="text-white font-bold text-lg mb-2 line-clamp-1">
              {series.title}
            </h3>

            {/* Metadata */}
            <div className="flex items-center gap-3 text-xs text-gray-300 mb-3">
              {series.episode_count > 0 && (
                <span>{series.episode_count} {series.episode_count === 1 ? 'Episode' : 'Episodes'}</span>
              )}
              {series.category && (
                <span className="capitalize">{series.category.replace(/_/g, ' ')}</span>
              )}
              {series.audience && series.audience !== 'all' && (
                <span className="capitalize">{series.audience}</span>
              )}
            </div>

            {/* Description */}
            {series.description && (
              <p className="text-sm text-gray-400 line-clamp-3 mb-3">
                {series.description}
              </p>
            )}

            {/* Tags/Categories */}
            {series.category && (
              <div className="flex flex-wrap gap-2">
                <span className="px-2 py-1 bg-purple-500/20 text-purple-300 rounded text-xs border border-purple-500/30">
                  {series.category.replace(/_/g, ' ')}
                </span>
                {series.audience && series.audience !== 'all' && (
                  <span className="px-2 py-1 bg-blue-500/20 text-blue-300 rounded text-xs border border-blue-500/30">
                    {series.audience}
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      <style>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateX(-50%) translateY(${previewPosition === 'top' ? '10px' : '-10px'});
          }
          to {
            opacity: 1;
            transform: translateX(-50%) translateY(0);
          }
        }
      `}</style>
    </div>
  );
};

export default SeriesCard;

