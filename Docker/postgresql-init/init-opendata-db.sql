-- PostgreSQL initialization for X-Road Metrics
-- Creates the opendata database and users for DEV instance
-- Database naming convention: opendata_{instance} where instance is lowercased

-- Create the database
CREATE DATABASE opendata_dev
    WITH TEMPLATE template0
    ENCODING 'utf8'
    LC_COLLATE 'en_US.utf8'
    LC_CTYPE 'en_US.utf8';

-- Create users

-- anonymizer_dev: Full access - used by anonymizer module to write data
CREATE USER anonymizer_dev WITH PASSWORD 'anonymizer_devsecret';
GRANT CREATE, CONNECT ON DATABASE opendata_dev TO anonymizer_dev WITH GRANT OPTION;

-- opendata_dev: Read-only - used by opendata module to read data
CREATE USER opendata_dev WITH PASSWORD 'opendata_devsecret';
GRANT CONNECT ON DATABASE opendata_dev TO opendata_dev;

-- networking_dev: Read-only - used by networking module to read data
CREATE USER networking_dev WITH PASSWORD 'networking_devsecret';
GRANT CONNECT ON DATABASE opendata_dev TO networking_dev;

-- PostgreSQL 15+ compatibility: Grant schema permissions
-- Starting from PostgreSQL 15, the public schema ownership changed to pg_database_owner.
-- Users need explicit CREATE and USAGE on public schema to create tables.
-- See: https://www.postgresql.org/docs/15/release-15.html#id-1.11.6.18.4
\connect opendata_dev
GRANT CREATE, USAGE ON SCHEMA public TO anonymizer_dev;

-- Note: SELECT permissions on the logs table are granted by the anonymizer module
-- when it runs, via the postgres.readonly-users configuration setting.
