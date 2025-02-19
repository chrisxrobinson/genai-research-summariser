from uuid import UUID

from fastapi import FastAPI, HTTPException
from mangum import Mangum
from pydantic import BaseModel

from .database import storage


class ResearchCreate(BaseModel):
    title: str
    content: str


app = FastAPI()


@app.get("/research")
async def list_research():
    # Implement DynamoDB scan/query here
    pass


@app.get("/research/{research_id}")
async def get_research(research_id: UUID):
    item = await storage.get_item(str(research_id))
    if not item:
        raise HTTPException(status_code=404, detail="Research not found")
    return item


@app.post("/research")
async def add_research(research: ResearchCreate):
    research_id = str(UUID())
    item = {
        "id": research_id,
        "title": research.title,
        "content": research.content,
    }
    await storage.put_item(item)
    return item


handler = Mangum(app)
