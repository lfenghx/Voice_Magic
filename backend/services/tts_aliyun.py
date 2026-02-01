import os
import base64
import threading
import queue

try:
    import dashscope
    from dashscope.audio.qwen_tts_realtime import QwenTtsRealtime, QwenTtsRealtimeCallback, AudioFormat
    STREAMING_AVAILABLE = True
except ImportError:
    STREAMING_AVAILABLE = False

from .tts_service import TTSServiceBase


class TTSServiceAliyun(TTSServiceBase):
    def __init__(self):
        super().__init__()

    async def connect(self, websocket, message):
        voice_type = message.get("voice_type", "official")
        voice_name = message.get("voice_name")
        websocket_url = "wss://dashscope.aliyuncs.com/api-ws/v1/realtime"

        if voice_type == "design":
            model = "qwen3-tts-vd-realtime-2025-12-16"
        elif voice_type == "clone":
            model = "qwen3-tts-vc-realtime-2025-11-27"
        elif voice_type == "official":
            model = "qwen3-tts-flash-realtime-2025-11-27"
        else:
            model = "qwen3-tts-flash"

        self.active_connections[websocket] = {
            "model": model,
            "voice_name": voice_name,
            "websocket_url": websocket_url,
            "event_queue": queue.Queue()
        }

        await websocket.send_json({
            "type": "connected",
            "message": "WebSocket连接成功"
        })

    async def synthesize(self, websocket, message):
        if websocket not in self.active_connections:
            await websocket.send_json({
                "type": "error",
                "message": "请先连接"
            })
            return

        config = self.active_connections[websocket]
        text = message.get("text")

        if not text:
            await websocket.send_json({
                "type": "error",
                "message": "请输入文本"
            })
            return

        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            await websocket.send_json({
                "type": "error",
                "message": "未配置API Key"
            })
            return

        dashscope.api_key = api_key

        try:
            event_queue = config["event_queue"]

            class WebSocketCallback(QwenTtsRealtimeCallback):
                def __init__(self, ws, queue):
                    self.ws = ws
                    self.queue = queue

                def on_open(self):
                    pass

                def on_close(self, close_status_code, close_msg):
                    self.queue.put({
                        "type": "error",
                        "message": f"连接异常关闭 ({close_status_code}): {close_msg}"
                    })

                def on_event(self, response):
                    try:
                        event_type = response.get('type', '')
                        if event_type == 'response.audio.delta':
                            audio_data = base64.b64decode(response['delta'])
                            self.queue.put({
                                "type": "audio",
                                "data": base64.b64encode(audio_data).decode()
                            })
                        elif event_type == 'response.done':
                            self.queue.put({"type": "done"})
                        elif event_type == 'session.finished':
                            self.queue.put({"type": "finished"})
                        elif event_type == 'error':
                            self.queue.put({
                                "type": "error",
                                "message": response.get('error').get('message')
                            })
                    except Exception as e:
                        self.queue.put({"type": "error", "message": str(e)})

                def on_error(self, message):
                    self.queue.put({"type": "error", "message": message})

            def run_tts():
                try:
                    callback = WebSocketCallback(websocket, event_queue)

                    qwen_tts_realtime = QwenTtsRealtime(
                        model=config["model"],
                        callback=callback,
                        url=config["websocket_url"]
                    )

                    qwen_tts_realtime.connect()

                    if config["voice_name"]:
                        qwen_tts_realtime.update_session(
                            voice=config["voice_name"],
                            response_format=AudioFormat.PCM_24000HZ_MONO_16BIT,
                            mode='server_commit'
                        )
                    else:
                        qwen_tts_realtime.update_session(
                            response_format=AudioFormat.PCM_24000HZ_MONO_16BIT,
                            mode='server_commit'
                        )

                    qwen_tts_realtime.append_text(text)
                    qwen_tts_realtime.finish()
                except Exception as e:
                    event_queue.put({"type": "error", "message": str(e)})

            thread = threading.Thread(target=run_tts)
            thread.start()

            await websocket.send_json({
                "type": "started"
            })

            while True:
                try:
                    event = event_queue.get(timeout=60)
                    await websocket.send_json(event)

                    if event.get("type") in ["finished", "error"]:
                        break
                except queue.Empty:
                    break

            thread.join(timeout=5)

        except Exception as e:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })

    async def close(self, websocket):
        if websocket in self.active_connections:
            del self.active_connections[websocket]
