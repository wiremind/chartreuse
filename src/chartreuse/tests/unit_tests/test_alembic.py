import os
import tempfile

from pytest_mock.plugin import MockerFixture

import chartreuse.utils


def test_respect_empty_database(mocker: MockerFixture) -> None:
    """
    Test that is_postgres_empty returns empty even if alembic table exists
    """
    table_list = ["alembic_version"]
    mocker.patch(
        "chartreuse.utils.AlembicMigrationHelper._get_table_list",
        return_value=table_list,
    )
    alembic_migration_helper = chartreuse.utils.AlembicMigrationHelper(
        database_url="foo", alembic_section_name="test", configure=False
    )
    assert alembic_migration_helper.is_postgres_empty()


def test_respect_not_empty_database(mocker: MockerFixture) -> None:
    """
    Test that is_postgres_empty return False when tables exist
    """
    table_list = ["alembic_version", "foobar"]
    mocker.patch(
        "chartreuse.utils.AlembicMigrationHelper._get_table_list",
        return_value=table_list,
    )
    mocker.patch(
        "chartreuse.utils.AlembicMigrationHelper._get_alembic_current",
        return_value="123",
    )
    alembic_migration_helper = chartreuse.utils.AlembicMigrationHelper(
        database_url="foo", alembic_section_name="test", configure=False
    )
    assert alembic_migration_helper.is_postgres_empty() is False


def test_detect_needed_migration(mocker: MockerFixture) -> None:
    """
    Test that chartreuse detects that a migration is needed.
    """
    sample_alembic_output = """
2018-11-29 17:58:32 - wiremind_python.settings - DEBUG - Database: postgresql://***/public
2018-11-29 17:58:32 - wiremind_python.settings - DEBUG - redis instance at localhost is  activated
2018-11-29 17:58:32 - alembic.runtime.migration - INFO - Context impl PostgresqlImpl.
2018-11-29 17:58:32 - alembic.runtime.migration - INFO - Will assume transactional DDL.
e1f79bafdfa2
    """
    table_list = ["alembic_version", "foobar"]
    mocker.patch(
        "chartreuse.utils.AlembicMigrationHelper._get_table_list",
        return_value=table_list,
    )
    mocker.patch(
        "chartreuse.utils.AlembicMigrationHelper._get_alembic_current",
        return_value=sample_alembic_output,
    )
    alembic_migration_helper = chartreuse.utils.AlembicMigrationHelper(
        database_url="foo", alembic_section_name="test", configure=False
    )

    assert alembic_migration_helper.is_migration_needed


def test_detect_not_needed_migration(mocker: MockerFixture) -> None:
    """
    Test that chartreuse detects that a migration is not needed.
    """
    sample_alembic_output = """
2018-11-29 17:58:32 - wiremind_python.settings - DEBUG - Database: postgresql://***/public
2018-11-29 17:58:32 - wiremind_python.settings - DEBUG - redis instance at localhost is  activated
2018-11-29 17:58:32 - alembic.runtime.migration - INFO - Context impl PostgresqlImpl.
2018-11-29 17:58:32 - alembic.runtime.migration - INFO - Will assume transactional DDL.
e1f79bafdfa2 (head)
    """
    table_list = ["alembic_version", "foobar"]
    mocker.patch(
        "chartreuse.utils.AlembicMigrationHelper._get_table_list",
        return_value=table_list,
    )
    mocker.patch(
        "chartreuse.utils.AlembicMigrationHelper._get_alembic_current",
        return_value=sample_alembic_output,
    )
    alembic_migration_helper = chartreuse.utils.AlembicMigrationHelper(
        database_url="foo", alembic_section_name="test", configure=False
    )

    assert alembic_migration_helper.is_migration_needed is False


def test_detect_needed_migration_non_existent(mocker: MockerFixture) -> None:
    """
    Test that chartreuse detects that an empty answer means migration is needed
    """
    sample_alembic_output = """
    """
    table_list = ["alembic_version", "foobar"]
    mocker.patch(
        "chartreuse.utils.AlembicMigrationHelper._get_table_list",
        return_value=table_list,
    )
    mocker.patch(
        "chartreuse.utils.AlembicMigrationHelper._get_alembic_current",
        return_value=sample_alembic_output,
    )
    alembic_migration_helper = chartreuse.utils.AlembicMigrationHelper(
        database_url="foo", alembic_section_name="test", configure=False
    )

    assert alembic_migration_helper.is_migration_needed


def test_detect_database_is_empty(mocker: MockerFixture) -> None:
    """
    Test that chartreuse detects that a database is empty
    """
    sample_alembic_output = """
    """
    table_list = ["alembic_version"]
    mocker.patch(
        "chartreuse.utils.AlembicMigrationHelper._get_table_list",
        return_value=table_list,
    )
    mocker.patch(
        "chartreuse.utils.AlembicMigrationHelper._get_alembic_current",
        return_value=sample_alembic_output,
    )

    alembic_migration_helper = chartreuse.utils.AlembicMigrationHelper(
        database_url="foo", alembic_section_name="test", configure=False
    )

    assert alembic_migration_helper.is_postgres_empty()


def test_detect_database_is_not_empty(mocker: MockerFixture) -> None:
    """
    Test that chartreuse detects that a database is not empty and allow migration.
    """
    sample_alembic_output = """
    """
    table_list = ["alembic_version", "foobar"]
    mocker.patch(
        "chartreuse.utils.AlembicMigrationHelper._get_table_list",
        return_value=table_list,
    )
    mocker.patch(
        "chartreuse.utils.AlembicMigrationHelper._get_alembic_current",
        return_value=sample_alembic_output,
    )

    alembic_migration_helper = chartreuse.utils.AlembicMigrationHelper(
        database_url="foo", alembic_section_name="test", configure=False
    )

    assert alembic_migration_helper.is_postgres_empty() is False


def test_additional_parameters(mocker: MockerFixture) -> None:
    """
    Test that alembic additional parameters are respectedf for upgrade_db
    """
    mocker.patch("chartreuse.utils.AlembicMigrationHelper._get_table_list", return_value="foo")
    mocker.patch(
        "chartreuse.utils.AlembicMigrationHelper._get_alembic_current",
        return_value="bar",
    )

    mocked_run_command = mocker.patch("chartreuse.utils.alembic_migration_helper.run_command")

    alembic_migration_helper = chartreuse.utils.AlembicMigrationHelper(
        database_url="foo", alembic_section_name="test", configure=False, additional_parameters="foo bar"
    )
    alembic_migration_helper.upgrade_db()
    mocked_run_command.assert_called_with("alembic -c alembic.ini foo bar upgrade head", cwd="/app/alembic")


def test_additional_parameters_current(mocker: MockerFixture) -> None:
    """
    Test that alembic additional parameters are respected in _get_alembic_current
    """
    mocker.patch("chartreuse.utils.AlembicMigrationHelper._get_table_list", return_value="foo")
    mocked_run_command = mocker.patch("chartreuse.utils.alembic_migration_helper.run_command")
    mocked_run_command.return_value = ("bar", None, 0)

    alembic_migration_helper = chartreuse.utils.AlembicMigrationHelper(
        database_url="foo", alembic_section_name="test", configure=False, additional_parameters="foo bar"
    )
    alembic_migration_helper._get_alembic_current()
    mocked_run_command.assert_called_with(
        "alembic -c alembic.ini foo bar current", cwd="/app/alembic", return_result=True
    )


def test_multi_database_configuration_postgresql_section(mocker: MockerFixture) -> None:
    """
    Test that multi-database configuration correctly updates PostgreSQL section in alembic.ini
    """
    # Sample alembic.ini content with multiple sections
    sample_alembic_ini = """[postgresql]
script_location = postgresl
sqlalchemy.url = postgresql://wiremind_owner@localhost:5432/wiremind
prepend_sys_path = ..
file_template = %%(year)d%%(month).2d%%(day).2d-%%(slug)s

[clickhouse]
script_location = clickhouse
sqlalchemy.url = clickhouse://default@localhost:8123/wiremind
prepend_sys_path = ..
file_template = %%(year)d%%(month).2d%%(day).2d-%%(slug)s

[loggers]
keys = root,sqlalchemy,alembic
"""

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a temporary alembic.ini file
        alembic_ini_path = os.path.join(temp_dir, "alembic.ini")
        with open(alembic_ini_path, "w") as f:
            f.write(sample_alembic_ini)

        # Test configuring PostgreSQL section
        chartreuse.utils.AlembicMigrationHelper(
            alembic_directory_path=temp_dir,
            alembic_config_file_path="alembic.ini",
            database_url="postgresql://new_user:new_pass@new_host:5432/new_db",
            alembic_section_name="postgresql",
            configure=True,
            skip_db_checks=True,
        )

        # Read the file and verify PostgreSQL section was updated
        with open(alembic_ini_path) as f:
            content = f.read()

        # Verify PostgreSQL URL was updated
        assert "postgresql://new_user:new_pass@new_host:5432/new_db" in content
        # Verify ClickHouse URL was NOT changed
        assert "clickhouse://default@localhost:8123/wiremind" in content
        # Verify sections are still intact
        assert "[postgresql]" in content
        assert "[clickhouse]" in content
        assert "[loggers]" in content


def test_multi_database_configuration_clickhouse_section(mocker: MockerFixture) -> None:
    """
    Test that multi-database configuration correctly updates ClickHouse section in alembic.ini
    """
    # Sample alembic.ini content with multiple sections
    sample_alembic_ini = """[postgresql]
script_location = postgresl
sqlalchemy.url = postgresql://wiremind_owner@localhost:5432/wiremind
prepend_sys_path = ..
file_template = %%(year)d%%(month).2d%%(day).2d-%%(slug)s

[clickhouse]
script_location = clickhouse
sqlalchemy.url = clickhouse://default@localhost:8123/wiremind
prepend_sys_path = ..
file_template = %%(year)d%%(month).2d%%(day).2d-%%(slug)s

[loggers]
keys = root,sqlalchemy,alembic
"""

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a temporary alembic.ini file
        alembic_ini_path = os.path.join(temp_dir, "alembic.ini")
        with open(alembic_ini_path, "w") as f:
            f.write(sample_alembic_ini)

        # Test configuring ClickHouse section
        chartreuse.utils.AlembicMigrationHelper(
            alembic_directory_path=temp_dir,
            alembic_config_file_path="alembic.ini",
            database_url="clickhouse://new_user:new_pass@new_host:8123/new_db",
            alembic_section_name="clickhouse",
            configure=True,
            skip_db_checks=True,
        )

        # Read the file and verify ClickHouse section was updated
        with open(alembic_ini_path) as f:
            content = f.read()

        # Verify ClickHouse URL was updated
        assert "clickhouse://new_user:new_pass@new_host:8123/new_db" in content
        # Verify PostgreSQL URL was NOT changed
        assert "postgresql://wiremind_owner@localhost:5432/wiremind" in content
        # Verify sections are still intact
        assert "[postgresql]" in content
        assert "[clickhouse]" in content
        assert "[loggers]" in content


def test_multi_database_configuration_both_sections(mocker: MockerFixture) -> None:
    """
    Test that multi-database configuration correctly updates both sections independently
    """
    # Sample alembic.ini content with multiple sections
    sample_alembic_ini = """[postgresql]
script_location = postgresl
sqlalchemy.url = postgresql://wiremind_owner@localhost:5432/wiremind
prepend_sys_path = ..
file_template = %%(year)d%%(month).2d%%(day).2d-%%(slug)s

[clickhouse]
script_location = clickhouse
sqlalchemy.url = clickhouse://default@localhost:8123/wiremind
prepend_sys_path = ..
file_template = %%(year)d%%(month).2d%%(day).2d-%%(slug)s

[loggers]
keys = root,sqlalchemy,alembic
"""

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a temporary alembic.ini file
        alembic_ini_path = os.path.join(temp_dir, "alembic.ini")
        with open(alembic_ini_path, "w") as f:
            f.write(sample_alembic_ini)

        # Configure PostgreSQL section first
        chartreuse.utils.AlembicMigrationHelper(
            alembic_directory_path=temp_dir,
            alembic_config_file_path="alembic.ini",
            database_url="postgresql://pg_user:pg_pass@pg_host:5432/pg_db",
            alembic_section_name="postgresql",
            configure=True,
            skip_db_checks=True,
        )

        # Configure ClickHouse section second
        chartreuse.utils.AlembicMigrationHelper(
            alembic_directory_path=temp_dir,
            alembic_config_file_path="alembic.ini",
            database_url="clickhouse://ch_user:ch_pass@ch_host:8123/ch_db",
            alembic_section_name="clickhouse",
            configure=True,
            skip_db_checks=True,
        )

        # Read the file and verify both sections were updated correctly
        with open(alembic_ini_path) as f:
            final_content = f.read()

        # Verify both URLs are now updated correctly
        assert "postgresql://pg_user:pg_pass@pg_host:5432/pg_db" in final_content
        assert "clickhouse://ch_user:ch_pass@ch_host:8123/ch_db" in final_content
        # Verify original URLs are gone
        assert "postgresql://wiremind_owner@localhost:5432/wiremind" not in final_content
        assert "clickhouse://default@localhost:8123/wiremind" not in final_content
        # Verify sections are still intact
        assert "[postgresql]" in final_content
        assert "[clickhouse]" in final_content
        assert "[loggers]" in final_content


def test_single_database_configuration_with_alembic_section(mocker: MockerFixture) -> None:
    """
    Test that single-database configuration works when alembic_section_name is specified
    """
    # Sample simple alembic.ini content (single database)
    sample_alembic_ini = """[alembic]
script_location = alembic
sqlalchemy.url = postgresql://old@localhost:5432/old
prepend_sys_path = ..
file_template = %%(year)d%%(month).2d%%(day).2d-%%(slug)s
"""

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a temporary alembic.ini file
        alembic_ini_path = os.path.join(temp_dir, "alembic.ini")
        with open(alembic_ini_path, "w") as f:
            f.write(sample_alembic_ini)

        # Test single database configuration with explicit section name
        chartreuse.utils.AlembicMigrationHelper(
            alembic_directory_path=temp_dir,
            alembic_config_file_path="alembic.ini",
            database_url="postgresql://new_user:new_pass@new_host:5432/new_db",
            alembic_section_name="alembic",
            configure=True,
            skip_db_checks=True,
        )

        # Read the file and verify URL was updated
        with open(alembic_ini_path) as f:
            content = f.read()

        # Verify URL was updated
        assert "postgresql://new_user:new_pass@new_host:5432/new_db" in content
        # Verify original URL is gone
        assert "postgresql://old@localhost:5432/old" not in content
        # Verify section is still intact
        assert "[alembic]" in content
