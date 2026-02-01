import os
import json
from pathlib import Path

class VoiceStorage:
    def __init__(self, storage_file):
        self.storage_file = storage_file
        self.voices = self._load_voices()

    def _load_voices(self):
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载音色文件失败: {e}")
                return {}
        return {}

    def _save_voices(self):
        try:
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.voices, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存音色文件失败: {e}")

    def add_voice(self, voice_name, description, display_name=None, preview_file=None, ref_text=None, audio_file=None):
        import time
        self.voices[voice_name] = {
            "description": description,
            "display_name": display_name or "",
            "preview_file": preview_file or "",
            "ref_text": ref_text or "",
            "audio_file": audio_file or "",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self._save_voices()

    def list_voices(self):
        voices_list = []
        for voice_name, info in self.voices.items():
            voices_list.append({
                "voice_name": voice_name,
                "description": info.get('description', ''),
                "display_name": info.get('display_name', ''),
                "preview_file": info.get('preview_file', ''),
                "ref_text": info.get('ref_text', ''),
                "audio_file": info.get('audio_file', ''),
                "created_at": info.get('created_at', '')
            })
        return voices_list

    def delete_voice(self, voice_name):
        if voice_name in self.voices:
            del self.voices[voice_name]
            self._save_voices()
            return True
        return False

class SettingsStorage:
    def __init__(self):
        self.settings_file = "data/settings.json"
        self.settings = self._load_settings()

    def _load_settings(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载设置文件失败: {e}")
                return {}
        return {}

    def _save_settings(self):
        try:
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存设置文件失败: {e}")

    def save_api_key(self, api_key):
        self.settings["api_key"] = api_key
        self._save_settings()

    def get_api_key(self):
        return self.settings.get("api_key", "")

    def save_region(self, region):
        self.settings["region"] = region
        self._save_settings()

    def get_region(self):
        return self.settings.get("region", "beijing")
