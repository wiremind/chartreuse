# Chartreuse: Alembic migration within kubernetes

Chartreuse is a wrapper around Alembic to ease, detect and automate alembic migrations on deployed applications.

Chartreuse is made to work as Helm hooks. You need to use Chartreuse a a sub-chart of your project.

# Install

This Python package requires a `Custom Resource Definition`:

    $ kubectl apply -f customResourceDescription-expecteddeploymentscales.yaml

# Configuration

TBD

## How it works

The steps are:

 - Pre-deployment job (i.e a script that is run n kubernetes BEFORE deploying the new version of your app in kubernetes):
    - Detect if an alembic/eslembic migration is required, if not, exit
    - Stop all celeries, nginx-uwsgi, cron by scaling down all related deployments to 0
 - Run normal kubernetes deployment (which could re-scale-up deployments, no guarantee here)
 - Post-deployment job:
    - Detect if an alembic/eslembic migration is required, if not, exit
    - Stop all celeries, nginx-uwsgi, cron by scaling down all related deployments to 0
    - Do alembic/eslembic migration
    - Restart all pods that have been stopped before
