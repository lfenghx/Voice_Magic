<template>
  <div class="voice-clone-container">
    <div class="header brand">
      <el-button @click="goBack" circle>
        <el-icon><ArrowLeft /></el-icon>
      </el-button>
      <div class="titles">
        <h1 class="brand-title">元视界AI妙妙屋—魔法语音</h1>
        <div class="sub-title">音色克隆</div>
      </div>
      
    </div>
    
    <div class="content">
      <div class="record-section" v-loading="loading" element-loading-text="正在处理...">
        <el-alert
          v-if="!isSecureContext"
          title="录音功能不可用"
          type="error"
          description="检测到当前环境不安全（如非 Localhost 的 HTTP 连接），浏览器已禁用录音功能。请使用 Localhost 或 HTTPS 访问。"
          show-icon
          :closable="false"
          style="margin-bottom: 20px;"
        />
        <h2>录制声音</h2>
        <el-form :model="form" label-width="100px">
          <el-form-item label="克隆来源">
            <el-radio-group v-model="cloneMode">
              <el-radio label="record">录音克隆</el-radio>
              <el-radio label="upload">上传音频克隆</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="录音时长">
            <el-input-number
              v-model="recordDuration"
              :min="1"
              :max="60"
              :step="1"
            />
            <span style="margin-left: 10px">秒</span>
          </el-form-item>
          
          <el-form-item label="显示名称">
            <el-input
              v-model="form.display_name"
              placeholder="例如：猫娘、老板、客服小姐姐"
            />
          </el-form-item>
          
          <template v-if="cloneMode === 'upload'">
            <el-form-item label="上传音频">
              <el-upload
                drag
                :auto-upload="false"
                :show-file-list="false"
                accept="audio/*,video/mp4"
                :on-change="handleUploadChange"
              >
                <i class="el-icon-upload"></i>
                <div class="el-upload__text">拖拽文件到此或点击上传</div>
                <div class="el-upload__tip">支持常见音频格式（wav/mp3/aac等）和mp4</div>
              </el-upload>
            </el-form-item>
          </template>
          
          <el-form-item>
            <el-button
              v-if="cloneMode === 'record' && !isRecording"
              type="primary"
              @click="startRecording"
              size="large"
            >
              <el-icon><Microphone /></el-icon>
              开始录音
            </el-button>
            <el-button
              v-else-if="cloneMode === 'record' && isRecording"
              type="danger"
              @click="stopRecording"
              size="large"
            >
              <el-icon><VideoPause /></el-icon>
              停止录音 ({{ remainingTime }}s)
            </el-button>
          </el-form-item>
        </el-form>
        
        <div v-if="recordedBlob" class="recorded-audio">
          <h3>音频预览</h3>
          <audio :src="recordedUrl" controls />
          <el-button
            type="primary"
            @click="cloneVoice"
            :loading="loading"
            style="margin-top: 10px"
          >
            克隆声音
          </el-button>
        </div>
      </div>
      
      <div class="voices-section" v-loading="loading" element-loading-text="正在加载音色...">
        <h2>已克隆的音色</h2>
        <div v-if="cloneVoices.length === 0" class="empty-state">
          <p>暂无音色，请先录制并克隆</p>
        </div>
        <div v-else class="voices-grid">
          <div
            v-for="voice in cloneVoices"
            :key="voice.voice_name"
            class="voice-card"
            :class="{ active: selectedVoice === voice.voice_name }"
            @click="selectVoice(voice)"
          >
            <div class="voice-header">
              <h3>{{ voice.display_name || voice.voice_name }}</h3>
              <el-button
                type="danger"
                size="small"
                circle
                @click.stop="deleteVoice(voice.voice_name)"
              >
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
            <p class="voice-time">创建时间: {{ voice.created_at }}</p>
          </div>
        </div>
      </div>
      
      <div class="tts-section" v-loading="synthesizing" element-loading-text="正在合成语音...">
        <h2>语音合成</h2>
        <el-form label-width="100px">
          <el-form-item label="选择音色">
            <el-select
              v-model="selectedVoice"
              placeholder="请选择音色"
              style="width: 100%"
            >
              <el-option
                v-for="voice in cloneVoices"
                :key="voice.voice_name"
                :label="voice.display_name || voice.voice_name"
                :value="voice.voice_name"
              />
            </el-select>
          </el-form-item>
          
          <el-form-item label="输入文本">
            <el-input
              v-model="ttsText"
              type="textarea"
              :rows="4"
              placeholder="请输入要转换的文字"
            />
          </el-form-item>
          
          <el-form-item>
            <el-button
              type="primary"
              @click="synthesize"
              :loading="synthesizing"
              :disabled="!selectedVoice || !ttsText"
              size="large"
            >
              生成语音
            </el-button>
          </el-form-item>
        </el-form>
        
        <div v-if="audioUrl" class="audio-player">
          <audio :src="audioUrl" controls autoplay />
        </div>
      </div>
    </div>
    
    
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Delete, Microphone, VideoPause } from '@element-plus/icons-vue'
import { useVoiceStore } from '@/stores/voice'
import api from '@/api'

const router = useRouter()
const voiceStore = useVoiceStore()

const form = ref({
  preferred_name: '',
  display_name: ''
})

const recordDuration = ref(10)
const isRecording = ref(false)
const remainingTime = ref(0)
const recordedBlob = ref(null)
const recordedUrl = ref('')
let mediaRecorder = null
let audioChunks = []
const cloneMode = ref('record')
const isSecureContext = ref(true)

const selectedVoice = ref('')
const ttsText = ref('')
const audioUrl = ref('')
const synthesizing = ref(false)
const settingsVisible = ref(false)

const cloneVoices = computed(() => voiceStore.cloneVoices)
const loading = computed(() => voiceStore.loading)
const cloneVoiceApi = voiceStore.cloneVoice
const deleteCloneVoice = voiceStore.deleteCloneVoice
const loadCloneVoices = voiceStore.loadCloneVoices

const createWavUrl = (chunks) => {
  const gain = 5.0 // 增加增益倍数，原为 1.8
  const total = chunks.reduce((n, c) => n + atob(c).length, 0)
  const raw = new Uint8Array(total)
  let offset = 0
  for (const c of chunks) {
    const b = atob(c)
    const len = b.length
    for (let i = 0; i < len; i++) raw[offset + i] = b.charCodeAt(i)
    offset += len
  }
  const samples = total / 2
  const pcm = new DataView(new ArrayBuffer(total))
  const src = new DataView(raw.buffer)
  let woff = 0
  for (let i = 0; i < samples; i++) {
    const s = src.getInt16(i * 2, true)
    let v = Math.round(s * gain)
    if (v > 32767) v = 32767
    if (v < -32768) v = -32768
    pcm.setInt16(woff, v, true)
    woff += 2
  }
  const header = new ArrayBuffer(44)
  const view = new DataView(header)
  const writeStr = (o, s) => { for (let i = 0; i < s.length; i++) view.setUint8(o + i, s.charCodeAt(i)) }
  const sampleRate = 24000
  const channels = 1
  const bytesPerSample = 2
  const dataSize = total
  writeStr(0, 'RIFF')
  view.setUint32(4, 36 + dataSize, true)
  writeStr(8, 'WAVE')
  writeStr(12, 'fmt ')
  view.setUint32(16, 16, true)
  view.setUint16(20, 1, true)
  view.setUint16(22, channels, true)
  view.setUint32(24, sampleRate, true)
  view.setUint32(28, sampleRate * channels * bytesPerSample, true)
  view.setUint16(32, channels * bytesPerSample, true)
  view.setUint16(34, bytesPerSample * 8, true)
  writeStr(36, 'data')
  view.setUint32(40, dataSize, true)
  const wav = new Uint8Array(44 + dataSize)
  wav.set(new Uint8Array(header), 0)
  wav.set(new Uint8Array(pcm.buffer), 44)
  return URL.createObjectURL(new Blob([wav], { type: 'audio/wav' }))
}

const convertToWav = async (blob) => {
  const arrayBuffer = await blob.arrayBuffer()
  const AudioCtx = window.AudioContext || window.webkitAudioContext
  const audioCtx = new AudioCtx()
  const decoded = await audioCtx.decodeAudioData(arrayBuffer)
  const targetRate = 24000
  const offline = new OfflineAudioContext(1, Math.ceil(decoded.duration * targetRate), targetRate)
  const source = offline.createBufferSource()
  source.buffer = decoded
  source.connect(offline.destination)
  source.start(0)
  const rendered = await offline.startRendering()
  const ch = rendered.getChannelData(0)
  const dataSize = ch.length * 2
  const header = new ArrayBuffer(44)
  const view = new DataView(header)
  const writeStr = (o, s) => { for (let i = 0; i < s.length; i++) view.setUint8(o + i, s.charCodeAt(i)) }
  writeStr(0, 'RIFF')
  view.setUint32(4, 36 + dataSize, true)
  writeStr(8, 'WAVE')
  writeStr(12, 'fmt ')
  view.setUint32(16, 16, true)
  view.setUint16(20, 1, true)
  view.setUint16(22, 1, true)
  view.setUint32(24, targetRate, true)
  view.setUint32(28, targetRate * 2, true)
  view.setUint16(32, 2, true)
  view.setUint16(34, 16, true)
  writeStr(36, 'data')
  view.setUint32(40, dataSize, true)
  const pcm16 = new DataView(new ArrayBuffer(dataSize))
  let offset = 0
  for (let i = 0; i < ch.length; i++) {
    let s = Math.max(-1, Math.min(1, ch[i]))
    pcm16.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true)
    offset += 2
  }
  return new Blob([new Uint8Array(header), new Uint8Array(pcm16.buffer)], { type: 'audio/wav' })
}

const convertFileToWav = async (file) => {
  const arrayBuffer = await file.arrayBuffer()
  const AudioCtx = window.AudioContext || window.webkitAudioContext
  const audioCtx = new AudioCtx()
  const decoded = await audioCtx.decodeAudioData(arrayBuffer)
  const targetRate = 24000
  const offline = new OfflineAudioContext(1, Math.ceil(decoded.duration * targetRate), targetRate)
  const source = offline.createBufferSource()
  source.buffer = decoded
  source.connect(offline.destination)
  source.start(0)
  const rendered = await offline.startRendering()
  const ch = rendered.getChannelData(0)
  const dataSize = ch.length * 2
  const header = new ArrayBuffer(44)
  const view = new DataView(header)
  const writeStr = (o, s) => { for (let i = 0; i < s.length; i++) view.setUint8(o + i, s.charCodeAt(i)) }
  writeStr(0, 'RIFF')
  view.setUint32(4, 36 + dataSize, true)
  writeStr(8, 'WAVE')
  writeStr(12, 'fmt ')
  view.setUint32(16, 16, true)
  view.setUint16(20, 1, true)
  view.setUint16(22, 1, true)
  view.setUint32(24, targetRate, true)
  view.setUint32(28, targetRate * 2, true)
  view.setUint16(32, 2, true)
  view.setUint16(34, 16, true)
  writeStr(36, 'data')
  view.setUint32(40, dataSize, true)
  const pcm16 = new DataView(new ArrayBuffer(dataSize))
  let offset = 0
  for (let i = 0; i < ch.length; i++) {
    let s = Math.max(-1, Math.min(1, ch[i]))
    pcm16.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true)
    offset += 2
  }
  return new Blob([new Uint8Array(header), new Uint8Array(pcm16.buffer)], { type: 'audio/wav' })
}

const handleUploadChange = async (file) => {
  try {
    const raw = file.raw
    if (!raw) return
    const wavBlob = await convertFileToWav(raw)
    recordedBlob.value = wavBlob
    recordedUrl.value = URL.createObjectURL(wavBlob)
    ElMessage.success('音频已加载，准备克隆')
  } catch (e) {
    ElMessage.error('无法解析音频文件，请尝试更换格式')
  }
}

const measureBlobDuration = async (blob) => {
  const arrayBuffer = await blob.arrayBuffer()
  const AudioCtx = window.AudioContext || window.webkitAudioContext
  const audioCtx = new AudioCtx()
  const decoded = await audioCtx.decodeAudioData(arrayBuffer)
  return decoded.duration
}

const goBack = () => {
  router.push('/')
}

const showSettings = () => {
  settingsVisible.value = true
}

const toSlug = async (s) => {
  const isAscii = /^[a-zA-Z0-9\-\s]+$/.test(s || '')
  if (isAscii) {
    const ascii = (s || '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').substring(0, 16)
    return ascii || `v${Date.now()}`
  }
  try {
    const { slug } = await api.post('/utils/pinyin', { text: s || '' })
    return slug || `v${Date.now()}`
  } catch {
    const ascii = (s || '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').substring(0, 16)
    return ascii || `v${Date.now()}`
  }
}

const startRecording = async () => {
  try {
    if (cloneMode.value !== 'record') {
      ElMessage.warning('当前为上传模式，请切换到录音克隆')
      return
    }
    
    // 检查是否为安全上下文（录音功能在非安全上下文如 HTTP + IP 地址下不可用）
    if (window.isSecureContext === false) {
      ElMessage.error('录音功能受浏览器安全策略限制，请使用 http://localhost:3001 或 https 协议访问')
      return
    }
    
    // 检查浏览器是否支持mediaDevices API
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      // 处理不支持的情况
      if (navigator.getUserMedia) {
        // 旧版浏览器支持方式
        navigator.getUserMedia({ audio: true }, 
          (stream) => {
            handleMediaStream(stream)
          },
          (error) => {
            ElMessage.error('无法访问麦克风: ' + error.message)
          }
        )
      } else {
        ElMessage.error('您的浏览器不支持录音功能，请尝试使用最新版本的Chrome、Firefox或Edge浏览器')
      }
      return
    }
    
    // 现代浏览器支持方式
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    handleMediaStream(stream)
    
  } catch (error) {
    ElMessage.error('无法访问麦克风: ' + error.message)
  }
}

// 处理媒体流的辅助函数
const handleMediaStream = (stream) => {
  mediaRecorder = new MediaRecorder(stream)
  audioChunks = []
  
  mediaRecorder.ondataavailable = (event) => {
    audioChunks.push(event.data)
  }
  
  mediaRecorder.onstop = () => {
    recordedBlob.value = new Blob(audioChunks, { type: 'audio/wav' })
    recordedUrl.value = URL.createObjectURL(recordedBlob.value)
    stream.getTracks().forEach(track => track.stop())
  }
  
  mediaRecorder.start()
  isRecording.value = true
  remainingTime.value = recordDuration.value
  
  const timer = setInterval(() => {
    remainingTime.value--
    if (remainingTime.value <= 0) {
      clearInterval(timer)
      stopRecording()
    }
  }, 1000)
}

const stopRecording = () => {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop()
  }
  isRecording.value = false
}

const cloneVoice = async () => {
  if (!recordedBlob.value) {
    ElMessage.warning('请先选择或录制音频')
    return
  }
  
  const seconds = await measureBlobDuration(recordedBlob.value)
  if (seconds < 1) {
    ElMessage.error('音频过短，请上传至少1秒的音频')
    return
  }
  
  const formData = new FormData()
  const wavBlob = await convertToWav(recordedBlob.value)
  formData.append('audio_file', wavBlob, 'recorded.wav')
  formData.append('preferred_name', await toSlug(form.value.display_name || form.value.preferred_name))
  formData.append('display_name', form.value.display_name || form.value.preferred_name || '')
  
  try {
    await cloneVoiceApi(formData)
    ElMessage.success('声音克隆成功')
    form.value.preferred_name = ''
    form.value.display_name = ''
    recordedBlob.value = null
    recordedUrl.value = ''
  } catch (error) {
    const msg = error.response?.data?.detail || error.message || '未知错误'
    ElMessage.error('声音克隆失败: ' + msg)
  }
}

const selectVoice = (voice) => {
  selectedVoice.value = voice.voice_name
}

const deleteVoice = async (voiceName) => {
  try {
    await deleteCloneVoice(voiceName)
    ElMessage.success('音色删除成功')
    if (selectedVoice.value === voiceName) {
      selectedVoice.value = ''
    }
  } catch (error) {
    ElMessage.error('音色删除失败: ' + error.message)
  }
}

const synthesize = async () => {
  if (!selectedVoice.value) {
    ElMessage.warning('请选择音色')
    return
  }
  
  if (!ttsText.value) {
    ElMessage.warning('请输入文本')
    return
  }
  
  synthesizing.value = true
  audioUrl.value = ''
  
  try {
    const wsUrl = `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws/tts/streaming`
    const ws = new WebSocket(wsUrl)
    
    ws.onopen = () => {
      ws.send(JSON.stringify({
        action: 'connect',
        voice_type: 'clone',
        voice_name: selectedVoice.value
      }))
      
      setTimeout(() => {
        ws.send(JSON.stringify({
          action: 'synthesize',
          text: ttsText.value
        }))
      }, 500)
    }
    
    let audioChunks = []
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      if (data.type === 'audio') {
        audioChunks.push(data.data)
      } else if (data.type === 'finished') {
        ws.close()
        audioUrl.value = createWavUrl(audioChunks)
        synthesizing.value = false
      } else if (data.type === 'error') {
        ElMessage.error('语音合成失败: ' + data.message)
        synthesizing.value = false
        ws.close()
      }
    }
    
    ws.onerror = () => {
      ElMessage.error('WebSocket连接失败')
      synthesizing.value = false
    }
    
  } catch (error) {
    ElMessage.error('语音合成失败: ' + error.message)
    synthesizing.value = false
  }
}

onMounted(() => {
  isSecureContext.value = window.isSecureContext
  loadCloneVoices()
})
</script>

<style scoped>
.voice-clone-container {
  min-height: 100vh;
  padding: 20px;
  background: linear-gradient(135deg, #FFE29F 0%, #FFA751 100%);
}

.header {
  display: flex;
  justify-content: left;
  align-items: center;
  margin-bottom: 30px;
  background: white;
  padding: 20px;
  border-radius: 10px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  position: relative;
  height: 100px;
}

.title { display: none; }
.brand .titles { display: flex; flex-direction: column; align-items: center; position: absolute; left: 50%; transform: translateX(-50%); pointer-events: none; }
.brand-title { font-size: 34px; font-weight: 800; color: #ff8c00; letter-spacing: 1px; margin: 0; font-family: 'Comic Sans MS', 'Quicksand', 'Baloo 2', sans-serif; text-shadow: 0 2px 6px rgba(0,0,0,0.08); }
.sub-title { font-size: 22px; font-weight: bold; color: #7a4f1b; margin-top: 6px; font-family: 'Comic Sans MS', 'Quicksand', 'Baloo 2', sans-serif; }
.header .el-button { z-index: 2; }

.content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.record-section,
.voices-section,
.tts-section {
  background: linear-gradient(180deg, #FFFDF2 0%, #FFE6B3 100%);
  padding: 30px;
  border-radius: 15px;
  box-shadow: 0 6px 20px rgba(255, 154, 158, 0.3);
  border: 1px solid rgba(255, 154, 158, 0.3);
}

.tts-section {
  grid-column: 1 / -1;
}

h2 {
  font-size: 28px;
  color: #3a2d18;
  margin-bottom: 20px;
  font-weight: 800;
  text-shadow: 0 1px 4px rgba(255, 167, 81, 0.25);
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #999;
}

.voices-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 15px;
}

.voice-card {
  border: 2px solid #e0e0e0;
  border-radius: 10px;
  padding: 15px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.voice-card:hover {
  border-color: #667eea;
  transform: translateY(-2px);
}

.voice-card.active {
  border-color: #667eea;
  background: #f0f4ff;
}

.voice-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.voice-header h3 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.voice-desc {
  font-size: 14px;
  color: #666;
  margin-bottom: 5px;
}

.voice-time {
  font-size: 12px;
  color: #999;
  margin: 0;
}

.recorded-audio {
  margin-top: 20px;
  padding: 20px;
  background: #f5f5f5;
  border-radius: 10px;
}

.recorded-audio h3 {
  margin: 0 0 10px 0;
  font-size: 16px;
  color: #333;
}

.recorded-audio audio {
  width: 100%;
}

.audio-player {
  margin-top: 20px;
}

.audio-player audio {
  width: 100%;
}
</style>
