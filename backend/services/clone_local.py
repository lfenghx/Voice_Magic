import os
from pathlib import Path
import time

from .clone_service import CloneServiceBase


class CloneServiceLocal(CloneServiceBase):
    def __init__(self):
        super().__init__()

    def clone_voice(self, audio_file, ref_text=None, preferred_name=None, display_name=None):
        file_path = Path(audio_file)
        if not file_path.exists():
            raise FileNotFoundError(f"音频文件不存在: {audio_file}")

        with open(file_path, "rb") as f:
            header = f.read(44)
            if len(header) < 44:
                raise ValueError("音频文件格式不正确")
            sample_rate = int.from_bytes(header[24:28], "little")
            channels = int.from_bytes(header[22:24], "little")
            bits_per_sample = int.from_bytes(header[34:36], "little")
            data_size = int.from_bytes(header[40:44], "little")
            if sample_rate == 0 or channels == 0 or bits_per_sample == 0:
                raise ValueError("音频文件元数据异常")
            duration = data_size / (sample_rate * channels * (bits_per_sample // 8))
            if duration < 1.0:
                raise ValueError("音频过短，请上传至少1秒的音频")

        audio_bytes = file_path.read_bytes()
        save_filename = f"{preferred_name}_cloned.wav"
        save_filepath = f"uploads/{save_filename}"
        os.makedirs("uploads", exist_ok=True)
        with open(save_filepath, "wb") as f:
            f.write(audio_bytes)

        print(ref_text)
        self.storage.add_voice(
            voice_name=preferred_name,
            description="录音克隆",
            display_name=display_name or preferred_name,
            audio_file=save_filename,
            ref_text=ref_text,
        )

        return {
            "voice_name": preferred_name,
            "description": "录音克隆",
            "display_name": display_name or preferred_name,
            "audio_file": save_filename,
            "ref_text": ref_text,
            "created_at": time.time()
        }
