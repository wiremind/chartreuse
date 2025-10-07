"""Extended unit tests for chartreuse_upgrade module."""

import os

import pytest
from pytest_mock.plugin import MockerFixture

from chartreuse.chartreuse_upgrade import ensure_safe_run, main


class TestEnsureSafeRun:
    """Test cases for ensure_safe_run function."""

    def test_ensure_safe_run_matching_versions(self, mocker: MockerFixture) -> None:
        """Test ensure_safe_run with matching major.minor versions."""
        mocker.patch("chartreuse.chartreuse_upgrade.get_version", return_value="5.2.1")
        mocker.patch.dict(os.environ, {"HELM_CHART_VERSION": "5.2.0"})

        # Should not raise any exception
        ensure_safe_run()

    def test_ensure_safe_run_mismatched_versions(self, mocker: MockerFixture) -> None:
        """Test ensure_safe_run with mismatched major.minor versions."""
        mocker.patch("chartreuse.chartreuse_upgrade.get_version", return_value="5.1.3")
        mocker.patch.dict(os.environ, {"HELM_CHART_VERSION": "5.2.0"})

        with pytest.raises(ValueError) as exc_info:
            ensure_safe_run()

        assert "don't have the same 'major.minor'" in str(exc_info.value)
        assert "5.1.3" in str(exc_info.value)
        assert "5.2.0" in str(exc_info.value)

    def test_ensure_safe_run_missing_helm_version(self, mocker: MockerFixture) -> None:
        """Test ensure_safe_run with missing HELM_CHART_VERSION environment variable."""
        mocker.patch("chartreuse.chartreuse_upgrade.get_version", return_value="5.1.3")
        mocker.patch.dict(os.environ, {}, clear=True)

        with pytest.raises(ValueError) as exc_info:
            ensure_safe_run()

        assert "Couldn't get the Chartreuse's Helm Chart version" in str(exc_info.value)

    def test_ensure_safe_run_empty_helm_version(self, mocker: MockerFixture) -> None:
        """Test ensure_safe_run with empty HELM_CHART_VERSION environment variable."""
        mocker.patch("chartreuse.chartreuse_upgrade.get_version", return_value="5.1.3")
        mocker.patch.dict(os.environ, {"HELM_CHART_VERSION": ""})

        with pytest.raises(ValueError) as exc_info:
            ensure_safe_run()

        assert "Couldn't get the Chartreuse's Helm Chart version" in str(exc_info.value)

    def test_ensure_safe_run_different_major_versions(
        self, mocker: MockerFixture
    ) -> None:
        """Test ensure_safe_run with different major versions."""
        mocker.patch("chartreuse.chartreuse_upgrade.get_version", return_value="4.2.1")
        mocker.patch.dict(os.environ, {"HELM_CHART_VERSION": "5.2.0"})

        with pytest.raises(ValueError) as exc_info:
            ensure_safe_run()

        assert "(['5', '2'] != ['4', '2'])" in str(exc_info.value)

    def test_ensure_safe_run_complex_version_formats(
        self, mocker: MockerFixture
    ) -> None:
        """Test ensure_safe_run with complex version formats."""
        mocker.patch(
            "chartreuse.chartreuse_upgrade.get_version", return_value="5.2.1-alpha.1"
        )
        mocker.patch.dict(os.environ, {"HELM_CHART_VERSION": "5.2.0-beta.2"})

        # Should not raise any exception as major.minor match
        ensure_safe_run()


class TestMainMultiDatabase:
    """Test cases for main function with multi-database configuration."""

    def test_main_multi_database_success(self, mocker: MockerFixture) -> None:
        """Test main function with successful multi-database configuration."""
        # Mock ensure_safe_run
        mocker.patch("chartreuse.chartreuse_upgrade.ensure_safe_run")

        # Mock config loading
        mock_config = [
            {
                "name": "main",
                "url": "postgresql://user:pass@localhost:5432/maindb",
                "alembic_directory_path": "/app/alembic/main",
                "alembic_config_file_path": "alembic.ini",
            }
        ]
        mock_load_config = mocker.patch(
            "chartreuse.chartreuse_upgrade.load_multi_database_config",
            return_value=mock_config,
        )

        # Mock MultiChartreuse
        mock_multi_chartreuse = mocker.patch(
            "chartreuse.chartreuse_upgrade.MultiChartreuse"
        )
        mock_chartreuse_instance = mocker.MagicMock()
        mock_chartreuse_instance.is_migration_needed = True
        mock_multi_chartreuse.return_value = mock_chartreuse_instance

        # Mock KubernetesDeploymentManager
        mock_k8s_manager = mocker.patch(
            "chartreuse.chartreuse_upgrade.KubernetesDeploymentManager"
        )
        mock_k8s_instance = mocker.MagicMock()
        mock_k8s_manager.return_value = mock_k8s_instance

        # Set up environment
        mocker.patch.dict(
            os.environ,
            {
                "CHARTREUSE_MULTI_CONFIG_PATH": "/app/config.yaml",
                "CHARTREUSE_ENABLE_STOP_PODS": "true",
                "CHARTREUSE_RELEASE_NAME": "test-release",
                "CHARTREUSE_UPGRADE_BEFORE_DEPLOYMENT": "false",
                "HELM_IS_INSTALL": "false",
            },
        )

        main()

        # Verify mocks were called correctly
        mock_load_config.assert_called_once_with("/app/config.yaml")
        mock_multi_chartreuse.assert_called_once()
        mock_chartreuse_instance.upgrade.assert_called_once()
        mock_k8s_instance.stop_pods.assert_called_once()
        mock_k8s_instance.start_pods.assert_called_once()

    def test_main_multi_database_no_migration_needed(
        self, mocker: MockerFixture
    ) -> None:
        """Test main function when no migration is needed."""
        mocker.patch("chartreuse.chartreuse_upgrade.ensure_safe_run")

        mock_config = [
            {
                "name": "main",
                "url": "postgresql://user:pass@localhost:5432/maindb",
                "alembic_directory_path": "/app/alembic/main",
                "alembic_config_file_path": "alembic.ini",
            }
        ]
        mocker.patch(
            "chartreuse.chartreuse_upgrade.load_multi_database_config",
            return_value=mock_config,
        )

        mock_multi_chartreuse = mocker.patch(
            "chartreuse.chartreuse_upgrade.MultiChartreuse"
        )
        mock_chartreuse_instance = mocker.MagicMock()
        mock_chartreuse_instance.is_migration_needed = False
        mock_multi_chartreuse.return_value = mock_chartreuse_instance

        mock_k8s_manager = mocker.patch(
            "chartreuse.chartreuse_upgrade.KubernetesDeploymentManager"
        )
        mock_k8s_instance = mocker.MagicMock()
        mock_k8s_manager.return_value = mock_k8s_instance

        mocker.patch.dict(
            os.environ,
            {
                "CHARTREUSE_MULTI_CONFIG_PATH": "/app/config.yaml",
                "CHARTREUSE_ENABLE_STOP_PODS": "true",
                "CHARTREUSE_RELEASE_NAME": "test-release",
                "CHARTREUSE_UPGRADE_BEFORE_DEPLOYMENT": "false",
                "HELM_IS_INSTALL": "false",
            },
        )

        main()

        # Verify no pods were stopped/started and no upgrade occurred
        mock_chartreuse_instance.upgrade.assert_not_called()
        mock_k8s_instance.stop_pods.assert_not_called()
        mock_k8s_instance.start_pods.assert_not_called()

    def test_main_multi_database_config_load_failure(
        self, mocker: MockerFixture
    ) -> None:
        """Test main function with config loading failure."""
        mocker.patch("chartreuse.chartreuse_upgrade.ensure_safe_run")

        mocker.patch(
            "chartreuse.chartreuse_upgrade.load_multi_database_config",
            side_effect=FileNotFoundError("Config file not found"),
        )

        mocker.patch.dict(
            os.environ,
            {
                "CHARTREUSE_MULTI_CONFIG_PATH": "/app/missing_config.yaml",
                "CHARTREUSE_RELEASE_NAME": "test-release",
            },
        )

        with pytest.raises(FileNotFoundError):
            main()

    def test_main_multi_database_stop_pods_disabled(
        self, mocker: MockerFixture
    ) -> None:
        """Test main function with ENABLE_STOP_PODS disabled."""
        mocker.patch("chartreuse.chartreuse_upgrade.ensure_safe_run")

        mock_config = [
            {
                "name": "main",
                "url": "postgresql://user:pass@localhost:5432/maindb",
                "alembic_directory_path": "/app/alembic/main",
                "alembic_config_file_path": "alembic.ini",
            }
        ]
        mocker.patch(
            "chartreuse.chartreuse_upgrade.load_multi_database_config",
            return_value=mock_config,
        )

        mock_multi_chartreuse = mocker.patch(
            "chartreuse.chartreuse_upgrade.MultiChartreuse"
        )
        mock_chartreuse_instance = mocker.MagicMock()
        mock_chartreuse_instance.is_migration_needed = True
        mock_multi_chartreuse.return_value = mock_chartreuse_instance

        mock_k8s_manager = mocker.patch(
            "chartreuse.chartreuse_upgrade.KubernetesDeploymentManager"
        )
        mock_k8s_instance = mocker.MagicMock()
        mock_k8s_manager.return_value = mock_k8s_instance

        mocker.patch.dict(
            os.environ,
            {
                "CHARTREUSE_MULTI_CONFIG_PATH": "/app/config.yaml",
                "CHARTREUSE_ENABLE_STOP_PODS": "false",
                "CHARTREUSE_RELEASE_NAME": "test-release",
                "CHARTREUSE_UPGRADE_BEFORE_DEPLOYMENT": "false",
                "HELM_IS_INSTALL": "false",
            },
        )

        main()

        # Verify upgrade was called but pods were not stopped/started
        mock_chartreuse_instance.upgrade.assert_called_once()
        mock_k8s_instance.stop_pods.assert_not_called()
        mock_k8s_instance.start_pods.assert_not_called()

    def test_main_multi_database_upgrade_before_deployment(
        self, mocker: MockerFixture
    ) -> None:
        """Test main function with UPGRADE_BEFORE_DEPLOYMENT and not HELM_IS_INSTALL."""
        mocker.patch("chartreuse.chartreuse_upgrade.ensure_safe_run")

        mock_config = [
            {
                "name": "main",
                "url": "postgresql://user:pass@localhost:5432/maindb",
                "alembic_directory_path": "/app/alembic/main",
                "alembic_config_file_path": "alembic.ini",
            }
        ]
        mocker.patch(
            "chartreuse.chartreuse_upgrade.load_multi_database_config",
            return_value=mock_config,
        )

        mock_multi_chartreuse = mocker.patch(
            "chartreuse.chartreuse_upgrade.MultiChartreuse"
        )
        mock_chartreuse_instance = mocker.MagicMock()
        mock_chartreuse_instance.is_migration_needed = True
        mock_multi_chartreuse.return_value = mock_chartreuse_instance

        mock_k8s_manager = mocker.patch(
            "chartreuse.chartreuse_upgrade.KubernetesDeploymentManager"
        )
        mock_k8s_instance = mocker.MagicMock()
        mock_k8s_manager.return_value = mock_k8s_instance

        mocker.patch.dict(
            os.environ,
            {
                "CHARTREUSE_MULTI_CONFIG_PATH": "/app/config.yaml",
                "CHARTREUSE_ENABLE_STOP_PODS": "true",
                "CHARTREUSE_RELEASE_NAME": "test-release",
                "CHARTREUSE_UPGRADE_BEFORE_DEPLOYMENT": "true",
                "HELM_IS_INSTALL": "false",
            },
        )

        main()

        # Verify pods were stopped and upgrade was called, but start_pods was not called
        mock_chartreuse_instance.upgrade.assert_called_once()
        mock_k8s_instance.stop_pods.assert_called_once()
        mock_k8s_instance.start_pods.assert_not_called()

    def test_main_multi_database_start_pods_failure(
        self, mocker: MockerFixture
    ) -> None:
        """Test main function when start_pods fails."""
        mocker.patch("chartreuse.chartreuse_upgrade.ensure_safe_run")

        mock_config = [
            {
                "name": "main",
                "url": "postgresql://user:pass@localhost:5432/maindb",
                "alembic_directory_path": "/app/alembic/main",
                "alembic_config_file_path": "alembic.ini",
            }
        ]
        mocker.patch(
            "chartreuse.chartreuse_upgrade.load_multi_database_config",
            return_value=mock_config,
        )

        mock_multi_chartreuse = mocker.patch(
            "chartreuse.chartreuse_upgrade.MultiChartreuse"
        )
        mock_chartreuse_instance = mocker.MagicMock()
        mock_chartreuse_instance.is_migration_needed = True
        mock_multi_chartreuse.return_value = mock_chartreuse_instance

        mock_k8s_manager = mocker.patch(
            "chartreuse.chartreuse_upgrade.KubernetesDeploymentManager"
        )
        mock_k8s_instance = mocker.MagicMock()
        mock_k8s_instance.start_pods.side_effect = Exception("Failed to start pods")
        mock_k8s_manager.return_value = mock_k8s_instance

        # Mock logger to verify error was logged
        mock_logger = mocker.patch("chartreuse.chartreuse_upgrade.logger")

        mocker.patch.dict(
            os.environ,
            {
                "CHARTREUSE_MULTI_CONFIG_PATH": "/app/config.yaml",
                "CHARTREUSE_ENABLE_STOP_PODS": "true",
                "CHARTREUSE_RELEASE_NAME": "test-release",
                "CHARTREUSE_UPGRADE_BEFORE_DEPLOYMENT": "false",
                "HELM_IS_INSTALL": "false",
            },
        )

        # Should not raise exception, just log error
        main()

        # Verify error was logged
        mock_logger.error.assert_called_once()
        assert "Couldn't scale up new pods" in str(mock_logger.error.call_args)


class TestMainSingleDatabase:
    """Test cases for main function with single-database configuration."""

    def test_main_single_database_success(self, mocker: MockerFixture) -> None:
        """Test main function with successful single-database configuration."""
        mocker.patch("chartreuse.chartreuse_upgrade.ensure_safe_run")

        mock_chartreuse = mocker.patch("chartreuse.chartreuse_upgrade.Chartreuse")
        mock_chartreuse_instance = mocker.MagicMock()
        mock_chartreuse_instance.is_migration_needed = True
        mock_chartreuse.return_value = mock_chartreuse_instance

        mock_k8s_manager = mocker.patch(
            "chartreuse.chartreuse_upgrade.KubernetesDeploymentManager"
        )
        mock_k8s_instance = mocker.MagicMock()
        mock_k8s_manager.return_value = mock_k8s_instance

        # Set up environment for single-database mode (no CHARTREUSE_MULTI_CONFIG_PATH)
        mocker.patch.dict(
            os.environ,
            {
                "CHARTREUSE_ALEMBIC_DIRECTORY_PATH": "/app/alembic",
                "CHARTREUSE_ALEMBIC_CONFIG_FILE_PATH": "alembic.ini",
                "CHARTREUSE_ALEMBIC_URL": "postgresql://user:pass@localhost:5432/db",
                "CHARTREUSE_ALEMBIC_ALLOW_MIGRATION_FOR_EMPTY_DATABASE": "true",
                "CHARTREUSE_ALEMBIC_ADDITIONAL_PARAMETERS": "--verbose",
                "CHARTREUSE_ENABLE_STOP_PODS": "true",
                "CHARTREUSE_RELEASE_NAME": "test-release",
                "CHARTREUSE_UPGRADE_BEFORE_DEPLOYMENT": "false",
                "HELM_IS_INSTALL": "false",
            },
            clear=True,
        )

        main()

        # Verify Chartreuse was initialized correctly
        mock_chartreuse.assert_called_once_with(
            alembic_directory_path="/app/alembic",
            alembic_config_file_path="alembic.ini",
            postgresql_url="postgresql://user:pass@localhost:5432/db",
            alembic_allow_migration_for_empty_database=True,
            alembic_additional_parameters="--verbose",
            release_name="test-release",
            kubernetes_helper=mock_k8s_instance,
        )

        # Verify upgrade flow
        mock_chartreuse_instance.upgrade.assert_called_once()
        mock_k8s_instance.stop_pods.assert_called_once()
        mock_k8s_instance.start_pods.assert_called_once()

    def test_main_single_database_default_values(self, mocker: MockerFixture) -> None:
        """Test main function with default values for optional environment variables."""
        mocker.patch("chartreuse.chartreuse_upgrade.ensure_safe_run")

        mock_chartreuse = mocker.patch("chartreuse.chartreuse_upgrade.Chartreuse")
        mock_chartreuse_instance = mocker.MagicMock()
        mock_chartreuse_instance.is_migration_needed = False
        mock_chartreuse.return_value = mock_chartreuse_instance

        mock_k8s_manager = mocker.patch(
            "chartreuse.chartreuse_upgrade.KubernetesDeploymentManager"
        )
        mock_k8s_instance = mocker.MagicMock()
        mock_k8s_manager.return_value = mock_k8s_instance

        # Set minimal required environment variables
        mocker.patch.dict(
            os.environ,
            {
                "CHARTREUSE_ALEMBIC_URL": "postgresql://user:pass@localhost:5432/db",
                "CHARTREUSE_ALEMBIC_ALLOW_MIGRATION_FOR_EMPTY_DATABASE": "false",
                "CHARTREUSE_ALEMBIC_ADDITIONAL_PARAMETERS": "",
                "CHARTREUSE_ENABLE_STOP_PODS": "false",
                "CHARTREUSE_RELEASE_NAME": "test-release",
                "CHARTREUSE_UPGRADE_BEFORE_DEPLOYMENT": "false",
                "HELM_IS_INSTALL": "false",
            },
            clear=True,
        )

        main()

        # Verify Chartreuse was initialized with default values
        # Note: The boolean parsing in single-database mode uses bool(env_var)
        # which means any non-empty string is True
        mock_chartreuse.assert_called_once_with(
            alembic_directory_path="/app/alembic",  # Default value
            alembic_config_file_path="alembic.ini",  # Default value
            postgresql_url="postgresql://user:pass@localhost:5432/db",
            alembic_allow_migration_for_empty_database=True,  # "false" -> bool("false") -> True
            alembic_additional_parameters="",
            release_name="test-release",
            kubernetes_helper=mock_k8s_instance,
        )

        # No migration needed, so no pods operations
        mock_chartreuse_instance.upgrade.assert_not_called()
        mock_k8s_instance.stop_pods.assert_not_called()
        mock_k8s_instance.start_pods.assert_not_called()


class TestMainBooleanParsing:
    """Test cases for boolean environment variable parsing."""

    @pytest.mark.parametrize(
        "bool_str,expected",
        [
            ("true", True),
            ("TRUE", True),
            ("True", True),
            ("false", True),  # bool("false") -> True (non-empty string)
            ("FALSE", True),  # bool("FALSE") -> True (non-empty string)
            ("False", True),  # bool("False") -> True (non-empty string)
            ("", False),  # bool("") -> False (empty string)
            ("0", True),  # bool("0") -> True (non-empty string)
            ("1", True),  # bool("1") -> True (non-empty string)
        ],
    )
    def test_boolean_parsing_variations(
        self, mocker: MockerFixture, bool_str: str, expected: bool
    ) -> None:
        """Test various boolean string parsing in environment variables."""
        mocker.patch("chartreuse.chartreuse_upgrade.ensure_safe_run")

        mock_chartreuse = mocker.patch("chartreuse.chartreuse_upgrade.Chartreuse")
        mock_chartreuse_instance = mocker.MagicMock()
        mock_chartreuse_instance.is_migration_needed = False
        mock_chartreuse.return_value = mock_chartreuse_instance

        mocker.patch("chartreuse.chartreuse_upgrade.KubernetesDeploymentManager")

        # Set up environment for single-database mode (no CHARTREUSE_MULTI_CONFIG_PATH)
        # Note: In single-database mode, boolean parsing uses bool(env_var)
        # which means any non-empty string is True, empty string is False
        mocker.patch.dict(
            os.environ,
            {
                "CHARTREUSE_ALEMBIC_URL": "postgresql://user:pass@localhost:5432/db",
                "CHARTREUSE_ALEMBIC_ALLOW_MIGRATION_FOR_EMPTY_DATABASE": bool_str,
                "CHARTREUSE_ALEMBIC_ADDITIONAL_PARAMETERS": "",
                "CHARTREUSE_ENABLE_STOP_PODS": "false",
                "CHARTREUSE_RELEASE_NAME": "test-release",
                "CHARTREUSE_UPGRADE_BEFORE_DEPLOYMENT": "false",
                "HELM_IS_INSTALL": "false",
            },
            clear=True,
        )

        main()

        # Check that the boolean was parsed correctly
        call_args = mock_chartreuse.call_args[1]
        assert call_args["alembic_allow_migration_for_empty_database"] == expected
