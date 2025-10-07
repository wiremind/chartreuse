# import logging

# from pytest_mock.plugin import MockerFixture

# from .conftest import are_pods_scaled_down, assert_sql_upgraded

# logger = logging.getLogger(__name__)


# # def test_chartreuse_blackbox_post_upgrade(
# #     prepare_container_image_and_helm_chart: MockerFixture,
# #     populate_cluster_with_chartreuse_post_upgrade: MockerFixture,
# #     mocker: MockerFixture,
# # ) -> None:
# #     """
# #     Test chartreuse considered as a blackbox, in post-install,post-upgrade configuration
# #     """
# #     assert_sql_upgraded()
# #     assert not are_pods_scaled_down()


# # def test_chartreuse_blackbox_pre_upgrade(
# #     prepare_container_image_and_helm_chart: MockerFixture,
# #     populate_cluster_with_chartreuse_pre_upgrade: MockerFixture,
# #     mocker: MockerFixture,
# # ) -> None:
# #     """
# #     Test chartreuse considered as a blackbox, in pre-upgrade configuration
# #     """
# #     assert_sql_upgraded()
# #     assert not are_pods_scaled_down()
