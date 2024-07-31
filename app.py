from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.db import Base,engine
from core.routers.blogs import blog_router


Base.metadata.create_all(engine)

app = FastAPI(
  title="Buddy Blog API",
  description="api documentation for buddy-blog",
  version="1.0.0",
  root_path="/api"
)

origins = [
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(blog_router)