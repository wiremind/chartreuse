import logging

import wiremind_kubernetes.kubernetes_helper

from .config_loader import DatabaseConfig
from .utils import AlembicMigrationHelper

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    logging.basicConfig(
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
        level=logging.INFO,
    )


class Chartreuse:
    """Handles single or multiple database migrations."""

    def __init__(
        self,
        databases_config: dict[str, DatabaseConfig],
        release_name: str,
        kubernetes_helper: wiremind_kubernetes.kubernetes_helper.KubernetesDeploymentManager | None = None,
    ):
        configure_logging()

        self.databases_config = databases_config
        self.migration_helpers: dict[str, AlembicMigrationHelper] = {}

        # Initialize migration helpers for each database
        for db_name, db_config in databases_config.items():
            logger.info("Initializing migration helper for database: %s", db_name)

            # Build additional parameters with section name
            additional_params = db_config.additional_parameters

            # Use database name as section name for alembic -n parameter
            section_param = f"-n {db_name}"

            additional_params = f"{additional_params} {section_param}".strip()

            helper = AlembicMigrationHelper(
                alembic_directory_path=db_config.alembic_directory_path,
                alembic_config_file_path=db_config.alembic_config_file_path,
                database_url=db_config.url,
                allow_migration_for_empty_database=db_config.allow_migration_for_empty_database,
                additional_parameters=additional_params,
                alembic_section_name=db_name,
                is_patroni_postgresql=db_config.is_patroni_postgresql,
            )
            self.migration_helpers[db_name] = helper

        # Initialize Kubernetes helper
        if kubernetes_helper:
            self.kubernetes_helper = kubernetes_helper
        else:
            self.kubernetes_helper = wiremind_kubernetes.kubernetes_helper.KubernetesDeploymentManager(
                use_kubeconfig=None, release_name=release_name
            )

    @property
    def is_migration_needed(self) -> bool:
        """Check if any database needs migration."""
        for db_name, helper in self.migration_helpers.items():
            if helper.is_migration_needed:
                logger.info("Database '%s' needs migration", db_name)
                return True
        return False

    def upgrade(self) -> None:
        """Upgrade all databases that need migration."""
        for db_name, helper in self.migration_helpers.items():
            if helper.is_migration_needed:
                logger.info("Upgrading database: %s", db_name)
                helper.upgrade_db()
                logger.info("Successfully upgraded database: %s", db_name)
            else:
                logger.info("Database '%s' is up to date", db_name)
