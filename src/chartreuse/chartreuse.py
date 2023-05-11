import logging

import wiremind_kubernetes.kubernetes_helper

from .utils import AlembicMigrationHelper


def configure_logging() -> None:
    logging.basicConfig(
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
        level=logging.INFO,
    )


class Chartreuse:
    def __init__(
        self,
        alembic_directory_path: str,
        alembic_config_file_path: str,
        postgresql_url: str,
        release_name: str,
        alembic_allow_migration_for_empty_database: bool,
        alembic_additional_parameters: str = "",
        kubernetes_helper: wiremind_kubernetes.kubernetes_helper.KubernetesDeploymentManager = None,
    ):
        configure_logging()

        self.alembic_migration_helper = AlembicMigrationHelper(
            alembic_directory_path=alembic_directory_path,
            alembic_config_file_path=alembic_config_file_path,
            database_url=postgresql_url,
            allow_migration_for_empty_database=alembic_allow_migration_for_empty_database,
            additional_parameters=alembic_additional_parameters,
        )

        if kubernetes_helper:
            self.kubernetes_helper = kubernetes_helper
        else:
            self.kubernetes_helper = wiremind_kubernetes.kubernetes_helper.KubernetesDeploymentManager(
                use_kubeconfig=None, release_name=release_name
            )

        self.is_migration_needed = self.check_migration_needed()

    def check_migration_needed(self) -> bool:
        return self.alembic_migration_helper.is_migration_needed

    def upgrade(self) -> None:
        if self.check_migration_needed():
            self.alembic_migration_helper.upgrade_db()
