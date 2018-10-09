# -*- coding: utf-8 -*-
from future.standard_library import install_aliases

install_aliases()

import functools
import os
import re
import shlex
import socket
import subprocess
import sys
import time
import urllib.parse

import kubernetes
import sqlalchemy


def _run_command(command):
    """
    Run command, print stdout/stderr, check that command exited correctly, return stdout/err
    """
    print("Running %s" % command)
    process = subprocess.Popen(
        shlex.split(command),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    out, err = process.communicate()
    if out:
        print(out)
    if err:
        print(err)
    if process.returncode:
        raise subprocess.CalledProcessError(process.returncode, command)
    return (out, err)


def retry_kubernetes_request(function):
    """
    Decorator that retries a failed Kubernetes API request if needed
    """
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except kubernetes.client.rest.ApiException as e:
            if e.status == 404:
                print("Not found, ignoring.")
                return
            print(e)
            print("Retrying in 5 seconds...")
            time.sleep(5)
            return function(*args, **kwargs)
        finally:
            print("Done.")

    return wrapper


class KubernetesHelper(object):
    """
    A simple helper for Kubernetes manipulation.
    """

    deployment_namespace = None
    client_appsv1_api = None
    client_custom_objects_api = None

    def __init__(self):
        kubernetes.config.load_incluster_config()
        self.client_appsv1_api = kubernetes.client.AppsV1Api()
        self.client_custom_objects_api = kubernetes.client.CustomObjectsApi()
        self.deployment_namespace = open(
            "/var/run/secrets/kubernetes.io/serviceaccount/namespace"
        ).read()

    @retry_kubernetes_request
    def get_deployment_scale(self, deployment_name):
        print("Getting deployment scale for %s" % deployment_name)
        return self.client_appsv1_api.read_namespaced_deployment_scale(
            deployment_name, self.deployment_namespace, pretty="true"
        )

    @retry_kubernetes_request
    def scale_down_deployment(self, deployment_name):
        body = self.get_deployment_scale(deployment_name)
        print("Deleting all Pods for %s" % deployment_name)
        body.spec.replicas = 0
        self.client_appsv1_api.patch_namespaced_deployment_scale(
            deployment_name, self.deployment_namespace, body, pretty="true"
        )

    @retry_kubernetes_request
    def scale_up_deployment(self, deployment_name, pod_amount):
        body = self.get_deployment_scale(deployment_name)
        print("Recreating backend Pods for %s" % deployment_name)
        body.spec.replicas = pod_amount
        self.client_appsv1_api.patch_namespaced_deployment_scale(
            deployment_name, self.deployment_namespace, body, pretty="true"
        )
        print("Done recreating.")

    @retry_kubernetes_request
    def is_deployment_stopped(self, deployment_name):
        print("Asking if deployment %s is stopped" % deployment_name)
        replicas = self.client_appsv1_api.read_namespaced_deployment_scale(
            deployment_name, self.deployment_namespace, pretty="true"
        ).status.replicas
        return replicas == 0

    @retry_kubernetes_request
    def get_deployment_name_to_be_stopped_list(self):
        """
        Return a list of celery or any other deployment that requires
        stop before migration and start after migration.
        """
        print("Getting deployment-to-be-stopped-before-deployment list")
        release_name = os.environ['RELEASE_NAME']
        deployment_list = self.client_appsv1_api.list_namespaced_deployment(
            watch=False,
            label_selector="chartreuse=enabled,release=%s" % release_name,
            namespace=self.deployment_namespace,
        ).items
        deployment_name_list = [deployment.metadata.name for deployment in deployment_list]
        print("List is: %s" % deployment_name_list)
        return deployment_name_list

    @retry_kubernetes_request
    def get_expected_deployment_scale_dict(self):
        """
        Return a dict of expected deployment scale

        key: Deployment name
        value: expected Deployment Scale (replicas)
        """
        print("Getting Expected Deployment Scale list")
        release_name = os.environ['RELEASE_NAME']
        eds_list = self.client_custom_objects_api.list_namespaced_custom_object(
            namespace=self.deployment_namespace,
            group="wiremind.fr",
            version="v1",
            plural="expecteddeploymentscales",
            label_selector="release=%s" % release_name,
        )
        eds_dict = {eds['spec']['deploymentName']: eds['spec']['expectedScale'] for eds in eds_list['items']}
        print("List is %s" % eds_dict)
        return eds_dict

class AlembicMigrationHelper(object):
    database_url = None
    allow_migration_for_empty_database = False

    def __init__(self, database_url, allow_migration_for_empty_database=False):
        if not database_url:
            raise EnvironmentError("database_url not set, not upgrading database.")

        self.database_url = database_url
        self.allow_migration_for_empty_database = allow_migration_for_empty_database

        os.chdir("/app/alembic")
        cleaned_url = database_url.replace("/", r"\/")
        _run_command(
            "sed -i -e 's/sqlalchemy.url.*=.*/sqlalchemy.url=%s/' %s"
            % (cleaned_url, "alembic.ini")
        )
        self._check_migration_possible()

    def _check_migration_possible(self):
        if not self.is_postgres_domain_name_resolvable():
            print("Postgres server does not exist yet, not upgrading database.")
            sys.exit(0)
        if (
            not self.allow_migration_for_empty_database
            and self.is_postgres_empty()
        ):
            print("Database is not populated yet, not upgrading it.")
            sys.exit(0)
        if not self.is_migration_needed():
            print("Database does not need migration, exiting.")
            sys.exit(0)

    def is_postgres_domain_name_resolvable(self):
        os.chdir("/app/alembic")
        hostname = urllib.parse.urlparse(self.database_url).hostname
        try:
            socket.gethostbyname(hostname)
        except socket.gaierror:
            print(
                "Could not resolve hostname %s, assuming postgres server does not exist yet."
                % hostname
            )
            return False
        return True

    def is_postgres_empty(self):
        os.chdir("/app/alembic")
        table_list = sqlalchemy.create_engine(self.database_url).table_names()
        print("Tables in database: %s" % table_list)
        # Don't count "alembic" table
        table_name = "alembic_version"
        if table_name in table_list:
            table_list.remove(table_name)
        if table_list:
            return False
        return True

    def is_migration_needed(self):
        os.chdir("/app/alembic")
        head_re = re.compile(r"^\w+ \(head\)$", re.MULTILINE)
        alembic_current, _ = _run_command("alembic current")
        print("Current revision: %s" % alembic_current)
        if head_re.search(alembic_current):
            return False
        return True

    def migrate_db(self):
        print("Database needs to be upgraded. Proceeding.")
        _run_command("alembic history -r current:head")

        print("Upgrading database...")
        _run_command("alembic upgrade head")

        print("Done upgrading database.")
