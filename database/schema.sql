-- =====================================================================
-- AI-Powered Career Platform — Database Schema
-- Run this against an empty database, e.g.:
--   psql -U your_user -d career_platform -f schema.sql
-- =====================================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto; -- for gen_random_uuid()

-- ---------------------------------------------------------------------
-- USERS
-- ---------------------------------------------------------------------
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(150) NOT NULL,
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    role            VARCHAR(20) NOT NULL CHECK (role IN ('student', 'professional', 'organization', 'admin')),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- ---------------------------------------------------------------------
-- PROFILES  (one-to-one with users, for student/professional roles)
-- ---------------------------------------------------------------------
CREATE TABLE profiles (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    headline            VARCHAR(255),
    bio                 TEXT,
    profile_picture_url TEXT,
    location            VARCHAR(150),
    university          VARCHAR(255),
    degree              VARCHAR(255),
    field_of_study      VARCHAR(255),
    graduation_year     INTEGER CHECK (graduation_year IS NULL OR (graduation_year BETWEEN 1950 AND 2100)),
    cgpa                NUMERIC(3,2) CHECK (cgpa IS NULL OR (cgpa >= 0 AND cgpa <= 4.0)),
    career_goals        TEXT,
    github_url          TEXT,
    portfolio_url       TEXT,
    website_url         TEXT,
    profile_completion  INTEGER NOT NULL DEFAULT 0 CHECK (profile_completion BETWEEN 0 AND 100),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- SKILLS (global catalog) + USER_SKILLS (join table)
-- ---------------------------------------------------------------------
CREATE TABLE skills (
    id      SERIAL PRIMARY KEY,
    name    VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE user_skills (
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    skill_id    INTEGER NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    proficiency VARCHAR(20) CHECK (proficiency IN ('beginner', 'intermediate', 'advanced', 'expert')),
    PRIMARY KEY (user_id, skill_id)
);

-- ---------------------------------------------------------------------
-- EDUCATION / EXPERIENCE / PROJECTS / CERTIFICATIONS
-- ---------------------------------------------------------------------
CREATE TABLE education_entries (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    institution     VARCHAR(255) NOT NULL,
    degree          VARCHAR(255),
    field_of_study  VARCHAR(255),
    start_year      INTEGER,
    end_year        INTEGER,
    description     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE experience_entries (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company         VARCHAR(255) NOT NULL,
    title           VARCHAR(255) NOT NULL,
    start_date      DATE,
    end_date        DATE,
    is_current      BOOLEAN NOT NULL DEFAULT FALSE,
    description     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE project_entries (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    url             TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE certification_entries (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            VARCHAR(255) NOT NULL,
    issuer          VARCHAR(255),
    issue_date      DATE,
    credential_url  TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- ORGANIZATIONS
-- ---------------------------------------------------------------------
CREATE TABLE organizations (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                VARCHAR(255) NOT NULL,
    logo_url            TEXT,
    description         TEXT,
    industry            VARCHAR(150),
    location            VARCHAR(150),
    website             TEXT,
    contact_email       VARCHAR(255),
    is_verified         BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE organization_members (
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role            VARCHAR(30) NOT NULL DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'member')),
    joined_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (organization_id, user_id)
);

-- ---------------------------------------------------------------------
-- OPPORTUNITIES
-- ---------------------------------------------------------------------
CREATE TABLE opportunities (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id         UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    title                   VARCHAR(255) NOT NULL,
    description             TEXT NOT NULL,
    type                    VARCHAR(20) NOT NULL CHECK (type IN
        ('job', 'internship', 'scholarship', 'fellowship', 'competition', 'event', 'training', 'other')),
    work_mode               VARCHAR(20) CHECK (work_mode IN ('remote', 'hybrid', 'on_site')),
    location                VARCHAR(150),
    salary_or_stipend       VARCHAR(100),
    deadline                TIMESTAMPTZ,
    education_requirement   VARCHAR(255),
    min_experience_years    NUMERIC(3,1) DEFAULT 0,
    min_cgpa                NUMERIC(3,2),
    eligibility_notes       TEXT,
    application_url         TEXT,
    status                  VARCHAR(20) NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'closed', 'draft')),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_opportunities_type ON opportunities(type);
CREATE INDEX idx_opportunities_status ON opportunities(status);
CREATE INDEX idx_opportunities_deadline ON opportunities(deadline);
CREATE INDEX idx_opportunities_org ON opportunities(organization_id);

CREATE TABLE opportunity_skills (
    opportunity_id  UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
    skill_id        INTEGER NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    importance      VARCHAR(20) NOT NULL DEFAULT 'required' CHECK (importance IN ('required', 'preferred')),
    PRIMARY KEY (opportunity_id, skill_id, importance)
);

-- ---------------------------------------------------------------------
-- APPLICATIONS / SAVED OPPORTUNITIES
-- ---------------------------------------------------------------------
CREATE TABLE applications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    opportunity_id  UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
    status          VARCHAR(20) NOT NULL DEFAULT 'applied' CHECK (status IN
        ('applied', 'under_review', 'shortlisted', 'rejected', 'accepted', 'withdrawn')),
    applied_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, opportunity_id)
);

CREATE INDEX idx_applications_user ON applications(user_id);
CREATE INDEX idx_applications_opportunity ON applications(opportunity_id);

CREATE TABLE saved_opportunities (
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    opportunity_id  UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
    saved_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, opportunity_id)
);

-- ---------------------------------------------------------------------
-- AI ANALYSES  (cached/explainable match results)
-- ---------------------------------------------------------------------
CREATE TABLE ai_analyses (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    opportunity_id      UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
    match_score         INTEGER NOT NULL CHECK (match_score BETWEEN 0 AND 100),
    eligibility_score   INTEGER NOT NULL CHECK (eligibility_score BETWEEN 0 AND 100),
    skills_score        INTEGER CHECK (skills_score BETWEEN 0 AND 100),
    education_score     INTEGER CHECK (education_score BETWEEN 0 AND 100),
    experience_score    INTEGER CHECK (experience_score BETWEEN 0 AND 100),
    matched_skills      JSONB NOT NULL DEFAULT '[]',
    missing_skills      JSONB NOT NULL DEFAULT '[]',
    explanation         TEXT,
    eligibility_notes   TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, opportunity_id)
);

-- ---------------------------------------------------------------------
-- updated_at auto-touch trigger
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION touch_updated_at() RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION touch_updated_at();
CREATE TRIGGER trg_profiles_updated_at BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION touch_updated_at();
CREATE TRIGGER trg_organizations_updated_at BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION touch_updated_at();
CREATE TRIGGER trg_opportunities_updated_at BEFORE UPDATE ON opportunities
    FOR EACH ROW EXECUTE FUNCTION touch_updated_at();
CREATE TRIGGER trg_applications_updated_at BEFORE UPDATE ON applications
    FOR EACH ROW EXECUTE FUNCTION touch_updated_at();
