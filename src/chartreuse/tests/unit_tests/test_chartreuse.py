"""Unit tests for chartreuse main module."""

import logging
from unittest.mock import MagicMock

from pytest_mock.plugin import MockerFixture

from chartreuse.chartreuse import Chartreuse, MultiChartreuse, configure_logging


class TestConfigureLogging:
    """Test cases for configure_logging function."""

    def test_configure_logging(self, mocker: MockerFixture) -> None:
        """Test that logging is configured correctly."""
        mock_basic_config = mocker.patch("logging.basicConfig")

        configure_logging()

        mock_basic_config.assert_called_once_with(
            format="%(asctime)s %(levelname)s: %(message)s",
            datefmt="%H:%M:%S",
            level=logging.INFO,
        )


class TestChartreuse:
    """Test cases for Chartreuse class."""

    def test_chartreuse_init_with_kubernetes_helper(
        self, mocker: MockerFixture
    ) -> None:
        """Test Chartreuse initialization with provided kubernetes helper."""
        # Mock AlembicMigrationHelper
        mock_alembic_helper = mocker.patch(
            "chartreuse.chartreuse.AlembicMigrationHelper"
        )
        mock_alembic_instance = MagicMock()
        mock_alembic_instance.is_migration_needed = True
        mock_alembic_helper.return_value = mock_alembic_instance

        # Mock configure_logging
        mocker.patch("chartreuse.chartreuse.configure_logging")

        # Create a mock kubernetes helper
        mock_k8s_helper = MagicMock()

        chartreuse = Chartreuse(
            alembic_directory_path="/app/alembic",
            alembic_config_file_path="alembic.ini",
            postgresql_url="postgresql://user:pass@localhost:5432/db",
            release_name="test-release",
            alembic_allow_migration_for_empty_database=True,
            alembic_additional_parameters="--verbose",
            kubernetes_helper=mock_k8s_helper,
        )

        # Verify AlembicMigrationHelper was initialized correctly
        mock_alembic_helper.assert_called_once_with(
            alembic_directory_path="/app/alembic",
            alembic_config_file_path="alembic.ini",
            database_url="postgresql://user:pass@localhost:5432/db",
            allow_migration_for_empty_database=True,
            additional_parameters="--verbose",
        )

        # Verify kubernetes helper is set
        assert chartreuse.kubernetes_helper == mock_k8s_helper
        assert chartreuse.is_migration_needed is True

    def test_chartreuse_init_without_kubernetes_helper(
        self, mocker: MockerFixture
    ) -> None:
        """Test Chartreuse initialization without provided kubernetes helper."""
        # Mock AlembicMigrationHelper
        mock_alembic_helper = mocker.patch(
            "chartreuse.chartreuse.AlembicMigrationHelper"
        )
        mock_alembic_instance = MagicMock()
        mock_alembic_instance.is_migration_needed = False
        mock_alembic_helper.return_value = mock_alembic_instance

        # Mock KubernetesDeploymentManager
        mock_k8s_manager = mocker.patch(
            "wiremind_kubernetes.kubernetes_helper.KubernetesDeploymentManager"
        )
        mock_k8s_instance = MagicMock()
        mock_k8s_manager.return_value = mock_k8s_instance

        # Mock configure_logging
        mocker.patch("chartreuse.chartreuse.configure_logging")

        chartreuse = Chartreuse(
            alembic_directory_path="/app/alembic",
            alembic_config_file_path="alembic.ini",
            postgresql_url="postgresql://user:pass@localhost:5432/db",
            release_name="test-release",
            alembic_allow_migration_for_empty_database=False,
        )

        # Verify KubernetesDeploymentManager was initialized
        mock_k8s_manager.assert_called_once_with(
            use_kubeconfig=None, release_name="test-release"
        )

        assert chartreuse.kubernetes_helper == mock_k8s_instance
        assert chartreuse.is_migration_needed is False

    def test_check_migration_needed(self, mocker: MockerFixture) -> None:
        """Test check_migration_needed method."""
        mock_alembic_helper = mocker.patch(
            "chartreuse.chartreuse.AlembicMigrationHelper"
        )
        mock_alembic_instance = MagicMock()
        mock_alembic_instance.is_migration_needed = True
        mock_alembic_helper.return_value = mock_alembic_instance

        mocker.patch("chartreuse.chartreuse.configure_logging")
        mock_k8s_helper = MagicMock()

        chartreuse = Chartreuse(
            alembic_directory_path="/app/alembic",
            alembic_config_file_path="alembic.ini",
            postgresql_url="postgresql://user:pass@localhost:5432/db",
            release_name="test-release",
            alembic_allow_migration_for_empty_database=True,
            kubernetes_helper=mock_k8s_helper,
        )

        result = chartreuse.check_migration_needed()
        assert result is True

        # Change the mock return value
        mock_alembic_instance.is_migration_needed = False
        result = chartreuse.check_migration_needed()
        assert result is False

    def test_upgrade_when_migration_needed(self, mocker: MockerFixture) -> None:
        """Test upgrade method when migration is needed."""
        mock_alembic_helper = mocker.patch(
            "chartreuse.chartreuse.AlembicMigrationHelper"
        )
        mock_alembic_instance = MagicMock()
        mock_alembic_instance.is_migration_needed = True
        mock_alembic_helper.return_value = mock_alembic_instance

        mocker.patch("chartreuse.chartreuse.configure_logging")
        mock_k8s_helper = MagicMock()

        chartreuse = Chartreuse(
            alembic_directory_path="/app/alembic",
            alembic_config_file_path="alembic.ini",
            postgresql_url="postgresql://user:pass@localhost:5432/db",
            release_name="test-release",
            alembic_allow_migration_for_empty_database=True,
            kubernetes_helper=mock_k8s_helper,
        )

        chartreuse.upgrade()

        # Verify upgrade_db was called
        mock_alembic_instance.upgrade_db.assert_called_once()

    def test_upgrade_when_migration_not_needed(self, mocker: MockerFixture) -> None:
        """Test upgrade method when migration is not needed."""
        mock_alembic_helper = mocker.patch(
            "chartreuse.chartreuse.AlembicMigrationHelper"
        )
        mock_alembic_instance = MagicMock()
        mock_alembic_instance.is_migration_needed = False
        mock_alembic_helper.return_value = mock_alembic_instance

        mocker.patch("chartreuse.chartreuse.configure_logging")
        mock_k8s_helper = MagicMock()

        chartreuse = Chartreuse(
            alembic_directory_path="/app/alembic",
            alembic_config_file_path="alembic.ini",
            postgresql_url="postgresql://user:pass@localhost:5432/db",
            release_name="test-release",
            alembic_allow_migration_for_empty_database=True,
            kubernetes_helper=mock_k8s_helper,
        )

        chartreuse.upgrade()

        # Verify upgrade_db was not called
        mock_alembic_instance.upgrade_db.assert_not_called()


class TestMultiChartreuse:
    """Test cases for MultiChartreuse class."""

    def test_multi_chartreuse_init_with_kubernetes_helper(
        self, mocker: MockerFixture
    ) -> None:
        """Test MultiChartreuse initialization with provided kubernetes helper."""
        # Mock AlembicMigrationHelper
        mock_alembic_helper = mocker.patch(
            "chartreuse.chartreuse.AlembicMigrationHelper"
        )

        # Create mock instances for different databases
        mock_main_instance = MagicMock()
        mock_main_instance.is_migration_needed = True

        mock_sec_instance = MagicMock()
        mock_sec_instance.is_migration_needed = False

        # Configure the mock to return different instances for different calls
        mock_alembic_helper.side_effect = [mock_main_instance, mock_sec_instance]

        # Mock configure_logging
        mocker.patch("chartreuse.chartreuse.configure_logging")

        # Create a mock kubernetes helper
        mock_k8s_helper = MagicMock()

        databases_config: list[dict[str, any]] = [
            {
                "name": "main",
                "alembic_directory_path": "/app/alembic/main",
                "alembic_config_file_path": "alembic.ini",
                "url": "postgresql://user:pass@localhost:5432/maindb",
                "allow_migration_for_empty_database": True,
                "additional_parameters": "--verbose",
            },
            {
                "name": "secondary",
                "alembic_directory_path": "/app/alembic/secondary",
                "alembic_config_file_path": "alembic.ini",
                "url": "postgresql://user:pass@localhost:5433/secdb",
            },
        ]

        multi_chartreuse = MultiChartreuse(
            databases_config=databases_config,
            release_name="test-release",
            kubernetes_helper=mock_k8s_helper,
        )

        # Verify AlembicMigrationHelper was called for each database
        assert mock_alembic_helper.call_count == 2

        # Verify migration helpers are stored correctly
        assert "main" in multi_chartreuse.migration_helpers
        assert "secondary" in multi_chartreuse.migration_helpers
        assert multi_chartreuse.migration_helpers["main"] == mock_main_instance
        assert multi_chartreuse.migration_helpers["secondary"] == mock_sec_instance

        # Verify kubernetes helper is set
        assert multi_chartreuse.kubernetes_helper == mock_k8s_helper

        # Verify migration is needed (because main db needs migration)
        assert multi_chartreuse.is_migration_needed is True

    def test_multi_chartreuse_init_without_kubernetes_helper(
        self, mocker: MockerFixture
    ) -> None:
        """Test MultiChartreuse initialization without provided kubernetes helper."""
        # Mock AlembicMigrationHelper
        mock_alembic_helper = mocker.patch(
            "chartreuse.chartreuse.AlembicMigrationHelper"
        )
        mock_alembic_instance = MagicMock()
        mock_alembic_instance.is_migration_needed = False
        mock_alembic_helper.return_value = mock_alembic_instance

        # Mock KubernetesDeploymentManager
        mock_k8s_manager = mocker.patch(
            "wiremind_kubernetes.kubernetes_helper.KubernetesDeploymentManager"
        )
        mock_k8s_instance = MagicMock()
        mock_k8s_manager.return_value = mock_k8s_instance

        # Mock configure_logging
        mocker.patch("chartreuse.chartreuse.configure_logging")

        databases_config: list[dict[str, any]] = [
            {
                "name": "test",
                "alembic_directory_path": "/app/alembic",
                "alembic_config_file_path": "alembic.ini",
                "url": "postgresql://user:pass@localhost:5432/db",
            }
        ]

        multi_chartreuse = MultiChartreuse(
            databases_config=databases_config,
            release_name="test-release",
        )

        # Verify KubernetesDeploymentManager was initialized
        mock_k8s_manager.assert_called_once_with(
            use_kubeconfig=None, release_name="test-release"
        )

        assert multi_chartreuse.kubernetes_helper == mock_k8s_instance

    def test_check_migration_needed_with_mixed_needs(
        self, mocker: MockerFixture
    ) -> None:
        """Test check_migration_needed with some databases needing migration."""
        mock_alembic_helper = mocker.patch(
            "chartreuse.chartreuse.AlembicMigrationHelper"
        )

        # Create mock instances
        mock_main_instance = MagicMock()
        mock_main_instance.is_migration_needed = False

        mock_sec_instance = MagicMock()
        mock_sec_instance.is_migration_needed = True

        mock_alembic_helper.side_effect = [mock_main_instance, mock_sec_instance]

        mocker.patch("chartreuse.chartreuse.configure_logging")
        mock_k8s_helper = MagicMock()

        databases_config: list[dict[str, any]] = [
            {
                "name": "main",
                "alembic_directory_path": "/app/alembic/main",
                "alembic_config_file_path": "alembic.ini",
                "url": "postgresql://user:pass@localhost:5432/maindb",
            },
            {
                "name": "secondary",
                "alembic_directory_path": "/app/alembic/secondary",
                "alembic_config_file_path": "alembic.ini",
                "url": "postgresql://user:pass@localhost:5433/secdb",
            },
        ]

        multi_chartreuse = MultiChartreuse(
            databases_config=databases_config,
            release_name="test-release",
            kubernetes_helper=mock_k8s_helper,
        )

        # Should return True because secondary needs migration
        result = multi_chartreuse.check_migration_needed()
        assert result is True

    def test_check_migration_needed_none_need_migration(
        self, mocker: MockerFixture
    ) -> None:
        """Test check_migration_needed when no databases need migration."""
        mock_alembic_helper = mocker.patch(
            "chartreuse.chartreuse.AlembicMigrationHelper"
        )

        mock_instance = MagicMock()
        mock_instance.is_migration_needed = False
        mock_alembic_helper.return_value = mock_instance

        mocker.patch("chartreuse.chartreuse.configure_logging")
        mock_k8s_helper = MagicMock()

        databases_config: list[dict[str, any]] = [
            {
                "name": "test",
                "alembic_directory_path": "/app/alembic",
                "alembic_config_file_path": "alembic.ini",
                "url": "postgresql://user:pass@localhost:5432/db",
            }
        ]

        multi_chartreuse = MultiChartreuse(
            databases_config=databases_config,
            release_name="test-release",
            kubernetes_helper=mock_k8s_helper,
        )

        result = multi_chartreuse.check_migration_needed()
        assert result is False

    def test_upgrade_only_needed_databases(self, mocker: MockerFixture) -> None:
        """Test upgrade method only upgrades databases that need migration."""
        mock_alembic_helper = mocker.patch(
            "chartreuse.chartreuse.AlembicMigrationHelper"
        )

        # Create mock instances
        mock_main_instance = MagicMock()
        mock_main_instance.is_migration_needed = True

        mock_sec_instance = MagicMock()
        mock_sec_instance.is_migration_needed = False

        mock_alembic_helper.side_effect = [mock_main_instance, mock_sec_instance]

        mocker.patch("chartreuse.chartreuse.configure_logging")
        mock_k8s_helper = MagicMock()

        databases_config: list[dict[str, any]] = [
            {
                "name": "main",
                "alembic_directory_path": "/app/alembic/main",
                "alembic_config_file_path": "alembic.ini",
                "url": "postgresql://user:pass@localhost:5432/maindb",
            },
            {
                "name": "secondary",
                "alembic_directory_path": "/app/alembic/secondary",
                "alembic_config_file_path": "alembic.ini",
                "url": "postgresql://user:pass@localhost:5433/secdb",
            },
        ]

        multi_chartreuse = MultiChartreuse(
            databases_config=databases_config,
            release_name="test-release",
            kubernetes_helper=mock_k8s_helper,
        )

        multi_chartreuse.upgrade()

        # Verify only main database was upgraded
        mock_main_instance.upgrade_db.assert_called_once()
        mock_sec_instance.upgrade_db.assert_not_called()

    def test_multi_chartreuse_default_values(self, mocker: MockerFixture) -> None:
        """Test that default values are handled correctly for optional parameters."""
        mock_alembic_helper = mocker.patch(
            "chartreuse.chartreuse.AlembicMigrationHelper"
        )
        mock_alembic_instance = MagicMock()
        mock_alembic_instance.is_migration_needed = False
        mock_alembic_helper.return_value = mock_alembic_instance

        mocker.patch("chartreuse.chartreuse.configure_logging")
        mock_k8s_helper = MagicMock()

        databases_config = [
            {
                "name": "test",
                "alembic_directory_path": "/app/alembic",
                "alembic_config_file_path": "alembic.ini",
                "url": "postgresql://user:pass@localhost:5432/db",
                # No allow_migration_for_empty_database or additional_parameters
            }
        ]

        MultiChartreuse(
            databases_config=databases_config,
            release_name="test-release",
            kubernetes_helper=mock_k8s_helper,
        )

        # Verify AlembicMigrationHelper was called with defaults
        mock_alembic_helper.assert_called_once_with(
            alembic_directory_path="/app/alembic",
            alembic_config_file_path="alembic.ini",
            database_url="postgresql://user:pass@localhost:5432/db",
            allow_migration_for_empty_database=False,  # Default value
            additional_parameters="",  # Default value
        )
