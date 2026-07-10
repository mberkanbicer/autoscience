"""Dataset discovery connectors for research validation."""

import asyncio
from abc import ABC, abstractmethod
from typing import Any

import httpx
import structlog

logger = structlog.get_logger()


class DatasetConnector(ABC):
    """Abstract base for dataset connectors."""

    @abstractmethod
    async def search(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        """Search for datasets."""
        ...

    @abstractmethod
    async def get_dataset(self, identifier: str) -> dict[str, Any] | None:
        """Get detailed dataset info."""
        ...


class KaggleConnector(DatasetConnector):
    """Connector for Kaggle datasets via REST API."""

    def __init__(
        self,
        api_client: httpx.AsyncClient | None = None,
        username: str = "",
        api_key: str = "",
    ):
        self.client = api_client or httpx.AsyncClient()
        self.base_url = "https://www.kaggle.com/api/v1"
        self.username = username
        self.api_key = api_key

    def _auth(self) -> httpx.BasicAuth | None:
        if self.username and self.api_key:
            return httpx.BasicAuth(self.username, self.api_key)
        return None

    async def search(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        """Search Kaggle datasets (requires KAGGLE_USERNAME + KAGGLE_KEY)."""
        if not self._auth():
            return []

        try:
            response = await self.client.get(
                f"{self.base_url}/datasets/list",
                params={"search": query, "page": 1, "pageSize": limit},
                auth=self._auth(),
                timeout=30.0,
            )
            if response.status_code != 200:
                return []
            data = response.json()
            return [self._normalize_dataset(d) for d in data[:limit]]
        except httpx.HTTPStatusError as e:
            logger.error("kaggle_search_http_error", status=e.response.status_code, error=str(e))
            return []
        except httpx.RequestError as e:
            logger.warning("kaggle_search_network_error", error=str(e))
            return []
        except Exception as e:
            logger.error("kaggle_search_failed", error=str(e), exc_info=True)
            return []

    def _normalize_dataset(self, record: dict[str, Any]) -> dict[str, Any]:
        ref = record.get("ref", "") or record.get("datasetSlug", "")
        owner = record.get("ownerRef", "") or record.get("ownerSlug", "")
        identifier = f"{owner}/{ref}" if owner and ref else ref
        tags = [t.get("name", t) if isinstance(t, dict) else str(t) for t in record.get("tags", [])]
        return {
            "id": identifier,
            "name": record.get("title", ref)[:100],
            "description": (record.get("description") or record.get("subtitle") or "")[:500],
            "format": "mixed",
            "size_bytes": record.get("totalBytes", 0) or 0,
            "row_count": 0,
            "column_count": 0,
            "schema_json": {},
            "source_url": f"https://www.kaggle.com/datasets/{identifier}",
            "tags": tags[:10],
        }

    async def get_dataset(self, identifier: str) -> dict[str, Any] | None:
        """Get dataset details from Kaggle."""
        if not self._auth():
            return None
        try:
            response = await self.client.get(
                f"{self.base_url}/datasets/view/{identifier}",
                auth=self._auth(),
                timeout=30.0,
            )
            if response.status_code == 200:
                return self._normalize_dataset(response.json())
        except httpx.HTTPStatusError as e:
            logger.error("kaggle_get_http_error", identifier=identifier, status=e.response.status_code, error=str(e))
        except httpx.RequestError as e:
            logger.warning("kaggle_get_network_error", identifier=identifier, error=str(e))
        except Exception as e:
            logger.error("kaggle_get_failed", identifier=identifier, error=str(e), exc_info=True)
        return None


class HuggingFaceConnector(DatasetConnector):
    """Connector for HuggingFace datasets."""

    def __init__(self, api_client: httpx.AsyncClient | None = None):
        self.client = api_client or httpx.AsyncClient()
        self.base_url = "https://huggingface.co/api/datasets"

    async def search(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        """Search HuggingFace datasets."""
        try:
            response = await self.client.get(
                f"{self.base_url}?search={query}&limit={limit}",
                timeout=30.0,
            )
            if response.status_code == 200:
                data = response.json()
                return [
                    {
                        "id": d.get("id", ""),
                        "name": d.get("id", "").split("/")[-1] if "/" in d.get("id", "") else d.get("id", ""),
                        "description": d.get("description", d.get("cardData", {}).get("summary", ""))[:500],
                        "format": "mixed",
                        "size_bytes": 0,
                        "row_count": d.get("cardData", {}).get("dataset_size", {}).get("rows", 0) if isinstance(d.get("cardData"), dict) else 0,
                        "column_count": 0,
                        "schema_json": d.get("cardData", {}).get("features", {}),
                        "source_url": f"https://huggingface.co/datasets/{d.get('id', '')}",
                        "tags": d.get("tags", [])[:10],
                    }
                    for d in data
                ]
        except httpx.HTTPStatusError as e:
            logger.error("huggingface_search_http_error", status=e.response.status_code, error=str(e))
        except httpx.RequestError as e:
            logger.warning("huggingface_search_network_error", error=str(e))
        except Exception as e:
            logger.error("huggingface_search_failed", error=str(e), exc_info=True)

        return []

    async def get_dataset(self, identifier: str) -> dict[str, Any] | None:
        """Get dataset details from HuggingFace."""
        try:
            response = await self.client.get(
                f"https://huggingface.co/api/datasets/{identifier}",
                timeout=30.0,
            )
            if response.status_code == 200:
                d = response.json()
                return {
                    "id": identifier,
                    "name": d.get("id", "").split("/")[-1] if "/" in d.get("id", "") else d.get("id", ""),
                    "description": d.get("description", "")[:500],
                    "format": "mixed",
                    "size_bytes": d.get("size", {}).get("dataset", 0) if isinstance(d.get("size"), dict) else 0,
                    "row_count": d.get("cardData", {}).get("dataset_size", {}).get("rows", 0) if isinstance(d.get("cardData"), dict) else 0,
                    "column_count": len(d.get("cardData", {}).get("features", {})) if isinstance(d.get("cardData"), dict) else 0,
                    "schema_json": d.get("cardData", {}).get("features", {}),
                    "source_url": f"https://huggingface.co/datasets/{identifier}",
                    "tags": d.get("tags", [])[:10],
                }
        except httpx.HTTPStatusError as e:
            logger.error("huggingface_get_http_error", identifier=identifier, status=e.response.status_code, error=str(e))
        except httpx.RequestError as e:
            logger.warning("huggingface_get_network_error", identifier=identifier, error=str(e))
        except Exception as e:
            logger.error("huggingface_get_failed", identifier=identifier, error=str(e), exc_info=True)

        return None


class ZenodoConnector(DatasetConnector):
    """Connector for Zenodo datasets."""

    def __init__(self, api_client: httpx.AsyncClient | None = None):
        self.client = api_client or httpx.AsyncClient()
        self.base_url = "https://zenodo.org/api"

    async def search(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        """Search Zenodo records."""
        try:
            response = await self.client.get(
                f"{self.base_url}/records",
                params={"q": query, "size": limit, "type": "dataset"},
                timeout=30.0,
            )
            if response.status_code == 200:
                data = response.json()
                return [
                    {
                        "id": str(hit.get("id", "")),
                        "name": hit.get("metadata", {}).get("title", "")[:100],
                        "description": hit.get("metadata", {}).get("description", "")[:500],
                        "format": self._get_format(hit),
                        "size_bytes": hit.get("files", [{}])[0].get("size", 0) if hit.get("files") else 0,
                        "row_count": 0,
                        "column_count": 0,
                        "schema_json": {},
                        "source_url": hit.get("links", {}).get("html", ""),
                        "doi": hit.get("metadata", {}).get("doi", ""),
                    }
                    for hit in data.get("hits", {}).get("hits", [])
                ]
        except httpx.HTTPStatusError as e:
            logger.error("zenodo_search_http_error", status=e.response.status_code, error=str(e))
        except httpx.RequestError as e:
            logger.warning("zenodo_search_network_error", error=str(e))
        except Exception as e:
            logger.error("zenodo_search_failed", error=str(e), exc_info=True)

        return []

    def _get_format(self, record: dict) -> str:
        """Extract format from Zenodo record."""
        files = record.get("files", [])
        if files:
            return files[0].get("type", "unknown")
        return "unknown"

    async def get_dataset(self, identifier: str) -> dict[str, Any] | None:
        """Get Zenodo record details."""
        try:
            response = await self.client.get(
                f"{self.base_url}/records/{identifier}",
                timeout=30.0,
            )
            if response.status_code == 200:
                data = response.json()
                return {
                    "id": identifier,
                    "name": data.get("metadata", {}).get("title", "")[:100],
                    "description": data.get("metadata", {}).get("description", "")[:500],
                    "format": self._get_format(data),
                    "size_bytes": sum(f.get("size", 0) for f in data.get("files", [])) if data.get("files") else 0,
                    "row_count": 0,
                    "column_count": 0,
                    "schema_json": {},
                    "source_url": data.get("links", {}).get("html", ""),
                    "doi": data.get("metadata", {}).get("doi", ""),
                }
        except httpx.HTTPStatusError as e:
            logger.error("zenodo_get_http_error", identifier=identifier, status=e.response.status_code, error=str(e))
        except httpx.RequestError as e:
            logger.warning("zenodo_get_network_error", identifier=identifier, error=str(e))
        except Exception as e:
            logger.error("zenodo_get_failed", identifier=identifier, error=str(e), exc_info=True)

        return None


class DatasetManager:
    """Manages multiple dataset connectors."""

    def __init__(self):
        from app.config import get_settings

        settings = get_settings()
        self.connectors: dict[str, DatasetConnector] = {
            "huggingface": HuggingFaceConnector(),
            "zenodo": ZenodoConnector(),
            "kaggle": KaggleConnector(
                username=settings.kaggle_username,
                api_key=settings.kaggle_key,
            ),
        }

    async def search_all(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        """Search all connectors for datasets."""
        results = []

        async def search_connector(name: str, connector: DatasetConnector):
            try:
                connector_results = await connector.search(query, limit)
                for r in connector_results:
                    r["connector"] = name
            except Exception as e:
                logger.error("dataset_search_failed", connector=name, error=str(e), exc_info=True)
                connector_results = []
            return connector_results

        # Run searches in parallel
        tasks = [search_connector(name, conn) for name, conn in self.connectors.items()]
        all_results = await asyncio.gather(*tasks)

        # Deduplicate and merge
        seen_urls = set()
        for connector_results in all_results:
            for r in connector_results:
                url = r.get("source_url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    results.append(r)

        return results

    async def get_dataset(self, source: str, identifier: str) -> dict[str, Any] | None:
        """Get dataset from specific source."""
        connector = self.connectors.get(source)
        if connector:
            return await connector.get_dataset(identifier)
        return None
