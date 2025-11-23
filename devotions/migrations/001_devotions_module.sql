-- ============================================================================
-- DEVOTIONS & NOTES MODULE - DATABASE MIGRATIONS
-- ============================================================================

-- Plans & content
CREATE TABLE IF NOT EXISTS public.content_plans (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title text NOT NULL,
  description text,
  cover_url text,
  source text DEFAULT 'canvas', -- "canvas", "uploaded", "public"
  audience jsonb DEFAULT '{}'::jsonb, -- {campus:["Paradise"], departments:["Youth"]}
  is_assigned boolean DEFAULT false,
  created_by uuid,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.plan_days (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  plan_id uuid REFERENCES public.content_plans(id) ON DELETE CASCADE,
  day_index int NOT NULL,       -- 1..N
  scripture_ref text NOT NULL,  -- e.g. "Luke 11:1-13 (NIV)"
  scripture_text text NOT NULL, -- FULL text (no abridgment)
  devo_body text,               -- HTML/MD allowed
  media jsonb DEFAULT '[]'::jsonb, -- [{type:"audio"|"video", url:"..."}]
  created_at timestamptz DEFAULT now(),
  UNIQUE(plan_id, day_index)
);

-- Assignment & progress
CREATE TABLE IF NOT EXISTS public.plan_assignments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  plan_id uuid REFERENCES public.content_plans(id) ON DELETE CASCADE,
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  assigned_at timestamptz DEFAULT now(),
  start_on date,                -- optional start date
  notify_time time,             -- optional preferred reminder time
  progress jsonb DEFAULT '{}'::jsonb, -- {currentDay: n, completedDays: [n1,n2,...]}
  UNIQUE(plan_id, user_id)
);

CREATE TABLE IF NOT EXISTS public.plan_progress_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  plan_id uuid REFERENCES public.content_plans(id) ON DELETE CASCADE,
  day_index int NOT NULL,
  event text CHECK (event IN ('start','complete','note_saved','media_play')),
  meta jsonb DEFAULT '{}'::jsonb,
  occurred_at timestamptz DEFAULT now(),
  UNIQUE(user_id, plan_id, day_index, event) -- idempotent basics
);

-- Notes (private by default)
CREATE TABLE IF NOT EXISTS public.notes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  plan_id uuid REFERENCES public.content_plans(id) ON DELETE SET NULL,
  day_index int,
  title text,
  body text,                    -- rich text/MD; stored server-side
  tags text[] DEFAULT '{}',
  is_shared boolean DEFAULT false,      -- if true, can generate a share link
  share_token text UNIQUE,      -- unique token for sharing
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Highlights (optional)
CREATE TABLE IF NOT EXISTS public.highlights (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  plan_id uuid REFERENCES public.content_plans(id) ON DELETE SET NULL,
  day_index int,
  verse_ref text NOT NULL,      -- "Luke 11:9-10"
  text text NOT NULL,
  color text DEFAULT 'yellow',
  created_at timestamptz DEFAULT now()
);

-- ============================================================================
-- ROW LEVEL SECURITY POLICIES
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE public.content_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.plan_days ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.plan_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.plan_progress_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.highlights ENABLE ROW LEVEL SECURITY;

-- Content plans: public readable, admin writable
CREATE POLICY cp_sel ON public.content_plans FOR SELECT USING (true);
CREATE POLICY cp_mod ON public.content_plans FOR INSERT WITH CHECK (auth.role() = 'admin');
CREATE POLICY cp_upd ON public.content_plans FOR UPDATE USING (auth.role() = 'admin');
CREATE POLICY cp_del ON public.content_plans FOR DELETE USING (auth.role() = 'admin');

-- Plan days: public readable, admin writable
CREATE POLICY pd_sel ON public.plan_days FOR SELECT USING (true);
CREATE POLICY pd_mod ON public.plan_days FOR INSERT WITH CHECK (auth.role() = 'admin');
CREATE POLICY pd_upd ON public.plan_days FOR UPDATE USING (auth.role() = 'admin');
CREATE POLICY pd_del ON public.plan_days FOR DELETE USING (auth.role() = 'admin');

-- Plan assignments: user owns their assignments
CREATE POLICY pa_sel ON public.plan_assignments FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY pa_mod ON public.plan_assignments FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY pa_upd ON public.plan_assignments FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY pa_del ON public.plan_assignments FOR DELETE USING (auth.uid() = user_id);

-- Progress events: user owns their progress
CREATE POLICY ppe_sel ON public.plan_progress_events FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY ppe_mod ON public.plan_progress_events FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY ppe_upd ON public.plan_progress_events FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY ppe_del ON public.plan_progress_events FOR DELETE USING (auth.uid() = user_id);

-- Notes: user owns their notes, shared notes readable with token
CREATE POLICY notes_sel ON public.notes FOR SELECT USING (
  auth.uid() = user_id OR 
  (is_shared = true AND share_token IS NOT NULL)
);
CREATE POLICY notes_mod ON public.notes FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY notes_upd ON public.notes FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY notes_del ON public.notes FOR DELETE USING (auth.uid() = user_id);

-- Highlights: user owns their highlights
CREATE POLICY highlights_sel ON public.highlights FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY highlights_mod ON public.highlights FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY highlights_upd ON public.highlights FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY highlights_del ON public.highlights FOR DELETE USING (auth.uid() = user_id);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_content_plans_source ON public.content_plans(source);
CREATE INDEX IF NOT EXISTS idx_content_plans_assigned ON public.content_plans(is_assigned);
CREATE INDEX IF NOT EXISTS idx_plan_days_plan_id ON public.plan_days(plan_id);
CREATE INDEX IF NOT EXISTS idx_plan_assignments_user_id ON public.plan_assignments(user_id);
CREATE INDEX IF NOT EXISTS idx_plan_assignments_plan_id ON public.plan_assignments(plan_id);
CREATE INDEX IF NOT EXISTS idx_plan_progress_events_user_plan ON public.plan_progress_events(user_id, plan_id);
CREATE INDEX IF NOT EXISTS idx_notes_user_id ON public.notes(user_id);
CREATE INDEX IF NOT EXISTS idx_notes_plan_id ON public.notes(plan_id);
CREATE INDEX IF NOT EXISTS idx_notes_tags ON public.notes USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_notes_shared ON public.notes(is_shared, share_token);
CREATE INDEX IF NOT EXISTS idx_highlights_user_id ON public.highlights(user_id);

-- ============================================================================
-- SAMPLE DATA FOR TESTING
-- ============================================================================

-- Insert sample content plans
INSERT INTO public.content_plans (id, title, description, source, is_assigned, audience) VALUES
  ('550e8400-e29b-41d4-a716-446655440001', 'Daily Devotional', 'Start your day with God', 'canvas', true, '{"campus": ["all_campuses"]}'),
  ('550e8400-e29b-41d4-a716-446655440002', 'Bible Reading Plan', 'Read through the New Testament', 'canvas', true, '{"campus": ["all_campuses"]}'),
  ('550e8400-e29b-41d4-a716-446655440003', 'Prayer Workshop', 'Deepen your prayer life', 'canvas', false, '{"departments": ["Adults"]}'),
  ('550e8400-e29b-41d4-a716-446655440004', 'Personal Study', 'Your personal devotional plan', 'uploaded', false, '{}')
ON CONFLICT DO NOTHING;

-- Insert sample plan days
INSERT INTO public.plan_days (plan_id, day_index, scripture_ref, scripture_text, devo_body) VALUES
  ('550e8400-e29b-41d4-a716-446655440001', 1, 'Psalm 1:1-3 (NIV)', 'Blessed is the one who does not walk in step with the wicked or stand in the way that sinners take or sit in the company of mockers, but whose delight is in the law of the Lord, and who meditates on his law day and night. That person is like a tree planted by streams of water, which yields its fruit in season and whose leaf does not wither—whatever they do prospers.', 'Today we begin our journey through the Psalms. This opening passage sets the foundation for what it means to be blessed by God. Notice how the psalmist contrasts two ways of living: following the world or following God''s Word. The imagery of a tree planted by streams of water is powerful - when we root ourselves in God''s truth, we find stability and fruitfulness.'),
  
  ('550e8400-e29b-41d4-a716-446655440001', 2, 'Psalm 1:4-6 (NIV)', 'Not so the wicked! They are like chaff that the wind blows away. Therefore the wicked will not stand in the judgment, nor sinners in the assembly of the righteous. For the Lord watches over the way of the righteous, but the way of the wicked leads to destruction.', 'The contrast continues as we see the fate of those who choose not to follow God. The image of chaff being blown away by the wind shows how temporary and unstable a life without God can be. But take heart - the Lord watches over the way of the righteous. This doesn''t mean life will be easy, but it does mean we have God''s guidance and protection.'),
  
  ('550e8400-e29b-41d4-a716-446655440002', 1, 'John 1:1-5 (NIV)', 'In the beginning was the Word, and the Word was with God, and the Word was God. He was with God in the beginning. Through him all things were made; without him nothing was made that has been made. In him was life, and that life was the light of all mankind. The light shines in the darkness, and the darkness has not overcome it.', 'We begin our journey through the New Testament with the powerful opening of John''s Gospel. This passage reveals the divinity of Jesus Christ - He is the Word, He is God, He is the Creator of all things. The imagery of light and darkness is profound - Jesus brings life and light to a world that often feels dark and hopeless.'),
  
  ('550e8400-e29b-41d4-a716-446655440002', 2, 'John 1:6-13 (NIV)', 'There was a man sent from God whose name was John. He came as a witness to testify concerning that light, so that through him all might believe. He himself was not the light; he came only as a witness to the light. The true light that gives light to everyone was coming into the world. He was in the world, and though the world was made through him, the world did not recognize him. He came to that which was his own, but his own did not receive him. Yet to all who did receive him, to those who believed in his name, he gave the right to become children of God—children born not of natural descent, nor of human decision or a husband''s will, but born of God.', 'John the Baptist''s role is clear - he is a witness, not the light himself. This humility is a powerful example for us. The passage also reveals a heartbreaking truth: Jesus came to His own people, but many rejected Him. Yet there''s hope: to all who receive Him, He gives the right to become children of God. This is not about human effort or decision, but about God''s grace working in our hearts.')
ON CONFLICT DO NOTHING;

-- Insert sample plan assignments for testing
INSERT INTO public.plan_assignments (plan_id, user_id, assigned_at, progress) VALUES
  ('550e8400-e29b-41d4-a716-446655440001', '00000000-0000-0000-0000-000000000001', now(), '{"currentDay": 1, "completedDays": []}'),
  ('550e8400-e29b-41d4-a716-446655440002', '00000000-0000-0000-0000-000000000001', now(), '{"currentDay": 1, "completedDays": []}')
ON CONFLICT DO NOTHING;

-- Insert sample notes
INSERT INTO public.notes (user_id, plan_id, day_index, title, body, tags) VALUES
  ('00000000-0000-0000-0000-000000000001', '550e8400-e29b-41d4-a716-446655440001', 1, 'Reflection on Psalm 1', 'This passage really speaks to me about the importance of staying rooted in God''s Word. I love the tree imagery - it reminds me that spiritual growth takes time and consistent nourishment.', '{"reflection", "psalms", "growth"}'),
  ('00000000-0000-0000-0000-000000000001', '550e8400-e29b-41d4-a716-446655440002', 1, 'John 1 Insights', 'The concept of Jesus as the Word is so profound. It connects to Genesis 1 where God spoke creation into being. Jesus is that same creative, life-giving Word.', '{"john", "creation", "jesus"}')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- FUNCTIONS FOR PROGRESS TRACKING
-- ============================================================================

-- Function to update plan progress
CREATE OR REPLACE FUNCTION update_plan_progress(
  p_user_id uuid,
  p_plan_id uuid,
  p_day_index int,
  p_event text
) RETURNS void AS $$
BEGIN
  -- Insert progress event
  INSERT INTO public.plan_progress_events (user_id, plan_id, day_index, event, meta)
  VALUES (p_user_id, p_plan_id, p_day_index, p_event, '{}')
  ON CONFLICT (user_id, plan_id, day_index, event) DO NOTHING;
  
  -- Update assignment progress
  IF p_event = 'complete' THEN
    UPDATE public.plan_assignments 
    SET progress = jsonb_set(
      COALESCE(progress, '{}'::jsonb),
      '{completedDays}',
      COALESCE(progress->'completedDays', '[]'::jsonb) || p_day_index::text::jsonb
    )
    WHERE user_id = p_user_id AND plan_id = p_plan_id;
  ELSIF p_event = 'start' THEN
    UPDATE public.plan_assignments 
    SET progress = jsonb_set(
      COALESCE(progress, '{}'::jsonb),
      '{currentDay}',
      p_day_index::text::jsonb
    )
    WHERE user_id = p_user_id AND plan_id = p_plan_id;
  END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get user''s devotion library
CREATE OR REPLACE FUNCTION get_devotion_library(p_user_id uuid)
RETURNS TABLE (
  assigned jsonb,
  in_progress jsonb,
  completed jsonb,
  personal jsonb
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    -- Assigned plans
    COALESCE(
      jsonb_agg(
        jsonb_build_object(
          'id', cp.id,
          'title', cp.title,
          'description', cp.description,
          'cover_url', cp.cover_url,
          'source', cp.source,
          'assigned_at', pa.assigned_at
        )
      ) FILTER (WHERE cp.is_assigned = true), 
      '[]'::jsonb
    ) as assigned,
    
    -- In progress plans
    COALESCE(
      jsonb_agg(
        jsonb_build_object(
          'id', cp.id,
          'title', cp.title,
          'description', cp.description,
          'cover_url', cp.cover_url,
          'current_day', pa.progress->>'currentDay',
          'completed_days', pa.progress->'completedDays'
        )
      ) FILTER (WHERE pa.progress->>'currentDay' IS NOT NULL AND 
                (pa.progress->'completedDays' IS NULL OR jsonb_array_length(pa.progress->'completedDays') < 
                 (SELECT COUNT(*) FROM public.plan_days WHERE plan_id = cp.id))),
      '[]'::jsonb
    ) as in_progress,
    
    -- Completed plans
    COALESCE(
      jsonb_agg(
        jsonb_build_object(
          'id', cp.id,
          'title', cp.title,
          'description', cp.description,
          'cover_url', cp.cover_url,
          'completed_at', pa.updated_at
        )
      ) FILTER (WHERE pa.progress->'completedDays' IS NOT NULL AND 
                jsonb_array_length(pa.progress->'completedDays') >= 
                (SELECT COUNT(*) FROM public.plan_days WHERE plan_id = cp.id)),
      '[]'::jsonb
    ) as completed,
    
    -- Personal plans
    COALESCE(
      jsonb_agg(
        jsonb_build_object(
          'id', cp.id,
          'title', cp.title,
          'description', cp.description,
          'cover_url', cp.cover_url,
          'created_at', cp.created_at
        )
      ) FILTER (WHERE cp.source = 'uploaded' AND cp.created_by = p_user_id),
      '[]'::jsonb
    ) as personal
    
  FROM public.content_plans cp
  LEFT JOIN public.plan_assignments pa ON cp.id = pa.plan_id AND pa.user_id = p_user_id
  WHERE cp.is_assigned = true OR cp.source = 'uploaded' OR pa.user_id = p_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
