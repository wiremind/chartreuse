# -*- coding: utf-8 -*-
# noqa: W0212
# pylint: disable=W0212

import unittest

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
