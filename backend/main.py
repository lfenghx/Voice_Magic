from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from pathlib import Path

from api import voice_design, voice_clone, tts, utils

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

BASE_DIR = Path(__file__).resolve().parent
PREVIEWS_DIR = BASE_DIR / "previews"

# 确保previews文件夹存在，不存在则创建
if not PREVIEWS_DIR.exists():
    PREVIEWS_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/previews", StaticFiles(directory=str(PREVIEWS_DIR)), name="previews")

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

@app.get("/")
async def root():
    return {"message": "元视界AI妙妙屋—声音魔法 API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
