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
    - Detect if an alembic migration is required, if not, exit
    - Stop all celeries, nginx-uwsgi, cron
 - Run normal kubernetes deployment
 - Post-deployment job:
    - Detect if an alembic migration is required, if not, exit
    - Do alembic migration
    - Restart all pods that have been stopped before
