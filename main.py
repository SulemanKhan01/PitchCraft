from fastapi import FastAPI

from src.routers import upload


app = FastAPI()

app.include_router(upload.router)

@app.get("/")
def read_root():
    return {"msg" : "Server is running"}