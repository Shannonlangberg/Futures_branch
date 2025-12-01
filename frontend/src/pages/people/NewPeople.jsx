import React, { useState, useEffect } from 'react';
import { 
  UserPlusIcon, 
  CalendarIcon, 
  MapPinIcon, 
  CheckCircleIcon,
  AcademicCapIcon,
  PhoneIcon,
  EnvelopeIcon,
  UserGroupIcon,
  ChevronDownIcon,
  ChevronUpIcon
} from '@heroicons/react/24/outline';

const NewPeople = () => {
  const [newPeople, setNewPeople] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pathways, setPathways] = useState([]);
  const [expandedCards, setExpandedCards] = useState({});
  const [assigningPathway, setAssigningPathway] = useState({});
  const [updatingStatus, setUpdatingStatus] = useState({});

  useEffect(() => {
    loadNewPeople();
    loadPathways();
  }, []);

  const loadNewPeople = async () => {
    try {
      setLoading(true);
      
      const response = await fetch('/api/persons?new_people=true', {
        credentials: 'include',
        cache: 'no-store'
      });
      
      if (response.ok) {
        const data = await response.json();
        const persons = data.persons || [];
        
        // Load pathway info for each person
        const personsWithPathways = await Promise.all(
          persons.map(async (person) => {
            try {
              const pathwayResponse = await fetch(`/api/journeys/person/${person.id}`, {
                credentials: 'include'
              });
              if (pathwayResponse.ok) {
                const pathwayData = await pathwayResponse.json();
                person.assigned_pathways = pathwayData.pathways || [];
              }
            } catch (err) {
              console.error(`Error loading pathways for ${person.id}:`, err);
            }
            return person;
          })
        );
        
        setNewPeople(personsWithPathways);
      }
    } catch (err) {
      console.error('Error loading new people:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadPathways = async () => {
    try {
      console.log('[NewPeople] ===== LOADING PATHWAYS =====');
      // NOTE: This uses the same endpoint as /journeys page
      // All pathways created/managed at /journeys will appear here
      const response = await fetch('/api/journeys', {
        credentials: 'include',
        headers: {
          'Cache-Control': 'no-cache'
        }
      });
      
      console.log('[NewPeople] Response status:', response.status);
      console.log('[NewPeople] Response headers:', response.headers);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('[NewPeople] API Error:', response.status, errorText);
        alert(`Failed to load pathways: ${response.status}\n${errorText.substring(0, 200)}`);
        return;
      }
      
      const data = await response.json();
      console.log('[NewPeople] ===== RAW API RESPONSE =====');
      console.log('[NewPeople] Full response:', JSON.stringify(data, null, 2));
      console.log('[NewPeople] Pathways array:', data.pathways);
      console.log('[NewPeople] Pathways count:', data.pathways?.length || 0);
      
        // NO FILTERING - show everything
        const allPathways = data.pathways || [];
        console.log(`[NewPeople] Using ALL pathways (no filter): ${allPathways.length} pathways`);
        
        // Log each pathway
        allPathways.forEach((p, idx) => {
          console.log(`[NewPeople] Pathway ${idx + 1}:`, {
            id: p.id,
            name: p.name,
            is_active: p.is_active,
            is_template: p.is_template
          });
        });
        
        setPathways(allPathways);
        console.log(`[NewPeople] ===== SET PATHWAYS STATE: ${allPathways.length} pathways =====`);
        
        if (allPathways.length === 0) {
          console.error('[NewPeople] ⚠️ NO PATHWAYS FOUND IN API RESPONSE!');
          alert('No pathways found. Check console for API response details.');
        } else {
          console.log('[NewPeople] ✓ Pathways loaded successfully!');
        }
    } catch (err) {
      console.error('[NewPeople] ===== ERROR LOADING PATHWAYS =====');
      console.error('[NewPeople] Error:', err);
      console.error('[NewPeople] Error stack:', err.stack);
      alert(`Error loading pathways: ${err.message}\nCheck console for details.`);
    }
  };

  const assignPathway = async (personId, pathwayId) => {
    if (!personId || !pathwayId) {
      console.error('Missing personId or pathwayId:', { personId, pathwayId });
      alert('Error: Missing person or pathway information');
      return;
    }

    try {
      setAssigningPathway({ ...assigningPathway, [personId]: true });
      
      const pathwayIdInt = typeof pathwayId === 'string' ? parseInt(pathwayId, 10) : pathwayId;
      
      if (isNaN(pathwayIdInt)) {
        console.error('Invalid pathway ID:', pathwayId);
        alert('Error: Invalid pathway ID');
        return;
      }
      
      console.log(`[NewPeople] Assigning pathway ${pathwayIdInt} to person ${personId}`);
      
      const requestBody = {
        pathway_id: pathwayIdInt,
        start_immediately: true
      };
      
      console.log('[NewPeople] Request body:', JSON.stringify(requestBody));
      
      const response = await fetch(`/api/journeys/person/${personId}/assign`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(requestBody)
      });
      
      console.log('[NewPeople] Response status:', response.status, response.statusText);
      
      let result;
      try {
        result = await response.json();
      } catch (jsonErr) {
        const text = await response.text();
        console.error('[NewPeople] Failed to parse JSON response:', text);
        alert(`Server error: ${response.status} ${response.statusText}`);
        return;
      }
      
      console.log('[NewPeople] Assignment response:', result);
      
      if (response.ok) {
        alert('Pathway assigned successfully!');
        await loadNewPeople(); // Reload to get updated pathway info
      } else {
        const errorMsg = result.error || result.message || `Failed to assign pathway (${response.status})`;
        console.error('[NewPeople] Assignment error:', errorMsg, result);
        alert(`Error: ${errorMsg}`);
      }
    } catch (err) {
      console.error('[NewPeople] Error assigning pathway:', err);
      alert(`Failed to assign pathway: ${err.message || 'Network error'}`);
    } finally {
      setAssigningPathway({ ...assigningPathway, [personId]: false });
    }
  };

  const updateFollowUpStatus = async (personId, status) => {
    try {
      setUpdatingStatus({ ...updatingStatus, [personId]: true });
      
      const response = await fetch(`/api/persons/${personId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          follow_up_status: status
        })
      });
      
      if (response.ok) {
        await loadNewPeople(); // Reload to get updated status
      } else {
        const error = await response.json();
        alert(error.error || 'Failed to update status');
      }
    } catch (err) {
      console.error('Error updating status:', err);
      alert('Failed to update status');
    } finally {
      setUpdatingStatus({ ...updatingStatus, [personId]: false });
    }
  };

  const toggleCard = (personId) => {
    setExpandedCards({
      ...expandedCards,
      [personId]: !expandedCards[personId]
    });
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString();
    } catch {
      return 'Unknown';
    }
  };

  return (
    <div className="h-full bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6 overflow-y-auto">
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold text-white mb-2">New People</h2>
            <p className="text-white/60">People who joined in the last 30 days • {newPeople.length} total</p>
          </div>
          <div className="text-sm text-white/60 flex items-center gap-3">
            <div>
              Pathways available: <span className="font-bold text-white">{pathways.length}</span>
            </div>
            <button
              onClick={() => {
                console.log('[NewPeople] Manual refresh clicked');
                loadPathways();
              }}
              className="px-3 py-1 bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 rounded text-xs border border-blue-500/30"
            >
              🔄 Reload Pathways
            </button>
            {pathways.length > 0 && (
              <div className="text-green-400 text-xs">
                ✓ {pathways.length} pathway{pathways.length !== 1 ? 's' : ''} ready
              </div>
            )}
          </div>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12 text-white/60">Loading new people...</div>
      ) : (
        <div className="space-y-4">
          {newPeople.length > 0 ? (
            newPeople.map((person) => {
              const isExpanded = expandedCards[person.id];
              const hasPathway = person.assigned_pathways && person.assigned_pathways.length > 0;
              const currentPathway = hasPathway ? person.assigned_pathways[0] : null;
              
              return (
                <div
                  key={person.id}
                  className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-6 hover:border-white/20 transition-all"
                >
                  {/* Header */}
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <UserPlusIcon className="h-6 w-6 text-blue-400" />
                        <h3 className="text-xl font-semibold text-white">
                          {person.preferred_name || person.full_name}
                        </h3>
                        {person.follow_up_status === 'needed' && (
                          <span className="px-2 py-1 text-xs font-semibold bg-red-500/20 text-red-300 rounded-full">
                            Needs Follow-up
                          </span>
                        )}
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-white/60">
                        <div className="flex items-center gap-2">
                          <CalendarIcon className="h-4 w-4" />
                          Visit Date: {formatDate(person.created_at || person.date_added)}
                        </div>
                        <div className="flex items-center gap-2">
                          <MapPinIcon className="h-4 w-4" />
                          Campus: {person.campus || 'Unknown'}
                        </div>
                        {person.email && (
                          <div className="flex items-center gap-2">
                            <EnvelopeIcon className="h-4 w-4" />
                            {person.email}
                          </div>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={() => toggleCard(person.id)}
                      className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                    >
                      {isExpanded ? (
                        <ChevronUpIcon className="h-5 w-5 text-white/60" />
                      ) : (
                        <ChevronDownIcon className="h-5 w-5 text-white/60" />
                      )}
                    </button>
                  </div>

                  {/* Quick Stats */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div className="bg-white/5 rounded-lg p-4">
                      <div className="text-white/60 text-sm mb-1">Service Attended</div>
                      <div className="text-white font-medium">{person.service_attended || 'Unknown'}</div>
                    </div>
                    <div className="bg-white/5 rounded-lg p-4">
                      <div className="text-white/60 text-sm mb-1">Follow-up Status</div>
                      <div className="text-white font-medium capitalize">
                        {person.follow_up_status || 'Needed'}
                      </div>
                    </div>
                    <div className="bg-white/5 rounded-lg p-4">
                      <div className="text-white/60 text-sm mb-1">Assigned Pathway</div>
                      <div className="text-white font-medium">
                        {currentPathway ? currentPathway.pathway_name : 'None'}
                      </div>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex flex-wrap gap-2 mb-4">
                    <button
                      onClick={() => updateFollowUpStatus(person.id, 'contacted')}
                      disabled={updatingStatus[person.id]}
                      className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                      <PhoneIcon className="h-4 w-4" />
                      Mark as Contacted
                    </button>
                    <div className="relative">
                      <select
                        id={`pathway-select-${person.id}`}
                        onChange={(e) => {
                          console.log('[NewPeople] ===== DROPDOWN CHANGED =====');
                          console.log('[NewPeople] Selected value:', e.target.value);
                          console.log('[NewPeople] Selected index:', e.target.selectedIndex);
                          console.log('[NewPeople] All options:', Array.from(e.target.options).map(opt => ({ value: opt.value, text: opt.text })));
                          if (e.target.value) {
                            const pathwayId = parseInt(e.target.value);
                            console.log(`[NewPeople] Selected pathway ${pathwayId} for person ${person.id}`);
                            assignPathway(person.id, pathwayId);
                            e.target.value = '';
                          }
                        }}
                        onFocus={(e) => {
                          console.log('[NewPeople] ===== DROPDOWN FOCUSED =====');
                          console.log('[NewPeople] Pathways in state:', pathways.length);
                          console.log('[NewPeople] Pathways array:', pathways);
                          console.log('[NewPeople] Select element:', e.target);
                          console.log('[NewPeople] Options count:', e.target.options.length);
                        }}
                        onClick={(e) => {
                          console.log('[NewPeople] ===== DROPDOWN CLICKED =====');
                          console.log('[NewPeople] Pathways count:', pathways.length);
                          console.log('[NewPeople] Pathways:', pathways);
                          console.log('[NewPeople] Select element options:', Array.from(e.target.options).map(o => o.text));
                        }}
                        disabled={assigningPathway[person.id]}
                        className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed border border-purple-500/50 outline-none focus:ring-2 focus:ring-purple-500/50 cursor-pointer"
                        style={{ minWidth: '200px', paddingRight: '2.5rem', zIndex: 10 }}
                      >
                        <option value="" disabled>
                          {pathways.length === 0 ? 'Loading pathways...' : 'Assign Pathway...'}
                        </option>
                        {pathways.length > 0 ? (
                          pathways.map((pathway, idx) => {
                            if (idx === 0) {
                              console.log(`[NewPeople] Rendering first pathway option:`, pathway);
                            }
                            return (
                              <option key={pathway.id} value={String(pathway.id)}>
                                {pathway.name} {pathway.is_template ? '(Template)' : ''}
                              </option>
                            );
                          })
                        ) : (
                          <option value="" disabled>No pathways - Check console</option>
                        )}
                      </select>
                      <div className="absolute right-3 top-1/2 transform -translate-y-1/2 pointer-events-none z-0">
                        <ChevronDownIcon className="h-4 w-4 text-white" />
                      </div>
                      {/* Debug info - always visible */}
                      <div className="text-xs text-white/60 mt-1">
                        {pathways.length} pathway{pathways.length !== 1 ? 's' : ''} loaded | Click dropdown to see options
                      </div>
                    </div>
                    <select
                      onChange={(e) => {
                        if (e.target.value) {
                          updateFollowUpStatus(person.id, e.target.value);
                          e.target.value = '';
                        }
                      }}
                      disabled={updatingStatus[person.id]}
                      className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed border-none outline-none"
                    >
                      <option value="">Update Status...</option>
                      <option value="needed">Needed</option>
                      <option value="contacted">Contacted</option>
                      <option value="connected">Connected</option>
                      <option value="joined_events">Joined Events</option>
                    </select>
                  </div>

                  {/* Expanded Details */}
                  {isExpanded && (
                    <div className="mt-4 pt-4 border-t border-white/10 space-y-4">
                      {/* Pathway Progress */}
                      {currentPathway && (
                        <div className="bg-purple-500/10 border border-purple-500/30 rounded-lg p-4">
                          <div className="flex items-center gap-2 mb-2">
                            <AcademicCapIcon className="h-5 w-5 text-purple-400" />
                            <div className="text-purple-400 font-semibold">Assigned Pathway: {currentPathway.pathway_name}</div>
                          </div>
                          <div className="text-white/80 text-sm">
                            Progress: {currentPathway.progress_percentage || 0}%
                          </div>
                          {currentPathway.current_step && (
                            <div className="text-white/60 text-sm mt-1">
                              Current Step: {currentPathway.current_step.step_name}
                            </div>
                          )}
                        </div>
                      )}

                      {/* Contact Info */}
                      {(person.email || person.phone) && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {person.email && (
                            <div className="flex items-center gap-2 text-white/80">
                              <EnvelopeIcon className="h-4 w-4" />
                              <a href={`mailto:${person.email}`} className="hover:text-blue-400">
                                {person.email}
                              </a>
                            </div>
                          )}
                          {person.phone && (
                            <div className="flex items-center gap-2 text-white/80">
                              <PhoneIcon className="h-4 w-4" />
                              <a href={`tel:${person.phone}`} className="hover:text-blue-400">
                                {person.phone}
                              </a>
                            </div>
                          )}
                        </div>
                      )}

                      {/* AI Follow-up Message */}
                      {person.ai_follow_up_message && (
                        <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                          <div className="text-blue-400 font-semibold mb-2">AI Follow-up Message</div>
                          <div className="text-white/80">{person.ai_follow_up_message}</div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })
          ) : (
            <div className="text-center py-12 text-white/60">
              No new people in the last 30 days
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default NewPeople;

