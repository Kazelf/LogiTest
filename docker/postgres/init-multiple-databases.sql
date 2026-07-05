DO
$$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'logitest') THEN
      CREATE ROLE logitest LOGIN PASSWORD 'logitest';
   END IF;

   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'shoplite') THEN
      CREATE ROLE shoplite LOGIN PASSWORD 'shoplite';
   END IF;
END
$$;

SELECT 'CREATE DATABASE logitest_ai OWNER logitest'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'logitest_ai')\gexec

SELECT 'CREATE DATABASE shoplite OWNER shoplite'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'shoplite')\gexec
