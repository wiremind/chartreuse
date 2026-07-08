import unittest

import kubernetes
from pytest_mock import MockerFixture

from chartreuse.kubernetes_helper import STOPPED_ANNOTATION, KubernetesDeploymentManager


def _make_kdm(mocker: MockerFixture) -> KubernetesDeploymentManager:
    mocker.patch("kubernetes.client.AppsV1Api")
    mocker.patch("kubernetes.client.CoreV1Api")
    mocker.patch("kubernetes.client.AutoscalingV2Api")
    mocker.patch("kubernetes.client.CustomObjectsApi")
    return KubernetesDeploymentManager(
        should_load_kubernetes_config=False,
        namespace="foo",
        release_name="concerned",
    )


def _make_deployment(mocker: MockerFixture, annotations: dict | None, replicas: int) -> unittest.mock.MagicMock:
    deployment = mocker.MagicMock()
    deployment.metadata.annotations = annotations
    deployment.spec.replicas = replicas
    return deployment


def test_stop_pods_priority(mocker: MockerFixture) -> None:
    """
    Test that we honor priorities when stopping workloads.

    i.e that we stop all deployments with the highest priority first, then wait for all of those to be stopped
    then continue.
    """
    kdm = _make_kdm(mocker)
    mocker.patch.object(
        kdm,
        "_get_expected_deployment_scale_dict",
        return_value={
            0: {"last": 42},
            2: {"first": 17},
            1: {"second": 17},
        },
    )
    mocked_stop_deployments = mocker.patch.object(kdm, "_stop_deployments")

    kdm.stop_pods()

    assert mocked_stop_deployments.mock_calls == [
        unittest.mock.call({"first": 17}),
        unittest.mock.call({"second": 17}),
        unittest.mock.call({"last": 42}),
    ]


def test_stop_deployments_correctly_wait(mocker: MockerFixture) -> None:
    """
    Test that we wait for deployments to be stopped
    """
    kdm = _make_kdm(mocker)
    deployment_dict = {"my-pod": 42, "my-other-pod": 113}
    mocker.patch.object(kdm, "disable_hpa")
    mocker.patch.object(kdm, "scale_down_deployment")
    mocker.patch.object(kdm, "annotate_deployment")
    mocked_are_deployments_stopped = mocker.patch.object(
        kdm, "_are_deployments_stopped", side_effect=[False, False, True]
    )
    mocker.patch("time.sleep")

    kdm._stop_deployments(deployment_dict)

    assert mocked_are_deployments_stopped.mock_calls == [
        unittest.mock.call(deployment_dict),
        unittest.mock.call(deployment_dict),
        unittest.mock.call(deployment_dict),
    ]


def test_stop_deployments_annotates_stopped_deployments(mocker: MockerFixture) -> None:
    """
    Test that _stop_deployments marks every Deployment it scales down with STOPPED_ANNOTATION.
    """
    kdm = _make_kdm(mocker)
    mocker.patch.object(kdm, "_are_deployments_stopped", return_value=True)
    mocker.patch.object(kdm, "disable_hpa")
    mocker.patch.object(kdm, "scale_down_deployment")
    mocked_annotate = mocker.patch.object(kdm, "annotate_deployment")

    kdm._stop_deployments({"my-pod": 42, "my-other-pod": 113})

    assert mocked_annotate.mock_calls == [
        unittest.mock.call("my-pod", {STOPPED_ANNOTATION: "concerned"}),
        unittest.mock.call("my-other-pod", {STOPPED_ANNOTATION: "concerned"}),
    ]


def test_start_pods_clears_stopped_annotation(mocker: MockerFixture) -> None:
    kdm = _make_kdm(mocker)
    mocker.patch.object(kdm, "_get_expected_deployment_scale_dict", return_value={0: {"worker": 2}})
    mocker.patch.object(kdm, "re_enable_hpa")
    mocker.patch.object(kdm, "scale_up_deployment")
    mocked_annotate = mocker.patch.object(kdm, "annotate_deployment")

    kdm.start_pods()

    assert mocked_annotate.mock_calls == [unittest.mock.call("worker", {STOPPED_ANNOTATION: None})]


def test_restore_stopped_pods(mocker: MockerFixture) -> None:
    """
    Test that restore_stopped_pods only restores Deployments still carrying STOPPED_ANNOTATION,
    only scales those still at 0 replicas, and always clears the annotation.
    """
    kdm = _make_kdm(mocker)
    mocker.patch.object(
        kdm,
        "_get_expected_deployment_scale_dict",
        return_value={
            0: {
                "stopped-worker": 2,  # annotated, still at 0: restore to expectedScale
                "untouched-worker": 3,  # not annotated (deliberately at 0): leave alone
                "already-scaled": 1,  # annotated but replicas > 0: only clear the annotation
            },
            1: {"gone": 1},  # Deployment does not exist anymore: skip
        },
    )
    deployments = {
        "stopped-worker": _make_deployment(mocker, {STOPPED_ANNOTATION: "concerned"}, 0),
        "untouched-worker": _make_deployment(mocker, None, 0),
        "already-scaled": _make_deployment(mocker, {STOPPED_ANNOTATION: "concerned"}, 4),
    }

    def read_deployment(name: str, namespace: str) -> unittest.mock.MagicMock:
        if name not in deployments:
            raise kubernetes.client.rest.ApiException(status=404)
        return deployments[name]

    kdm.client_appsv1_api.read_namespaced_deployment.side_effect = read_deployment
    mocked_re_enable_hpa = mocker.patch.object(kdm, "re_enable_hpa")
    mocked_scale_up = mocker.patch.object(kdm, "scale_up_deployment")
    mocked_annotate = mocker.patch.object(kdm, "annotate_deployment")

    kdm.restore_stopped_pods()

    assert mocked_re_enable_hpa.mock_calls == [
        unittest.mock.call(deployment_name="stopped-worker"),
        unittest.mock.call(deployment_name="already-scaled"),
    ]
    assert mocked_scale_up.mock_calls == [unittest.mock.call("stopped-worker", 2)]
    assert mocked_annotate.mock_calls == [
        unittest.mock.call("stopped-worker", {STOPPED_ANNOTATION: None}),
        unittest.mock.call("already-scaled", {STOPPED_ANNOTATION: None}),
    ]


def test_restore_stopped_pods_rearms_hpa_when_expected_scale_is_zero(mocker: MockerFixture) -> None:
    """
    An EDS expectedScale of 0 cannot re-arm an HPA with minReplicas >= 1: restore to 1 instead
    and let the HPA enforce its own minimum.
    """
    kdm = _make_kdm(mocker)
    mocker.patch.object(kdm, "_get_expected_deployment_scale_dict", return_value={0: {"worker": 0}})
    kdm.client_appsv1_api.read_namespaced_deployment.return_value = _make_deployment(
        mocker, {STOPPED_ANNOTATION: "concerned"}, 0
    )
    mocker.patch.object(kdm, "re_enable_hpa")
    mocker.patch.object(kdm, "get_deployment_hpa", return_value=iter([mocker.MagicMock()]))
    mocked_scale_up = mocker.patch.object(kdm, "scale_up_deployment")
    mocker.patch.object(kdm, "annotate_deployment")

    kdm.restore_stopped_pods()

    assert mocked_scale_up.mock_calls == [unittest.mock.call("worker", 1)]
