BEGIN;

CREATE EXTENSION IF NOT EXISTS pgtap WITH SCHEMA extensions;

SELECT plan(8);

SELECT ok(
  (
    SELECT functions.prosecdef
      AND owners.rolname = 'sejong_schema_owner'
      AND functions.proconfig = ARRAY['search_path=pg_catalog, pg_temp']::text[]
    FROM pg_catalog.pg_proc AS functions
    JOIN pg_catalog.pg_roles AS owners ON owners.oid = functions.proowner
    WHERE functions.oid = pg_catalog.to_regprocedure(
      'app_private.validate_active_kb_question()'
    )
  ),
  'ACTIVE-question validator is schema-owner SECURITY DEFINER with fixed search_path'
);

SELECT results_eq(
  $actual$
    SELECT pg_catalog.format(
      '%I.%I(%s)',
      namespaces.nspname,
      functions.proname,
      pg_catalog.pg_get_function_identity_arguments(functions.oid)
    )::text COLLATE "C" AS function_identity
    FROM pg_catalog.pg_proc AS functions
    JOIN pg_catalog.pg_namespace AS namespaces
      ON namespaces.oid = functions.pronamespace
    WHERE namespaces.nspname = 'app_private'
      AND functions.prosecdef
    ORDER BY function_identity
  $actual$,
  $expected$
    SELECT expected.function_identity COLLATE "C"
    FROM (
      VALUES
        ('app_private.validate_active_kb_question()'::text)
    ) AS expected(function_identity)
    ORDER BY expected.function_identity
  $expected$,
  'validator is the sole SECURITY DEFINER among all app_private functions'
);

SELECT is(
  (
    SELECT pg_catalog.count(*)::integer
    FROM pg_catalog.pg_proc AS functions
    CROSS JOIN LATERAL pg_catalog.aclexplode(
      COALESCE(functions.proacl, pg_catalog.acldefault('f', functions.proowner))
    ) AS privileges
    WHERE functions.oid = pg_catalog.to_regprocedure(
      'app_private.validate_active_kb_question()'
    )
      AND privileges.grantee = 0
      AND privileges.privilege_type = 'EXECUTE'
  ),
  0,
  'PUBLIC has no direct EXECUTE on the private trigger validator'
);

SELECT ok(
  NOT pg_catalog.has_function_privilege(
    'anon', 'app_private.validate_active_kb_question()', 'EXECUTE'
  )
  AND NOT pg_catalog.has_function_privilege(
    'authenticated', 'app_private.validate_active_kb_question()', 'EXECUTE'
  )
  AND NOT pg_catalog.has_function_privilege(
    'sejong_backend', 'app_private.validate_active_kb_question()', 'EXECUTE'
  ),
  'browser and backend roles cannot directly execute the private trigger validator'
);

SELECT results_eq(
  $actual$
    SELECT
      namespaces.nspname::text COLLATE "C" AS schema_name,
      relations.relname::text COLLATE "C" AS table_name,
      triggers.tgname::text COLLATE "C" AS trigger_name,
      triggers.tgtype::integer AS trigger_type,
      triggers.tgenabled::text COLLATE "C" AS enabled,
      triggers.tgdeferrable,
      triggers.tginitdeferred,
      pg_catalog.format(
        '%I.%I(%s)',
        function_namespaces.nspname,
        functions.proname,
        pg_catalog.pg_get_function_identity_arguments(functions.oid)
      )::text COLLATE "C" AS function_identity,
      pg_catalog.pg_get_triggerdef(triggers.oid)::text COLLATE "C"
        AS trigger_definition
    FROM pg_catalog.pg_trigger AS triggers
    JOIN pg_catalog.pg_class AS relations ON relations.oid = triggers.tgrelid
    JOIN pg_catalog.pg_namespace AS namespaces
      ON namespaces.oid = relations.relnamespace
    JOIN pg_catalog.pg_proc AS functions ON functions.oid = triggers.tgfoid
    JOIN pg_catalog.pg_namespace AS function_namespaces
      ON function_namespaces.oid = functions.pronamespace
    WHERE NOT triggers.tgisinternal
      AND triggers.tgfoid = pg_catalog.to_regprocedure(
        'app_private.validate_active_kb_question()'
      )
    ORDER BY schema_name, table_name, trigger_name
  $actual$,
  $expected$
    SELECT
      expected.schema_name COLLATE "C",
      expected.table_name COLLATE "C",
      expected.trigger_name COLLATE "C",
      expected.trigger_type,
      expected.enabled COLLATE "C",
      expected.tgdeferrable,
      expected.tginitdeferred,
      expected.function_identity COLLATE "C",
      expected.trigger_definition COLLATE "C"
    FROM (
      VALUES
        (
          'app_private'::text,
          'kb_documents'::text,
          'ctrg_kb_documents_require_question'::text,
          21::integer,
          'O'::text,
          true,
          true,
          'app_private.validate_active_kb_question()'::text,
          'CREATE CONSTRAINT TRIGGER ctrg_kb_documents_require_question AFTER INSERT OR UPDATE ON app_private.kb_documents DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION app_private.validate_active_kb_question()'::text
        ),
        (
          'app_private'::text,
          'kb_question_examples'::text,
          'ctrg_kb_question_examples_require_active_question'::text,
          29::integer,
          'O'::text,
          true,
          true,
          'app_private.validate_active_kb_question()'::text,
          'CREATE CONSTRAINT TRIGGER ctrg_kb_question_examples_require_active_question AFTER INSERT OR DELETE OR UPDATE ON app_private.kb_question_examples DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION app_private.validate_active_kb_question()'::text
        )
    ) AS expected(
      schema_name,
      table_name,
      trigger_name,
      trigger_type,
      enabled,
      tgdeferrable,
      tginitdeferred,
      function_identity,
      trigger_definition
    )
    ORDER BY expected.schema_name, expected.table_name, expected.trigger_name
  $expected$,
  'both ACTIVE-question triggers retain exact table, event, row, deferred, and function bindings'
);

SELECT ok(
  NOT pg_catalog.has_schema_privilege('sejong_backend', 'app_private', 'USAGE'),
  'backend retains no app_private schema usage'
);

SELECT is(
  (
    SELECT pg_catalog.count(*)::integer
    FROM pg_catalog.pg_class AS relations
    JOIN pg_catalog.pg_namespace AS namespaces
      ON namespaces.oid = relations.relnamespace
    CROSS JOIN pg_catalog.unnest(
      ARRAY[
        'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE',
        'REFERENCES', 'TRIGGER', 'MAINTAIN'
      ]::text[]
    ) AS requested(privilege_name)
    WHERE namespaces.nspname = 'app_private'
      AND relations.relkind IN ('r', 'p')
      AND pg_catalog.has_table_privilege(
        'sejong_backend', relations.oid, requested.privilege_name
      )
  ),
  0,
  'backend retains no effective privilege on any private base or partitioned table'
);

SELECT ok(
  (
    SELECT pg_catalog.md5(functions.prosrc) =
      '6014f41ed693231e30a9369dd0e394a4'
      AND functions.prosrc !~* '\mEXECUTE\M'
      AND functions.prosrc LIKE '%FROM app_private.kb_documents%'
      AND functions.prosrc LIKE '%FROM app_private.kb_question_examples%'
    FROM pg_catalog.pg_proc AS functions
    WHERE functions.oid = pg_catalog.to_regprocedure(
      'app_private.validate_active_kb_question()'
    )
  ),
  'validator body fingerprint and schema-qualified static SQL remain unchanged'
);

SELECT * FROM finish();

ROLLBACK;
