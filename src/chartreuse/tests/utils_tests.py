import unittest

import kubernetes.client.rest

from chartreuse.utils import retry_kubernetes_request


class RetryTestCase(unittest.TestCase):
    counter = 0

    def setUp(self):
        self.counter = 0

    def test_no_retry_required(self):
        self.counter = 0

        @retry_kubernetes_request
        def succeeds():
            self.counter += 1
            return "success"

        r = succeeds()

        self.assertEqual(r, "success")
        self.assertEqual(self.counter, 1)

    def test_retries_once(self):
        self.counter = 0

        @retry_kubernetes_request
        def fails_once():
            self.counter += 1
            if self.counter < 2:
                raise kubernetes.client.rest.ApiException("failed")
            else:
                return "success"

        r = fails_once()
        self.assertEqual(r, "success")
        self.assertEqual(self.counter, 2)

    def test_limit_is_reached(self):
        self.counter = 0

        @retry_kubernetes_request
        def always_fails():
            self.counter += 1
            raise kubernetes.client.rest.ApiException("failed")

        with self.assertRaises(kubernetes.client.rest.ApiException):
            always_fails()
        self.assertEqual(self.counter, 2)
