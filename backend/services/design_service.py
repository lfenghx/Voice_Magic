from utils.storage import VoiceStorage


class DesignServiceBase:
    def __init__(self):
        self.storage = VoiceStorage("data/voices.json")

    def create_custom_voice(self, voice_prompt, preview_text, preferred_name=None, display_name=None):
        raise NotImplementedError

    def list_voices(self):
        voices = self.storage.list_voices()
        return voices

    def delete_voice(self, voice_name):
        return self.storage.delete_voice(voice_name)

    def optimize_prompt(self, prompt):
        raise NotImplementedError
