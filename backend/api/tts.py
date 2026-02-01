from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import os
import json

if os.getenv("QWEN3_TTS_ENV") == "aliyun":
    from services.tts_aliyun import TTSServiceAliyun as TTSService
else:
    from services.tts_local import TTSServiceLocal as TTSService


router = APIRouter()
tts_service = None

def init_tts_service():
    global tts_service
    if tts_service is None:
        tts_service = TTSService()
    return tts_service

@router.websocket("/tts/streaming")
async def websocket_tts(websocket: WebSocket):
    await websocket.accept()

    if tts_service is None:
        # Fallback if lifespan didn't run for some reason,
        # though lifespan is the preferred way
        init_tts_service()


    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            action = message.get("action")

            if action == "connect":
                await tts_service.connect(websocket, message)
            elif action == "synthesize":
                await tts_service.synthesize(websocket, message)
            elif action == "close":
                await tts_service.close(websocket)
                break

    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close()
