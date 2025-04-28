"""
Unit tests for the CloudWatch metrics utility functions
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

# Import the metrics utility functions
from src.utils.metrics import publish_metric, record_lambda_invocation, record_api_call


class TestMetricsUtils(unittest.TestCase):
    """Test CloudWatch metrics utility functions"""

    @patch("src.utils.metrics.cloudwatch.put_metric_data")
    def test_publish_metric_success(self, mock_put_metric):
        """Test publish_metric function - successful case"""
        # Setup mock
        mock_put_metric.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}

        # Execute function
        result = publish_metric("TestMetric", 42.0, "Count")

        # Verify
        mock_put_metric.assert_called_once()
        call_args = mock_put_metric.call_args[1]
        self.assertEqual(call_args["Namespace"], "LkmlAssistant")
        self.assertEqual(call_args["MetricData"][0]["MetricName"], "TestMetric")
        self.assertEqual(call_args["MetricData"][0]["Value"], 42.0)
        self.assertEqual(call_args["MetricData"][0]["Unit"], "Count")
        self.assertTrue(result)

    @patch("src.utils.metrics.cloudwatch.put_metric_data")
    def test_publish_metric_with_dimensions(self, mock_put_metric):
        """Test publish_metric function with dimensions"""
        # Setup mock
        mock_put_metric.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}

        # Execute function with dimensions
        dimensions = [
            {"Name": "Environment", "Value": "dev"},
            {"Name": "FunctionName", "Value": "TestFunction"},
        ]

        result = publish_metric("TestMetric", 42.0, "Count", dimensions=dimensions)

        # Verify
        mock_put_metric.assert_called_once()
        call_args = mock_put_metric.call_args[1]
        self.assertEqual(call_args["MetricData"][0]["Dimensions"], dimensions)
        self.assertTrue(result)

    @patch("src.utils.metrics.cloudwatch.put_metric_data")
    def test_publish_metric_with_custom_namespace(self, mock_put_metric):
        """Test publish_metric function with custom namespace"""
        # Setup mock
        mock_put_metric.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}

        # Execute function with custom namespace
        result = publish_metric("TestMetric", 42.0, "Count", namespace="CustomNamespace")

        # Verify
        mock_put_metric.assert_called_once()
        call_args = mock_put_metric.call_args[1]
        self.assertEqual(call_args["Namespace"], "CustomNamespace")
        self.assertTrue(result)

    @patch("src.utils.metrics.cloudwatch.put_metric_data")
    def test_publish_metric_error(self, mock_put_metric):
        """Test publish_metric function handling errors"""
        # Setup mock to raise exception
        mock_put_metric.side_effect = Exception("Test exception")

        # Execute function
        result = publish_metric("TestMetric", 42.0, "Count")

        # Verify
        mock_put_metric.assert_called_once()
        self.assertFalse(result)

    @patch("src.utils.metrics.publish_metric")
    def test_record_lambda_invocation(self, mock_publish):
        """Test record_lambda_invocation function"""
        # Setup mock
        mock_publish.return_value = True

        # Execute function
        record_lambda_invocation("TestFunction", True, 123.45, 42)

        # Verify
        # Should have 3 calls to publish_metric:
        # 1. Invocations
        # 2. InvocationStatus
        # 3. Duration
        # 4. RecordCount
        self.assertEqual(mock_publish.call_count, 4)

        # Check Invocations metric
        args1, kwargs1 = mock_publish.call_args_list[0]
        self.assertEqual(args1[0], "Invocations")
        self.assertEqual(args1[1], 1)
        self.assertEqual(args1[2], "Count")
        self.assertIn({"Name": "FunctionName", "Value": "TestFunction"}, kwargs1["dimensions"])

        # Check Duration metric
        args3, kwargs3 = mock_publish.call_args_list[2]
        self.assertEqual(args3[0], "Duration")
        self.assertEqual(args3[1], 123.45)
        self.assertEqual(args3[2], "Milliseconds")

        # Check RecordCount metric
        args4, kwargs4 = mock_publish.call_args_list[3]
        self.assertEqual(args4[0], "RecordCount")
        self.assertEqual(args4[1], 42)
        self.assertEqual(args4[2], "Count")

    @patch("src.utils.metrics.publish_metric")
    def test_record_api_call(self, mock_publish):
        """Test record_api_call function"""
        # Setup mock
        mock_publish.return_value = True

        # Execute function
        record_api_call("PatchworkAPI", "/patches", True, 234.56, 200)

        # Verify
        # Should have 3 calls to publish_metric:
        # 1. ApiCalls
        # 2. ApiCallStatus
        # 3. ApiLatency
        # 4. ApiStatusCode
        self.assertEqual(mock_publish.call_count, 4)

        # Check ApiCalls metric
        args1, kwargs1 = mock_publish.call_args_list[0]
        self.assertEqual(args1[0], "ApiCalls")
        self.assertEqual(args1[1], 1)
        self.assertEqual(args1[2], "Count")
        self.assertIn({"Name": "API", "Value": "PatchworkAPI"}, kwargs1["dimensions"])
        self.assertIn({"Name": "Endpoint", "Value": "/patches"}, kwargs1["dimensions"])

        # Check ApiLatency metric
        args3, kwargs3 = mock_publish.call_args_list[2]
        self.assertEqual(args3[0], "ApiLatency")
        self.assertEqual(args3[1], 234.56)
        self.assertEqual(args3[2], "Milliseconds")

        # Check ApiStatusCode metric
        args4, kwargs4 = mock_publish.call_args_list[3]
        self.assertEqual(args4[0], "ApiStatusCode")
        self.assertEqual(args4[1], 1)
        self.assertEqual(args4[2], "Count")
        self.assertIn({"Name": "StatusCode", "Value": "200"}, kwargs4["dimensions"])


if __name__ == "__main__":
    unittest.main()
