-- Migration: Activate US Region and Add Gwinnette Campus
-- Created: 2025-10-15
-- Description: Activates United States region and adds Gwinnette campus

-- Activate United States region
UPDATE regions 
SET active = 1, coming_soon = 0 
WHERE code = 'US';

-- Insert Gwinnette campus if it doesn't exist
INSERT OR IGNORE INTO campuses_new (
    campus_id, 
    name, 
    display_name, 
    region_id, 
    active, 
    service_times, 
    detection_patterns,
    country
) VALUES (
    'gwinnette', 
    'Gwinnette Campus', 
    'Gwinnette', 
    2,  -- United States region_id
    1,  -- active
    '["9:00 AM", "11:00 AM"]', 
    '["gwinnette", "gwinette", "gwinnett"]',
    'United States'
);

