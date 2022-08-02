# Changelog

## v4.2.0 (2022-08-02)
### Feature
- Added an environment variable `CHARTREUSE_ALEMBIC_CONFIG_FILE_PATH` to customise alembic configuration file path

## v4.1.0 (2022-08-01)
### Feature
- Correctly add mypy support
- Added a basic .gitignore file for python projects
- Added an environment variable `CHARTREUSE_ALEMBIC_DIRECTORY_PATH` to customise alembic directory path

## v4.0.3 (2021-10-09)
### Fixes
- Test python 3.10 in CI.

## v4.0.2 (2021-10-08)
### Fixes
- fix: upgrade wiremind-kubernetes to ignore failed (like Evicted) Pods when stop-pods.

## v4.0.1 (2021-10-04)
### Fixes
- setup.py: require wiremind-kubernetes>=6.3.2 that itself requires kubernetes>=18.

# 4.0.0 (2021-10-01)
## Breaking Changes
- Drop eslembic support
- drop wiremind.fr CRD
## Fix
- Avoid logging the PG password when `sed`ing alembic.ini.
### Chore
- Open source

# 3.1.0 (2021-05-03)
## Feature
- Add support for PG clusters managed by postgres-operator (Patroni PG):
  - Wait for the PG cluster to be configured before running the migrations.
  - When Alembic run migrations against a Patroni PG, the owner Role should be set.

# 3.0.1 (2021-04-13)
## Fix
- ensure_safe_run: Support more sem versions.
- Upgrade dependencies

# 3.0.0 (2021-02-17)
## BREAKING CHANGE
- Check the compatibility between Chartreuse's python package version and Chartreuse's Helm Chart version. Raise if the versions are not compatible.
- helm-chart: Deprecate `.Values.runMigrationInPreDeployment`, use `.Values.upgradeBeforeDeployment` instead.
## Feature
- Make it possible to control the upgradeJobs execution order (via `.Values.upgradeJobWeight`) in the case of multiple Chartreuses running. The upgradeJobs will be executed in weighted order.
## Fixes
- Uses logger instead of print in eslembic_migration_helper and alembic_migration_helper.
- helm-chart: Add `.Chart.Name` to the Job name to be able to use Chartreuse chart multiple times on a umbrella chart
- `alembic.additionalParameters` will also be passed to `alembic current`

# 2.3.2 (2020-09-28)
## Fixes
- ensure_safe_run now allows running Chartreuse inside a Chart with a different patch version

# 2.3.1 (2020-09-28)
## Fixes
- Be less agressive even if this allows users to upgrade the package without upgrading the Chart.

# 2.3.0 (2020-09-21)
## Features
- Add the possibility to specify a priorityClassName for the pods chartreuse launches
- Check the compatibility between Chartreuse's package version and Chartreuse's Helm Chart version.
- Chartreuse now runs on Python >=3.7.0

# 2.2.1 (2020-06-08)
## Fix
- attribute error when ES upgrade/migration is not wanted.

# 2.2.0 (2020-06-04)
## Fix
- unify `.Values.runMigrationInPreDeployment` and `.Values.upgradeBeforeDeployment` with backward compatibility.
`.Values.runMigrationInPreDeployment` will be deprecated in the next major version.

# 2.1.0 (2020-05-15)
## Fix
- Add the appropriate roles to support interacting with wiremind.fr's EDSs. See wiremind-kubernetes==5.1.0's ChangeLog.

# 2.0.0 (2020-04-23)
## BREAKING CHANGES
- helm: move most alembic/eslembic parameters to eslembic and alembic prefix.
- Rename most environment variables used by chartreuse.
- Remove pre-deployment job that stop-pods before deployment, since helm 3 will re-start them anyway.
## Features
- Chartreuse: add a upgradeBeforeDeployment value allowing to move chartreuse migration to pre-deployment instead of post-deployment, false by default. Note that in such case, a deployment failure may cause new database schema version but old code to be on the environment (you may want to disable helmDefaults.atomic parameter in helmfile.yaml of your project)
- Chartreuse: Allow to keep pods started and not do stop-pods.
- alembic: allow to give additional parameters to alembic.
- eslembic: Split eslembic upgrade to eslembic upgrade and eslembic migrate as a post job
- eslembic: allow to enable eslembic upgrade through `eslembic.upgrade.enabled` value
- helm: Add `additionalEnvironmentVariables` parameter to inject envvars into Chartreuse Pods.
- helm: Add support for built-in secret.
- helm: delete all roles, serviceaccounts, secrets, configmap after success
- helm: delete post-rollback job that is useless with helm 3
- Upgrade to eslembic v6.x.x

# 1.1.0 (2020-03-10)
## Features
## Fixes:
- Set terminationGracePeriodSeconds: 0 in all jobs.

# 1.0.0 (2020-02-03)
Please note that python code and helm chart versions are now synchronized.
## BREAKING CHANGES
- Drop python 3.5.
## Features
- Add CHARTREUSE_ESLEMBIC_ENABLE_CLEAN environment variable to clean index (wiremind.chartreuse.eslembic.cleanIndex variable in helm).
- Upgrade eslembic to v5.0.1

# 0.9.3 (2019-12-22)
## Fixes
- Factor run_command helper, allowing to have live output printing.
- Helm chart: enable RBACs
