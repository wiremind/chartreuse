"""
Unit tests for config_loader module.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from pydantic import ValidationError

from chartreuse.config_loader import DatabaseConfig, MultiDatabaseConfig, load_multi_database_config


class TestDatabaseConfig:
    """Test cases for DatabaseConfig model."""

    def test_valid_database_config(self):
        """Test creating a valid database configuration."""
        config_data = {
            "dialect": "postgresql",
            "user": "testuser",
            "password": "testpass",
            "host": "localhost",
            "port": 5432,
            "database": "testdb",
            "alembic_directory_path": "/app/alembic",
        }

        config = DatabaseConfig(**config_data)

        assert config.dialect == "postgresql"
        assert config.user == "testuser"
        assert config.password == "testpass"
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.database == "testdb"
        assert config.alembic_directory_path == "/app/alembic"
        assert config.alembic_config_file_path == "alembic.ini"  # default value
        assert config.allow_migration_for_empty_database is True  # default value
        assert config.additional_parameters == ""  # default value

    def test_database_config_url_computation(self):
        """Test that the URL is computed correctly from components."""
        config = DatabaseConfig(
            dialect="postgresql",
            user="myuser",
            password="mypass",
            host="example.com",
            port=5432,
            database="mydb",
            alembic_directory_path="/app/alembic",
        )

        expected_url = "postgresql://myuser:mypass@example.com:5432/mydb"
        assert config.url == expected_url

    def test_database_config_with_optional_fields(self):
        """Test database configuration with all optional fields set."""
        config_data = {
            "dialect": "mysql",
            "user": "testuser",
            "password": "testpass",
            "host": "localhost",
            "port": 3306,
            "database": "testdb",
            "alembic_directory_path": "/app/alembic",
            "alembic_config_file_path": "custom_alembic.ini",
            "allow_migration_for_empty_database": False,
            "additional_parameters": "-x custom_param=value",
        }

        config = DatabaseConfig(**config_data)

        assert config.alembic_config_file_path == "custom_alembic.ini"
        assert config.allow_migration_for_empty_database is False
        assert config.additional_parameters == "-x custom_param=value"

    def test_database_config_missing_required_fields(self):
        """Test that missing required fields raise validation errors."""
        incomplete_config = {
            "dialect": "postgresql",
            "user": "testuser",
            # Missing password, host, port, database, alembic_directory_path
        }

        with pytest.raises(ValidationError) as excinfo:
            DatabaseConfig(**incomplete_config)

        error_dict = excinfo.value.errors()
        required_fields = ["password", "host", "port", "database", "alembic_directory_path"]

        for field in required_fields:
            assert any(error["loc"] == (field,) for error in error_dict)

    def test_database_config_invalid_port(self):
        """Test validation of port field."""
        # Test port too small
        with pytest.raises(ValidationError) as excinfo:
            DatabaseConfig(
                dialect="postgresql",
                user="testuser",
                password="testpass",
                host="localhost",
                port=0,  # Invalid: too small
                database="testdb",
                alembic_directory_path="/app/alembic",
            )
        assert "greater than 0" in str(excinfo.value)

        # Test port too large
        with pytest.raises(ValidationError) as excinfo:
            DatabaseConfig(
                dialect="postgresql",
                user="testuser",
                password="testpass",
                host="localhost",
                port=65536,  # Invalid: too large
                database="testdb",
                alembic_directory_path="/app/alembic",
            )
        assert "less than or equal to 65535" in str(excinfo.value)

    def test_database_config_dialect_validation(self):
        """Test dialect validation with supported and unsupported dialects."""
        # Test supported dialect
        config = DatabaseConfig(
            dialect="postgresql",
            user="testuser",
            password="testpass",
            host="localhost",
            port=5432,
            database="testdb",
            alembic_directory_path="/app/alembic",
        )
        assert config.dialect == "postgresql"

        # Test unsupported dialect (should still work but log warning)
        config = DatabaseConfig(
            dialect="unsupported_db",
            user="testuser",
            password="testpass",
            host="localhost",
            port=5432,
            database="testdb",
            alembic_directory_path="/app/alembic",
        )
        assert config.dialect == "unsupported_db"

    def test_additional_parameters_empty_string_handling(self):
        """Test that additional_parameters defaults to empty string when not provided."""
        config = DatabaseConfig(
            dialect="postgresql",
            user="testuser",
            password="testpass",
            host="localhost",
            port=5432,
            database="testdb",
            alembic_directory_path="/app/alembic",
        )
        assert config.additional_parameters == ""


class TestMultiDatabaseConfig:
    """Test cases for MultiDatabaseConfig model."""

    def test_valid_multi_database_config(self):
        """Test creating a valid multi-database configuration."""
        db_config = DatabaseConfig(
            dialect="postgresql",
            user="testuser",
            password="testpass",
            host="localhost",
            port=5432,
            database="testdb",
            alembic_directory_path="/app/alembic",
        )

        config = MultiDatabaseConfig(databases={"main": db_config})

        assert "main" in config.databases
        assert config.databases["main"] == db_config

    def test_multi_database_config_multiple_databases(self):
        """Test multi-database configuration with multiple databases."""
        db1 = DatabaseConfig(
            dialect="postgresql",
            user="user1",
            password="pass1",
            host="host1",
            port=5432,
            database="db1",
            alembic_directory_path="/app/alembic1",
        )

        db2 = DatabaseConfig(
            dialect="mysql",
            user="user2",
            password="pass2",
            host="host2",
            port=3306,
            database="db2",
            alembic_directory_path="/app/alembic2",
        )

        config = MultiDatabaseConfig(databases={"main": db1, "analytics": db2})

        assert len(config.databases) == 2
        assert "main" in config.databases
        assert "analytics" in config.databases
        assert config.databases["main"] == db1
        assert config.databases["analytics"] == db2

    def test_multi_database_config_empty_databases(self):
        """Test that empty databases dictionary raises validation error."""
        with pytest.raises(ValidationError) as excinfo:
            MultiDatabaseConfig(databases={})

        assert "At least one database must be configured" in str(excinfo.value)

    def test_multi_database_config_missing_databases(self):
        """Test that missing databases field raises validation error."""
        with pytest.raises(ValidationError) as excinfo:
            MultiDatabaseConfig()

        error_dict = excinfo.value.errors()
        assert any(error["loc"] == ("databases",) for error in error_dict)


class TestLoadMultiDatabaseConfig:
    """Test cases for load_multi_database_config function."""

    def test_load_valid_config_file(self):
        """Test loading a valid configuration file."""
        config_content = {
            "databases": {
                "main": {
                    "dialect": "postgresql",
                    "user": "testuser",
                    "password": "testpass",
                    "host": "localhost",
                    "port": 5432,
                    "database": "testdb",
                    "alembic_directory_path": "/app/alembic",
                },
                "analytics": {
                    "dialect": "mysql",
                    "user": "analyticsuser",
                    "password": "analyticspass",
                    "host": "analytics-host",
                    "port": 3306,
                    "database": "analytics",
                    "alembic_directory_path": "/app/alembic/analytics",
                    "allow_migration_for_empty_database": False,
                },
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_content, f)
            config_path = f.name

        try:
            databases = load_multi_database_config(config_path)

            assert len(databases) == 2
            assert "main" in databases
            assert "analytics" in databases

            # Check main database
            main_db = databases["main"]
            assert main_db.dialect == "postgresql"
            assert main_db.user == "testuser"
            assert main_db.password == "testpass"
            assert main_db.host == "localhost"
            assert main_db.port == 5432
            assert main_db.database == "testdb"
            assert main_db.alembic_directory_path == "/app/alembic"
            assert main_db.allow_migration_for_empty_database is True  # default
            assert main_db.url == "postgresql://testuser:testpass@localhost:5432/testdb"

            # Check analytics database
            analytics_db = databases["analytics"]
            assert analytics_db.dialect == "mysql"
            assert analytics_db.user == "analyticsuser"
            assert analytics_db.allow_migration_for_empty_database is False
            assert analytics_db.url == "mysql://analyticsuser:analyticspass@analytics-host:3306/analytics"

        finally:
            Path(config_path).unlink()

    def test_load_single_database_config(self):
        """Test loading a configuration with a single database."""
        config_content = {
            "databases": {
                "main": {
                    "dialect": "postgresql",
                    "user": "testuser",
                    "password": "testpass",
                    "host": "localhost",
                    "port": 5432,
                    "database": "testdb",
                    "alembic_directory_path": "/app/alembic",
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_content, f)
            config_path = f.name

        try:
            databases = load_multi_database_config(config_path)

            assert len(databases) == 1
            assert "main" in databases
            main_db = databases["main"]
            assert main_db.dialect == "postgresql"

        finally:
            Path(config_path).unlink()

    def test_load_nonexistent_file(self):
        """Test loading a configuration file that doesn't exist."""
        with pytest.raises(FileNotFoundError) as excinfo:
            load_multi_database_config("/nonexistent/config.yaml")

        assert "Configuration file not found" in str(excinfo.value)

    def test_load_invalid_yaml(self):
        """Test loading a file with invalid YAML."""
        invalid_yaml = "databases:\n  main:\n    dialect: postgresql\n  invalid: yaml: content:"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(invalid_yaml)
            config_path = f.name

        try:
            with pytest.raises(ValueError) as excinfo:
                load_multi_database_config(config_path)

            assert "Invalid YAML in configuration file" in str(excinfo.value)

        finally:
            Path(config_path).unlink()

    def test_load_config_missing_required_fields(self):
        """Test loading a configuration with missing required fields."""
        config_content = {
            "databases": {
                "main": {
                    "dialect": "postgresql",
                    "user": "testuser",
                    # Missing required fields: password, host, port, database, alembic_directory_path
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_content, f)
            config_path = f.name

        try:
            with pytest.raises(ValueError) as excinfo:
                load_multi_database_config(config_path)

            assert "Invalid configuration" in str(excinfo.value)

        finally:
            Path(config_path).unlink()

    def test_load_config_empty_databases(self):
        """Test loading a configuration with empty databases."""
        config_content = {"databases": {}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_content, f)
            config_path = f.name

        try:
            with pytest.raises(ValueError) as excinfo:
                load_multi_database_config(config_path)

            assert "Invalid configuration" in str(excinfo.value)

        finally:
            Path(config_path).unlink()

    def test_load_config_no_databases_key(self):
        """Test loading a configuration without 'databases' key."""
        config_content = {"invalid_key": "value"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_content, f)
            config_path = f.name

        try:
            with pytest.raises(ValueError) as excinfo:
                load_multi_database_config(config_path)

            assert "Invalid configuration" in str(excinfo.value)

        finally:
            Path(config_path).unlink()

    def test_load_config_with_all_optional_fields(self):
        """Test loading a configuration with all optional fields specified."""
        config_content = {
            "databases": {
                "main": {
                    "dialect": "postgresql",
                    "user": "testuser",
                    "password": "testpass",
                    "host": "localhost",
                    "port": 5432,
                    "database": "testdb",
                    "alembic_directory_path": "/app/alembic",
                    "alembic_config_file_path": "custom_alembic.ini",
                    "allow_migration_for_empty_database": False,
                    "additional_parameters": "-x custom=value",
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_content, f)
            config_path = f.name

        try:
            databases = load_multi_database_config(config_path)

            assert len(databases) == 1
            db = databases["main"]
            assert db.alembic_config_file_path == "custom_alembic.ini"
            assert db.allow_migration_for_empty_database is False
            assert db.additional_parameters == "-x custom=value"

        finally:
            Path(config_path).unlink()

    @patch("chartreuse.config_loader.logger")
    def test_load_config_logs_info(self, mock_logger):
        """Test that loading a valid config logs appropriate info messages."""
        config_content = {
            "databases": {
                "main": {
                    "dialect": "postgresql",
                    "user": "testuser",
                    "password": "testpass",
                    "host": "localhost",
                    "port": 5432,
                    "database": "testdb",
                    "alembic_directory_path": "/app/alembic",
                },
                "analytics": {
                    "dialect": "mysql",
                    "user": "analyticsuser",
                    "password": "analyticspass",
                    "host": "analytics-host",
                    "port": 3306,
                    "database": "analytics",
                    "alembic_directory_path": "/app/alembic/analytics",
                },
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_content, f)
            config_path = f.name

        try:
            load_multi_database_config(config_path)

            # Check that info was logged about loaded databases
            mock_logger.info.assert_called_once()
            log_call = mock_logger.info.call_args[0]
            # The logger uses % formatting, so check format string and args separately
            assert "Loaded configuration for %d database(s): %s" == log_call[0]
            assert log_call[1] == 2
            # Check that both database names are present (order may vary)
            database_names = log_call[2]
            assert "main" in database_names
            assert "analytics" in database_names

        finally:
            Path(config_path).unlink()

    @patch("chartreuse.config_loader.logger")
    def test_unsupported_dialect_logs_warning(self, mock_logger):
        """Test that using an unsupported dialect logs a warning."""
        config_content = {
            "databases": {
                "main": {
                    "dialect": "unsupported_dialect",
                    "user": "testuser",
                    "password": "testpass",
                    "host": "localhost",
                    "port": 5432,
                    "database": "testdb",
                    "alembic_directory_path": "/app/alembic",
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_content, f)
            config_path = f.name

        try:
            load_multi_database_config(config_path)

            # Check that warning was logged about unsupported dialect
            mock_logger.warning.assert_called_once()
            log_call = mock_logger.warning.call_args[0]
            assert "unsupported_dialect" in log_call[1]
            assert "might not be supported" in log_call[0]

        finally:
            Path(config_path).unlink()
