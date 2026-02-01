from utils.storage import VoiceStorage


class CloneServiceBase:
    def __init__(self):
        self.storage = VoiceStorage("data/cloned_voices.json")

    def clone_voice(self, audio_file, ref_text=None, preferred_name=None, display_name=None):
        raise NotImplementedError

    def list_voices(self):
        voices = self.storage.list_voices()
        return voices

    def delete_voice(self, voice_name):
        return self.storage.delete_voice(voice_name)
