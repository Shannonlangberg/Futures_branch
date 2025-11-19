import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { XMarkIcon } from '@heroicons/react/24/outline';

// Status badge component matching Heartbeat dashboard
const StatusBadge = ({ status, score }) => {
  const statusConfig = {
    healthy: {
      color: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
      label: 'Healthy',
      icon: '✓'
    },
    watch: {
      color: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
      label: 'Watch',
      icon: '⚠'
    },
    at_risk: {
      color: 'bg-orange-500/20 text-orange-300 border-orange-500/40',
      label: 'At Risk',
      icon: '⚡'
    },
    critical: {
      color: 'bg-red-500/20 text-red-300 border-red-500/40',
      label: 'Critical',
      icon: '🚨'
    }
  };

  const config = statusConfig[status] || statusConfig.watch;

  return (
    <div
      className={`inline-flex items-center px-4 py-2 rounded-full border text-sm font-semibold ${config.color}`}
    >
      <span className="mr-2">{config.icon}</span>
      <span className="uppercase tracking-wide">{config.label}</span>
      {typeof score === 'number' && (
        <span className="ml-3 font-bold">{Math.round(score)}</span>
      )}
    </div>
  );
};

// Score card component
const ScoreCard = ({ label, value, weight, color, maxValue = 100, onClick }) => {
  const percentage = Math.min((value / maxValue) * 100, 100);
  const colorClasses = {
    blue: 'bg-blue-500',
    purple: 'bg-purple-500',
    indigo: 'bg-indigo-500',
    pink: 'bg-pink-500'
  };
  
  return (
    <div 
      className={`bg-slate-800/50 rounded-xl p-5 border border-slate-700/50 transition-all ${
        onClick ? 'cursor-pointer hover:bg-slate-800/70 hover:border-slate-600 hover:scale-[1.02]' : ''
      }`}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      <div className="flex items-center justify-between mb-3">
          <div>
          <div className="text-xs text-slate-400 uppercase tracking-wide mb-1">{label}</div>
          <div className="text-3xl font-bold text-white">{Math.round(value)}</div>
          </div>
        <div className="text-right">
          <div className="text-xs text-slate-500">Weight</div>
          <div className="text-sm font-semibold text-slate-300">{weight}</div>
        </div>
      </div>
      <div className="w-full bg-slate-900/50 rounded-full h-3 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${colorClasses[color] || colorClasses.blue}`}
            style={{ width: `${percentage}%` }}
          />
        </div>
      <div className="mt-2 text-xs text-slate-400 flex items-center justify-between">
        <span>{percentage.toFixed(1)}% of maximum</span>
        {onClick && (
          <span className="text-slate-500 text-[10px]">Click to view details →</span>
        )}
      </div>
    </div>
  );
};

// Activity timeline item
const ActivityItem = ({ icon, title, date, details, type = 'default' }) => {
  const typeColors = {
    attendance: 'border-blue-500/30 bg-blue-500/10',
    serving: 'border-amber-500/30 bg-amber-500/10',
    connect: 'border-purple-500/30 bg-purple-500/10',
    discipleship: 'border-indigo-500/30 bg-indigo-500/10',
    care: 'border-pink-500/30 bg-pink-500/10',
    default: 'border-slate-700/50 bg-slate-800/50'
  };

  return (
    <div className={`flex items-start gap-3 p-3 rounded-lg border ${typeColors[type] || typeColors.default}`}>
      <div className="text-xl">{icon}</div>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-white mb-1">{title}</div>
        {details && (
          <div className="text-xs text-slate-400 mb-1">{details}</div>
        )}
        {date && (
          <div className="text-xs text-slate-500">
            {new Date(date).toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
              year: 'numeric'
            })}
          </div>
        )}
      </div>
    </div>
  );
};

const PersonHealthReport = () => {
  const { personId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [data, setData] = useState(null);
  const [recalculating, setRecalculating] = useState(false);
  const [showPathwayModal, setShowPathwayModal] = useState(false);
  const [pathways, setPathways] = useState([]);
  const [selectedPathwayId, setSelectedPathwayId] = useState(null);
  const [showCompleteModal, setShowCompleteModal] = useState(false);
  const [stepToComplete, setStepToComplete] = useState(null);
  const [completionDate, setCompletionDate] = useState(new Date().toISOString().split('T')[0]);
  const [isEditingCompletion, setIsEditingCompletion] = useState(false);
  const [aiSuggestion, setAiSuggestion] = useState(null);
  const [loadingSuggestion, setLoadingSuggestion] = useState(false);
  const [showCategoryModal, setShowCategoryModal] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState(null);

  useEffect(() => {
    fetchPersonData();
    fetchPathways();
  }, [personId]);

  useEffect(() => {
    // Fetch AI suggestion when pathway data is available
    if (data?.pathway?.id) {
      fetchAISuggestion();
    }
  }, [data?.pathway?.id]);

  const fetchPathways = async () => {
    try {
      const response = await fetch('/api/pathways', {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setPathways(data.pathways || []);
      }
    } catch (err) {
      console.error('Error loading pathways:', err);
    }
  };

  const fetchAISuggestion = async () => {
    if (!data?.pathway?.id) {
      console.warn('Cannot fetch AI suggestion: no pathway ID');
      return;
    }
    
    try {
      setLoadingSuggestion(true);
      const response = await fetch(`/api/pathways/progress/${data.pathway.id}/ai-suggestion`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        const result = await response.json();
        console.log('AI suggestion response:', result);
        if (result.suggestion) {
          setAiSuggestion(result);
        } else {
          console.warn('No suggestion in response:', result);
          setAiSuggestion({ suggestion: null, message: result.message });
        }
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
        console.error('Error fetching AI suggestion:', response.status, errorData);
        setAiSuggestion({ suggestion: null, error: errorData.error || 'Failed to get suggestion' });
      }
    } catch (err) {
      console.error('Error fetching AI suggestion:', err);
      setAiSuggestion({ suggestion: null, error: 'Failed to connect to server' });
    } finally {
      setLoadingSuggestion(false);
    }
  };

  const handleAssignPathway = async () => {
    if (!selectedPathwayId) {
      alert('Please select a pathway');
      return;
    }

    try {
      const response = await fetch(`/api/pathways/person/${personId}/assign`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          pathway_id: parseInt(selectedPathwayId),
          start_immediately: true
        }),
      });

      const result = await response.json();

      if (response.ok) {
        alert('Pathway assigned successfully!');
        setShowPathwayModal(false);
        await fetchPersonData();
      } else {
        alert(result.error || 'Failed to assign pathway');
      }
    } catch (err) {
      console.error('Error assigning pathway:', err);
      alert('Failed to assign pathway');
    }
  };

  const handleCompleteStepClick = (stepId) => {
    if (!data.pathway) {
      alert('No pathway assigned');
      return;
    }
    
    // Set today's date as default
    setCompletionDate(new Date().toISOString().split('T')[0]);
    setStepToComplete(stepId);
    setIsEditingCompletion(false);
    setShowCompleteModal(true);
  };

  const handleEditCompletionClick = (stepId, currentDate) => {
    if (!data.pathway) {
      alert('No pathway assigned');
      return;
    }
    
    // Set the existing completion date or today as default
    if (currentDate) {
      const date = new Date(currentDate);
      setCompletionDate(date.toISOString().split('T')[0]);
    } else {
      setCompletionDate(new Date().toISOString().split('T')[0]);
    }
    setStepToComplete(stepId);
    setIsEditingCompletion(true);
    setShowCompleteModal(true);
  };

  const handleCompleteStep = async () => {
    if (!stepToComplete || !data.pathway) {
      return;
    }

    try {
      let response;
      if (isEditingCompletion) {
        // Update existing completion
        response = await fetch(`/api/pathways/progress/${data.pathway.id}/update-completion`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify({
            step_id: stepToComplete,
            completed_at: completionDate
          }),
        });
      } else {
        // Create new completion
        response = await fetch(`/api/pathways/progress/${data.pathway.id}/complete-step`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify({
            step_id: stepToComplete,
            completed_at: completionDate
          }),
        });
      }

      const result = await response.json();

      if (response.ok) {
        setShowCompleteModal(false);
        setStepToComplete(null);
        setIsEditingCompletion(false);
        await fetchPersonData();
      } else {
        alert(result.error || (isEditingCompletion ? 'Failed to update completion date' : 'Failed to complete step'));
      }
    } catch (err) {
      console.error('Error completing step:', err);
      alert(isEditingCompletion ? 'Failed to update completion date' : 'Failed to complete step');
    }
  };

  const fetchPersonData = async () => {
      try {
        setLoading(true);
        setError('');

      const response = await fetch(`/api/heartbeat/person/${personId}`, {
        credentials: 'include'
        });

        if (!response.ok) {
          if (response.status === 404) {
            throw new Error('Person not found');
          }
          throw new Error('Failed to load person details');
        }

      const result = await response.json();
        
      if (result.error) {
        throw new Error(result.error);
        }
        
      setData(result);
      } catch (err) {
      console.error('Person heartbeat load error:', err);
      setError(err.message || 'Unable to load person details.');
      } finally {
        setLoading(false);
      }
    };

  const handleRecalculate = async () => {
    try {
      setRecalculating(true);
      const response = await fetch(`/api/heartbeat/recalculate/person/${personId}`, {
        method: 'POST',
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Recalculation failed');
      }

      const result = await response.json();
      alert('Recalculation complete!');
      
      // Reload data
      await fetchPersonData();
    } catch (err) {
      console.error('Recalculation error:', err);
      alert('Failed to recalculate. Please try again.');
    } finally {
      setRecalculating(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
        <div className="max-w-7xl mx-auto flex items-center justify-center py-20">
          <div className="flex items-center gap-3 text-slate-400 text-sm">
            <span className="inline-block w-5 h-5 border-2 border-slate-500 border-t-transparent rounded-full animate-spin" />
            Loading heartbeat data...
          </div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
        <div className="max-w-7xl mx-auto">
          <button
            type="button"
            onClick={() => navigate('/heartbeat')}
            className="mb-4 text-sm text-slate-400 hover:text-slate-200 flex items-center gap-2"
          >
            ← Back to Heartbeat
          </button>
          <div className="py-6 text-center text-sm text-red-300 bg-red-900/20 rounded-lg border border-red-800/40">
            {error || 'Person not found'}
          </div>
        </div>
      </div>
    );
  }

  const { person, heartbeat, recent_activity, pathway } = data;
  const hasHeartbeat = heartbeat !== null;
  const hasPathway = pathway !== null;

  // Combine all recent activity for timeline
  const allActivities = [];
  
  if (recent_activity) {
    recent_activity.attendance?.forEach(a => {
      allActivities.push({
        type: 'attendance',
        icon: '🏛️',
        title: 'Service Attendance',
        date: a.created_at,
        details: `Source: ${a.source}`,
        data: a
      });
    });

    recent_activity.serving?.forEach(s => {
      allActivities.push({
        type: 'serving',
        icon: '🤝',
        title: `Served: ${s.role || 'Team Member'}`,
        date: s.created_at,
        details: `Status: ${s.status}`,
        data: s
      });
    });

    recent_activity.connect_groups?.forEach(c => {
      allActivities.push({
        type: 'connect',
        icon: '👥',
        title: 'Connect Group',
        date: c.date,
        details: `Status: ${c.status}`,
        data: c
      });
    });

    recent_activity.discipleship_steps?.forEach(d => {
      allActivities.push({
        type: 'discipleship',
        icon: '✨',
        title: d.type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        date: d.date,
        details: d.description,
        data: d
      });
    });

    recent_activity.open_care_cases?.forEach(c => {
      allActivities.push({
        type: 'care',
        icon: '💜',
        title: `Care Case: ${c.type.replace(/_/g, ' ')}`,
        date: c.created_at,
        details: `${c.priority} priority - ${c.status}`,
        data: c
      });
    });
  }

  // Sort by date (newest first)
  allActivities.sort((a, b) => {
    const dateA = new Date(a.date || a.data?.created_at || 0);
    const dateB = new Date(b.date || b.data?.created_at || 0);
    return dateB - dateA;
  });

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Back Button */}
        <button
          type="button"
          onClick={() => navigate('/heartbeat')}
          className="text-sm text-slate-400 hover:text-slate-200 flex items-center gap-2 transition"
        >
          ← Back to Heartbeat
        </button>

        {/* Header Card */}
        <div className="bg-gradient-to-br from-slate-900/90 to-slate-800/90 border border-slate-700/70 rounded-2xl p-6 shadow-xl">
          <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-6">
            <div className="flex-1">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-purple-500/40 to-blue-500/40 flex items-center justify-center text-3xl font-bold text-white shadow-lg">
                  {person.full_name
                    ?.split(' ')
                    .map((n) => n[0])
                    .join('')
                    .toUpperCase()
                    .slice(0, 2) || '??'}
                </div>
                <div>
                  <h1 className="text-3xl font-bold text-white mb-1">{person.full_name}</h1>
                  {person.preferred_name && person.preferred_name !== person.full_name && (
                    <p className="text-sm text-slate-400">Preferred: {person.preferred_name}</p>
                  )}
                  <div className="flex flex-wrap items-center gap-3 mt-2 text-sm text-slate-300">
                    {person.campus && (
                      <span className="px-2 py-1 bg-slate-800/50 rounded-lg text-xs">
                        📍 {person.campus}
                      </span>
                    )}
                    {person.department && (
                      <span className="px-2 py-1 bg-slate-800/50 rounded-lg text-xs capitalize">
                        👥 {person.department.replace(/_/g, ' ')}
                      </span>
                    )}
                  </div>
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-4 text-sm text-slate-300">
                {person.email && (
                  <div className="flex items-center gap-1">
                    <span className="text-slate-500">✉️</span>
                    <span>{person.email}</span>
                  </div>
                )}
                {person.phone && (
                  <div className="flex items-center gap-1">
                    <span className="text-slate-500">📞</span>
                    <span>{person.phone}</span>
                  </div>
                )}
              </div>
            </div>
            <div className="flex flex-col items-end gap-3">
              {hasHeartbeat ? (
                <>
                  <StatusBadge status={heartbeat.status} score={heartbeat.total_score} />
                  <button
                    type="button"
                    onClick={handleRecalculate}
                    disabled={recalculating}
                    className="px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-lg font-semibold hover:scale-105 transition-all disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                  >
                    {recalculating ? 'Recalculating...' : '🔄 Recalculate'}
                  </button>
                </>
              ) : (
                <div className="text-center">
                  <div className="text-sm text-slate-400 mb-2">No Heartbeat Data</div>
                  <button
                    type="button"
                    onClick={handleRecalculate}
                    disabled={recalculating}
                    className="px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-lg font-semibold hover:scale-105 transition-all disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                  >
                    {recalculating ? 'Calculating...' : 'Calculate Heartbeat'}
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {hasHeartbeat ? (
          <>
            {/* Score Breakdown */}
        <div className="bg-gradient-to-br from-slate-900/90 to-slate-800/90 border border-slate-700/70 rounded-2xl p-6 shadow-xl">
          <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
            <span>📊</span>
                Heartbeat Score Breakdown
          </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                <ScoreCard
                  label="Gather"
                  value={heartbeat.gather_score}
                  weight="35%"
                  color="blue"
                  onClick={() => {
                    setSelectedCategory('gather');
                    setShowCategoryModal(true);
                  }}
                />
                <ScoreCard
                  label="Engagement"
                  value={heartbeat.engagement_score}
                  weight="25%"
                  color="purple"
                  onClick={() => {
                    setSelectedCategory('engagement');
                    setShowCategoryModal(true);
                  }}
                />
                <ScoreCard
                  label="Spiritual"
                  value={heartbeat.spiritual_score}
                  weight="25%"
                  color="indigo"
                  onClick={() => {
                    setSelectedCategory('spiritual');
                    setShowCategoryModal(true);
                  }}
                />
                <ScoreCard
                  label="Care"
                  value={heartbeat.care_score}
                  weight="15%"
                  color="pink"
                  onClick={() => {
                    setSelectedCategory('care');
                    setShowCategoryModal(true);
                  }}
                />
            </div>

              {/* Total Score */}
              <div className="bg-gradient-to-br from-purple-900/30 to-blue-900/30 border border-purple-500/40 rounded-xl p-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <div className="text-xs text-purple-300 uppercase tracking-wide mb-1">Total Heartbeat Score</div>
                    <div className="text-4xl font-bold text-white">{Math.round(heartbeat.total_score)}</div>
                    <div className="text-sm text-purple-300 mt-1">out of 100</div>
                  </div>
                  <div className="text-6xl opacity-20">💜</div>
                </div>
                <div className="w-full bg-slate-900/50 rounded-full h-4 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-purple-500 to-blue-500 rounded-full transition-all duration-500"
                    style={{ width: `${Math.min(heartbeat.total_score, 100)}%` }}
                  />
                </div>
                <div className="mt-4 text-xs text-purple-300/80">
                  Calculated: {new Date(heartbeat.calculated_at).toLocaleString()}
                </div>
              </div>
            </div>

            {/* Risk Factors */}
            {heartbeat.risk_reasons && heartbeat.risk_reasons.length > 0 && (
              <div className="bg-gradient-to-br from-red-900/20 to-orange-900/20 border border-red-500/40 rounded-2xl p-6 shadow-xl">
                <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                  <span>⚠️</span>
                  Risk Factors
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {heartbeat.risk_reasons.map((reason, idx) => (
                    <div
                      key={idx}
                      className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-sm text-red-200"
                    >
                      {reason.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Discipleship Pathway */}
            {hasPathway ? (
              <div className="bg-gradient-to-br from-indigo-900/20 to-purple-900/20 border border-indigo-500/40 rounded-2xl p-6 shadow-xl">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                    <span>🎓</span>
                    Discipleship Pathway: {pathway.pathway_name}
                  </h2>
                  <span className="px-3 py-1 bg-indigo-500/20 text-indigo-300 rounded-full text-xs font-semibold">
                    {pathway.progress_percentage}% Complete
                  </span>
                </div>
                
                {/* Progress Bar */}
                <div className="mb-6">
                  <div className="w-full bg-slate-900/50 rounded-full h-4 overflow-hidden mb-2">
                    <div
                      className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-500"
                      style={{ width: `${pathway.progress_percentage}%` }}
                    />
                  </div>
                  <div className="flex items-center justify-between text-xs text-slate-400">
                    <span>{pathway.completed_steps} of {pathway.total_steps} steps completed</span>
                    <span>{pathway.progress_percentage}%</span>
                  </div>
                </div>

                {/* Next Step */}
                {pathway.next_step ? (
                  <div className="bg-indigo-500/10 border border-indigo-500/30 rounded-lg p-4 mb-4">
                    <div className="text-sm font-semibold text-indigo-300 mb-1">Next Step:</div>
                    <div className="text-lg font-bold text-white mb-1">{pathway.next_step.step_name}</div>
                    {pathway.next_step.step_description && (
                      <div className="text-sm text-slate-300 mb-2">{pathway.next_step.step_description}</div>
                    )}
                    
                    {/* Suggested Next Step */}
                    {loadingSuggestion && (
                      <div className="mt-4 pt-4 border-t border-indigo-500/20">
                        <div className="flex items-center gap-2 text-sm text-indigo-200/70">
                          <div className="inline-block w-4 h-4 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin"></div>
                          <span>Getting suggestion...</span>
                        </div>
                      </div>
                    )}
                    {!loadingSuggestion && aiSuggestion?.suggestion && (
                      <div className="mt-4 pt-4 border-t border-indigo-500/20">
                        <div className="flex items-start gap-2 mb-2">
                          <span className="text-lg">💭</span>
                          <div className="text-xs font-semibold text-purple-300 uppercase tracking-wide">Suggested Next Step</div>
                        </div>
                        <div className="text-sm text-slate-200 italic leading-relaxed">
                          {aiSuggestion.suggestion}
                        </div>
                      </div>
                    )}
                    {!loadingSuggestion && (!aiSuggestion || !aiSuggestion.suggestion) && (
                      <div className="mt-4 pt-4 border-t border-indigo-500/20">
                        <button
                          onClick={fetchAISuggestion}
                          className="text-xs text-purple-300 hover:text-purple-200 flex items-center gap-1 transition-colors"
                        >
                          <span>💭</span>
                          <span>Get suggested next step</span>
                        </button>
                        {aiSuggestion?.error && (
                          <div className="text-xs text-red-300 mt-2">{aiSuggestion.error}</div>
                        )}
                        {aiSuggestion?.message && (
                          <div className="text-xs text-slate-400 mt-2 italic">{aiSuggestion.message}</div>
                        )}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4 mb-4">
                    <div className="flex items-center gap-2">
                      <span className="text-2xl">🎉</span>
                      <div>
                        <div className="text-sm font-semibold text-green-300 mb-1">Pathway Complete!</div>
                        <div className="text-sm text-slate-300">All steps have been completed.</div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Pathway Steps List */}
                <div className="space-y-2">
                  <div className="text-sm font-semibold text-slate-300 mb-2">All Steps:</div>
                  {pathway.pathway && pathway.pathway.steps ? (
                    pathway.pathway.steps.map((step) => {
                      const isCompleted = step.is_completed || false;
                      const isCurrent = pathway.next_step && pathway.next_step.id === step.id;
                      
                      return (
                        <div
                          key={step.id}
                          className={`flex items-center gap-3 p-3 rounded-lg border ${
                            isCompleted
                              ? 'bg-green-500/10 border-green-500/30'
                              : isCurrent
                              ? 'bg-indigo-500/20 border-indigo-500/40'
                              : 'bg-slate-700/50 border-slate-600/50'
                          }`}
                        >
                          <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                            isCompleted
                              ? 'bg-green-500/20 text-green-400'
                              : isCurrent
                              ? 'bg-indigo-500/20 text-indigo-400'
                              : 'bg-slate-600 text-slate-400'
                          }`}>
                            {isCompleted ? '✓' : step.step_order}
                          </div>
                          <div className="flex-1">
                            <div className={`font-medium ${
                              isCompleted ? 'text-green-300' : isCurrent ? 'text-indigo-300' : 'text-slate-300'
                            }`}>
                              {step.step_name}
                            </div>
                            {step.step_description && (
                              <div className="text-xs text-slate-400 mt-1">{step.step_description}</div>
                            )}
                            {isCompleted && step.completed_at && (
                              <div 
                                onClick={() => handleEditCompletionClick(step.id, step.completed_at)}
                                className="text-xs text-green-300/70 mt-1 cursor-pointer hover:text-green-300 hover:underline"
                                title="Click to edit completion date"
                              >
                                Completed: {new Date(step.completed_at).toLocaleDateString('en-US', {
                                  month: 'short',
                                  day: 'numeric',
                                  year: 'numeric'
                                })}
                              </div>
                            )}
                          </div>
                          {isCurrent && (
                            <span className="px-2 py-1 bg-indigo-500/20 text-indigo-300 rounded text-xs font-semibold">
                              Current
                            </span>
                          )}
                          {!isCompleted && !isCurrent && (
                            <button
                              onClick={() => handleCompleteStepClick(step.id)}
                              className="px-3 py-1 bg-indigo-600 hover:bg-indigo-700 text-white rounded text-xs font-semibold"
                              title="Mark as completed"
                            >
                              Complete
                            </button>
                          )}
                        </div>
                      );
                    })
                  ) : (
                    <div className="text-sm text-slate-400">Loading pathway steps...</div>
                  )}
                </div>
              </div>
            ) : (
              <div className="bg-gradient-to-br from-slate-900/90 to-slate-800/90 border border-slate-700/70 rounded-2xl p-6 shadow-xl">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                    <span>🎓</span>
                    Discipleship Pathway
                  </h2>
                  <button
                    onClick={() => setShowPathwayModal(true)}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-semibold"
                  >
                    Assign Pathway
                  </button>
                </div>
                <p className="text-slate-400 mb-2">No pathway assigned yet.</p>
                <p className="text-sm text-slate-500">
                  Assign a pathway to track their discipleship journey and next steps.
                </p>
                </div>
              )}

            {/* Recent Activity Timeline */}
            {allActivities.length > 0 && (
              <div className="bg-gradient-to-br from-slate-900/90 to-slate-800/90 border border-slate-700/70 rounded-2xl p-6 shadow-xl">
                <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                  <span>📅</span>
                  Recent Activity (Last 12 Weeks)
                </h2>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {allActivities.slice(0, 20).map((activity, idx) => (
                    <ActivityItem
                      key={idx}
                      icon={activity.icon}
                      title={activity.title}
                      date={activity.date || activity.data?.created_at}
                      details={activity.details}
                      type={activity.type}
                    />
                  ))}
            </div>
                {allActivities.length === 0 && (
                  <div className="text-center py-8 text-slate-400">
                    No recent activity recorded
                    </div>
                  )}
              </div>
            )}
          </>
        ) : (
          <div className="bg-gradient-to-br from-slate-900/90 to-slate-800/90 border border-slate-700/70 rounded-2xl p-6 shadow-xl text-center">
            <div className="text-6xl mb-4 opacity-50">💜</div>
            <h2 className="text-xl font-semibold text-white mb-2">No Heartbeat Data</h2>
            <p className="text-slate-400 mb-4">
              This person doesn't have a heartbeat calculation yet. Click "Calculate Heartbeat" above to generate one.
            </p>
            <p className="text-sm text-slate-500">
              Note: You'll need attendance, engagement, and other data in the system for accurate scores.
            </p>
                    </div>
                  )}

        {/* Assign Pathway Modal */}
        {showPathwayModal && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
            <div className="bg-slate-800 rounded-xl border border-slate-700 max-w-2xl w-full">
              <div className="p-6 border-b border-slate-700 flex items-center justify-between">
                <h2 className="text-2xl font-bold text-white">Assign Pathway</h2>
                <button
                  onClick={() => {
                    setShowPathwayModal(false);
                    setSelectedPathwayId(null);
                  }}
                  className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
                >
                  <XMarkIcon className="w-6 h-6 text-slate-400" />
                </button>
              </div>

              <div className="p-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Select Pathway
                  </label>
                  <select
                    value={selectedPathwayId || ''}
                    onChange={(e) => setSelectedPathwayId(e.target.value)}
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="">Choose a pathway...</option>
                    {pathways.map((pathway) => (
                      <option key={pathway.id} value={pathway.id}>
                        {pathway.name} {pathway.is_template && '(Template)'}
                      </option>
                    ))}
                  </select>
                </div>

                {selectedPathwayId && (
                  <div className="bg-slate-700/50 rounded-lg p-4">
                    <div className="text-sm text-slate-300">
                      {pathways.find(p => p.id === parseInt(selectedPathwayId))?.description || 'No description'}
                    </div>
                    <div className="text-xs text-slate-400 mt-2">
                      {pathways.find(p => p.id === parseInt(selectedPathwayId))?.step_count || 0} steps
                    </div>
                    </div>
                  )}

                <div className="flex gap-3 pt-4 border-t border-slate-700">
                  <button
                    onClick={() => {
                      setShowPathwayModal(false);
                      setSelectedPathwayId(null);
                    }}
                    className="flex-1 px-6 py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleAssignPathway}
                    disabled={!selectedPathwayId}
                    className="flex-1 px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Assign Pathway
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Complete Step Modal */}
        {showCompleteModal && stepToComplete && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
            <div className="bg-slate-800 rounded-xl border border-slate-700 max-w-md w-full">
              <div className="p-6 border-b border-slate-700 flex items-center justify-between">
                <h2 className="text-2xl font-bold text-white">
                  {isEditingCompletion ? 'Edit Completion Date' : 'Complete Step'}
                </h2>
                <button
                  onClick={() => {
                    setShowCompleteModal(false);
                    setStepToComplete(null);
                    setIsEditingCompletion(false);
                  }}
                  className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
                >
                  <XMarkIcon className="w-6 h-6 text-slate-400" />
                </button>
              </div>

              <div className="p-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Completion Date
                  </label>
                  <input
                    type="date"
                    value={completionDate}
                    onChange={(e) => setCompletionDate(e.target.value)}
                    max={new Date().toISOString().split('T')[0]}
                    className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-indigo-500"
                  />
                  <p className="text-xs text-slate-400 mt-1">
                    Select the date when this step was completed. Defaults to today's date.
                  </p>
                </div>

                <div className="flex gap-3 pt-4 border-t border-slate-700">
                  <button
                    onClick={() => {
                      setShowCompleteModal(false);
                      setStepToComplete(null);
                      setIsEditingCompletion(false);
                    }}
                    className="flex-1 px-6 py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleCompleteStep}
                    className="flex-1 px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors"
                  >
                    {isEditingCompletion ? 'Update Date' : 'Mark Complete'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Category Detail Modal */}
        {showCategoryModal && selectedCategory && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
            <div className="bg-slate-800 rounded-xl border border-slate-700 max-w-4xl w-full max-h-[90vh] flex flex-col">
              <div className="p-6 border-b border-slate-700 flex items-center justify-between">
                <h2 className="text-2xl font-bold text-white">
                  {selectedCategory === 'gather' && '🏛️ Gather - Attendance Events'}
                  {selectedCategory === 'engagement' && '👥 Engagement - Connect Groups & Serving'}
                  {selectedCategory === 'spiritual' && '✨ Spiritual - Discipleship Steps'}
                  {selectedCategory === 'care' && '💜 Care - Care Cases & Touchpoints'}
                </h2>
                <button
                  onClick={() => {
                    setShowCategoryModal(false);
                    setSelectedCategory(null);
                  }}
                  className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
                >
                  <XMarkIcon className="w-6 h-6 text-slate-400" />
                </button>
              </div>

              <div className="p-6 overflow-y-auto flex-1">
                {(() => {
                  if (!data || !data.recent_activity) {
                    return (
                      <div className="text-center py-12">
                        <p className="text-slate-400 text-lg mb-2">No activity data available</p>
                      </div>
                    );
                  }

                  let categoryEvents = [];
                  let categoryIcon = '';
                  let categoryColor = '';
                  const recent_activity = data.recent_activity;

                  if (selectedCategory === 'gather' && recent_activity?.attendance) {
                    categoryEvents = recent_activity.attendance.map(a => ({
                      ...a,
                      type: 'attendance',
                      icon: '🏛️',
                      title: 'Service Attendance',
                      date: a.created_at,
                      details: `Source: ${a.source || 'Unknown'}`,
                      color: 'blue'
                    }));
                    categoryIcon = '🏛️';
                    categoryColor = 'blue';
                  } else if (selectedCategory === 'engagement') {
                    const connectEvents = (recent_activity?.connect_groups || []).map(c => ({
                      ...c,
                      type: 'connect',
                      icon: '👥',
                      title: 'Connect Group Attendance',
                      date: c.date || c.created_at,
                      details: `Status: ${c.status || 'attended'}`,
                      color: 'purple'
                    }));
                    const servingEvents = (recent_activity?.serving || []).map(s => ({
                      ...s,
                      type: 'serving',
                      icon: '🤝',
                      title: `Served: ${s.role || 'Team Member'}`,
                      date: s.created_at,
                      details: `Status: ${s.status || 'active'}`,
                      color: 'purple'
                    }));
                    categoryEvents = [...connectEvents, ...servingEvents].sort((a, b) => {
                      const dateA = new Date(a.date || a.created_at || 0);
                      const dateB = new Date(b.date || b.created_at || 0);
                      return dateB - dateA;
                    });
                    categoryIcon = '👥';
                    categoryColor = 'purple';
                  } else if (selectedCategory === 'spiritual' && recent_activity?.discipleship_steps) {
                    categoryEvents = recent_activity.discipleship_steps.map(d => {
                      // Handle Person milestones (baptism, DNA, etc.) vs DiscipleshipStep records
                      const isPersonMilestone = d.is_person_milestone;
                      let title = '';
                      let icon = '✨';
                      
                      if (isPersonMilestone) {
                        // Use description for Person milestones (e.g., "Baptism", "DNA Completed")
                        title = d.description || d.type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                        // Use specific icons for milestones
                        if (d.type === 'baptism') icon = '💧';
                        else if (d.type === 'dna_completed') icon = '📖';
                        else if (d.type === 'filled_holy_spirit') icon = '🔥';
                        else if (d.type === 'rise_attended') icon = '🌟';
                        else if (d.type === 'first_served') icon = '🤝';
                      } else {
                        // Regular DiscipleshipStep
                        title = d.type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                      }
                      
                      return {
                        ...d,
                        type: 'discipleship',
                        icon: icon,
                        title: title,
                        date: d.date || d.created_at,
                        details: d.description || '',
                        color: 'indigo'
                      };
                    });
                    categoryIcon = '✨';
                    categoryColor = 'indigo';
                  } else if (selectedCategory === 'care' && recent_activity?.open_care_cases) {
                    categoryEvents = recent_activity.open_care_cases.map(c => ({
                      ...c,
                      type: 'care',
                      icon: '💜',
                      title: `Care Case: ${c.type?.replace(/_/g, ' ') || 'Unknown'}`,
                      date: c.created_at,
                      details: `${c.priority || 'unknown'} priority - ${c.status || 'open'}`,
                      color: 'pink'
                    }));
                    categoryIcon = '💜';
                    categoryColor = 'pink';
                  }

                  if (categoryEvents.length === 0) {
                    return (
                      <div className="text-center py-12">
                        <div className="text-6xl mb-4 opacity-50">{categoryIcon}</div>
                        <p className="text-slate-400 text-lg mb-2">No events found</p>
                        <p className="text-slate-500 text-sm">
                          {selectedCategory === 'gather' && 'No attendance events recorded for this person.'}
                          {selectedCategory === 'engagement' && 'No connect group or serving events recorded for this person.'}
                          {selectedCategory === 'spiritual' && 'No discipleship steps recorded for this person.'}
                          {selectedCategory === 'care' && 'No open care cases for this person.'}
                        </p>
                      </div>
                    );
                  }

                  return (
                    <div className="space-y-3">
                      <div className="text-sm text-slate-400 mb-4">
                        Showing {categoryEvents.length} event{categoryEvents.length !== 1 ? 's' : ''}
                        {selectedCategory === 'spiritual' ? ' (All milestones)' : ' (Last 12 weeks)'}
                      </div>
                      {categoryEvents.map((event, idx) => {
                        const eventDate = new Date(event.date || event.created_at);
                        return (
                          <div
                            key={idx}
                            className={`border rounded-lg p-4 ${
                              categoryColor === 'blue' ? 'border-blue-500/30 bg-blue-500/10' :
                              categoryColor === 'purple' ? 'border-purple-500/30 bg-purple-500/10' :
                              categoryColor === 'indigo' ? 'border-indigo-500/30 bg-indigo-500/10' :
                              'border-pink-500/30 bg-pink-500/10'
                            }`}
                          >
                            <div className="flex items-start gap-3">
                              <div className="text-2xl">{event.icon}</div>
                              <div className="flex-1 min-w-0">
                                <div className="font-semibold text-white mb-1">{event.title}</div>
                                {event.details && (
                                  <div className="text-sm text-slate-300 mb-2">{event.details}</div>
                                )}
                                <div className="text-xs text-slate-400">
                                  {eventDate.toLocaleDateString('en-US', {
                                    month: 'short',
                                    day: 'numeric',
                                    year: 'numeric',
                                    hour: '2-digit',
                                    minute: '2-digit'
                                  })}
                                </div>
                                {/* Additional event-specific details */}
                                {event.source && (
                                  <div className="mt-2 text-xs text-slate-500">
                                    Source: {event.source}
                                  </div>
                                )}
                                {event.role && (
                                  <div className="mt-2 text-xs text-slate-500">
                                    Role: {event.role}
                                  </div>
                                )}
                                {event.description && (
                                  <div className="mt-2 text-xs text-slate-400">
                                    {event.description}
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  );
                })()}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PersonHealthReport;
