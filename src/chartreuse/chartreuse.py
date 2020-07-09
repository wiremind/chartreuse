import logging
import os
from typing import List

import kubernetes
import wiremind_kubernetes.kubernetes_helper

from .utils import AlembicMigrationHelper, EslembicMigrationHelper

CHARTREUSE_MIGRATE_JOB_NAME = "chartreuse-migrate"


def configure_logging() -> None:
    logging.basicConfig(
        format="%(asctime)s %(levelname)s: %(message)s", datefmt="%H:%M:%S", level=logging.INFO,
    )


def _get_container_image() -> str:
    return os.environ["CHARTREUSE_MIGRATE_CONTAINER_IMAGE"]


def _get_image_pull_secrets() -> List[str]:
    return [kubernetes.client.V1LocalObjectReference(os.environ["CHARTREUSE_MIGRATE_IMAGE_PULL_SECRET"])]


class Chartreuse:
    def __init__(
        self,
        postgresql_url: str,
        elasticsearch_url: str,
        release_name: str,
        alembic_allow_migration_for_empty_database: bool,
        eslembic_clean_index: bool = False,
        eslembic_enable_migrate: bool = False,
        alembic_additional_parameters: str = "",
        kubernetes_helper: wiremind_kubernetes.kubernetes_helper.KubernetesDeploymentManager = None,
    ):
        self.alembic_migration_helper = AlembicMigrationHelper(
            postgresql_url,
            allow_migration_for_empty_database=alembic_allow_migration_for_empty_database,
            additional_parameters=alembic_additional_parameters,
        )
        if elasticsearch_url:
            self.eslembic_migration_helper = EslembicMigrationHelper(elasticsearch_url)
        self.eslembic_clean_index = eslembic_clean_index
        self.eslembic_enable_migrate = eslembic_enable_migrate

        if kubernetes_helper:
            self.kubernetes_helper = kubernetes_helper
        else:
            self.kubernetes_helper = wiremind_kubernetes.kubernetes_helper.KubernetesDeploymentManager(
                use_kubeconfig=None, release_name=release_name
            )

        configure_logging()

        self.is_migration_needed = self.check_migration_needed()

    def _check_no_migrate_job_is_running_and_delete_finished(self):
        """
        Check that no "chartreuse migrate" job is already running.
        If so, raise: we NEVER want to upgrade at the same time than a previous "eslembic migrate".
        If there is a finished job, delete it.
        """
        try:
            job: kubernetes.client.V1Job = self.kubernetes_helper.get_job(CHARTREUSE_MIGRATE_JOB_NAME)
            if job.status.succeeded != 1:
                raise Exception(
                    f"Job {CHARTREUSE_MIGRATE_JOB_NAME} is already running, aborting"
                )  # XXX what exception?
            self.kubernetes_helper.delete_job(CHARTREUSE_MIGRATE_JOB_NAME)
        except kubernetes.client.rest.ApiException as e:
            if e.status == 404:
                return

    def check_migration_needed(self):
        alembic_migration_possible = self.alembic_migration_helper.is_migration_needed
        eslembic_migration_possible = (
            self._eslembic_migration_is_enabled() and self.eslembic_migration_helper.is_migration_needed
        )
        if eslembic_migration_possible:
            self._check_no_migrate_job_is_running_and_delete_finished()
        return alembic_migration_possible or eslembic_migration_possible

    def create_post_upgrade_job(self):
        if not self._eslembic_migration_is_enabled():
            raise ValueError("ESlembic is not enabled.")
        environment = dict(CHARTREUSE_ESLEMBIC_URL=self.eslembic_migration_helper.elasticsearch_url,)
        if self.eslembic_clean_index:
            environment["CHARTREUSE_ESLEMBIC_ENABLE_CLEAN"] = "1"
        else:
            environment["CHARTREUSE_ESLEMBIC_ENABLE_CLEAN"] = ""
        if self.eslembic_enable_migrate:
            environment["CHARTREUSE_ESLEMBIC_ENABLE_MIGRATE"] = "1"
        else:
            environment["CHARTREUSE_ESLEMBIC_ENABLE_MIGRATE"] = ""

        job: kubernetes.client.V1Job = self.kubernetes_helper.generate_job(
            job_name=CHARTREUSE_MIGRATE_JOB_NAME,
            container_image=_get_container_image(),
            command="chartreuse-migrate",
            environment_variables=environment,
            labels={
                "app.kubernetes.io/component": "chartreuse-migrate",
                "app.kubernetes.io/instance": self.kubernetes_helper.release_name,
                "app.kubernetes.io/managed-by": "chartreuse",
            },
            image_pull_secrets=_get_image_pull_secrets(),
        )
        self.kubernetes_helper.create_job(job)

    def upgrade(self):
        if self.alembic_migration_helper.is_migration_needed:
            self.alembic_migration_helper.upgrade_db()

        if self._eslembic_migration_is_enabled() and self.eslembic_migration_helper.is_migration_needed:
            # Note: in eslembic, "upgrade" is to upgrade index itself, aka schema, while "migrate" is to migrate all data
            self.eslembic_migration_helper.upgrade_db()
            if self.eslembic_enable_migrate or self.eslembic_clean_index:
                self.create_post_upgrade_job()

    def _eslembic_migration_is_enabled(self) -> bool:
        return hasattr(self, "eslembic_migration_helper")
