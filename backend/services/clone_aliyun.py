import os
import json
import base64
import requests
from pathlib import Path

from services.clone_service import CloneServiceBase


class CloneServiceAliyun(CloneServiceBase):
    def __init__(self):
        super().__init__()

        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        self.customization_url = "https://dashscope.aliyuncs.com/api/v1/services/audio/tts/customization"
        self.target_model = "qwen3-tts-vc-realtime-2025-11-27"

    def clone_voice(self, audio_file, ref_text=None, preferred_name=None, display_name=None):
        if not self.api_key:
            raise ValueError("未找到API Key，请先配置")

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

        audio_data = file_path.read_bytes()
        base64_str = base64.b64encode(audio_data).decode()
        data_uri = f"data:audio/wav;base64,{base64_str}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "qwen-voice-enrollment",
            "input": {
                "action": "create",
                "target_model": self.target_model,
                "preferred_name": preferred_name,
                "audio": {"data": data_uri, "format": "wav"}
            }
        }

        try:
            response = requests.post(
                self.customization_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            print(f"克隆接口状态码: {response.status_code}")
            print(f"克隆接口返回: {response.text[:500]}")

            if response.status_code != 200:
                try:
                    error_data = response.json()
                    error_code = error_data.get("code", "")
                    error_msg = error_data.get("message", "")

                    if "Audio.PreprocessError" in error_code or "No segments meet" in error_msg:
                        raise ValueError("音频有效时长不足，请确保录音时长超过5秒且声音清晰（去除静音后需满足时长要求）")

                    raise ValueError(f"克隆失败: {error_msg}")
                except json.JSONDecodeError:
                    response.raise_for_status()

            result = response.json()

            voice_name = result["output"]["voice"]

            self.storage.add_voice(
                voice_name=voice_name,
                description="录音克隆",
                display_name=display_name or preferred_name or voice_name,
                audio_file=audio_file,
                ref_text=ref_text,
            )

            return {
                "voice_name": voice_name,
                "description": "录音克隆",
                "display_name": display_name or preferred_name or voice_name,
                "audio_file": audio_file,
                "ref_text": ref_text,
                "created_at": result.get("created_at", "")
            }

        except ValueError as e:
            raise e
        except requests.exceptions.RequestException as e:
            raise Exception(f"网络请求失败: {e}")
        except Exception as e:
            raise Exception(f"发生错误: {e}")
