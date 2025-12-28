import os
import json
import base64
import requests
from dotenv import load_dotenv
from utils.storage import VoiceStorage

load_dotenv()

class VoiceDesignService:
    def __init__(self):
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        self.storage = VoiceStorage("data/voices.json")
        self.voice_design_url = "https://dashscope.aliyuncs.com/api/v1/services/audio/tts/customization"
        
        self.target_model = "qwen3-tts-vd-realtime-2025-12-16"
    
    def create_custom_voice(self, voice_prompt, preview_text="你好，这是我的声音。", preferred_name=None, display_name=None):
        if not self.api_key:
            raise ValueError("未找到API Key，请先配置")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "qwen-voice-design",
            "input": {
                "action": "create",
                "target_model": self.target_model,
                "voice_prompt": voice_prompt,
                "language": "zh"
            },
            "parameters": {
                "sample_rate": 24000,
                "response_format": "wav"
            }
        }
        
        if preview_text:
            data["input"]["preview_text"] = preview_text
        
        if preferred_name:
            data["input"]["preferred_name"] = preferred_name
        
        try:
            response = requests.post(self.voice_design_url, headers=headers, json=data, timeout=60)
            
            response.raise_for_status()
            result = response.json()
            
            if result.get("output"):
                voice_name = result["output"].get("voice")
                base64_audio = result["output"]["preview_audio"]["data"]
                audio_bytes = base64.b64decode(base64_audio)
                
                # 增加音频增益（放大音量）
                try:
                    import struct
                    # WAV 头部通常是 44 字节
                    if len(audio_bytes) > 44:
                        header = audio_bytes[:44]
                        pcm_data = audio_bytes[44:]
                        
                        # 16-bit PCM, Little Endian
                        count = len(pcm_data) // 2
                        samples = struct.unpack(f"<{count}h", pcm_data)
                        
                        gain = 5.0 # 与前端保持一致的增益
                        new_samples = []
                        for s in samples:
                            v = int(s * gain)
                            if v > 32767: v = 32767
                            if v < -32768: v = -32768
                            new_samples.append(v)
                            
                        new_pcm_data = struct.pack(f"<{count}h", *new_samples)
                        audio_bytes = header + new_pcm_data
                        print("预览音频增益处理成功")
                except Exception as e:
                    print(f"预览音频增益处理失败: {e}")
                
                preview_filename = f"{voice_name}_preview.wav"
                preview_file = f"previews/{preview_filename}"
                os.makedirs("previews", exist_ok=True)
                with open(preview_file, "wb") as f:
                    f.write(audio_bytes)
                
                self.storage.add_voice(
                    voice_name=voice_name,
                    description=voice_prompt,
                    display_name=display_name or preferred_name or voice_name,
                    preview_file=preview_filename
                )
                
                return {
                    "voice_name": voice_name,
                    "description": voice_prompt,
                    "display_name": display_name or preferred_name or voice_name,
                    "preview_file": preview_filename,
                    "created_at": result.get("created_at", "")
                }
            else:
                raise Exception(f"创建失败: {result}")
                
        except requests.exceptions.RequestException as e:
            print(f"网络请求错误: {e}")
            print(f"响应内容: {response.text if 'response' in locals() else 'N/A'}")
            raise Exception(f"网络请求发生错误: {e}")
        except Exception as e:
            print(f"处理错误: {e}")
            import traceback
            traceback.print_exc()
            raise Exception(f"请求失败: {e}")
    
    def list_voices(self):
        voices = self.storage.list_voices()
        return voices
    
    def delete_voice(self, voice_name):
        return self.storage.delete_voice(voice_name)
    
    def optimize_prompt(self, prompt):
        if not self.api_key:
            raise ValueError("未找到API Key，请先配置")
        
        from dashscope import Generation
        import dashscope
        
        dashscope.base_http_api_url = 'https://dashscope.aliyuncs.com/api/v1'
        
        messages = [
            {"role": "system", "content": "你是一个专业的音色设计助理，负责将用户简洁的音色描述优化为详细、专业的音色设计提示词。优化后的提示词应该包含模仿对象，说清楚年轻范围，性别特征（比如22岁女性，32岁男主播等），音色特质（如甜美、低沉、磁性等）、情感倾向、语音特点（如语速、语调等）等方面的详细描述，以便生成更符合的AI音色。输出要求：仅输出音色描述文本，无需包含其他解释内容"},
            {"role": "user", "content": prompt},
        ]
        
        try:
            response = Generation.call(
                api_key=self.api_key,
                model="qwen-turbo",
                messages=messages,
                result_format="message",
                enable_thinking=False,
            )
            
            if response.status_code == 200:
                return response.output.choices[0].message.content
            else:
                raise Exception(f"优化失败: HTTP {response.status_code}, {response.message}")
                
        except Exception as e:
            print(f"优化提示词错误: {e}")
            raise Exception(f"优化提示词失败: {e}")
