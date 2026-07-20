from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, vault, utils, community, square, chat

app = FastAPI(
    title="Campus Square - Auth Engine",
    description="Multi-tenant verification & identity routing for colleges & institutes.",
    version="1.0.0"
)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(auth.router)
app.include_router(vault.router)
app.include_router(utils.router)
app.include_router(community.router)
app.include_router(square.router)
app.include_router(chat.router)

@app.get("/")
def root():
    return {"message" : "Welcome to the Campus Square API"}