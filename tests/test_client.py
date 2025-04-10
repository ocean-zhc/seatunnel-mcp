# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""Tests for the SeaTunnel client."""

import pytest
import httpx
from unittest.mock import patch, MagicMock

from src.seatunnel_mcp.client import SeaTunnelClient


@pytest.fixture
def client():
    """Create a client for testing."""
    return SeaTunnelClient(base_url="http://localhost:8090", api_key="test_key")


def test_init(client):
    """Test client initialization."""
    assert client.base_url == "http://localhost:8090"
    assert client.api_key == "test_key"
    assert client.headers == {
        "Content-Type": "application/json",
        "Authorization": "Bearer test_key",
    }


def test_get_connection_settings(client):
    """Test get_connection_settings."""
    settings = client.get_connection_settings()
    assert settings == {
        "url": "http://localhost:8090",
        "has_api_key": True,
    }


def test_update_connection_settings(client):
    """Test update_connection_settings."""
    settings = client.update_connection_settings(
        url="http://new-host:8090",
        api_key="new_key",
    )
    assert client.base_url == "http://new-host:8090"
    assert client.api_key == "new_key"
    assert client.headers["Authorization"] == "Bearer new_key"
    assert settings == {
        "url": "http://new-host:8090",
        "has_api_key": True,
    }


@patch("httpx.Client")
def test_submit_job(mock_client, client):
    """Test submit_job."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"jobId": "123"}
    mock_response.raise_for_status.return_value = None

    mock_client_instance = MagicMock()
    mock_client_instance.request.return_value = mock_response
    mock_client.return_value.__enter__.return_value = mock_client_instance

    job_content = "env { job.mode = \"batch\" }"
    result = client.submit_job(
        job_content=job_content,
        jobName="test_job",
        format="hocon",
    )

    mock_client_instance.request.assert_called_once_with(
        "POST",
        "http://localhost:8090/submit-job",
        headers={
            "Content-Type": "text/plain",
            "Authorization": "Bearer test_key",
        },
        params={"jobName": "test_job", "format": "hocon"},
        content=job_content,
    )
    
    assert result == {"jobId": "123"}


@patch("httpx.Client")
def test_submit_jobs(mock_client, client):
    """Test submit_jobs."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"jobIds": ["123", "456"]}
    mock_response.raise_for_status.return_value = None

    mock_client_instance = MagicMock()
    mock_client_instance.request.return_value = mock_response
    mock_client.return_value.__enter__.return_value = mock_client_instance

    # 直接作为请求体的任意数据
    request_body = [
        {
            "params": {"jobId": "123", "jobName": "job-1"},
            "env": {"job.mode": "batch"},
            "source": [{"plugin_name": "FakeSource", "plugin_output": "fake"}],
            "transform": [],
            "sink": [{"plugin_name": "Console", "plugin_input": ["fake"]}]
        },
        {
            "params": {"jobId": "456", "jobName": "job-2"},
            "env": {"job.mode": "batch"},
            "source": [{"plugin_name": "FakeSource", "plugin_output": "fake"}],
            "transform": [],
            "sink": [{"plugin_name": "Console", "plugin_input": ["fake"]}]
        }
    ]
    
    result = client.submit_jobs(request_body=request_body)

    mock_client_instance.request.assert_called_once_with(
        "POST",
        "http://localhost:8090/submit-jobs",
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer test_key",
        },
        json=request_body,
    )
    
    assert result == {"jobIds": ["123", "456"]}


@patch("httpx.Client")
def test_submit_job_upload(mock_client, client):
    """Test submit_job_upload."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"jobId": "123"}
    mock_response.raise_for_status.return_value = None

    mock_client_instance = MagicMock()
    mock_client_instance.request.return_value = mock_response
    mock_client.return_value.__enter__.return_value = mock_client_instance

    # Mock file-like object
    config_file = MagicMock()
    config_file.name = "test_job.conf"
    
    result = client.submit_job_upload(
        config_file=config_file,
        jobName="test_job",
    )

    mock_client_instance.request.assert_called_once_with(
        "POST",
        "http://localhost:8090/submit-job/upload",
        headers={
            "Authorization": "Bearer test_key",
        },
        params={"jobName": "test_job"},
        files={'config_file': config_file},
    )
    
    assert result == {"jobId": "123"}


@patch("httpx.Client")
def test_submit_job_upload_json(mock_client, client):
    """Test submit_job_upload with JSON file."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"jobId": "123"}
    mock_response.raise_for_status.return_value = None

    mock_client_instance = MagicMock()
    mock_client_instance.request.return_value = mock_response
    mock_client.return_value.__enter__.return_value = mock_client_instance

    # Mock file-like object with json extension
    config_file = MagicMock()
    config_file.name = "test_job.json"
    
    result = client.submit_job_upload(
        config_file=config_file,
        jobName="test_job",
        format="json",  # Explicitly specify format
    )

    mock_client_instance.request.assert_called_once_with(
        "POST",
        "http://localhost:8090/submit-job/upload",
        headers={
            "Authorization": "Bearer test_key",
        },
        params={"jobName": "test_job", "format": "json"},
        files={'config_file': config_file},
    )
    
    assert result == {"jobId": "123"}


@patch("httpx.Client")
@patch("builtins.open")
def test_submit_job_upload_path(mock_open, mock_client, client):
    """Test submit_job_upload with a file path."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"jobId": "123"}
    mock_response.raise_for_status.return_value = None

    mock_client_instance = MagicMock()
    mock_client_instance.request.return_value = mock_response
    mock_client.return_value.__enter__.return_value = mock_client_instance
    
    # Mock the file object returned by open()
    mock_file = MagicMock()
    mock_open.return_value = mock_file
    
    file_path = "/path/to/test_job.conf"
    result = client.submit_job_upload(
        config_file=file_path,
        jobName="test_job",
        jobId="987654321",
    )

    # Check that open was called with the file path
    mock_open.assert_called_once_with(file_path, 'rb')
    
    # Check that the request was made with the proper parameters
    mock_client_instance.request.assert_called_once_with(
        "POST",
        "http://localhost:8090/submit-job/upload",
        headers={
            "Authorization": "Bearer test_key",
        },
        params={"jobName": "test_job", "jobId": "987654321"},
        files={'config_file': mock_file},
    )
    
    # Verify the mock file was closed after the request
    mock_file.close.assert_called_once()
    
    assert result == {"jobId": "123"} 