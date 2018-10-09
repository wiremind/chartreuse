# Alembic migration within kubernetes

# Install

This Python package requires a `Custom Resource Definition`:

    $ kubectl apply -f customResourceDescription-expecteddeploymentscales.yaml

## Steps

 - Pre-deployment job: Stop all celeries
 - Run normal deployment
 - Post-deployment job:
    - Migrate
    - Restart all celeries

It has been decided to keep the nginx/uwsgi alive (unless manual intervention of planned downtime for long migrations).
