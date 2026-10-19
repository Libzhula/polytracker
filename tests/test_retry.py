import unittest

from polytracker_showcase.ingestion import (
    RetryPolicy,
    is_retryable_status,
    retry_delay_seconds,
)


class RetryPolicyTests(unittest.TestCase):
    def test_retryable_status_classification(self):
        self.assertTrue(is_retryable_status(429))
        self.assertTrue(is_retryable_status(503))
        self.assertFalse(is_retryable_status(400))
        self.assertFalse(is_retryable_status(404))

    def test_exponential_delay_has_lower_and_upper_boundaries(self):
        policy = RetryPolicy(base_seconds=0.5, max_seconds=2.0)

        self.assertEqual(retry_delay_seconds(-1, policy), 0.5)
        self.assertEqual(retry_delay_seconds(0, policy), 0.5)
        self.assertEqual(retry_delay_seconds(1, policy), 1.0)
        self.assertEqual(retry_delay_seconds(2, policy), 2.0)
        self.assertEqual(retry_delay_seconds(20, policy), 2.0)

    def test_retry_after_is_clamped_to_policy(self):
        policy = RetryPolicy(base_seconds=1.0, max_seconds=5.0)

        self.assertEqual(retry_delay_seconds(0, policy, retry_after_seconds=-3), 0.0)
        self.assertEqual(retry_delay_seconds(0, policy, retry_after_seconds=3.5), 3.5)
        self.assertEqual(retry_delay_seconds(0, policy, retry_after_seconds=10), 5.0)

    def test_invalid_policy_bounds_are_rejected(self):
        with self.assertRaises(ValueError):
            RetryPolicy(max_attempts=0)
        with self.assertRaises(ValueError):
            RetryPolicy(base_seconds=-1)
        with self.assertRaises(ValueError):
            RetryPolicy(base_seconds=2, max_seconds=1)
