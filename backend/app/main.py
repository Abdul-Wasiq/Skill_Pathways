import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import auth, profiles, opportunities, ai, posts, notifications, connections, search, feed, admin
from app.config import settings
from app.database import init_pool, close_pool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Career, Scholarship & Internship Platform API",
    description="AI-powered career platform backend.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_pool()
    logger.info("Database pool initialized.")


@app.on_event("shutdown")
def on_shutdown():
    close_pool()


# --- Safe error responses (spec §27, §38) — never leak internals -----

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Invalid request data.", "errors": exc.errors()},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Log unexpected failures while returning a safe client response."""
    logger.exception("Unhandled error on %s %s", request.method, request.url)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Something went wrong on our end. Please try again."},
    )


app.include_router(auth.router)
app.include_router(profiles.router)
app.include_router(opportunities.router)
app.include_router(ai.router)
app.include_router(posts.router)
app.include_router(notifications.router)
app.include_router(connections.router)
app.include_router(search.router)
app.include_router(feed.router)
app.include_router(admin.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
