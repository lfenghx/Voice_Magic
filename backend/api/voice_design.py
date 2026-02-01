import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

if os.getenv("QWEN3_TTS_ENV") == "aliyun":
    from services.design_aliyun import DesignServiceAliyun as VoiceDesignService
else:
    from services.design_local import DesignServiceLocal as VoiceDesignService


router = APIRouter()
voice_design_service = VoiceDesignService()

class CreateVoiceRequest(BaseModel):
    voice_prompt: str
    preview_text: Optional[str] = "你好，这是我的声音。"
    preferred_name: Optional[str] = None
    display_name: Optional[str] = None

class VoiceResponse(BaseModel):
    voice_name: str
    description: str
    display_name: str
    preview_file: str
    ref_text: str
    created_at: str

@router.post("/create", response_model=dict)
async def create_voice(request: CreateVoiceRequest):
    try:
        result = voice_design_service.create_custom_voice(
            voice_prompt=request.voice_prompt,
            preview_text=request.preview_text,
            preferred_name=request.preferred_name,
            display_name=request.display_name
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list", response_model=List[VoiceResponse])
async def list_voices():
    try:
        voices = voice_design_service.list_voices()
        return voices
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{voice_name}")
async def delete_voice(voice_name: str):
    try:
        success = voice_design_service.delete_voice(voice_name)
        if success:
            return {"message": "删除成功"}
        else:
            raise HTTPException(status_code=404, detail="音色不存在")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class OptimizePromptRequest(BaseModel):
    prompt: str

@router.post("/optimize-prompt", response_model=dict)
async def optimize_prompt(request: OptimizePromptRequest):
    try:
        optimized_prompt = voice_design_service.optimize_prompt(request.prompt)
        return {"optimized_prompt": optimized_prompt}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
