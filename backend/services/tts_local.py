import os
import torch
import threading
import base64
import numpy as np
from qwen_tts import Qwen3TTSModel
from .tts_service import TTSServiceBase


LOCAL_DIR = os.path.dirname(os.path.abspath(__file__))

class TTSServiceLocal(TTSServiceBase):
    _base_model = None
    _custom_model = None
    _model_lock = threading.Lock()

    def __init__(self):
        super().__init__()
        self._ensure_models_loaded()

    def _ensure_models_loaded(self):
        from qwen_tts import Qwen3TTSModel

        with TTSServiceLocal._model_lock:
            if TTSServiceLocal._base_model is None:
                print("正在预加载本地 TTS 模型（单例模式），请稍候...")

                TTSServiceLocal._base_model = Qwen3TTSModel.from_pretrained(
                    "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
                    device_map="cuda:0",
                    dtype=torch.bfloat16,
                )
                TTSServiceLocal._custom_model = Qwen3TTSModel.from_pretrained(
                    "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
                    device_map="cuda:0",
                    dtype=torch.bfloat16,
                )
                print("本地 TTS 模型预加载完成。")

    @property
    def base_model(self):
        return TTSServiceLocal._base_model

    @property
    def custom_model(self):
        return TTSServiceLocal._custom_model

    async def connect(self, websocket, message):
        print(message)
        voice_type = message.get("voice_type", "official")
        voice_name = message.get("voice_name")

        # 将连接信息存储在 active_connections 中，而不是全局 self.model，
        # 因为可能有多个并发连接
        self.active_connections[websocket] = {
            "voice_type": voice_type,
            "voice_name": voice_name
        }

        await websocket.send_json({
            "type": "connected",
            "message": "本地TTS模型连接成功"
        })

    async def synthesize(self, websocket, message):
        print(message)
        if websocket not in self.active_connections:
            await websocket.send_json({"type": "error", "message": "请先连接"})
            return

        conn_info = self.active_connections[websocket]
        voice_type = conn_info["voice_type"]
        voice_name = conn_info["voice_name"]

        # 同步生成
        try:
            if voice_type == "design" or voice_type == "clone":
                ref_audio = os.path.join(LOCAL_DIR, "../previews", voice_name + "_preview.wav")
                print(ref_audio)
                wavs, sr = self.base_model.generate_voice_clone(
                    text=message.get("text"),
                    language=message.get("language", "auto"),
                    ref_audio=ref_audio,
                    x_vector_only_mode=True,
                )
            elif voice_type == "official":
                # 这是一个简化的示例，实际生成参数请根据 qwen_tts 的 API 调整
                wavs, sr = self.custom_model.generate_custom_voice(
                    text=message.get("text"),
                    language=message.get("language", "auto"),
                    speaker=voice_name,
                    instruct=message.get("instruct", ""),
                )

            # 处理音频数据
            audio_data = wavs
            if isinstance(audio_data, torch.Tensor):
                audio_data = audio_data.cpu().float().numpy()
            elif isinstance(audio_data, list):
                audio_data = np.array(audio_data)

            # 确保已经是 numpy 数组
            if not isinstance(audio_data, np.ndarray):
                 audio_data = np.array(audio_data)

            # 确保是 1D 数组
            if audio_data.ndim > 1:
                audio_data = audio_data.flatten()

            # 转换为 Int16 PCM
            if audio_data.dtype.kind == 'f':
                # 裁剪并归一化到 Int16 范围
                audio_data = np.clip(audio_data, -1.0, 1.0)
                audio_data = (audio_data * 32767).astype(np.int16)

            # 转换为 Base64
            pcm_data = audio_data.tobytes()
            b64_data = base64.b64encode(pcm_data).decode('utf-8')

            # 发送音频数据
            await websocket.send_json({
                "type": "audio",
                "data": b64_data
            })

            # 发送完成信号
            await websocket.send_json({
                "type": "finished",
                "message": "合成完成"
            })
        except Exception as e:
            await websocket.send_json({"type": "error", "message": str(e)})

    async def close(self, websocket):
        pass
