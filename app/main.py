from fastapi import Depends, FastAPI

from app.routes import router
from app.security import verify_api_key

app = FastAPI(title="Production Control API")


@app.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(router, dependencies=[Depends(verify_api_key)])