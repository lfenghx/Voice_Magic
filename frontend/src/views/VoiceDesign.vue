<template>
  <div class="voice-design-container">
    <div class="header brand">
      <el-button @click="goBack" circle>
        <el-icon><ArrowLeft /></el-icon>
      </el-button>
      <div class="titles">
        <h1 class="brand-title">元视界AI妙妙屋—魔法语音</h1>
        <div class="sub-title">音色创造</div>
      </div>
      
    </div>
    
    <div class="content">
      <div class="create-section" v-loading="loading" element-loading-text="正在创建音色...">
        <h2>创建新音色</h2>
        <el-form :model="form" label-width="100px">
          <el-form-item label="音色描述">
            <el-input
              v-model="form.voice_prompt"
              type="textarea"
              :rows="3"
              placeholder="例如：温柔的女声，音色甜美，语速适中"
            />
            <div style="margin-top: 10px;">
              <el-button
                type="primary"
                @click="optimizePrompt"
                :loading="optimizing"
                size="small"
              >
                AI润色
              </el-button>
            </div>
          </el-form-item>
          
          <el-form-item label="预览文本">
            <el-input
              v-model="form.preview_text"
              placeholder="你好，这是我的声音。"
            />
          </el-form-item>
          
          <el-form-item label="显示名称">
            <el-input
              v-model="form.display_name"
              placeholder="例如：猫娘、老板、客服小姐姐"
            />
          </el-form-item>
          
          <el-form-item>
            <el-button
              type="primary"
              @click="createVoice"
              :loading="loading"
              size="large"
            >
              创建音色
            </el-button>
          </el-form-item>
        </el-form>
      </div>
      
      <div class="voices-section" v-loading="loading" element-loading-text="正在加载音色...">
        <h2>已创建的音色</h2>
        <div v-if="designVoices.length === 0" class="empty-state">
          <p>暂无音色，请先创建</p>
        </div>
        <div v-else class="voices-grid">
          <div
            v-for="voice in designVoices"
            :key="voice.voice_name"
            class="voice-card"
            :class="{ active: selectedVoice === voice.voice_name }"
            :data-voice="voice.voice_name"
            @click="selectVoice(voice)"
          >
            <div class="voice-header">
              <h3>{{ voice.display_name || voice.voice_name }}</h3>
              <div class="voice-actions">
                <el-button
                  type="primary"
                  size="small"
                  circle
                  @click.stop="previewVoice(voice)"
                >
                  <el-icon><VideoPlay /></el-icon>
                </el-button>
                <el-button
                  type="danger"
                  size="small"
                  circle
                  @click.stop="deleteVoice(voice.voice_name)"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
            <p class="voice-desc">{{ voice.description }}</p>
            <p class="voice-time">创建时间: {{ voice.created_at }}</p>
            <audio
              v-if="voice.preview_file"
              :ref="el => { if (el) audioRefs[voice.voice_name] = el }"
              :src="getPreviewUrl(voice.preview_file)"
              controls
              class="preview-audio"
            />
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
                v-for="voice in designVoices"
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
import { ArrowLeft, Delete, VideoPlay } from '@element-plus/icons-vue'
import { useVoiceStore } from '@/stores/voice'
import api from '@/api'

const router = useRouter()
const voiceStore = useVoiceStore()

const form = ref({
  voice_prompt: '',
  preview_text: '你好，这是我的声音。',
  preferred_name: '',
  display_name: ''
})

const selectedVoice = ref('')
const ttsText = ref('')
const audioUrl = ref('')
const synthesizing = ref(false)
const settingsVisible = ref(false)
const audioRefs = ref({})
const optimizing = ref(false)

const designVoices = computed(() => voiceStore.designVoices)
const loading = computed(() => voiceStore.loading)
const createDesignVoice = voiceStore.createDesignVoice
const deleteDesignVoice = voiceStore.deleteDesignVoice
const loadDesignVoices = voiceStore.loadDesignVoices

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

const goBack = () => {
  router.push('/')
}

const showSettings = () => {}

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

const optimizePrompt = async () => {
  if (!form.value.voice_prompt) {
    ElMessage.warning('请先输入音色描述')
    return
  }
  
  optimizing.value = true
  
  try {
    const response = await api.post('/voice-design/optimize-prompt', {
      prompt: form.value.voice_prompt
    })
    
    form.value.voice_prompt = response.optimized_prompt
    ElMessage.success('提示词优化成功')
  } catch (error) {
    ElMessage.error('提示词优化失败: ' + error.message)
  } finally {
    optimizing.value = false
  }
}

const createVoice = async () => {
  if (!form.value.voice_prompt) {
    ElMessage.warning('请输入音色描述')
    return
  }
  
  try {
    const payload = {
      voice_prompt: form.value.voice_prompt,
      preview_text: form.value.preview_text,
      preferred_name: await toSlug(form.value.display_name || form.value.preferred_name),
      display_name: form.value.display_name || form.value.preferred_name || ''
    }
    await createDesignVoice(payload)
    ElMessage.success('音色创建成功')
    form.value.voice_prompt = ''
    form.value.preferred_name = ''
    form.value.display_name = ''
  } catch (error) {
    ElMessage.error('音色创建失败: ' + error.message)
  }
}

const selectVoice = (voice) => {
  selectedVoice.value = voice.voice_name
}

const deleteVoice = async (voiceName) => {
  try {
    await deleteDesignVoice(voiceName)
    ElMessage.success('音色删除成功')
    if (selectedVoice.value === voiceName) {
      selectedVoice.value = ''
    }
  } catch (error) {
    ElMessage.error('音色删除失败: ' + error.message)
  }
}

const getPreviewUrl = (previewFile) => {
  return `/previews/${encodeURIComponent(previewFile)}`
}

const previewVoice = (voice) => {
  console.log('点击播放按钮，音色:', voice)
  const audio = audioRefs.value[voice.voice_name]
  console.log('音频元素:', audio)
  if (audio) {
    console.log('音频源:', audio.src)
    audio.play().catch(error => {
      console.error('播放失败:', error)
      ElMessage.error('播放失败: ' + error.message)
    })
  } else {
    console.error('找不到音频元素:', voice.voice_name, '所有refs:', audioRefs.value)
    ElMessage.error('找不到音频文件')
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
        voice_type: 'design',
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
  console.log('组件挂载，开始加载音色列表')
  loadDesignVoices()
  console.log('当前音色列表:', designVoices.value)
})
</script>

<style scoped>
.voice-design-container {
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

.create-section,
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

.voices-section {
  max-height: 500px;
  overflow-y: auto;
  padding-right: 10px;
}

.voices-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 15px;
  padding-bottom: 10px;
}

.voices-section::-webkit-scrollbar {
  width: 8px;
}

.voices-section::-webkit-scrollbar-track {
  background: rgba(255, 154, 158, 0.2);
  border-radius: 4px;
}

.voices-section::-webkit-scrollbar-thumb {
  background: rgba(255, 100, 100, 0.5);
  border-radius: 4px;
}

.voices-section::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 100, 100, 0.7);
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

.voice-actions {
  display: flex;
  gap: 5px;
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

.preview-audio {
  width: 100%;
  margin-top: 10px;
}

.audio-player {
  margin-top: 20px;
}

.audio-player audio {
  width: 100%;
}
</style>
