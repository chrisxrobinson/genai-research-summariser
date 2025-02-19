from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

from app.database import Storage
from app.research_service import (
    ResearchCreate,
    create_research_item,
    get_research_item_by_id,
)


@pytest.fixture
def mock_storage():
    # Create a mock storage instance with a test table name
    storage = Storage(table_name="test-table", bucket_name="test-bucket")

    # Mock the DynamoDB table operations
    storage.table = MagicMock()
    storage.table.get_item = MagicMock()
    storage.table.put_item = MagicMock()

    # Make the methods async
    storage.get_item = AsyncMock(side_effect=storage.get_item)
    storage.put_item = AsyncMock(side_effect=storage.put_item)

    return storage


@pytest.mark.asyncio
async def test_create_research_item(mock_storage):
    with patch("app.research_service.storage", mock_storage):
        research = ResearchCreate(
            title="Test Research", abstract="Test abstract content"
        )
        item = await create_research_item(research)
        assert item.title == "Test Research"
        assert item.abstract == "Test abstract content"
        assert UUID(item.id)  # Verify ID is valid UUID


@pytest.mark.asyncio
async def test_get_research_item_by_id(mock_storage):
    with patch("app.research_service.storage", mock_storage):
        # First create an item
        research = ResearchCreate(
            title="Find Me", abstract="Find this abstract"
        )
        created_item = await create_research_item(research)

        # Then try to retrieve it
        found_item = await get_research_item_by_id(UUID(created_item.id))
        assert found_item is not None
        assert found_item.title == "Find Me"
        assert found_item.abstract == "Find this abstract"


@pytest.mark.asyncio
async def test_get_nonexistent_research_item(mock_storage):
    with patch("app.research_service.storage", mock_storage):
        result = await get_research_item_by_id(
            UUID("00000000-0000-0000-0000-000000000000")
        )
        assert result is None
