import os
import time
import torch
import soundfile as sf
import threading
from .design_service import DesignServiceBase


class DesignServiceLocal(DesignServiceBase):
    _design_model = None
    _model_lock = threading.Lock()

    def __init__(self):
        super().__init__()
        self._ensure_models_loaded()

    def _ensure_models_loaded(self):
        from qwen_tts import Qwen3TTSModel

        with DesignServiceLocal._model_lock:
            if DesignServiceLocal._design_model is None:
                print("正在预加载本地 DESIGN 模型（单例模式），请稍候...")

                DesignServiceLocal._design_model = Qwen3TTSModel.from_pretrained(
                    "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
                    device_map="cuda:0",
                    dtype=torch.bfloat16,
                )
                print("本地 DESIGN 模型预加载完成。")

    @property
    def design_model(self):
        return DesignServiceLocal._design_model

    def create_custom_voice(self, voice_prompt, preview_text="你好，这是我的声音。", preferred_name=None, display_name=None):
        wavs, sr = self.design_model.generate_voice_design(
            text=preview_text,
            language="auto",
            instruct=voice_prompt,
        )

        preview_filename = f"{preferred_name}_preview.wav"
        preview_file = f"previews/{preview_filename}"
        os.makedirs("previews", exist_ok=True)
        sf.write(preview_file, wavs[0], sr)

        self.storage.add_voice(
            voice_name=preferred_name,
            description=voice_prompt,
            display_name=display_name or preferred_name,
            preview_file=preview_filename,
            ref_text=preview_text,
        )

        return {
            "voice_name": preferred_name,
            "description": voice_prompt,
            "display_name": display_name or preferred_name,
            "preview_file": preview_filename,
            "created_at": time.time()
        }

    def list_voices(self):
        voices = self.storage.list_voices()
        return voices

    def delete_voice(self, voice_name):
        return self.storage.delete_voice(voice_name)
