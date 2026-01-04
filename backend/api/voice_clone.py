from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional
from services.voice_clone_service import VoiceCloneService
from utils.paths import get_uploads_dir

router = APIRouter()
voice_clone_service = VoiceCloneService()

class CloneVoiceRequest(BaseModel):
    audio_file: str
    preferred_name: Optional[str] = None
    display_name: Optional[str] = None

class VoiceResponse(BaseModel):
    voice_name: str
    description: str
    display_name: str
    audio_file: str
    created_at: str

@router.post("/clone", response_model=dict)
async def clone_voice(
    audio_file: UploadFile = File(...),
    preferred_name: Optional[str] = Form(None),
    display_name: Optional[str] = Form(None)
):
    try:
        upload_dir = get_uploads_dir()
        
        file_path = upload_dir / audio_file.filename
        with open(file_path, "wb") as f:
            content = await audio_file.read()
            f.write(content)
        
        try:
            result = voice_clone_service.clone_voice(
                audio_file=str(file_path),
                preferred_name=preferred_name,
                display_name=display_name
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list", response_model=List[VoiceResponse])
async def list_voices():
    try:
        voices = voice_clone_service.list_voices()
        return voices
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{voice_name}")
async def delete_voice(voice_name: str):
    try:
        success = voice_clone_service.delete_voice(voice_name)
        if success:
            return {"message": "删除成功"}
        else:
            raise HTTPException(status_code=404, detail="音色不存在")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
