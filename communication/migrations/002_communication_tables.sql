-- ============================================================================
-- COMMUNICATION PLATFORM TABLES - DATABASE MIGRATIONS
-- ============================================================================

-- Campaign management tables
CREATE TABLE IF NOT EXISTS public.campaigns (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  description text,
  
  -- Campaign type and status
  campaign_type text NOT NULL CHECK (campaign_type IN ('email', 'sms', 'push')),
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'scheduled', 'active', 'paused', 'completed', 'cancelled')),
  
  -- Content
  subject_line text,  -- Email subject
  content text NOT NULL,  -- Email HTML or SMS text
  content_text text,  -- Plain text version for email
  
  -- Targeting and scheduling
  target_criteria jsonb NOT NULL DEFAULT '{}'::jsonb,
  -- Format: {"campus": ["Paradise", "Sunshine Coast"], "department": ["Adults"], "tags": ["New", "Leader"]}
  
  scheduled_at timestamptz,
  sent_at timestamptz,
  
  -- Campaign metrics
  total_recipients integer DEFAULT 0,
  sent_count integer DEFAULT 0,
  delivered_count integer DEFAULT 0,
  open_count integer DEFAULT 0,
  click_count integer DEFAULT 0,
  reply_count integer DEFAULT 0,
  bounce_count integer DEFAULT 0,
  unsubscribe_count integer DEFAULT 0,
  
  -- System fields
  created_by uuid NOT NULL,  -- User ID
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- Campaign recipients tracking
CREATE TABLE IF NOT EXISTS public.campaign_recipients (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  campaign_id uuid NOT NULL REFERENCES public.campaigns(id) ON DELETE CASCADE,
  person_id uuid NOT NULL REFERENCES public.person(id) ON DELETE CASCADE,
  
  -- Delivery status
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'delivered', 'failed', 'bounced')),
  
  -- Engagement tracking
  opened_at timestamptz,
  clicked_at timestamptz,
  replied_at timestamptz,
  unsubscribed_at timestamptz,
  
  -- System fields
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  
  UNIQUE(campaign_id, person_id)
);

-- Campaign templates
CREATE TABLE IF NOT EXISTS public.campaign_templates (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  description text,
  
  -- Template type
  template_type text NOT NULL CHECK (template_type IN ('email', 'sms', 'push')),
  
  -- Content
  subject_line text,  -- Email subject
  content text NOT NULL,  -- Email HTML or SMS text
  content_text text,  -- Plain text version for email
  
  -- Template settings
  is_default boolean DEFAULT false,
  is_public boolean DEFAULT false,
  
  -- System fields
  created_by uuid NOT NULL,  -- User ID
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- Communication preferences
CREATE TABLE IF NOT EXISTS public.communication_preferences (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  person_id uuid NOT NULL REFERENCES public.person(id) ON DELETE CASCADE,
  
  -- Email preferences
  email_enabled boolean DEFAULT true,
  email_frequency text DEFAULT 'weekly' CHECK (email_frequency IN ('daily', 'weekly', 'monthly', 'never')),
  email_categories jsonb DEFAULT '[]'::jsonb,  -- ["newsletter", "events", "devotions"]
  
  -- SMS preferences
  sms_enabled boolean DEFAULT true,
  sms_frequency text DEFAULT 'weekly' CHECK (sms_frequency IN ('daily', 'weekly', 'monthly', 'never')),
  sms_categories jsonb DEFAULT '[]'::jsonb,  -- ["reminders", "urgent", "events"]
  
  -- Push preferences
  push_enabled boolean DEFAULT true,
  push_categories jsonb DEFAULT '[]'::jsonb,  -- ["devotions", "events", "community"]
  
  -- System fields
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  
  UNIQUE(person_id)
);

-- Engagement tracking
CREATE TABLE IF NOT EXISTS public.engagement_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  campaign_id uuid REFERENCES public.campaigns(id) ON DELETE SET NULL,
  person_id uuid NOT NULL REFERENCES public.person(id) ON DELETE CASCADE,
  
  -- Event details
  event_type text NOT NULL CHECK (event_type IN ('open', 'click', 'reply', 'bounce', 'unsubscribe', 'sms_delivered', 'sms_read', 'sms_reply')),
  event_data jsonb DEFAULT '{}'::jsonb,  -- Additional event metadata
  
  -- System fields
  occurred_at timestamptz NOT NULL DEFAULT now()
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_campaigns_status ON public.campaigns(status);
CREATE INDEX IF NOT EXISTS idx_campaigns_type ON public.campaigns(campaign_type);
CREATE INDEX IF NOT EXISTS idx_campaigns_created_by ON public.campaigns(created_by);
CREATE INDEX IF NOT EXISTS idx_campaigns_scheduled_at ON public.campaigns(scheduled_at);

CREATE INDEX IF NOT EXISTS idx_campaign_recipients_campaign_id ON public.campaign_recipients(campaign_id);
CREATE INDEX IF NOT EXISTS idx_campaign_recipients_person_id ON public.campaign_recipients(person_id);
CREATE INDEX IF NOT EXISTS idx_campaign_recipients_status ON public.campaign_recipients(status);

CREATE INDEX IF NOT EXISTS idx_campaign_templates_type ON public.campaign_templates(template_type);
CREATE INDEX IF NOT EXISTS idx_campaign_templates_created_by ON public.campaign_templates(created_by);

CREATE INDEX IF NOT EXISTS idx_communication_preferences_person_id ON public.communication_preferences(person_id);

CREATE INDEX IF NOT EXISTS idx_engagement_events_campaign_id ON public.engagement_events(campaign_id);
CREATE INDEX IF NOT EXISTS idx_engagement_events_person_id ON public.engagement_events(person_id);
CREATE INDEX IF NOT EXISTS idx_engagement_events_type ON public.engagement_events(event_type);
CREATE INDEX IF NOT EXISTS idx_engagement_events_occurred_at ON public.engagement_events(occurred_at);

-- ============================================================================
-- ROW LEVEL SECURITY POLICIES
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE public.campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.campaign_recipients ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.campaign_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.communication_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.engagement_events ENABLE ROW LEVEL SECURITY;

-- Campaigns: users can see campaigns they created or are assigned to
CREATE POLICY campaigns_sel ON public.campaigns FOR SELECT USING (
  created_by = auth.uid() OR 
  auth.role() = 'admin'
);
CREATE POLICY campaigns_mod ON public.campaigns FOR INSERT WITH CHECK (created_by = auth.uid());
CREATE POLICY campaigns_upd ON public.campaigns FOR UPDATE USING (created_by = auth.uid()) WITH CHECK (created_by = auth.uid());
CREATE POLICY campaigns_del ON public.campaigns FOR DELETE USING (created_by = auth.uid());

-- Campaign recipients: users can see recipients for their campaigns
CREATE POLICY campaign_recipients_sel ON public.campaign_recipients FOR SELECT USING (
  EXISTS (
    SELECT 1 FROM public.campaigns 
    WHERE campaigns.id = campaign_recipients.campaign_id 
    AND campaigns.created_by = auth.uid()
  ) OR auth.role() = 'admin'
);
CREATE POLICY campaign_recipients_mod ON public.campaign_recipients FOR INSERT WITH CHECK (
  EXISTS (
    SELECT 1 FROM public.campaigns 
    WHERE campaigns.id = campaign_recipients.campaign_id 
    AND campaigns.created_by = auth.uid()
  )
);
CREATE POLICY campaign_recipients_upd ON public.campaign_recipients FOR UPDATE USING (
  EXISTS (
    SELECT 1 FROM public.campaigns 
    WHERE campaigns.id = campaign_recipients.campaign_id 
    AND campaigns.created_by = auth.uid()
  )
);

-- Campaign templates: users can see public templates and their own
CREATE POLICY campaign_templates_sel ON public.campaign_templates FOR SELECT USING (
  is_public = true OR 
  created_by = auth.uid() OR 
  auth.role() = 'admin'
);
CREATE POLICY campaign_templates_mod ON public.campaign_templates FOR INSERT WITH CHECK (created_by = auth.uid());
CREATE POLICY campaign_templates_upd ON public.campaign_templates FOR UPDATE USING (created_by = auth.uid()) WITH CHECK (created_by = auth.uid());
CREATE POLICY campaign_templates_del ON public.campaign_templates FOR DELETE USING (created_by = auth.uid());

-- Communication preferences: users can only see their own
CREATE POLICY communication_preferences_sel ON public.communication_preferences FOR SELECT USING (person_id = auth.uid());
CREATE POLICY communication_preferences_mod ON public.communication_preferences FOR INSERT WITH CHECK (person_id = auth.uid());
CREATE POLICY communication_preferences_upd ON public.communication_preferences FOR UPDATE USING (person_id = auth.uid()) WITH CHECK (person_id = auth.uid());

-- Engagement events: users can see events for their campaigns
CREATE POLICY engagement_events_sel ON public.engagement_events FOR SELECT USING (
  campaign_id IS NULL OR
  EXISTS (
    SELECT 1 FROM public.campaigns 
    WHERE campaigns.id = engagement_events.campaign_id 
    AND campaigns.created_by = auth.uid()
  ) OR auth.role() = 'admin'
);

-- ============================================================================
-- SAMPLE DATA FOR TESTING
-- ============================================================================

-- Insert sample campaigns
INSERT INTO public.campaigns (id, name, description, campaign_type, status, subject_line, content, target_criteria, created_by) VALUES
  ('550e8400-e29b-41d4-a716-446655440010', 'Weekly Newsletter', 'Weekly church newsletter with updates and events', 'email', 'active', 'This Week at Church - Exciting Updates!', '<h1>Weekly Newsletter</h1><p>Stay updated with all the latest news and events.</p>', '{"campus": ["all_campuses"], "department": ["all"]}', '00000000-0000-0000-0000-000000000001'),
  ('550e8400-e29b-41d4-a716-446655440011', 'Youth Group Reminder', 'Reminder for upcoming youth group meeting', 'sms', 'scheduled', NULL, 'Reminder: Youth Group tonight at 6pm! See you there!', '{"campus": ["all_campuses"], "department": ["Youth"]}', '00000000-0000-0000-0000-000000000001'),
  ('550e8400-e29b-41d4-a716-446655440012', 'Devotional Invitation', 'Invitation to join daily devotional plan', 'email', 'draft', 'Join Our Daily Devotional Journey', '<h1>Daily Devotional</h1><p>Start your day with God through our daily devotional plan.</p>', '{"campus": ["all_campuses"], "department": ["all"]}', '00000000-0000-0000-0000-000000000001')
ON CONFLICT DO NOTHING;

-- Insert sample campaign templates
INSERT INTO public.campaign_templates (id, name, description, template_type, subject_line, content, created_by) VALUES
  ('550e8400-e29b-41d4-a716-446655440020', 'Event Announcement', 'Template for announcing church events', 'email', 'New Event: {event_name}', '<h1>{event_name}</h1><p><strong>Date:</strong> {event_date}</p><p><strong>Time:</strong> {event_time}</p><p><strong>Location:</strong> {event_location}</p><p>{event_description}</p>', '00000000-0000-0000-0000-000000000001'),
  ('550e8400-e29b-41d4-a716-446655440021', 'SMS Reminder', 'Template for SMS reminders', 'sms', NULL, 'Reminder: {event_name} on {event_date} at {event_time}. See you there!', '00000000-0000-0000-0000-000000000001')
ON CONFLICT DO NOTHING;

-- Insert sample communication preferences
INSERT INTO public.communication_preferences (person_id, email_enabled, sms_enabled, push_enabled) VALUES
  ('00000000-0000-0000-0000-000000000001', true, true, true)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- FUNCTIONS FOR CAMPAIGN MANAGEMENT
-- ============================================================================

-- Function to get campaign statistics
CREATE OR REPLACE FUNCTION get_campaign_stats(p_user_id uuid)
RETURNS TABLE (
  total_campaigns bigint,
  active_campaigns bigint,
  draft_campaigns bigint,
  completed_campaigns bigint
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    COUNT(*) as total_campaigns,
    COUNT(*) FILTER (WHERE status = 'active') as active_campaigns,
    COUNT(*) FILTER (WHERE status = 'draft') as draft_campaigns,
    COUNT(*) FILTER (WHERE status = 'completed') as completed_campaigns
  FROM public.campaigns
  WHERE created_by = p_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to update campaign metrics
CREATE OR REPLACE FUNCTION update_campaign_metrics(
  p_campaign_id uuid,
  p_event_type text,
  p_count int DEFAULT 1
) RETURNS void AS $$
BEGIN
  CASE p_event_type
    WHEN 'sent' THEN
      UPDATE public.campaigns SET sent_count = sent_count + p_count WHERE id = p_campaign_id;
    WHEN 'delivered' THEN
      UPDATE public.campaigns SET delivered_count = delivered_count + p_count WHERE id = p_campaign_id;
    WHEN 'opened' THEN
      UPDATE public.campaigns SET open_count = open_count + p_count WHERE id = p_campaign_id;
    WHEN 'clicked' THEN
      UPDATE public.campaigns SET click_count = click_count + p_count WHERE id = p_campaign_id;
    WHEN 'replied' THEN
      UPDATE public.campaigns SET reply_count = reply_count + p_count WHERE id = p_campaign_id;
    WHEN 'bounced' THEN
      UPDATE public.campaigns SET bounce_count = bounce_count + p_count WHERE id = p_campaign_id;
    WHEN 'unsubscribed' THEN
      UPDATE public.campaigns SET unsubscribe_count = unsubscribe_count + p_count WHERE id = p_campaign_id;
  END CASE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
