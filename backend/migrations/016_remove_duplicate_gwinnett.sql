-- Migration: Remove Duplicate Gwinnett Campus
-- Created: 2025-10-15
-- Description: Removes the duplicate Gwinnette (with 'e') campus, keeping only Gwinnett

-- Delete the incorrectly spelled version (gwinnette with 'e')
-- Keep the correctly spelled version (gwinnett without 'e')
DELETE FROM campuses_new 
WHERE campus_id = 'gwinnette';

-- Make sure the correct spelling exists and is in US region
-- Update if it exists, insert if it doesn't
INSERT OR REPLACE INTO campuses_new (
    campus_id, 
    name, 
    display_name, 
    region_id, 
    active, 
    service_times, 
    detection_patterns,
    country
) VALUES (
    'gwinnett', 
    'Gwinnett Campus', 
    'Gwinnett', 
    2,  -- United States region_id
    1,  -- active
    '["9:00 AM", "11:00 AM"]', 
    '["gwinnett", "gwinnette", "gwinette"]',
    'United States'
);

