# Multi-Database Migration Support

Chartreuse now supports managing migrations for multiple databases simultaneously. This feature allows you to define multiple database configurations and run migrations across all of them.

## Configuration

### Single Database (Legacy)
The original single-database configuration using environment variables is still supported for backward compatibility.

### Multiple Databases (New)
To use multiple databases, create a YAML configuration file and set the `CHARTREUSE_MULTI_CONFIG_PATH` environment variable to point to it.

#### Configuration File Format

```yaml
databases:
  # Main application database
  main:
    alembic_directory_path: /app/alembic/main
    alembic_config_file_path: alembic.ini
    dialect: postgresql
    user: app_user
    password: app_password
    host: postgres-main
    port: 5432
    database: app_main
    allow_migration_for_empty_database: true
    additional_parameters: ""

  # Analytics database
  analytics:
    alembic_directory_path: /app/alembic/analytics
    alembic_config_file_path: alembic.ini
    dialect: postgresql
    user: analytics_user
    password: analytics_password
    host: postgres-analytics
    port: 5432
    database: analytics
    allow_migration_for_empty_database: false
    additional_parameters: ""
```

#### Configuration Fields

**Required fields:**
- Database name (used as key in the YAML)
- `alembic_directory_path`: Path to the Alembic directory for this database
- `alembic_config_file_path`: Alembic configuration file name

**Database connection components (all required):**
- `dialect`: Database dialect (e.g., postgresql, mysql, sqlite)
- `user`: Database username
- `password`: Database password
- `host`: Database host
- `port`: Database port
- `database`: Database name

**Optional fields:**
- `allow_migration_for_empty_database`: Whether to allow migrations on empty databases (default: false)
- `additional_parameters`: Additional parameters to pass to Alembic commands (default: "")

## Environment Variables

For multi-database mode:
- `CHARTREUSE_MULTI_CONFIG_PATH`: Path to the YAML configuration file
- `CHARTREUSE_ENABLE_STOP_PODS`: Whether to stop pods during migration (optional, default: true)
- `CHARTREUSE_RELEASE_NAME`: Kubernetes release name
- `CHARTREUSE_UPGRADE_BEFORE_DEPLOYMENT`: Whether to upgrade before deployment (optional, default: false)
- `HELM_IS_INSTALL`: Whether this is a Helm install operation (optional, default: false)

## Usage

### Setting up the environment
```bash
export CHARTREUSE_MULTI_CONFIG_PATH="/path/to/multi-database-config.yaml"
export CHARTREUSE_RELEASE_NAME="my-app"
export CHARTREUSE_ENABLE_STOP_PODS="true"
```

### Directory Structure Example
```
/app/
├── alembic/
│   ├── main/
│   │   ├── alembic.ini
│   │   ├── env.py
│   │   └── versions/
│   └── analytics/
│       ├── alembic.ini
│       ├── env.py
│       └── versions/
└── multi-database-config.yaml
```

### Configuration Validation
You can validate your configuration file before deployment:

```bash
python3 scripts/validate_config.py /path/to/multi-database-config.yaml
```

## Migration Behavior

When using multi-database configuration:

1. **Initialization**: All databases are initialized with their respective Alembic configurations
2. **Migration Check**: Each database is checked individually for pending migrations
3. **Migration Execution**: Only databases that need migration will be upgraded
4. **Error Handling**: If any database migration fails, the entire process fails
5. **Logging**: Detailed logs show which databases are being processed

## Backward Compatibility

The original single-database configuration using environment variables continues to work unchanged. The multi-database feature is only activated when `CHARTREUSE_MULTI_CONFIG_PATH` is set.

## Example Integration

In your Helm chart, you can use a ConfigMap to store the multi-database configuration:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: chartreuse-config
data:
  multi-database-config.yaml: |
    databases:
      main:
        alembic_directory_path: /app/alembic/main
        alembic_config_file_path: alembic.ini
        dialect: postgresql
        user: {{ .Values.database.main.user }}
        password: {{ .Values.database.main.password }}
        host: {{ .Values.database.main.host }}
        port: {{ .Values.database.main.port }}
        database: {{ .Values.database.main.name }}
        allow_migration_for_empty_database: true
        additional_parameters: ""
      analytics:
        alembic_directory_path: /app/alembic/analytics
        alembic_config_file_path: alembic.ini
        dialect: postgresql
        user: {{ .Values.database.analytics.user }}
        password: {{ .Values.database.analytics.password }}
        host: {{ .Values.database.analytics.host }}
        port: {{ .Values.database.analytics.port }}
        database: {{ .Values.database.analytics.name }}
        allow_migration_for_empty_database: false
        additional_parameters: ""
```

Then mount it in your migration job:

```yaml
env:
- name: CHARTREUSE_MULTI_CONFIG_PATH
  value: "/config/multi-database-config.yaml"
volumeMounts:
- name: config
  mountPath: /config
volumes:
- name: config
  configMap:
    name: chartreuse-config
```