import chartreuse.utils


def test_detect_needed_migration_empty_database(mocker):
    """
    Test that chartreuse detects that an empty database means migration is needed.
    """
    sample_eslembic_output = """
2018-11-29 17:58:33,500 - elasticsearch - INFO - HEAD http://url:9200/eslembic_version [status:200 request:0.01s]
2018-11-29 17:58:33,510 - elasticsearch - INFO - GET http://url:9200/eslembic_version/_search [status:200 request:0.01s]
2018-11-29 17:58:33,511 - eslembic.core.migration_runner - INFO - ESlembic version is v1.0.0, bla
    """
    mocker.patch("chartreuse.utils.EslembicMigrationHelper._get_eslembic_current", return_value=sample_eslembic_output)
    eslembic_migration_helper = chartreuse.utils.EslembicMigrationHelper("foo", configure=False)
    assert eslembic_migration_helper.is_migration_needed


def test_detect_not_needed_migration(mocker):
    """
    Test that chartreuse detects that a migration is not needed.
    """
    sample_eslembic_output = """
2018-11-29 17:58:33,500 - elasticsearch - INFO - HEAD http://url:9200/eslembic_version [status:200 request:0.01s]
2018-11-29 17:58:33,510 - elasticsearch - INFO - GET http://url:9200/eslembic_version/_search [status:200 request:0.01s]
2018-11-29 17:58:33,511 - eslembic.core.migration_runner - INFO - ESlembic version is v1.0.0 (head), init
    """
    mocker.patch("chartreuse.utils.EslembicMigrationHelper._get_eslembic_current", return_value=sample_eslembic_output)
    eslembic_migration_helper = chartreuse.utils.EslembicMigrationHelper("foo", configure=False)
    assert eslembic_migration_helper.is_migration_needed is False
