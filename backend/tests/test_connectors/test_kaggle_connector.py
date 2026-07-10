"""Tests for Kaggle dataset connector."""

import pytest

from app.connectors.dataset_connectors import KaggleConnector


@pytest.mark.asyncio
async def test_kaggle_search_without_credentials_returns_empty():
    connector = KaggleConnector(username="", api_key="")
    results = await connector.search("mnist", limit=5)
    assert results == []


@pytest.mark.asyncio
async def test_kaggle_normalize_dataset():
    connector = KaggleConnector(username="u", api_key="k")
    normalized = connector._normalize_dataset({
        "ref": "mnist",
        "ownerRef": "owner",
        "title": "MNIST Handwritten Digits",
        "description": "Classic digit dataset",
        "totalBytes": 1024,
        "tags": [{"name": "computer vision"}],
    })
    assert normalized["id"] == "owner/mnist"
    assert "kaggle.com" in normalized["source_url"]