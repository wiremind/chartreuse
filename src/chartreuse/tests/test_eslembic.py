# noqa: W0212
# pylint: disable=W0212

import unittest

import mock

import chartreuse.utils


class EslembicTestCase(unittest.TestCase):
    def setUp(self):
        self.original_configure = chartreuse.utils.EslembicMigrationHelper._configure
        self.original_check_migration_possible = chartreuse.utils.EslembicMigrationHelper.check_migration_possible
        chartreuse.utils.EslembicMigrationHelper._configure = lambda x: None
        chartreuse.utils.EslembicMigrationHelper.check_migration_possible = lambda x: None
        self.eslembicMigrationHelper = chartreuse.utils.EslembicMigrationHelper('foo')

    def tearDown(self):
        chartreuse.utils.EslembicMigrationHelper._configure = self.original_configure
        chartreuse.utils.EslembicMigrationHelper.check_migration_possible = self.original_check_migration_possible

    def test_detect_needed_migration(self):
        """
        Test that chartreuse detects that a migration is needed.
        """
        sample_eslembic_output = """
2018-11-29 17:58:33,500 - elasticsearch - INFO - HEAD http://url:9200/eslembic_version [status:200 request:0.01s]
2018-11-29 17:58:33,510 - elasticsearch - INFO - GET http://url:9200/eslembic_version/_search [status:200 request:0.01s]
2018-11-29 17:58:33,511 - eslembic.core.migration_runner - INFO - ESlembic version is v1.0.0, bla
        """
        with mock.patch('os.chdir'):
            with mock.patch(
                    'chartreuse.utils.eslembic_migration_helper.run_command',
                    return_value=(sample_eslembic_output, 'foo')
            ):
                self.assertTrue(self.eslembicMigrationHelper.is_migration_needed())

    def test_detect_not_needed_migration(self):
        """
        Test that chartreuse detects that a migration is not needed.
        """
        sample_eslembic_output = """
2018-11-29 17:58:33,500 - elasticsearch - INFO - HEAD http://url:9200/eslembic_version [status:200 request:0.01s]
2018-11-29 17:58:33,510 - elasticsearch - INFO - GET http://url:9200/eslembic_version/_search [status:200 request:0.01s]
2018-11-29 17:58:33,511 - eslembic.core.migration_runner - INFO - ESlembic version is v1.0.0 (head), init
        """
        with mock.patch('os.chdir'):
            with mock.patch(
                    'chartreuse.utils.eslembic_migration_helper.run_command',
                    return_value=(sample_eslembic_output, 'foo')
            ):
                self.assertFalse(self.eslembicMigrationHelper.is_migration_needed())

    def test_clean_index(self):
        """
        Test that chartreuse correctly call eslembic if clean_index is set.
        """
        with mock.patch('os.chdir'):
            with mock.patch(
                    'chartreuse.utils.eslembic_migration_helper.run_command',
            ) as mocked_run_command:
                self.eslembicMigrationHelper = chartreuse.utils.EslembicMigrationHelper('foo', True)
                self.eslembicMigrationHelper.migrate_db()
                mocked_run_command.assert_called_with('eslembic upgrade head --clean-index')

    def test_no_clean_index(self):
        """
        Test that chartreuse correctly call eslembic if clean_index is not set (default).
        """
        with mock.patch('os.chdir'):
            with mock.patch(
                    'chartreuse.utils.eslembic_migration_helper.run_command',
            ) as mocked_run_command:
                self.eslembicMigrationHelper.migrate_db()
                mocked_run_command.assert_called_with('eslembic upgrade head')
