from pytest_mock import MockerFixture

from chartreuse.utils.alembic_migration_helper import AlembicMigrationHelper


class TestPatroniPostgreSQLFeature:
    """Test cases for the is_patroni_postgresql feature."""

    def test_patroni_postgresql_flag_false_by_default(self, mocker: MockerFixture) -> None:
        """Test that is_patroni_postgresql defaults to False."""
        mocker.patch("chartreuse.utils.AlembicMigrationHelper._configure")
        mocker.patch("chartreuse.utils.AlembicMigrationHelper._check_migration_needed", return_value=False)

        helper = AlembicMigrationHelper(
            database_url="postgresql://user:pass@localhost:5432/db",
            alembic_section_name="test",
            skip_db_checks=True,  # Skip database checks for testing
        )

        assert helper.is_patroni_postgresql is False

    def test_patroni_postgresql_flag_set_to_true(self, mocker: MockerFixture) -> None:
        """Test that is_patroni_postgresql can be set to True."""
        mocker.patch("chartreuse.utils.AlembicMigrationHelper._configure")
        mocker.patch("chartreuse.utils.AlembicMigrationHelper._check_migration_needed", return_value=False)

        helper = AlembicMigrationHelper(
            database_url="postgresql://user:pass@localhost:5432/db",
            alembic_section_name="test",
            is_patroni_postgresql=True,
            skip_db_checks=True,  # Skip database checks for testing
        )

        assert helper.is_patroni_postgresql is True

    def test_patroni_postgresql_adds_parameter(self, mocker: MockerFixture) -> None:
        """Test that when is_patroni_postgresql=True, it adds the correct parameter."""
        mocker.patch("chartreuse.utils.AlembicMigrationHelper._configure")
        mocker.patch("chartreuse.utils.AlembicMigrationHelper._wait_postgres_is_configured")
        mocker.patch("chartreuse.utils.AlembicMigrationHelper._check_migration_needed", return_value=False)

        helper = AlembicMigrationHelper(
            database_url="postgresql://user:pass@localhost:5432/db",
            alembic_section_name="test",
            is_patroni_postgresql=True,
            additional_parameters="--verbose",
        )

        # Should have added the patroni_postgresql parameter
        assert " -x patroni_postgresql=yes" in helper.additional_parameters
        assert "--verbose" in helper.additional_parameters

    def test_patroni_postgresql_does_not_add_parameter_when_false(self, mocker: MockerFixture) -> None:
        """Test that when is_patroni_postgresql=False, it doesn't add the parameter."""
        mocker.patch("chartreuse.utils.AlembicMigrationHelper._configure")
        mocker.patch("chartreuse.utils.AlembicMigrationHelper._check_migration_needed", return_value=False)

        helper = AlembicMigrationHelper(
            database_url="postgresql://user:pass@localhost:5432/db",
            alembic_section_name="test",
            is_patroni_postgresql=False,
            additional_parameters="--verbose",
        )

        # Should not have added the patroni_postgresql parameter
        assert "patroni_postgresql=yes" not in helper.additional_parameters
        assert "--verbose" in helper.additional_parameters

    def test_patroni_postgresql_calls_wait_postgres_configured(self, mocker: MockerFixture) -> None:
        """Test that when is_patroni_postgresql=True, it calls _wait_postgres_is_configured."""
        mocker.patch("chartreuse.utils.AlembicMigrationHelper._configure")
        mock_wait = mocker.patch("chartreuse.utils.AlembicMigrationHelper._wait_postgres_is_configured")
        mocker.patch("chartreuse.utils.AlembicMigrationHelper._check_migration_needed", return_value=False)

        AlembicMigrationHelper(
            database_url="postgresql://user:pass@localhost:5432/db",
            alembic_section_name="test",
            is_patroni_postgresql=True,
        )

        mock_wait.assert_called_once()

    def test_patroni_postgresql_does_not_call_wait_postgres_configured_when_false(self, mocker: MockerFixture) -> None:
        """Test that when is_patroni_postgresql=False, it doesn't call _wait_postgres_is_configured."""
        mocker.patch("chartreuse.utils.AlembicMigrationHelper._configure")
        mock_wait = mocker.patch("chartreuse.utils.AlembicMigrationHelper._wait_postgres_is_configured")
        mocker.patch("chartreuse.utils.AlembicMigrationHelper._check_migration_needed", return_value=False)

        AlembicMigrationHelper(
            database_url="postgresql://user:pass@localhost:5432/db",
            alembic_section_name="test",
            is_patroni_postgresql=False,
        )

        mock_wait.assert_not_called()

    def test_patroni_postgresql_skips_wait_when_skip_db_checks_true(self, mocker: MockerFixture) -> None:
        """Test that when skip_db_checks=True, it doesn't call _wait_postgres_is_configured."""
        mocker.patch("chartreuse.utils.AlembicMigrationHelper._configure")
        mock_wait = mocker.patch("chartreuse.utils.AlembicMigrationHelper._wait_postgres_is_configured")
        mocker.patch("chartreuse.utils.AlembicMigrationHelper._check_migration_needed", return_value=False)

        AlembicMigrationHelper(
            database_url="postgresql://user:pass@localhost:5432/db",
            alembic_section_name="test",
            is_patroni_postgresql=True,
            skip_db_checks=True,
        )

        mock_wait.assert_not_called()

    def test_wait_postgres_is_configured_method_exists(self) -> None:
        """Test that the _wait_postgres_is_configured method exists and is callable."""
        # This is a basic sanity check that the method exists
        assert hasattr(AlembicMigrationHelper, "_wait_postgres_is_configured")
        assert callable(AlembicMigrationHelper._wait_postgres_is_configured)
