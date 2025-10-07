#!/usr/bin/env python3
"""
Configuration validator for Chartreuse multi-database setup.

Usage: python validate_config.py path/to/config.yaml
"""

import sys
from pathlib import Path

import yaml


def build_database_url(db_config: dict) -> str:
    """Build database URL from components."""
    required_components = ["dialect", "user", "password", "host", "port", "database"]
    missing_components = [comp for comp in required_components if comp not in db_config or not db_config[comp]]

    if missing_components:
        raise ValueError(f"Missing components: {missing_components}")

    dialect = db_config["dialect"]
    user = db_config["user"]
    password = db_config["password"]
    host = db_config["host"]
    port = db_config["port"]
    database = db_config["database"]

    return f"{dialect}://{user}:{password}@{host}:{port}/{database}"


def validate_config(config_path: str) -> bool:
    """Validate a multi-database configuration file."""

    try:
        # Check if file exists
        if not Path(config_path).exists():
            print(f"❌ Configuration file not found: {config_path}")
            return False

        # Load and parse YAML
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Validate structure
        if "databases" not in config:
            print("❌ Configuration must contain 'databases' key")
            return False

        databases = config["databases"]
        if not isinstance(databases, dict):
            print("❌ 'databases' must be a dictionary with database names as keys")
            return False

        if len(databases) == 0:
            print("❌ At least one database must be configured")
            return False

        # Validate each database
        required_fields = [
            "alembic_directory_path",
            "alembic_config_file_path",
            "dialect",
            "user",
            "password",
            "host",
            "port",
            "database",
        ]

        for db_name, db_config in databases.items():
            print(f"Validating database: {db_name}")

            # Check required fields
            for field in required_fields:
                if field not in db_config:
                    print(f"❌ Database '{db_name}' missing required field: {field}")
                    return False
                if not db_config[field]:
                    print(f"❌ Database '{db_name}' field '{field}' cannot be empty")
                    return False

            # Validate URL building
            try:
                url = build_database_url(db_config)
                print(f"  📍 Built URL: {url}")

                # Basic URL format validation
                if not url.startswith(("postgresql://", "mysql://", "sqlite://")):
                    print(
                        f"⚠️  Database {db_name}: URL format may be invalid (expected postgresql://, mysql://, or sqlite://)"
                    )

            except ValueError as e:
                print(f"❌ Database {db_name}: {e}")
                return False

            # Check optional boolean fields
            for bool_field in ["allow_migration_for_empty_database"]:
                if bool_field in db_config and not isinstance(db_config[bool_field], bool):
                    print(f"❌ Database {db_name}: '{bool_field}' must be true or false")
                    return False

            print(f"✅ Database {db_name}: OK")

        print("\n✅ Configuration is valid!")
        print(f"Found {len(databases)} database(s): {', '.join(databases.keys())}")
        return True

    except yaml.YAMLError as e:
        print(f"❌ Invalid YAML: {e}")
        return False
    except Exception as e:
        print(f"❌ Error validating configuration: {e}")
        return False


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python validate_config.py path/to/config.yaml")
        sys.exit(1)

    config_path = sys.argv[1]
    is_valid = validate_config(config_path)

    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
