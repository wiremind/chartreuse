"""Unit tests for config_loader module."""

import os
import tempfile

import pytest
import yaml

from chartreuse.config_loader import build_database_url, load_multi_database_config


class TestBuildDatabaseUrl:
    """Test cases for build_database_url function."""

    def test_build_database_url_success(self) -> None:
        """Test successful database URL building with all required components."""
        db_config = {
            "dialect": "postgresql",
            "user": "testuser",
            "password": "testpass",
            "host": "localhost",
            "port": "5432",
            "database": "testdb",
        }
        
        expected_url = "postgresql://testuser:testpass@localhost:5432/testdb"
        result = build_database_url(db_config)
        
        assert result == expected_url

    def test_build_database_url_missing_components(self) -> None:
        """Test that missing components raise ValueError."""
        db_config = {
            "dialect": "postgresql",
            "user": "testuser",
            # Missing password, host, port, database
        }
        
        with pytest.raises(ValueError) as exc_info:
            build_database_url(db_config)
        
        assert "Missing required components" in str(exc_info.value)
        assert "password" in str(exc_info.value)
        assert "host" in str(exc_info.value)
        assert "port" in str(exc_info.value)
        assert "database" in str(exc_info.value)

    def test_build_database_url_empty_components(self) -> None:
        """Test that empty string components are treated as missing."""
        db_config = {
            "dialect": "postgresql",
            "user": "",  # Empty string
            "password": "testpass",
            "host": "localhost",
            "port": "5432",
            "database": "testdb",
        }
        
        with pytest.raises(ValueError) as exc_info:
            build_database_url(db_config)
        
        assert "Missing required components" in str(exc_info.value)
        assert "user" in str(exc_info.value)

    def test_build_database_url_with_special_characters(self) -> None:
        """Test URL building with special characters in password."""
        db_config = {
            "dialect": "postgresql",
            "user": "test@user",
            "password": "test!@#$%pass",
            "host": "localhost",
            "port": "5432",
            "database": "test-db",
        }
        
        expected_url = "postgresql://test@user:test!@#$%pass@localhost:5432/test-db"
        result = build_database_url(db_config)
        
        assert result == expected_url


class TestLoadMultiDatabaseConfig:
    """Test cases for load_multi_database_config function."""

    def test_load_multi_database_config_success(self) -> None:
        """Test successful loading of multi-database configuration."""
        config_data = {
            "databases": {
                "main": {
                    "alembic_directory_path": "/app/alembic/main",
                    "alembic_config_file_path": "alembic.ini",
                    "dialect": "postgresql",
                    "user": "mainuser",
                    "password": "mainpass",
                    "host": "main.db.com",
                    "port": "5432",
                    "database": "maindb",
                    "allow_migration_for_empty_database": True,
                    "additional_parameters": "--verbose",
                },
                "secondary": {
                    "alembic_directory_path": "/app/alembic/secondary",
                    "alembic_config_file_path": "alembic.ini",
                    "dialect": "postgresql",
                    "user": "secuser",
                    "password": "secpass",
                    "host": "sec.db.com",
                    "port": "5433",
                    "database": "secdb",
                    "allow_migration_for_empty_database": False,
                },
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_file = f.name

        try:
            result = load_multi_database_config(temp_file)
            
            assert len(result) == 2
            
            # Check main database config
            main_db = next(db for db in result if db["name"] == "main")
            assert main_db["alembic_directory_path"] == "/app/alembic/main"
            assert main_db["url"] == "postgresql://mainuser:mainpass@main.db.com:5432/maindb"
            assert main_db["allow_migration_for_empty_database"] is True
            assert main_db["additional_parameters"] == "--verbose"
            
            # Check secondary database config
            sec_db = next(db for db in result if db["name"] == "secondary")
            assert sec_db["alembic_directory_path"] == "/app/alembic/secondary"
            assert sec_db["url"] == "postgresql://secuser:secpass@sec.db.com:5433/secdb"
            assert sec_db["allow_migration_for_empty_database"] is False
            assert sec_db.get("additional_parameters", "") == ""
            
        finally:
            os.unlink(temp_file)

    def test_load_multi_database_config_missing_databases_key(self) -> None:
        """Test that missing 'databases' key raises ValueError."""
        config_data = {
            "some_other_key": {
                "value": "test"
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_file = f.name

        try:
            with pytest.raises(ValueError) as exc_info:
                load_multi_database_config(temp_file)
            
            assert "Configuration must contain 'databases' key" in str(exc_info.value)
        finally:
            os.unlink(temp_file)

    def test_load_multi_database_config_databases_not_dict(self) -> None:
        """Test that non-dict 'databases' value raises ValueError."""
        config_data = {
            "databases": ["not", "a", "dict"]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_file = f.name

        try:
            with pytest.raises(ValueError) as exc_info:
                load_multi_database_config(temp_file)
            
            assert "'databases' must be a dictionary" in str(exc_info.value)
        finally:
            os.unlink(temp_file)

    def test_load_multi_database_config_missing_required_components(self) -> None:
        """Test that missing database components raise ValueError."""
        config_data = {
            "databases": {
                "incomplete": {
                    "alembic_directory_path": "/app/alembic",
                    "dialect": "postgresql",
                    "user": "user",
                    # Missing password, host, port, database
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_file = f.name

        try:
            with pytest.raises(ValueError) as exc_info:
                load_multi_database_config(temp_file)
            
            assert "Missing required components" in str(exc_info.value)
        finally:
            os.unlink(temp_file)

    def test_load_multi_database_config_file_not_found(self) -> None:
        """Test that missing config file raises FileNotFoundError."""
        non_existent_file = "/path/that/does/not/exist.yaml"
        
        with pytest.raises(FileNotFoundError) as exc_info:
            load_multi_database_config(non_existent_file)
        
        assert f"Configuration file not found: {non_existent_file}" in str(exc_info.value)

    def test_load_multi_database_config_invalid_yaml(self) -> None:
        """Test that invalid YAML raises ValueError."""
        invalid_yaml = """
        databases:
          main:
            key: value
          invalid: [unclosed bracket
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_yaml)
            temp_file = f.name

        try:
            with pytest.raises(ValueError) as exc_info:
                load_multi_database_config(temp_file)
            
            assert "Invalid YAML in configuration file" in str(exc_info.value)
        finally:
            os.unlink(temp_file)

    def test_load_multi_database_config_minimal_config(self) -> None:
        """Test loading with minimal required configuration."""
        config_data = {
            "databases": {
                "minimal": {
                    "alembic_directory_path": "/app/alembic",
                    "alembic_config_file_path": "alembic.ini",
                    "dialect": "postgresql",
                    "user": "user",
                    "password": "pass",
                    "host": "localhost",
                    "port": "5432",
                    "database": "db",
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_file = f.name

        try:
            result = load_multi_database_config(temp_file)
            
            assert len(result) == 1
            db_config = result[0]
            assert db_config["name"] == "minimal"
            assert db_config["url"] == "postgresql://user:pass@localhost:5432/db"
            assert db_config.get("allow_migration_for_empty_database", False) is False
            assert db_config.get("additional_parameters", "") == ""
            
        finally:
            os.unlink(temp_file)