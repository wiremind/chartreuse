# 2.0.0 (Unreleased)
## BREAKING CHANGES
- helm: move most alembic/eslembic parameters to eslembic and alembic prefix.
## Features
- eslembic: Split eslembic upgrade to eslembic migrate and eslembic upgrade as a post job
- eslembic: allow to disable/enable eslembic upgrade
## Fixes
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
- Add CHARTREUSE_ESLEMBIC_CLEAN_INDEX environment variable to clean index (wiremind.chartreuse.eslembic.cleanIndex variable in helm).
- Upgrade eslembic to v5.0.1

# 0.9.3 (2019-12-22)
## Fixes
- Factor run_command helper, allowing to have live output printing.
- Helm chart: enable RBACs
