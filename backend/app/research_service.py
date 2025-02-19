from typing import List, Optional, Tuple
from uuid import UUID, uuid4

from pydantic import BaseModel

from .database import storage


class ResearchItem(BaseModel):
    id: str
    title: str
    abstract: str
    summary: Optional[str] = None
    opportunities: Optional[str] = None


class ResearchCreate(BaseModel):
    title: str
    abstract: str


async def summarize_research(text: str) -> Tuple[str, str]:
    # Simulate AI summarization - replace with actual OpenAI call
    summary = f"Summary of: {text[:100]}..."
    opportunities = "Key opportunities identified from the research..."
    return summary, opportunities


async def create_research_item(research: ResearchCreate) -> ResearchItem:
    research_id = str(uuid4())
    summary, opportunities = await summarize_research(research.abstract)

    item = {
        "id": research_id,
        "title": research.title,
        "abstract": research.abstract,
        "summary": summary,
        "opportunities": opportunities,
    }

    await storage.put_item(item)
    return ResearchItem(**item)


async def get_all_research_items() -> List[ResearchItem]:
    # TODO: Implement DynamoDB scan operation
    return []


async def get_research_item_by_id(research_id: UUID) -> Optional[ResearchItem]:
    item_data = await storage.get_item(str(research_id))
    if not item_data:
        return None
    return ResearchItem(**item_data)
