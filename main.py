from fastapi import FastAPI

from src.routers import upload
from src.routers import chat


app = FastAPI()

app.include_router(upload.router)
app.include_router(chat.router)

@app.get("/")
def read_root():
    return {"msg" : "Server is running"}