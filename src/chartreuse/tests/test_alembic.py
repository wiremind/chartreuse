# noqa: W0212
# pylint: disable=W0212

import unittest

import mock

import chartreuse.utils


class AlembicTestCase(unittest.TestCase):
    def setUp(self):
        self.original_configure = chartreuse.utils.AlembicMigrationHelper._configure
        self.original_check_migration_possible = chartreuse.utils.AlembicMigrationHelper.check_migration_possible
        chartreuse.utils.AlembicMigrationHelper._configure = lambda x: None
        chartreuse.utils.AlembicMigrationHelper.check_migration_possible = lambda x: None
        self.alembicMigrationHelper = chartreuse.utils.AlembicMigrationHelper('foo')

    def tearDown(self):
        chartreuse.utils.AlembicMigrationHelper._configure = self.original_configure
        chartreuse.utils.AlembicMigrationHelper.check_migration_possible = self.original_check_migration_possible

    def test_respect_empty_database(self):
        """
        Test that is_postgres_empty returns empty even if alembic table exists
        """
        table_list = ['alembic_version']
        self.assertTrue(self.alembicMigrationHelper._is_postgres_empty(table_list))

    def test_respect_not_empty_database(self):
        """
        Test that is_postgres_empty says OK when tables exist
        """
        table_list = ['alembic_version', 'foobar']
        self.assertFalse(self.alembicMigrationHelper._is_postgres_empty(table_list))

    def test_detect_needed_migration(self):
        """
        Test that chartreuse detects that a migration is needed.
        """
        sample_alembic_output = """
2018-11-29 17:58:32 - wiremind_python.settings - DEBUG - Database: postgresql://***/public
2018-11-29 17:58:32 - wiremind_python.settings - DEBUG - redis instance at localhost is  activated
2018-11-29 17:58:32 - alembic.runtime.migration - INFO - Context impl PostgresqlImpl.
2018-11-29 17:58:32 - alembic.runtime.migration - INFO - Will assume transactional DDL.
e1f79bafdfa2
        """
        with mock.patch('os.chdir'):
            with mock.patch(
                    'chartreuse.utils.alembic_migration_helper.run_command',
                    return_value=(sample_alembic_output, 'foo')
            ):
                self.assertTrue(self.alembicMigrationHelper.is_migration_needed())

    def test_detect_not_needed_migration(self):
        """
        Test that chartreuse detects that a migration is not needed.
        """
        sample_alembic_output = """
2018-11-29 17:58:32 - wiremind_python.settings - DEBUG - Database: postgresql://***/public
2018-11-29 17:58:32 - wiremind_python.settings - DEBUG - redis instance at localhost is  activated
2018-11-29 17:58:32 - alembic.runtime.migration - INFO - Context impl PostgresqlImpl.
2018-11-29 17:58:32 - alembic.runtime.migration - INFO - Will assume transactional DDL.
e1f79bafdfa2 (head)
        """
        with mock.patch('os.chdir'):
            with mock.patch(
                    'chartreuse.utils.alembic_migration_helper.run_command',
                    return_value=(sample_alembic_output, 'foo')
            ):
                self.assertFalse(self.alembicMigrationHelper.is_migration_needed())

    def test_detect_needed_migration_non_existent(self):
        """
        Test that chartreuse detects that a migration is not needed.
        """
        sample_alembic_output = """
        """
        with mock.patch('os.chdir'):
            with mock.patch(
                    'chartreuse.utils.alembic_migration_helper.run_command',
                    return_value=(sample_alembic_output, 'foo')
            ):
                self.assertTrue(self.alembicMigrationHelper.is_migration_needed())

    def test_detect_database_is_empty(self):
        """
        Test that chartreuse detects that a database is empty and don't trigger migration.
        """
        sample_alembic_output = """
        """
        table_list = ["alembic_version"]
        with mock.patch('os.chdir'):
            with mock.patch(
                    'chartreuse.utils.alembic_migration_helper.run_command',
                    return_value=(sample_alembic_output, 'foo')
            ):
                with mock.patch(
                    'chartreuse.utils.alembic_migration_helper.AlembicMigrationHelper._get_table_list',
                    return_value=(table_list)
                ):
                    self.assertTrue(self.alembicMigrationHelper.is_postgres_empty())

    def test_detect_database_is_not_empty(self):
        """
        Test that chartreuse detects that a database is not empty and allow migration.
        """
        sample_alembic_output = """
        """
        table_list = ["alembic_version", "foo"]
        with mock.patch('os.chdir'):
            with mock.patch(
                    'chartreuse.utils.alembic_migration_helper.run_command',
                    return_value=(sample_alembic_output, 'foo')
            ):
                with mock.patch(
                    'chartreuse.utils.alembic_migration_helper.AlembicMigrationHelper._get_table_list',
                    return_value=(table_list)
                ):
                    self.assertFalse(self.alembicMigrationHelper.is_postgres_empty())
