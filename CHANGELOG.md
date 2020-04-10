# 1.0.1 (2020-04-10)
## Fixes
- setup.py: prevent upgrade to incompatible major version of wiremind-kube.

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
