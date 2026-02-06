class TTSServiceBase:
    def __init__(self):
        self.active_connections = {}
        self.active_tts = {}

    async def connect(self, websocket, message):
        raise NotImplementedError

    async def synthesize(self, websocket, message):
        raise NotImplementedError

    async def close(self, websocket):
        raise NotImplementedError
