import logging

import wiremind_kubernetes.kubernetes_helper

from .utils import AlembicMigrationHelper

logger = logging.getLogger(__name__)


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
        kubernetes_helper: wiremind_kubernetes.kubernetes_helper.KubernetesDeploymentManager | None = None,
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


class MultiChartreuse:
    """Handles multiple database migrations."""

    def __init__(
        self,
        databases_config: list[dict],
        release_name: str,
        kubernetes_helper: wiremind_kubernetes.kubernetes_helper.KubernetesDeploymentManager | None = None,
    ):
        configure_logging()

        self.databases_config = databases_config
        self.migration_helpers: dict[str, AlembicMigrationHelper] = {}

        # Initialize migration helpers for each database
        for db_config in databases_config:
            db_name = db_config["name"]
            logger.info(f"Initializing migration helper for database: {db_name}")

            # Build additional parameters with section name
            additional_params = db_config.get("additional_parameters", "")

            # Use database name as section name for alembic -n parameter
            section_param = f"-n {db_name}"

            if section_param:
                additional_params = f"{additional_params} {section_param}".strip()

            helper = AlembicMigrationHelper(
                alembic_directory_path=db_config["alembic_directory_path"],
                alembic_config_file_path=db_config["alembic_config_file_path"],
                database_url=db_config["url"],
                allow_migration_for_empty_database=db_config.get("allow_migration_for_empty_database", False),
                additional_parameters=additional_params,
                alembic_section_name=db_name,
            )
            self.migration_helpers[db_name] = helper

        # Initialize Kubernetes helper
        if kubernetes_helper:
            self.kubernetes_helper = kubernetes_helper
        else:
            self.kubernetes_helper = wiremind_kubernetes.kubernetes_helper.KubernetesDeploymentManager(
                use_kubeconfig=None, release_name=release_name
            )

        # Check if any migrations are needed
        self.is_migration_needed = self.check_migration_needed()

    def check_migration_needed(self) -> bool:
        """Check if any database needs migration."""
        for db_name, helper in self.migration_helpers.items():
            if helper.is_migration_needed:
                logger.info(f"Database '{db_name}' needs migration")
                return True
        return False

    def upgrade(self) -> None:
        """Upgrade all databases that need migration."""
        for db_name, helper in self.migration_helpers.items():
            if helper.is_migration_needed:
                logger.info(f"Upgrading database: {db_name}")
                helper.upgrade_db()
                logger.info(f"Successfully upgraded database: {db_name}")
            else:
                logger.info(f"Database '{db_name}' is up to date")
