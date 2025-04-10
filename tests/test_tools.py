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

"""Tests for the SeaTunnel MCP tools."""

import pytest
from unittest.mock import MagicMock

from src.seatunnel_mcp.client import SeaTunnelClient
from src.seatunnel_mcp.tools import (
    get_connection_settings_tool,
    update_connection_settings_tool,
    submit_job_tool,
    submit_job_upload_tool,
    submit_jobs_tool,
    stop_job_tool,
    get_job_info_tool,
    get_running_job_tool,
    get_running_jobs_tool,
    get_finished_jobs_tool,
    get_overview_tool,
    get_system_monitoring_information_tool,
    get_all_tools,
)


@pytest.fixture
def mock_client():
    """Create a mock client for testing."""
    client = MagicMock(spec=SeaTunnelClient)
    client.get_connection_settings.return_value = {
        "url": "http://localhost:8090",
        "has_api_key": True,
    }
    client.update_connection_settings.return_value = {
        "url": "http://new-host:8090",
        "has_api_key": True,
    }
    client.submit_job.return_value = {"jobId": "123"}
    client.submit_job_upload.return_value = {"jobId": "123"}
    client.submit_jobs.return_value = {"jobIds": ["123", "456"]}
    client.stop_job.return_value = {"status": "success"}
    client.get_job_info.return_value = {"jobId": "123", "status": "RUNNING"}
    client.get_running_job.return_value = {"jobId": "123", "status": "RUNNING"}
    client.get_running_jobs.return_value = {"jobs": [{"jobId": "123", "status": "RUNNING"}]}
    client.get_finished_jobs.return_value = {"jobs": [{"jobId": "456", "status": "FINISHED"}]}
    client.get_overview.return_value = {"cluster": "info"}
    client.get_system_monitoring_information.return_value = {"system": "info"}
    return client


@pytest.mark.asyncio
async def test_get_connection_settings_tool(mock_client):
    """Test get_connection_settings_tool."""
    tool = get_connection_settings_tool(mock_client)
    assert tool.name == "get-connection-settings"
    result = await tool.fn()
    mock_client.get_connection_settings.assert_called_once()
    assert result == {
        "url": "http://localhost:8090",
        "has_api_key": True,
    }


@pytest.mark.asyncio
async def test_update_connection_settings_tool(mock_client):
    """Test update_connection_settings_tool."""
    tool = update_connection_settings_tool(mock_client)
    assert tool.name == "update-connection-settings"
    result = await tool.fn(url="http://new-host:8090", api_key="new_key")
    mock_client.update_connection_settings.assert_called_once_with(
        url="http://new-host:8090", api_key="new_key"
    )
    assert result == {
        "url": "http://new-host:8090",
        "has_api_key": True,
    }


@pytest.mark.asyncio
async def test_submit_job_tool(mock_client):
    """Test submit_job_tool."""
    tool = submit_job_tool(mock_client)
    assert tool.name == "submit-job"
    job_content = "env { job.mode = \"batch\" }"
    result = await tool.fn(
        job_content=job_content,
        jobName="test_job",
        format="hocon",
    )
    mock_client.submit_job.assert_called_once_with(
        job_content=job_content,
        jobName="test_job",
        jobId=None,
        isStartWithSavePoint=None,
        format="hocon",
    )
    assert result == {"jobId": "123"}


@pytest.mark.asyncio
async def test_submit_job_upload_tool(mock_client):
    """Test submit_job_upload_tool."""
    tool = submit_job_upload_tool(mock_client)
    assert tool.name == "submit-job-upload"
    
    # Mock file-like object
    config_file = MagicMock()
    config_file.name = "test_job.conf"
    
    result = await tool.fn(
        config_file=config_file,
        jobName="test_job",
    )
    mock_client.submit_job_upload.assert_called_once_with(
        config_file=config_file,
        jobName="test_job",
        jobId=None,
        isStartWithSavePoint=None,
        format=None,
    )
    assert result == {"jobId": "123"}


@pytest.mark.asyncio
async def test_submit_job_upload_tool_path(mock_client):
    """Test submit_job_upload_tool with a file path."""
    tool = submit_job_upload_tool(mock_client)
    assert tool.name == "submit-job-upload"
    
    file_path = "/path/to/config.conf"
    result = await tool.fn(
        config_file=file_path,
        jobName="test_job",
        jobId="987654321",
    )
    mock_client.submit_job_upload.assert_called_once_with(
        config_file=file_path,
        jobName="test_job",
        jobId="987654321",
        isStartWithSavePoint=None,
        format=None,
    )
    assert result == {"jobId": "123"}


@pytest.mark.asyncio
async def test_submit_jobs_tool(mock_client):
    """Test submit_jobs_tool."""
    # Set up return value for submit_jobs
    mock_client.submit_jobs.return_value = {"jobIds": ["123", "456"]}
    
    # Create the tool
    tool = submit_jobs_tool(mock_client)
    assert tool.name == "submit-jobs"
    
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
    
    # Call the tool
    result = await tool.fn(request_body=request_body)
    
    # Verify the client method was called correctly
    mock_client.submit_jobs.assert_called_once_with(request_body=request_body)
    
    # Check the result
    assert result == {"jobIds": ["123", "456"]}


@pytest.mark.asyncio
async def test_stop_job_tool(mock_client):
    """Test stop_job_tool."""
    tool = stop_job_tool(mock_client)
    assert tool.name == "stop-job"
    result = await tool.fn(jobId="123")
    mock_client.stop_job.assert_called_once_with(jobId="123")
    assert result == {"status": "success"}


def test_get_all_tools(mock_client):
    """Test get_all_tools."""
    tools = get_all_tools(mock_client)
    assert len(tools) == 12
    tool_names = [tool.__name__ for tool in tools]
    assert "get-connection-settings" in tool_names
    assert "update-connection-settings" in tool_names
    assert "submit-job" in tool_names
    assert "submit-jobs" in tool_names
    assert "stop-job" in tool_names
    assert "get-job-info" in tool_names
    assert "get-running-job" in tool_names
    assert "get-running-jobs" in tool_names
    assert "get-finished-jobs" in tool_names
    assert "get-overview" in tool_names
    assert "get-system-monitoring-information" in tool_names 