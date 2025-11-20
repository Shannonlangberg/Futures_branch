# Pulse TV → Heartbeat Integration

## How It Works

### 1. When Someone Watches an Episode

When a user completes an episode on Pulse TV:

1. **Progress is Tracked** (`TVUserEpisodeProgress` table)
   - Records: `person_id`, `episode_id`, `completed_at`, `last_position_seconds`
   - Every 15 seconds, the frontend updates their progress

2. **On Episode Completion** → `_handle_episode_completion()` runs:
   
   **A. Creates Discipleship Steps:**
   - **ALWAYS** creates: `DiscipleshipStep` with type `tv_episode_completion` (+5 spiritual score)
   - **If episode has `create_custom_step=true`:** Creates custom step with episode/series title
   - **If episode has `discipleship_links`:** Creates linked steps (e.g., salvation, baptism, etc.)
   - **If series completed:** Creates `tv_series_completion` step (+10 spiritual score)

   **B. Triggers Heartbeat Recalculation:**
   - Calls `HeartbeatEngine.calculate_heartbeat(person_id)`
   - Recalculates:
     - **Spiritual Score** (includes TV completions)
     - **Total Score** (average of all scores)
     - **Pulse Status** (green/amber/red)

3. **Spiritual Score Calculation:**
   - Each episode completion: **+5 points** (capped at 20 points max)
   - Each series completion: **+10 points** (capped at 20 points max)
   - Max TV contribution to spiritual score: **40 points total**
   - Score is calculated based on recent activity (last 8 weeks)

### 2. Where It Shows Up

**A. Person's Heartbeat Profile:**
- Go to: `/heartbeat` → Click on a person
- See: "Watched on Pulse TV" section
- Shows: All completed episodes with thumbnails, series titles, completion dates

**B. Person's Discipleship History:**
- Shows all `DiscipleshipStep` records
- Includes: `tv_episode_completion`, `tv_series_completion`, `tv_custom_step`
- Visible in their profile/discipleship pathway

**C. Activity Feed:**
- Recent activity includes TV completions
- Shows up in timeline/recent activity sections

### 3. Most Watched Algorithm

**How "Most Watched" is Calculated:**

1. **Data Sources:**
   - Completed episodes (`completed = true`)
   - Partial watches (>50% watched)
   - Watch timestamps

2. **Scoring Formula:**
   - Base completion: **1 point**
   - Last 30 days: **2 points** (weighted)
   - Last 7 days: **3 points** (very recent, weighted higher)
   - Partial watch (>50%): **0.5 points** (less weight)

3. **Ranking:**
   - Total score = sum of all weighted views
   - Series ranked by total score (descending)
   - Returns top 12 most watched series

4. **Example:**
   ```
   Series A:
   - 50 completions (all old) = 50 points
   - 10 completions (last 30 days) = 20 points
   - 5 completions (last 7 days) = 15 points
   - 20 partial watches = 10 points
   Total: 95 points
   
   Series B:
   - 30 completions (all recent - last 7 days) = 90 points
   Total: 90 points
   
   Result: Series A ranks higher (95 > 90)
   ```

## Data Flow

```
User Watches Episode
    ↓
Frontend: Updates progress every 15s
    ↓
Backend: /api/tv/episode/{id}/progress
    ↓
Episode Marked Complete?
    ↓ YES
_handle_episode_completion(person_id, episode_id)
    ↓
1. Create DiscipleshipStep(s)
    - tv_episode_completion (+5 points)
    - tv_custom_step (if enabled)
    - tv_series_completion (+10 points if all done)
    - Linked steps (salvation, baptism, etc.)
    ↓
2. HeartbeatEngine.calculate_heartbeat(person_id)
    ↓
3. Updates:
    - HeartbeatSnapshot.spiritual_score
    - HeartbeatSnapshot.total_score
    - HeartbeatSnapshot.status (green/amber/red)
    ↓
4. Person's Profile Updated
    - Shows in Heartbeat profile
    - Shows in Discipleship history
    - Shows in Activity feed
```

## Key Tables

1. **`tv_user_episode_progress`**
   - Tracks who watched what and when
   - Used for "Most Watched" calculation
   - Links to Heartbeat via `person_id`

2. **`discipleship_steps`**
   - Stores TV completions as steps
   - Type: `tv_episode_completion`, `tv_series_completion`, `tv_custom_step`
   - Used by Heartbeat engine to calculate spiritual score

3. **`heartbeat_snapshots`**
   - Current Heartbeat status for each person
   - Includes spiritual score (influenced by TV completions)
   - Auto-updated when TV episode completed

## API Endpoints

- `GET /api/tv/most-watched` - Returns top watched series (uses actual watch data)
- `GET /api/tv/person/:personId/watched` - Returns all episodes a person has watched
- `POST /api/tv/episode/:id/progress` - Updates watch progress (triggers completion logic)

## Summary

**YES, Pulse TV fully links to Heartbeat:**
- ✅ Watching episodes creates discipleship steps
- ✅ Completing episodes boosts spiritual score (+5 points)
- ✅ Completing series boosts spiritual score (+10 points)
- ✅ Shows up in Heartbeat profile
- ✅ Shows up in discipleship history
- ✅ Triggers automatic Heartbeat recalculation
- ✅ Most watched uses real watch data, not guesses

It's all connected! 🎯

