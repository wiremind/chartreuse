# ChangeLog

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
