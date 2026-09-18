-- =====================================================================
-- Demo / seed data — fictional, safe to commit.
-- Run AFTER schema.sql:
--   psql -U your_user -d career_platform -f seed.sql
-- =====================================================================

-- Skills catalog
INSERT INTO skills (name) VALUES
    ('Python'), ('FastAPI'), ('Django'), ('PostgreSQL'), ('Docker'),
    ('AWS'), ('Git'), ('REST APIs'), ('JavaScript'), ('React'),
    ('Machine Learning'), ('Data Analysis'), ('SQL'), ('Node.js'), ('Communication')
ON CONFLICT (name) DO NOTHING;

-- Organizations
INSERT INTO organizations (id, name, description, industry, location, website, contact_email, is_verified)
VALUES
    ('a0000000-0000-0000-0000-000000000001', 'NovaTech Labs', 'A fictional software company focused on backend platforms.', 'Software', 'Remote', 'https://example.com/novatech', 'contact@novatech.example', TRUE),
    ('a0000000-0000-0000-0000-000000000002', 'FutureBridge Foundation', 'A fictional nonprofit funding student scholarships.', 'Education', 'Karachi, PK', 'https://example.com/futurebridge', 'grants@futurebridge.example', TRUE),
    ('a0000000-0000-0000-0000-000000000003', 'CodeSphere', 'A fictional dev-tools startup.', 'Software', 'Lahore, PK', 'https://example.com/codesphere', 'hello@codesphere.example', FALSE);

-- Demo organization account user (password: Password123! — bcrypt hash generated at app runtime is preferred;
-- this is a placeholder hash and WILL NOT match "Password123!" — replace via the app's signup flow instead).
-- HUMAN CONFIGURATION REQUIRED:
-- Do not rely on this row for login. Create real accounts through POST /api/auth/register.

-- Sample opportunities
INSERT INTO opportunities (id, organization_id, title, description, type, work_mode, location, salary_or_stipend,
    deadline, education_requirement, min_experience_years, min_cgpa, eligibility_notes, status)
VALUES
    ('b0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001',
     'Python Backend Intern', 'Work on internal FastAPI services and PostgreSQL data models.',
     'internship', 'remote', 'Remote', 'Stipend: $500/month', now() + interval '30 days',
     'Currently pursuing BS in Computer Science or related field', 0, NULL,
     'Open to students in final two years of study.', 'open'),

    ('b0000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000002',
     'AI Research Scholarship', 'Funding for undergraduate students pursuing AI/ML research.',
     'scholarship', NULL, NULL, 'Award: $2000/year', now() + interval '45 days',
     'BS Software Engineering or Computer Science', 0, 3.5,
     'Minimum CGPA of 3.5 required. Financial need documentation requested.', 'open'),

    ('b0000000-0000-0000-0000-000000000003', 'a0000000-0000-0000-0000-000000000003',
     'Junior Backend Developer', 'Full-time role building REST APIs and deployment pipelines.',
     'job', 'hybrid', 'Lahore, PK', '$800-1200/month', now() + interval '20 days',
     'BS in Computer Science or equivalent experience', 1, NULL,
     '1 year of professional or internship backend experience preferred.', 'open');

-- Opportunity <-> skills
INSERT INTO opportunity_skills (opportunity_id, skill_id, importance)
SELECT 'b0000000-0000-0000-0000-000000000001', id, 'required' FROM skills WHERE name IN ('Python', 'FastAPI', 'PostgreSQL', 'Git', 'REST APIs');
INSERT INTO opportunity_skills (opportunity_id, skill_id, importance)
SELECT 'b0000000-0000-0000-0000-000000000001', id, 'preferred' FROM skills WHERE name IN ('Docker');

INSERT INTO opportunity_skills (opportunity_id, skill_id, importance)
SELECT 'b0000000-0000-0000-0000-000000000002', id, 'required' FROM skills WHERE name IN ('Python', 'Machine Learning');

INSERT INTO opportunity_skills (opportunity_id, skill_id, importance)
SELECT 'b0000000-0000-0000-0000-000000000003', id, 'required' FROM skills WHERE name IN ('Python', 'Django', 'PostgreSQL', 'REST APIs');
INSERT INTO opportunity_skills (opportunity_id, skill_id, importance)
SELECT 'b0000000-0000-0000-0000-000000000003', id, 'preferred' FROM skills WHERE name IN ('Docker', 'AWS');
