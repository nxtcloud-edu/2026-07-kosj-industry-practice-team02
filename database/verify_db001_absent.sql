DO $db001_absence$
DECLARE
  missing_platform_schemas text[];
BEGIN
  IF EXISTS (
    SELECT 1
    FROM pg_catalog.pg_namespace AS namespace
    WHERE namespace.nspname IN ('app_private', 'app_api')
  ) THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P0001',
      MESSAGE = 'DB001_APPLICATION_SCHEMA_STILL_PRESENT';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM pg_catalog.pg_roles AS role
    WHERE role.rolname IN ('sejong_schema_owner', 'sejong_backend')
  ) THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P0001',
      MESSAGE = 'DB001_ROLE_STILL_PRESENT';
  END IF;

  SELECT array_agg(required_schema.name ORDER BY required_schema.name)
  INTO missing_platform_schemas
  FROM unnest(
    ARRAY[
      'auth',
      'extensions',
      'public',
      'storage',
      'supabase_migrations'
    ]::text[]
  ) AS required_schema(name)
  WHERE NOT EXISTS (
    SELECT 1
    FROM pg_catalog.pg_namespace AS namespace
    WHERE namespace.nspname = required_schema.name
  );

  IF missing_platform_schemas IS NOT NULL THEN
    RAISE EXCEPTION USING
      ERRCODE = 'P0001',
      MESSAGE = 'PLATFORM_SCHEMA_MISSING';
  END IF;
END;
$db001_absence$;
