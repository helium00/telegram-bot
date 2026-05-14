-- This script runs once when the PostgreSQL container is first created.
-- The POSTGRES_USER / POSTGRES_DB are already created by the official image
-- via environment variables, so we only need to tighten privileges here.

-- Revoke default public schema access
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO sagunto_bot_user;

-- Restrict future table privileges to the bot user only
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sagunto_bot_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO sagunto_bot_user;
