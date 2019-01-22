# -*- coding: utf-8 -*-
from future.standard_library import install_aliases

install_aliases()

import os
import re
import socket

import requests

from chartreuse.utils.helpers import run_command


class EslembicMigrationHelper(object):
    elasticsearch_url = None
    allow_migration_for_empty_database = False

    def __init__(self, elasticsearch_url):
        if not elasticsearch_url:
            raise EnvironmentError("elasticsearch_url not set, not upgrading elasticsearch.")

        self.elasticsearch_url = elasticsearch_url

        self._configure()

    def _configure(self):
        print("Eslembic: configuring for %s" % self.elasticsearch_url)
        os.chdir("/app/eslembic")
        cleaned_url = self.elasticsearch_url.replace("/", r"\/")
        run_command(
            "sed -i -e 's/elasticsearch_urls.*=.*/elasticsearch_urls=%s/' %s"
            % (cleaned_url, "eslembic.ini")
        )

    def check_migration_possible(self):
        if not self._is_elasticsearch_reachable():
            print("Elasticsearch service does not answer, not upgrading Elasticsearch.")
            return False
        # if (not self.allow_migration_for_empty_database and self.is_postgres_empty()):
        #     print("Elasticsearch is not populated yet, not upgrading it.")
        #     return False
        if not self.is_migration_needed():
            print("Elasticsearch does not need migration.")
            return False
        print("Elasticsearch database can be migrated.")
        return True

    def _is_elasticsearch_reachable(self):
        os.chdir("/app/eslembic")
        try:
            requests.get(self.elasticsearch_url)
        except socket.gaierror:
            print(
                "Could not resolve hostname, assuming elasticsearch service does not exist yet."
            )
        except requests.exceptions.ConnectionError:
            print(
                "Could not reach elasticsearch, assuming service does not exist yet or is down."
            )
            return False
        return True

    def is_migration_needed(self):
        os.chdir("/app/eslembic")
        head_re = re.compile(r"\(head\)", re.MULTILINE)
        eslembic_current, _ = run_command("eslembic current")
        print(eslembic_current)
        if head_re.search(eslembic_current):
            return False
        return True

    def migrate_db(self):
        os.chdir("/app/eslembic")
        print("Elasticsearch needs to be upgraded. Proceeding.")
        run_command("eslembic history")

        print("Upgrading Elasticsearch...")
        run_command("eslembic upgrade head")

        print("Done upgrading Elasticsearch.")
