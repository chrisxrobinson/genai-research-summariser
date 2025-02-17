from fastapi import FastAPI
from mangum import Mangum

app = FastAPI()

@app.get("/research")
def get_research():
    return {"message": "Summarized research content"}

handler = Mangum(app)
