from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.db import Base,engine


Base.metadata.create_all(engine)

app = FastAPI(
  title="Buddy Blog API",
  description="api documentation for buddy-blog",
  version=""
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