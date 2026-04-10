"""
AI产业集群空间服务系统主API路由
统一暴露所有服务的API端点 following API design specification
"""

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

# Import the unified v1 API routes
from apps.api.water_v1 import router as water_router
from apps.api.v1.meeting import router as meeting_router
from apps.api.v1.system import router as system_router

# Create main application
app = FastAPI(
    title="AI产业集群空间服务系统 API",
    description="统一的办公空间服务平台API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production should restrict specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create v1 version router
v1_router = APIRouter(prefix="/api/v1")

# Register all service routes to v1 version with proper prefixes
v1_router.include_router(water_router, tags=["水站服务"])
v1_router.include_router(meeting_router, tags=["会议室服务"])
v1_router.include_router(system_router, tags=["系统服务"])

# Add v1 router to main app
app.include_router(v1_router)

# Mount static files for portal and shared resources
portal_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "portal")
shared_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "shared")
meeting_frontend_dir = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "apps", "meeting", "frontend"
)

if os.path.exists(portal_dir):
    app.mount("/portal", StaticFiles(directory=portal_dir, html=True), name="portal")

if os.path.exists(shared_dir):
    app.mount("/shared", StaticFiles(directory=shared_dir), name="shared")

if os.path.exists(meeting_frontend_dir):
    app.mount(
        "/meeting-frontend",
        StaticFiles(directory=meeting_frontend_dir, html=True),
        name="meeting-frontend",
    )


@app.get("/")
async def root():
    return {"message": "AI产业集群空间服务系统 API v1.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    from datetime import datetime

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
    }


if __name__ == "__main__":
    import uvicorn
    from datetime import datetime

    uvicorn.run(app, host="0.0.0.0", port=8000)
