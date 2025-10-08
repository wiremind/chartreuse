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

    def test_ensure_safe_run_different_major_versions(self, mocker: MockerFixture) -> None:
        """Test ensure_safe_run with different major versions."""
        mocker.patch("chartreuse.chartreuse_upgrade.get_version", return_value="4.2.1")
        mocker.patch.dict(os.environ, {"HELM_CHART_VERSION": "5.2.0"})

        with pytest.raises(ValueError) as exc_info:
            ensure_safe_run()

        assert "(['5', '2'] != ['4', '2'])" in str(exc_info.value)

    def test_ensure_safe_run_complex_version_formats(self, mocker: MockerFixture) -> None:
        """Test ensure_safe_run with complex version formats."""
        mocker.patch("chartreuse.chartreuse_upgrade.get_version", return_value="5.2.1-alpha.1")
        mocker.patch.dict(os.environ, {"HELM_CHART_VERSION": "5.2.0-beta.2"})

        # Should not raise any exception as major.minor match
        ensure_safe_run()


class TestMainMultiDatabase:
    """Test cases for main function with multi-database configuration."""

    def test_main_multi_database_success(self, mocker: MockerFixture) -> None:
        """Test main function with successful multi-database configuration."""
        # Mock ensure_safe_run
        mocker.patch("chartreuse.chartreuse_upgrade.ensure_safe_run")

        # Mock file existence for config validation
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("os.path.isfile", return_value=True)
        mocker.patch("os.path.isfile", return_value=True)

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

        # Mock Chartreuse
        mock_multi_chartreuse = mocker.patch("chartreuse.chartreuse_upgrade.Chartreuse")
        mock_chartreuse_instance = mocker.MagicMock()
        mock_chartreuse_instance.is_migration_needed = True
        mock_multi_chartreuse.return_value = mock_chartreuse_instance

        # Mock KubernetesDeploymentManager
        mock_k8s_manager = mocker.patch("chartreuse.chartreuse_upgrade.KubernetesDeploymentManager")
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

    def test_main_multi_database_no_migration_needed(self, mocker: MockerFixture) -> None:
        """Test main function when no migration is needed."""
        mocker.patch("chartreuse.chartreuse_upgrade.ensure_safe_run")

        # Mock file existence for config validation
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("os.path.isfile", return_value=True)

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

        mock_multi_chartreuse = mocker.patch("chartreuse.chartreuse_upgrade.Chartreuse")
        mock_chartreuse_instance = mocker.MagicMock()
        mock_chartreuse_instance.is_migration_needed = False
        mock_multi_chartreuse.return_value = mock_chartreuse_instance

        mock_k8s_manager = mocker.patch("chartreuse.chartreuse_upgrade.KubernetesDeploymentManager")
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

    def test_main_multi_database_config_load_failure(self, mocker: MockerFixture) -> None:
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

    def test_main_multi_database_stop_pods_disabled(self, mocker: MockerFixture) -> None:
        """Test main function with ENABLE_STOP_PODS disabled."""
        mocker.patch("chartreuse.chartreuse_upgrade.ensure_safe_run")

        # Mock file existence for config validation
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("os.path.isfile", return_value=True)

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

        mock_multi_chartreuse = mocker.patch("chartreuse.chartreuse_upgrade.Chartreuse")
        mock_chartreuse_instance = mocker.MagicMock()
        mock_chartreuse_instance.is_migration_needed = True
        mock_multi_chartreuse.return_value = mock_chartreuse_instance

        mock_k8s_manager = mocker.patch("chartreuse.chartreuse_upgrade.KubernetesDeploymentManager")
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

    def test_main_multi_database_upgrade_before_deployment(self, mocker: MockerFixture) -> None:
        """Test main function with UPGRADE_BEFORE_DEPLOYMENT and not HELM_IS_INSTALL."""
        mocker.patch("chartreuse.chartreuse_upgrade.ensure_safe_run")

        # Mock file existence for config validation
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("os.path.isfile", return_value=True)

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

        mock_multi_chartreuse = mocker.patch("chartreuse.chartreuse_upgrade.Chartreuse")
        mock_chartreuse_instance = mocker.MagicMock()
        mock_chartreuse_instance.is_migration_needed = True
        mock_multi_chartreuse.return_value = mock_chartreuse_instance

        mock_k8s_manager = mocker.patch("chartreuse.chartreuse_upgrade.KubernetesDeploymentManager")
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

    def test_main_multi_database_start_pods_failure(self, mocker: MockerFixture) -> None:
        """Test main function when start_pods fails."""
        mocker.patch("chartreuse.chartreuse_upgrade.ensure_safe_run")

        # Mock file existence for config validation
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("os.path.isfile", return_value=True)

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

        mock_multi_chartreuse = mocker.patch("chartreuse.chartreuse_upgrade.Chartreuse")
        mock_chartreuse_instance = mocker.MagicMock()
        mock_chartreuse_instance.is_migration_needed = True
        mock_multi_chartreuse.return_value = mock_chartreuse_instance

        mock_k8s_manager = mocker.patch("chartreuse.chartreuse_upgrade.KubernetesDeploymentManager")
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

        # Mock file existence for config validation
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("os.path.isfile", return_value=True)

        # Mock config loading for single database
        mock_config = [
            {
                "name": "main",
                "url": "postgresql://user:pass@localhost:5432/db",
                "alembic_directory_path": "/app/alembic",
                "alembic_config_file_path": "alembic.ini",
                "alembic_allow_migration_for_empty_database": True,
                "alembic_additional_parameters": "--verbose",
            }
        ]
        mocker.patch(
            "chartreuse.chartreuse_upgrade.load_multi_database_config",
            return_value=mock_config,
        )

        mock_chartreuse = mocker.patch("chartreuse.chartreuse_upgrade.Chartreuse")
        mock_chartreuse_instance = mocker.MagicMock()
        mock_chartreuse_instance.is_migration_needed = True
        mock_chartreuse.return_value = mock_chartreuse_instance

        mock_k8s_manager = mocker.patch("chartreuse.chartreuse_upgrade.KubernetesDeploymentManager")
        mock_k8s_instance = mocker.MagicMock()
        mock_k8s_manager.return_value = mock_k8s_instance

        # Set up environment for unified mode (always requires CHARTREUSE_MULTI_CONFIG_PATH)
        mocker.patch.dict(
            os.environ,
            {
                "CHARTREUSE_MULTI_CONFIG_PATH": "/app/config.yaml",
                "CHARTREUSE_ENABLE_STOP_PODS": "true",
                "CHARTREUSE_RELEASE_NAME": "test-release",
                "CHARTREUSE_UPGRADE_BEFORE_DEPLOYMENT": "false",
                "HELM_IS_INSTALL": "false",
            },
            clear=True,
        )

        main()

        # Verify Chartreuse was initialized correctly with unified architecture
        mock_chartreuse.assert_called_once_with(
            databases_config=mock_config,
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

        # Mock file existence for config validation
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("os.path.isfile", return_value=True)

        # Mock config loading for single database with default values
        mock_config = [
            {
                "name": "main",
                "url": "postgresql://user:pass@localhost:5432/db",
                "alembic_directory_path": "/app/alembic",
                "alembic_config_file_path": "alembic.ini",
                "alembic_allow_migration_for_empty_database": False,
                "alembic_additional_parameters": "",
            }
        ]
        mocker.patch(
            "chartreuse.chartreuse_upgrade.load_multi_database_config",
            return_value=mock_config,
        )

        mock_chartreuse = mocker.patch("chartreuse.chartreuse_upgrade.Chartreuse")
        mock_chartreuse_instance = mocker.MagicMock()
        mock_chartreuse_instance.is_migration_needed = False
        mock_chartreuse.return_value = mock_chartreuse_instance

        mock_k8s_manager = mocker.patch("chartreuse.chartreuse_upgrade.KubernetesDeploymentManager")
        mock_k8s_instance = mocker.MagicMock()
        mock_k8s_manager.return_value = mock_k8s_instance

        # Set minimal required environment variables for unified mode
        mocker.patch.dict(
            os.environ,
            {
                "CHARTREUSE_MULTI_CONFIG_PATH": "/app/config.yaml",
                "CHARTREUSE_ENABLE_STOP_PODS": "false",
                "CHARTREUSE_RELEASE_NAME": "test-release",
                "CHARTREUSE_UPGRADE_BEFORE_DEPLOYMENT": "false",
                "HELM_IS_INSTALL": "false",
            },
            clear=True,
        )

        main()

        # Verify Chartreuse was initialized correctly with unified architecture
        mock_chartreuse.assert_called_once_with(
            databases_config=mock_config,
            release_name="test-release",
            kubernetes_helper=mock_k8s_instance,
        )


class TestMainBooleanParsing:
    """Test cases for boolean environment variable parsing."""

    @pytest.mark.parametrize(
        "bool_str,expected",
        [
            ("true", True),  # .lower() not in ("", "false", "0") -> "true" not in -> True
            ("TRUE", True),  # .lower() not in ("", "false", "0") -> "true" not in -> True
            ("True", True),  # .lower() not in ("", "false", "0") -> "true" not in -> True
            ("false", False),  # .lower() not in ("", "false", "0") -> "false" in -> False
            ("FALSE", False),  # .lower() not in ("", "false", "0") -> "false" in -> False
            ("False", False),  # .lower() not in ("", "false", "0") -> "false" in -> False
            ("", False),  # .lower() not in ("", "false", "0") -> "" in -> False
            ("0", False),  # .lower() not in ("", "false", "0") -> "0" in -> False
            ("1", True),  # .lower() not in ("", "false", "0") -> "1" not in -> True
        ],
    )
    def test_boolean_parsing_variations(self, mocker: MockerFixture, bool_str: str, expected: bool) -> None:
        """Test various boolean string parsing in environment variables."""
        mocker.patch("chartreuse.chartreuse_upgrade.ensure_safe_run")

        # Mock file existence for config validation
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("os.path.isfile", return_value=True)

        # Mock config loading
        mock_config = [
            {
                "name": "main",
                "url": "postgresql://user:pass@localhost:5432/db",
                "alembic_directory_path": "/app/alembic",
                "alembic_config_file_path": "alembic.ini",
            }
        ]
        mocker.patch(
            "chartreuse.chartreuse_upgrade.load_multi_database_config",
            return_value=mock_config,
        )

        mock_chartreuse = mocker.patch("chartreuse.chartreuse_upgrade.Chartreuse")
        mock_chartreuse_instance = mocker.MagicMock()
        mock_chartreuse_instance.is_migration_needed = True  # Set to True to test stop_pods behavior
        mock_chartreuse.return_value = mock_chartreuse_instance

        mock_k8s_manager = mocker.patch("chartreuse.chartreuse_upgrade.KubernetesDeploymentManager")
        mock_k8s_instance = mocker.MagicMock()
        mock_k8s_manager.return_value = mock_k8s_instance

        # Test boolean parsing for environment variables that are still parsed in main()
        # The boolean parsing logic: .lower() not in ("", "false", "0")
        # which means: empty string, "false", or "0" are False, everything else is True
        mocker.patch.dict(
            os.environ,
            {
                "CHARTREUSE_MULTI_CONFIG_PATH": "/app/config.yaml",
                "CHARTREUSE_ENABLE_STOP_PODS": bool_str,  # Test this boolean parsing
                "CHARTREUSE_RELEASE_NAME": "test-release",
                "CHARTREUSE_UPGRADE_BEFORE_DEPLOYMENT": "false",
                "HELM_IS_INSTALL": "false",
            },
            clear=True,
        )

        main()

        # Verify that stop_pods was called based on the boolean parsing result
        if expected:
            mock_k8s_instance.stop_pods.assert_called_once()
        else:
            mock_k8s_instance.stop_pods.assert_not_called()
