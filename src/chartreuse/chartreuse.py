import logging
import os

import kubernetes

import wiremind_kubernetes.kubernetes_helper

from .utils import AlembicMigrationHelper, EslembicMigrationHelper


def configure_logging() -> None:
    logging.basicConfig(
        format="%(asctime)s %(levelname)s: %(message)s", datefmt="%H:%M:%S", level=logging.INFO,
    )


def _get_container_image() -> str:
    return os.environ["CHARTREUSE_POST_UPGRADE_CONTAINER_IMAGE"]


class Chartreuse(object):
    def __init__(
        self,
        postgresql_url: str,
        elasticsearch_url: str,
        release_name: str,
        alembic_allow_migration_for_empty_database: bool,
        eslembic_clean_index: bool = False,
        eslembic_enable_upgrade: bool = False,
        alembic_additional_parameters: str = "",
    ):
        self.alembic_migration_helper = AlembicMigrationHelper(
            postgresql_url,
            allow_migration_for_empty_database=alembic_allow_migration_for_empty_database,
            additional_parameters=alembic_additional_parameters,
        )
        if elasticsearch_url:
            self.eslembic_migration_helper = EslembicMigrationHelper(elasticsearch_url)
        self.eslembic_clean_index = eslembic_clean_index
        self.eslembic_enable_upgrade = eslembic_enable_upgrade

        self.kubernetes_helper = wiremind_kubernetes.kubernetes_helper.KubernetesDeploymentManager(
            use_kubeconfig=None, release_name=release_name
        )

        configure_logging()

        self.is_migration_needed = self.check_migration_needed()

    def check_migration_needed(self):
        alembic_migration_possible = self.alembic_migration_helper.is_migration_needed
        eslembic_migration_possible = (
            self.eslembic_migration_helper and self.eslembic_migration_helper.is_migration_needed
        )
        return alembic_migration_possible or eslembic_migration_possible

    def create_post_upgrade_job(self):
        if not self.eslembic_migration_helper:
            raise ValueError("ESlembic is not enabled.")
        job_name = "chartreuse-post-upgrade"
        environment = dict(ELASTICSEARCH_URL=self.eslembic_migration_helper.elasticsearch_url,)
        if self.eslembic_clean_index:
            environment["CHARTREUSE_ESLEMBIC_ENABLE_CLEAN"] = "1"
        else:
            environment["CHARTREUSE_ESLEMBIC_ENABLE_CLEAN"] = ""

        job: kubernetes.client.V1Job = self.kubernetes_helper.generate_job(
            job_name=job_name,
            container_image=_get_container_image(),
            environment_variables=environment,
            labels={
                "app.kubernetes.io/component": "chartreuse-port-upgrade",
                "app.kubernetes.io/instance": self.kubernetes_helper.release_name,
                "app.kubernetes.io/managed-by": "chartreuse",
            },
        )
        self.kubernetes_helper.create_job(job)

    def migrate(self):
        if self.alembic_migration_helper.is_migration_needed:
            self.alembic_migration_helper.migrate_db()

        if self.eslembic_migration_helper and self.eslembic_migration_helper.is_migration_needed:
            # Note: in eslembic, "upgrade" is to upgrade index itself, aka schema, while "migrate" is to migrate all data
            self.eslembic_migration_helper.upgrade_db()
            self.create_post_upgrade_job()
