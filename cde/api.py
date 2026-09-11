import uuid
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from cde.logging import setup_logging, set_correlation_id
from .routes.beta import beta_router
from .routes.student import student_router
from .routes.admin import admin_router
from .db import db_adapter
from .indexes import ensure_indexes

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not db_adapter.check_replica_set():
        raise RuntimeError("MongoDB must run as a replica set. Refusing to start.")
    ensure_indexes(db_adapter.db)
    yield


app = FastAPI(title="CDE App", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    cid = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    set_correlation_id(cid)
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = cid
    return response


app.include_router(beta_router)
app.include_router(student_router)
app.include_router(admin_router)


@app.get("/")
def read_root():
    return {"message": "Welcome to CDE API"}
