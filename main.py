from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

app = FastAPI()


@app.get("/repos/{github_user}/{github_repo}/starneighbours")
async def root():
    return {"message": "Hello World"}
