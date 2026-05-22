"""文件上传 API"""
import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from fastapi.responses import JSONResponse

from depends.auth import get_current_user_required
from models.user import User
from utils.rate_limiter import limiter

router = APIRouter(prefix="/upload", tags=["文件上传"])

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp", "svg"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def get_upload_dir() -> str:
    base_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "data", "uploads", "images"
    )
    os.makedirs(base_dir, exist_ok=True)
    return base_dir


@router.post("/image")
@limiter.limit("20/minute")
async def upload_image(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user_required),
):
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: .{ext}，支持: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"文件大小超过限制 ({MAX_FILE_SIZE // 1024 // 1024}MB)")

    filename = f"{uuid.uuid4().hex}.{ext}"
    upload_dir = get_upload_dir()
    filepath = os.path.join(upload_dir, filename)

    with open(filepath, "wb") as f:
        f.write(contents)

    url = f"/data/uploads/images/{filename}"
    return JSONResponse(
        content={"success": True, "filename": filename, "url": url, "size": len(contents)},
        status_code=200,
    )
