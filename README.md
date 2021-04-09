# Chartreuse: Alembic migration within kubernetes

**"How to automate management of database schema migration at scale without having to write backward/forward compatible migrations, using CI/CD and Kubernetes"**

Chartreuse is a wrapper around [Alembic](https://alembic.sqlalchemy.org) and [Eslembic](https://gitlab.cayzn.com/wiremind/commons/eslembic) to ease,
detect and automate migrations on deployed applications.

Chartreuse leverages [Helm Hooks](https://helm.sh/docs/topics/charts_hooks/), the Hooks are defined in Chartreuse [Chart](./helm-chart). Please make sure Chartreuse Python **Package version** and Chartreuse **Chart version**, you use, share `major.minor` otherwise Chartreuse won't start.

<!-- Add how to fetch those versions -->

# Install

This Python package requires a `Custom Resource Definition`:

    $ kubectl apply -f customResourceDescription-expecteddeploymentscales.yaml

# Configuration

TBD

## How it works

The state diagram of your application while upgrading using Helm and using Chartreuse for your migrations is as follows:

![alt text](doc/chartreuse_sd.png)

- The diagram has been drawn using the free online software https://draw.io, the
source code is located at `doc/chartreuse_sd.xml`, feel free
to correct it or make it more understandable.

Notes:
- When running Chartreuse in pre-upgrade mode (`upgradeBeforeDeployment: true`), it will not start running (The Chartreuse Pod will hang in `Init` state) until one PG Pod (and ES Pod if ES is used) is running, see [here](https://gitlab.wiremind.io/wiremind/devops/chartreuse/-/blob/v3.0.0/helm-chart/chartreuse/templates/job.yaml#L37) and [here](https://gitlab.wiremind.io/wiremind/devops/chartreuse/-/blob/v3.0.0/helm-chart/chartreuse/templates/job.yaml#L56), so make sure these Pods are available to Chartreuse. To fix that:
  - You will need to delete the Chartreuse Job so the upgrade can resume and fix you PG and ES pods (or create them if they don't exist), then you can redeploy so your migrations can run.
  - You can also try the `upgradeBeforeDeployment: false` mode (maybe temporarily).

# Test

There are three kind of tests:

- Unit tests
- Integration tests: allows to run in a real environment, but still control chartreuse from the inside
- blackbox test: deploy a real Helm Release and test if databases are migrated. Requires the PYPI_PASSWORD_READONLY envvar to be set in order to fetch required eggs to build the test Docker image.
