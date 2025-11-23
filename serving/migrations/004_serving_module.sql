-- Migration 004: Serving Module Tables
-- This migration adds comprehensive serving/volunteer management tables

-- First, add dream_team_roles column to persons table if it doesn't exist
ALTER TABLE persons ADD COLUMN IF NOT EXISTS dream_team_roles JSON;

-- Create serving teams table
CREATE TABLE IF NOT EXISTS serving_teams (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    campus VARCHAR(50) NOT NULL,
    department VARCHAR(50),
    team_type VARCHAR(30) NOT NULL DEFAULT 'ministry',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    requires_background_check BOOLEAN NOT NULL DEFAULT FALSE,
    min_age INTEGER,
    max_age INTEGER,
    leader_id VARCHAR(36),
    co_leader_id VARCHAR(36),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create serving roles table
CREATE TABLE IF NOT EXISTS serving_roles (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    team_id VARCHAR(36) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    requires_training BOOLEAN NOT NULL DEFAULT FALSE,
    training_hours INTEGER,
    requires_background_check BOOLEAN NOT NULL DEFAULT FALSE,
    min_serving_age INTEGER,
    typical_duration_hours FLOAT,
    typical_frequency VARCHAR(30),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create team members table
CREATE TABLE IF NOT EXISTS team_members (
    id VARCHAR(36) PRIMARY KEY,
    person_id VARCHAR(36) NOT NULL,
    team_id VARCHAR(36) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    joined_date DATE NOT NULL DEFAULT CURRENT_DATE,
    left_date DATE,
    primary_role_id VARCHAR(36),
    secondary_roles JSON,
    is_leader BOOLEAN NOT NULL DEFAULT FALSE,
    can_schedule BOOLEAN NOT NULL DEFAULT FALSE,
    can_approve_requests BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create serving schedules table
CREATE TABLE IF NOT EXISTS serving_schedules (
    id VARCHAR(36) PRIMARY KEY,
    role_id VARCHAR(36) NOT NULL,
    team_id VARCHAR(36) NOT NULL,
    scheduled_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    timezone VARCHAR(50) NOT NULL DEFAULT 'Australia/Adelaide',
    assigned_person_id VARCHAR(36),
    backup_person_id VARCHAR(36),
    status VARCHAR(20) NOT NULL DEFAULT 'open',
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create serving requests table
CREATE TABLE IF NOT EXISTS serving_requests (
    id VARCHAR(36) PRIMARY KEY,
    person_id VARCHAR(36) NOT NULL,
    schedule_id VARCHAR(36),
    team_id VARCHAR(36) NOT NULL,
    request_type VARCHAR(30) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    requested_date DATE,
    start_time TIME,
    end_time TIME,
    reason TEXT,
    notes TEXT,
    approved_by VARCHAR(36),
    approved_at TIMESTAMP,
    approval_notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create serving records table
CREATE TABLE IF NOT EXISTS serving_records (
    id VARCHAR(36) PRIMARY KEY,
    person_id VARCHAR(36) NOT NULL,
    schedule_id VARCHAR(36),
    team_id VARCHAR(36) NOT NULL,
    role_id VARCHAR(36) NOT NULL,
    served_date DATE NOT NULL,
    start_time TIME,
    end_time TIME,
    actual_duration_hours FLOAT,
    status VARCHAR(20) NOT NULL DEFAULT 'scheduled',
    notes TEXT,
    checked_in_at TIMESTAMP,
    checked_out_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create person availability table
CREATE TABLE IF NOT EXISTS person_availability (
    id VARCHAR(36) PRIMARY KEY,
    person_id VARCHAR(36) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    preferred_days JSON,
    preferred_times JSON,
    preferred_teams JSON,
    unavailable_dates JSON,
    max_hours_per_week INTEGER,
    max_servings_per_month INTEGER,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Now add foreign key constraints after all tables exist
PRAGMA foreign_keys=OFF;

-- Add foreign key constraints
ALTER TABLE serving_roles ADD CONSTRAINT fk_serving_roles_team 
    FOREIGN KEY (team_id) REFERENCES serving_teams(id) ON DELETE CASCADE;

ALTER TABLE team_members ADD CONSTRAINT fk_team_members_person 
    FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE;

ALTER TABLE team_members ADD CONSTRAINT fk_team_members_team 
    FOREIGN KEY (team_id) REFERENCES serving_teams(id) ON DELETE CASCADE;

ALTER TABLE team_members ADD CONSTRAINT fk_team_members_role 
    FOREIGN KEY (primary_role_id) REFERENCES serving_roles(id) ON DELETE SET NULL;

ALTER TABLE serving_schedules ADD CONSTRAINT fk_serving_schedules_role 
    FOREIGN KEY (role_id) REFERENCES serving_roles(id) ON DELETE CASCADE;

ALTER TABLE serving_schedules ADD CONSTRAINT fk_serving_schedules_team 
    FOREIGN KEY (team_id) REFERENCES serving_teams(id) ON DELETE CASCADE;

ALTER TABLE serving_schedules ADD CONSTRAINT fk_serving_schedules_assigned 
    FOREIGN KEY (assigned_person_id) REFERENCES persons(id) ON DELETE SET NULL;

ALTER TABLE serving_schedules ADD CONSTRAINT fk_serving_schedules_backup 
    FOREIGN KEY (backup_person_id) REFERENCES persons(id) ON DELETE SET NULL;

ALTER TABLE serving_requests ADD CONSTRAINT fk_serving_requests_person 
    FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE;

ALTER TABLE serving_requests ADD CONSTRAINT fk_serving_requests_schedule 
    FOREIGN KEY (schedule_id) REFERENCES serving_schedules(id) ON DELETE SET NULL;

ALTER TABLE serving_requests ADD CONSTRAINT fk_serving_requests_team 
    FOREIGN KEY (team_id) REFERENCES serving_teams(id) ON DELETE CASCADE;

ALTER TABLE serving_requests ADD CONSTRAINT fk_serving_requests_approved 
    FOREIGN KEY (approved_by) REFERENCES persons(id) ON DELETE SET NULL;

ALTER TABLE serving_records ADD CONSTRAINT fk_serving_records_person 
    FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE;

ALTER TABLE serving_records ADD CONSTRAINT fk_serving_records_schedule 
    FOREIGN KEY (schedule_id) REFERENCES serving_schedules(id) ON DELETE SET NULL;

ALTER TABLE serving_records ADD CONSTRAINT fk_serving_records_team 
    FOREIGN KEY (team_id) REFERENCES serving_teams(id) ON DELETE CASCADE;

ALTER TABLE serving_records ADD CONSTRAINT fk_serving_records_role 
    FOREIGN KEY (role_id) REFERENCES serving_roles(id) ON DELETE CASCADE;

ALTER TABLE person_availability ADD CONSTRAINT fk_person_availability_person 
    FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE;

PRAGMA foreign_keys=ON;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_serving_teams_campus ON serving_teams(campus);
CREATE INDEX IF NOT EXISTS idx_serving_teams_department ON serving_teams(department);
CREATE INDEX IF NOT EXISTS idx_serving_teams_leader ON serving_teams(leader_id);
CREATE INDEX IF NOT EXISTS idx_serving_teams_active ON serving_teams(is_active);

CREATE INDEX IF NOT EXISTS idx_serving_roles_team ON serving_roles(team_id);
CREATE INDEX IF NOT EXISTS idx_serving_roles_active ON serving_roles(is_active);

CREATE INDEX IF NOT EXISTS idx_team_members_person ON team_members(person_id);
CREATE INDEX IF NOT EXISTS idx_team_members_team ON team_members(team_id);
CREATE INDEX IF NOT EXISTS idx_team_members_active ON team_members(is_active);

CREATE INDEX IF NOT EXISTS idx_serving_schedules_date ON serving_schedules(scheduled_date);
CREATE INDEX IF NOT EXISTS idx_serving_schedules_team ON serving_schedules(team_id);
CREATE INDEX IF NOT EXISTS idx_serving_schedules_assigned ON serving_schedules(assigned_person_id);
CREATE INDEX IF NOT EXISTS idx_serving_schedules_status ON serving_schedules(status);

CREATE INDEX IF NOT EXISTS idx_serving_requests_person ON serving_requests(person_id);
CREATE INDEX IF NOT EXISTS idx_serving_requests_team ON serving_requests(team_id);
CREATE INDEX IF NOT EXISTS idx_serving_requests_status ON serving_requests(status);
CREATE INDEX IF NOT EXISTS idx_serving_requests_type ON serving_requests(request_type);

CREATE INDEX IF NOT EXISTS idx_serving_records_person ON serving_records(person_id);
CREATE INDEX IF NOT EXISTS idx_serving_records_date ON serving_records(served_date);
CREATE INDEX IF NOT EXISTS idx_serving_records_team ON serving_records(team_id);
CREATE INDEX IF NOT EXISTS idx_serving_records_status ON serving_records(status);

CREATE INDEX IF NOT EXISTS idx_person_availability_person ON person_availability(person_id);
CREATE INDEX IF NOT EXISTS idx_person_availability_active ON person_availability(is_active);

-- Insert sample data for serving teams
INSERT INTO serving_teams (id, name, description, campus, department, team_type, is_active, requires_background_check, min_age, leader_id) VALUES
('st-001', 'Kids Ministry', 'Children''s ministry for ages 0-12', 'Copper Coast', 'Children', 'ministry', TRUE, TRUE, 18, NULL),
('st-002', 'Youth Ministry', 'Teen ministry for ages 13-18', 'Copper Coast', 'Youth', 'ministry', TRUE, TRUE, 18, NULL),
('st-003', 'Worship Team', 'Music and worship leadership', 'Copper Coast', 'Worship', 'ministry', TRUE, FALSE, 16, NULL),
('st-004', 'Hospitality', 'Greeting, ushering, and hospitality', 'Copper Coast', 'Guest Services', 'ministry', TRUE, FALSE, 16, NULL),
('st-005', 'Media Team', 'Sound, lighting, and technical support', 'Copper Coast', 'Technical', 'ministry', TRUE, FALSE, 16, NULL),
('st-006', 'Kids Ministry', 'Children''s ministry for ages 0-12', 'Adelaide Hills', 'Children', 'ministry', TRUE, TRUE, 18, NULL),
('st-007', 'Youth Ministry', 'Teen ministry for ages 13-18', 'Adelaide Hills', 'Youth', 'ministry', TRUE, TRUE, 18, NULL),
('st-008', 'Worship Team', 'Music and worship leadership', 'Adelaide Hills', 'Worship', 'ministry', TRUE, FALSE, 16, NULL);

-- Insert sample data for serving roles
INSERT INTO serving_roles (id, name, description, team_id, is_active, requires_training, training_hours, requires_background_check, min_serving_age, typical_duration_hours, typical_frequency) VALUES
('sr-001', 'Kids Check-In Volunteer', 'Welcome families and check in children', 'st-001', TRUE, TRUE, 2, TRUE, 18, 2.0, 'weekly'),
('sr-002', 'Kids Small Group Leader', 'Lead small group activities and discussions', 'st-001', TRUE, TRUE, 4, TRUE, 18, 2.0, 'weekly'),
('sr-003', 'Youth Small Group Leader', 'Lead teen small group discussions', 'st-002', TRUE, TRUE, 6, TRUE, 18, 2.0, 'weekly'),
('sr-004', 'Worship Leader', 'Lead worship songs and music', 'st-003', TRUE, TRUE, 8, FALSE, 18, 3.0, 'weekly'),
('sr-005', 'Worship Team Member', 'Play instrument or sing backup', 'st-003', TRUE, TRUE, 4, FALSE, 16, 3.0, 'weekly'),
('sr-006', 'Greeter', 'Welcome people at the entrance', 'st-004', TRUE, FALSE, 1, FALSE, 16, 1.5, 'weekly'),
('sr-007', 'Usher', 'Help with seating and offering', 'st-004', TRUE, FALSE, 1, FALSE, 16, 1.5, 'weekly'),
('sr-008', 'Sound Technician', 'Operate sound board and equipment', 'st-005', TRUE, TRUE, 6, FALSE, 16, 3.0, 'weekly'),
('sr-009', 'Lighting Technician', 'Operate lighting system', 'st-005', TRUE, TRUE, 4, FALSE, 16, 3.0, 'weekly'),
('sr-010', 'Kids Check-In Volunteer', 'Welcome families and check in children', 'st-006', TRUE, TRUE, 2, TRUE, 18, 2.0, 'weekly'),
('sr-011', 'Youth Small Group Leader', 'Lead teen small group discussions', 'st-006', TRUE, TRUE, 6, TRUE, 18, 2.0, 'weekly'),
('sr-012', 'Worship Team Member', 'Play instrument or sing backup', 'st-008', TRUE, TRUE, 4, FALSE, 16, 3.0, 'weekly');

-- Create views for easier data access
CREATE VIEW IF NOT EXISTS serving_stats AS
SELECT 
    t.campus,
    t.department,
    COUNT(DISTINCT t.id) as total_teams,
    COUNT(DISTINCT tr.id) as total_roles,
    COUNT(DISTINCT tm.person_id) as total_members,
    COUNT(DISTINCT CASE WHEN tm.is_active = 1 THEN tm.person_id END) as active_members
FROM serving_teams t
LEFT JOIN serving_roles tr ON t.id = tr.team_id
LEFT JOIN team_members tm ON t.id = tm.team_id
WHERE t.is_active = 1
GROUP BY t.campus, t.department;

CREATE VIEW IF NOT EXISTS person_serving_summary AS
SELECT 
    p.id,
    p.full_name,
    p.campus,
    COUNT(DISTINCT tm.team_id) as teams_count,
    COUNT(DISTINCT sr.id) as total_servings,
    SUM(COALESCE(sr.actual_duration_hours, 0)) as total_hours,
    MAX(sr.served_date) as last_served_date
FROM persons p
LEFT JOIN team_members tm ON p.id = tm.person_id AND tm.is_active = 1
LEFT JOIN serving_records sr ON p.id = sr.person_id AND sr.status = 'completed'
GROUP BY p.id, p.full_name, p.campus;
