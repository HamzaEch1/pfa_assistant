# api/main.py
import logging
from fastapi import FastAPI, Request, status, Response # Add Response import
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

# Import routers and core components
from .routers import auth as auth_router
from .routers import chat as chat_router
from .routers import admin as admin_router
from .core.config import settings
from .crud.db_utils import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Application Setup ---
app = FastAPI(
    title=settings.PAGE_TITLE + " API",
    description="API backend for the RAG Chatbot application.",
    version="0.1.0",
)

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Event Handlers ---
@app.on_event("startup")
async def startup_event():
    logger.info("Application startup...")
    init_db() # Ensure DB is initialized on startup
    logger.info("Application startup complete.")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown...")
    logger.info("Application shutdown complete.")

# --- Exception Handlers ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Request validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )

# --- Health Check Endpoint ---
# >>> ADD THIS SECTION <<<
@app.get("/health", tags=["Health Check"], status_code=status.HTTP_200_OK)
async def health_check():
    """Simple health check endpoint."""
    logger.debug("Health check endpoint '/health' accessed.")
    # Optionally add checks here (e.g., DB connection) if needed
    return {"status": "healthy"}
# >>> END OF ADDITION <<<

# --- Routers ---
logger.info("Including API routers...")
app.include_router(auth_router.router)
app.include_router(chat_router.router)
app.include_router(admin_router.router)

# --- Root Endpoint ---
@app.get("/", tags=["Root"])
async def read_root():
    logger.debug("Root endpoint '/' accessed.")
    return {"status": "API is running", "version": app.version}

# --- Main execution (for local debugging) ---
if __name__ == "__main__":
    import uvicorn
    logger.info("Running Uvicorn locally for debugging...")
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)