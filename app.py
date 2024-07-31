from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.db import Base, engine
from core.routes import blogs


Base.metadata.create_all(engine)

app = FastAPI(
    # title="Readre Blog API",
    # description="api documentation for Readre",
    # version="1.0.0"
)

origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(blogs.blog_router)
