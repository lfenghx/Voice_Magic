from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量必须在导入 api 模块之前，以便 api 模块内部能正确读取配置
load_dotenv()

from api import voice_clone, voice_design, tts, utils
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 在应用启动时初始化 TTS 服务（仅在 worker 进程中运行）
    tts.init_tts_service()
    yield

app = FastAPI(
    title="元视界AI妙妙屋—声音魔法 API",
    description="基于千问3 TTS 的音色创造和音色克隆服务",
    version="1.2.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
PREVIEWS_DIR = BASE_DIR / "previews"
UPLOADS_DIR = BASE_DIR / "uploads"

# 确保文件夹存在
if not PREVIEWS_DIR.exists():
    PREVIEWS_DIR.mkdir(parents=True, exist_ok=True)
if not UPLOADS_DIR.exists():
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/previews", StaticFiles(directory=str(PREVIEWS_DIR)), name="previews")
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

app.include_router(voice_design.router, prefix="/api/voice-design", tags=["音色创造"])
app.include_router(voice_clone.router, prefix="/api/voice-clone", tags=["音色克隆"])
app.include_router(utils.router, prefix="/api/utils", tags=["工具"])
app.include_router(tts.router, prefix="/ws", tags=["TTS WebSocket"])

@app.get("/test-audio/{filename}")
async def test_audio(filename: str):
    file_path = PREVIEWS_DIR / filename
    if os.path.exists(file_path):
        return {"exists": True, "path": str(file_path), "size": os.path.getsize(file_path)}
    else:
        return {"exists": False, "path": str(file_path)}

# 挂载前端静态文件
STATIC_DIR = BASE_DIR / "static"
if STATIC_DIR.exists():
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # 排除 API、WS 和预览路径，让它们由各自的路由处理器处理或返回 404
        if any(full_path.startswith(prefix) for prefix in ["api/", "ws/", "previews/", "uploads/"]):
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=404, content={"detail": "Not Found"})

        # 检查是否请求的是具体的静态文件
        file_path = STATIC_DIR / full_path
        if full_path != "" and file_path.exists() and file_path.is_file():
            return FileResponse(file_path)

        # 默认返回 index.html 支持 Vue Router History 模式
        return FileResponse(STATIC_DIR / "index.html")
else:
    @app.get("/")
    async def root():
        return {"message": "元视界AI妙妙屋—声音魔法 API", "version": "1.2.0"}

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
