from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import uvicorn
import os
import mimetypes

from api import voice_design, voice_clone, tts, utils
from utils.paths import get_dist_dir, get_previews_dir, find_preview_file

app = FastAPI(
    title="元视界AI妙妙屋—声音魔法 API",
    description="基于千问3 TTS 的音色创造和音色克隆服务",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PREVIEWS_DIR = get_previews_dir()
DIST_DIR = get_dist_dir()

@app.get("/previews/{filename}")
async def previews(filename: str):
    path = find_preview_file(filename)
    if not path:
        raise HTTPException(status_code=404, detail="预览音频不存在")
    media_type, _ = mimetypes.guess_type(str(path))
    return FileResponse(path=str(path), media_type=media_type or "application/octet-stream")

# 挂载前端静态文件
if DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="assets")

app.include_router(voice_design.router, prefix="/api/voice-design", tags=["音色创造"])
app.include_router(voice_clone.router, prefix="/api/voice-clone", tags=["音色克隆"])
app.include_router(utils.router, prefix="/api/utils", tags=["工具"])
app.include_router(tts.router, prefix="/ws", tags=["TTS WebSocket"])

@app.get("/test-audio/{filename}")
async def test_audio(filename: str):
    path = find_preview_file(filename)
    if path:
        return {"exists": True, "path": str(path), "size": os.path.getsize(path)}
    return {"exists": False, "path": str(PREVIEWS_DIR / filename)}

@app.get("/")
async def root():
    # 提供前端index.html文件
    if (DIST_DIR / "index.html").exists():
        with open(DIST_DIR / "index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    return {"message": "元视界AI妙妙屋—声音魔法 API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    reload_enabled = os.getenv("VOICEMAGIC_RELOAD") == "1"
    uvicorn_app = "main:app" if reload_enabled else app
    uvicorn.run(uvicorn_app, host="0.0.0.0", port=8000, reload=reload_enabled)
