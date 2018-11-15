# -*- coding: utf-8 -*-
from future.standard_library import install_aliases

install_aliases()

import os
import re
import socket
import sys
import urllib.parse
import time

import sqlalchemy

from wiremind_kubernetes import KubernetesHelper, _run_command


def stop_pods():
    """
    SQL migration implies that every worker should be restarted.
    We stop every worker before applying migration
    """
    kubernetes_helper = KubernetesHelper()
    celery_deployment_list = kubernetes_helper.get_deployment_name_to_be_stopped_list()

    if not celery_deployment_list:
        return

    print("Shutting down celery workers")
    for celery_deployment_name in celery_deployment_list:
        kubernetes_helper.scale_down_deployment(celery_deployment_name)

    # Make sure to wait for actual stop (can be looong)
    for _ in range(360):  # 1 hour
        time.sleep(10)
        stopped = 0
        for celery_deployment_name in celery_deployment_list:
            if kubernetes_helper.is_deployment_stopped(celery_deployment_name):
                stopped += 1
        if stopped == len(celery_deployment_list):
            break
        else:
            print("Celery workers not stopped yet. Waiting...")
    print("Celery workers have been stopped.")


class AlembicMigrationHelper(object):
    database_url = None
    allow_migration_for_empty_database = False

    def __init__(self, database_url, allow_migration_for_empty_database=False):
        if not database_url:
            raise EnvironmentError("database_url not set, not upgrading database.")

        self.database_url = database_url
        self.allow_migration_for_empty_database = allow_migration_for_empty_database

        self._configure()
        self._check_migration_possible()

    def _configure(self):
        os.chdir("/app/alembic")
        cleaned_url = self.database_url.replace("/", r"\/")
        _run_command(
            "sed -i -e 's/sqlalchemy.url.*=.*/sqlalchemy.url=%s/' %s"
            % (cleaned_url, "alembic.ini")
        )

    def _check_migration_possible(self):
        if not self.is_postgres_domain_name_resolvable():
            print("Postgres server does not exist yet, not upgrading database.")
            sys.exit(0)
        if not self.is_postgres_reachable():
            print("Postgres server does not answer, not upgrading database.")
            sys.exit(0)
        if (not self.allow_migration_for_empty_database and self.is_postgres_empty()):
            print("Database is not populated yet, not upgrading it.")
            sys.exit(0)
        if not self.is_migration_needed():
            print("Database does not need migration, exiting.")
            sys.exit(0)

    def is_postgres_domain_name_resolvable(self):
        os.chdir("/app/alembic")
        hostname = urllib.parse.urlparse(self.database_url).hostname
        try:
            socket.gethostbyname(hostname)
        except socket.gaierror:
            print(
                "Could not resolve hostname %s, assuming postgres server does not exist yet."
                % hostname
            )
            return False
        return True

    def is_postgres_reachable(self):
        os.chdir("/app/alembic")
        try:
            sqlalchemy.create_engine(self.database_url).table_names()
        except sqlalchemy.exc.OperationalError:
            print(
                "Could not reach postgresql, assuming postgres server does not exist yet or is down."
            )
            return False
        return True

    def is_postgres_empty(self):
        os.chdir("/app/alembic")
        table_list = sqlalchemy.create_engine(self.database_url).table_names()
        self._is_postgres_empty(table_list)

    def _is_postgres_empty(self, table_list):
        """
        Internal method called by is_postgres_empty to ease testing.
        """
        print("Tables in database: %s" % table_list)
        # Don't count "alembic" table
        table_name = "alembic_version"
        if table_name in table_list:
            table_list.remove(table_name)
        if table_list:
            return False
        return True

    def is_migration_needed(self):
        os.chdir("/app/alembic")
        head_re = re.compile(r"^\w+ \(head\)$", re.MULTILINE)
        alembic_current, _ = _run_command("alembic current")
        print("Current revision: %s" % alembic_current)
        if head_re.search(alembic_current):
            return False
        return True

    def migrate_db(self):
        print("Database needs to be upgraded. Proceeding.")
        _run_command("alembic history -r current:head")

        print("Upgrading database...")
        _run_command("alembic upgrade head")

        print("Done upgrading database.")
