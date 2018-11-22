# -*- coding: utf-8 -*-
import time

import wiremind_kubernetes

from . import AlembicMigrationHelper, EslembicMigrationHelper


class Chartreuse(object):
    def __init__(self, database_url, elasticsearch_url, allow_migration_for_empty_database):
        self.allow_migration_for_empty_database = allow_migration_for_empty_database

        self.alembic_migration_helper = AlembicMigrationHelper(
            database_url, allow_migration_for_empty_database
        )

        self.eslembic_migration_helper = \
            EslembicMigrationHelper(elasticsearch_url) if elasticsearch_url \
            else None

    def is_migration_possible(self):
        alembic_migration_possible = self.alembic_migration_helper.check_migration_possible()
        eslembic_migration_possible =  \
            self.eslembic_migration_helper.check_migration_possible() if self.eslembic_migration_helper \
            else False
        return alembic_migration_possible or eslembic_migration_possible

    def migrate(self):
        self.alembic_migration_helper.migrate_db()
        if self.eslembic_migration_helper:
            self.eslembic_migration_helper.migrate_db()

    def start_pods(self):
        """
        Start all Pods that should be started
        """
        kubernetes_helper = wiremind_kubernetes.KubernetesHelper()
        expected_deployment_scale_dict = kubernetes_helper.get_expected_deployment_scale_dict()

        if not expected_deployment_scale_dict:
            return

        print("Scaling up pods")
        for (name, amount) in expected_deployment_scale_dict.items():
            kubernetes_helper.scale_up_deployment(name, amount)

    def stop_pods(self):
        """
        SQL migration implies that every backend pod should be restarted.
        We stop them before applying migration
        """
        kubernetes_helper = wiremind_kubernetes.KubernetesHelper()
        deployment_list = kubernetes_helper.get_deployment_name_to_be_stopped_list()

        if not deployment_list:
            return

        print("Shutting down pods")
        for deployment_name in deployment_list:
            kubernetes_helper.scale_down_deployment(deployment_name)

        # Make sure to wait for actual stop (can be looong)
        for _ in range(360):  # 1 hour
            time.sleep(10)
            stopped = 0
            for deployment_name in deployment_list:
                if kubernetes_helper.is_deployment_stopped(deployment_name):
                    stopped += 1
            if stopped == len(deployment_list):
                break
            else:
                print("All pods not stopped yet. Waiting...")
        print("All pods have been stopped.")
