from fastapi import FastAPI

from src.routers import upload
from src.routers import chat
from src.routers import generate_coverletter
from src.routers import ws_chat

# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins =["http://localhost:5173"],
    allow_credentials = True,
    allow_methods=["*"],
    allow_headers = ["*"],
)

app.include_router(upload.router)
app.include_router(chat.router)
app.include_router(generate_coverletter.router)
app.include_router(ws_chat.router)

@app.get("/")
def read_root():
    return {"msg" : "Server is running"}