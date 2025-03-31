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

"""SeaTunnel API client for interacting with the REST API."""

import json
import logging
from typing import Dict, List, Any, Optional, Union
import httpx

logger = logging.getLogger(__name__)


class SeaTunnelClient:
    """Client for interacting with the SeaTunnel REST API."""

    def __init__(self, base_url: str, api_key: Optional[str] = None):
        """Initialize the client.

        Args:
            base_url: Base URL of the SeaTunnel REST API.
            api_key: Optional API key for authentication.
        """
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"

    def update_connection_settings(self, url: Optional[str] = None, api_key: Optional[str] = None) -> Dict[str, Any]:
        """Update connection settings.

        Args:
            url: New base URL for the SeaTunnel REST API.
            api_key: New API key for authentication.

        Returns:
            Dict with updated connection settings.
        """
        if url:
            self.base_url = url
        if api_key:
            self.api_key = api_key
            self.headers["Authorization"] = f"Bearer {api_key}" if api_key else None

        return self.get_connection_settings()

    def get_connection_settings(self) -> Dict[str, Any]:
        """Get current connection settings.

        Returns:
            Dict with current connection settings.
        """
        return {
            "url": self.base_url,
            "has_api_key": self.api_key is not None,
        }

    def _make_request(self, method: str, endpoint: str, **kwargs) -> httpx.Response:
        """Make a request to the SeaTunnel API.

        Args:
            method: HTTP method.
            endpoint: API endpoint.
            **kwargs: Additional arguments for the request.

        Returns:
            Response from the API.

        Raises:
            httpx.HTTPStatusError: If the request fails.
        """
        url = f"{self.base_url}{endpoint}"
        headers = kwargs.pop("headers", {})
        headers.update(self.headers)

        try:
            with httpx.Client() as client:
                response = client.request(method, url, headers=headers, **kwargs)
                response.raise_for_status()
                return response
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            raise

    def submit_job(
        self,
        job_content: str,
        jobName: Optional[str] = None,
        jobId: Optional[str] = None,
        isStartWithSavePoint: Optional[bool] = None,
        format: str = "hocon"
    ) -> Dict[str, Any]:
        """Submit a new job.

        Args:
            job_content: Job configuration content.
            jobName: Optional job name.
            jobId: Optional job ID.
            isStartWithSavePoint: Whether to start with savepoint.
            format: Job configuration format (hocon, json, yaml).

        Returns:
            Response from the API.
        """
        params = {}
        if jobName:
            params["jobName"] = jobName
        if jobId:
            params["jobId"] = jobId
        if isStartWithSavePoint is not None:
            params["isStartWithSavePoint"] = str(isStartWithSavePoint).lower()
        if format:
            params["format"] = format

        response = self._make_request(
            "POST",
            "/submit-job",
            params=params,
            content=job_content,
            headers={"Content-Type": "text/plain"}
        )

        return response.json()

    def stop_job(self, jobId: Union[str, int], isStartWithSavePoint: bool = False) -> Dict[str, Any]:
        """Stop a running job.

        Args:
            jobId: Job ID.
            isStartWithSavePoint: Whether to stop with savepoint.

        Returns:
            Response from the API.
        """
        data = {
            "jobId": jobId,
            "isStopWithSavePoint": isStartWithSavePoint
        }
        
        response = self._make_request("POST", "/stop-job", json=data)
        return response.json()

    def get_job_info(self, jobId: Union[str, int]) -> Dict[str, Any]:
        """Get information about a job.

        Args:
            jobId: Job ID.

        Returns:
            Response from the API.
        """
        response = self._make_request("GET", f"/job-info/{jobId}")
        return response.json()

    def get_running_job(self, jobId: Union[str, int]) -> Dict[str, Any]:
        """Get information about a running job.

        Args:
            jobId: Job ID.

        Returns:
            Response from the API.
        """
        response = self._make_request("GET", f"/running-job/{jobId}")
        return response.json()

    def get_running_jobs(self) -> Dict[str, Any]:
        """Get all running jobs.

        Returns:
            Response from the API.
        """
        response = self._make_request("GET", "/running-jobs")
        return response.json()

    def get_finished_jobs(self, state: str) -> Dict[str, Any]:
        """Get all finished jobs by state.

        Args:
            state: Job state (FINISHED, CANCELED, FAILED, UNKNOWABLE).

        Returns:
            Response from the API.
        """
        response = self._make_request("GET", f"/finished-jobs/{state}")
        return response.json()

    def get_overview(self, tags: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Get cluster overview.

        Args:
            tags: Optional tags for filtering.

        Returns:
            Response from the API.
        """
        params = tags or {}
        response = self._make_request("GET", "/overview", params=params)
        return response.json()

    def get_system_monitoring_information(self) -> Dict[str, Any]:
        """Get system monitoring information.

        Returns:
            Response from the API.
        """
        response = self._make_request("GET", "/system-monitoring-information")
        return response.json() 