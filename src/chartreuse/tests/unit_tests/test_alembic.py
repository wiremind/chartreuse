import chartreuse.utils


def test_respect_empty_database(mocker):
    """
    Test that is_postgres_empty returns empty even if alembic table exists
    """
    table_list = ["alembic_version"]
    mocker.patch("chartreuse.utils.AlembicMigrationHelper._get_table_list", return_value=table_list)
    alembic_migration_helper = chartreuse.utils.AlembicMigrationHelper("foo", configure=False)
    assert alembic_migration_helper.is_postgres_empty()


def test_respect_not_empty_database(mocker):
    """
    Test that is_postgres_empty return False when tables exist
    """
    table_list = ["alembic_version", "foobar"]
    mocker.patch("chartreuse.utils.AlembicMigrationHelper._get_table_list", return_value=table_list)
    mocker.patch("chartreuse.utils.AlembicMigrationHelper._get_alembic_current", return_value='123')
    alembic_migration_helper = chartreuse.utils.AlembicMigrationHelper("foo", configure=False)
    assert alembic_migration_helper.is_postgres_empty() is False


def test_detect_needed_migration(mocker):
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
    mocker.patch("chartreuse.utils.AlembicMigrationHelper._get_table_list", return_value=table_list)
    mocker.patch("chartreuse.utils.AlembicMigrationHelper._get_alembic_current", return_value=sample_alembic_output)
    alembic_migration_helper = chartreuse.utils.AlembicMigrationHelper("foo", configure=False)

    assert alembic_migration_helper.is_migration_needed


def test_detect_not_needed_migration(mocker):
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
    mocker.patch("chartreuse.utils.AlembicMigrationHelper._get_table_list", return_value=table_list)
    mocker.patch("chartreuse.utils.AlembicMigrationHelper._get_alembic_current", return_value=sample_alembic_output)
    alembic_migration_helper = chartreuse.utils.AlembicMigrationHelper("foo", configure=False)

    assert alembic_migration_helper.is_migration_needed is False


def test_detect_needed_migration_non_existent(mocker):
    """
    Test that chartreuse detects that an empty answer means migration is needed
    """
    sample_alembic_output = """
    """
    table_list = ["alembic_version", "foobar"]
    mocker.patch("chartreuse.utils.AlembicMigrationHelper._get_table_list", return_value=table_list)
    mocker.patch("chartreuse.utils.AlembicMigrationHelper._get_alembic_current", return_value=sample_alembic_output)
    alembic_migration_helper = chartreuse.utils.AlembicMigrationHelper("foo", configure=False)

    assert alembic_migration_helper.is_migration_needed


def test_detect_database_is_empty(mocker):
    """
    Test that chartreuse detects that a database is empty
    """
    sample_alembic_output = """
    """
    table_list = ["alembic_version"]
    mocker.patch("chartreuse.utils.AlembicMigrationHelper._get_table_list", return_value=table_list)
    mocker.patch("chartreuse.utils.AlembicMigrationHelper._get_alembic_current", return_value=sample_alembic_output)

    alembic_migration_helper = chartreuse.utils.AlembicMigrationHelper("foo", configure=False)

    assert alembic_migration_helper.is_postgres_empty()


def test_detect_database_is_not_empty(mocker):
    """
    Test that chartreuse detects that a database is not empty and allow migration.
    """
    sample_alembic_output = """
    """
    table_list = ["alembic_version", "foobar"]
    mocker.patch("chartreuse.utils.AlembicMigrationHelper._get_table_list", return_value=table_list)
    mocker.patch("chartreuse.utils.AlembicMigrationHelper._get_alembic_current", return_value=sample_alembic_output)

    alembic_migration_helper = chartreuse.utils.AlembicMigrationHelper("foo", configure=False)

    assert alembic_migration_helper.is_postgres_empty() is False
