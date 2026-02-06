<template>
  <div class="official-voice-container">
    <div class="header brand">
      <el-button @click="goBack" circle>
        <el-icon><ArrowLeft /></el-icon>
      </el-button>
      <div class="titles">
        <h1 class="brand-title">元视界AI妙妙屋—魔法语音</h1>
        <div class="sub-title">官方音色</div>
      </div>
    </div>

    <div class="content">
      <div class="selection-section">
        <h2>选择官方音色</h2>
        <div class="voices-grid">
          <div
            v-for="voice in officialVoices"
            :key="voice.name"
            class="voice-card"
            :class="{ active: selectedVoice === voice.name }"
            @click="selectVoice(voice)"
          >
            <div class="voice-header">
              <div class="voice-icon-wrapper">
                <span class="voice-icon">{{ voice.icon }}</span>
              </div>
              <h3>{{ voice.displayName }}</h3>
            </div>
            <p class="voice-desc">{{ voice.description }}</p>
          </div>
        </div>
      </div>

      <div class="details-section">
        <h2>音色详情</h2>
        <div v-if="selectedVoiceInfo" class="voice-detail-card">
          <div class="detail-header">
            <span class="detail-icon">{{ selectedVoiceInfo.icon }}</span>
            <div class="detail-titles">
              <h3>{{ selectedVoiceInfo.displayName }}</h3>
              <p class="detail-desc">{{ selectedVoiceInfo.description }}</p>
            </div>
          </div>
            <div class="detail-body">
            <div class="info-item">
              <span class="label">语言：</span>
              <span class="value">{{ selectedVoiceInfo.lang }}</span>
            </div>
            <div class="info-item">
              <span class="label">适用场景：</span>
              <span class="value">{{ selectedVoiceInfo.scenarios }}</span>
            </div>
            <div class="info-item">
              <span class="label">音色模型：</span>
              <span class="value">Qwen3-TTS-Flash</span>
            </div>
          </div>
        </div>
        <div v-else class="empty-state">
          <p>请点击左侧卡片选择一个官方音色</p>
        </div>
      </div>

      <div class="tts-section" v-loading="synthesizing" element-loading-text="正在合成语音...">
        <h2>语音合成</h2>
        <el-form label-width="100px">
          <el-row :gutter="20">
            <el-col :span="4">
              <el-form-item label="当前音色">
                <el-tag v-if="selectedVoice" type="success" size="large" effect="dark">
                  {{ selectedVoiceInfo?.icon }} {{ selectedVoiceInfo?.displayName }}
                </el-tag>
                <span v-else style="color: #999;">未选择</span>
              </el-form-item>
            </el-col>
            <el-col :span="20" v-if="!remote_tts_env">
              <el-form-item label="控制指令">
                <el-input
                  v-model="ttsInstruct"
                  placeholder="例如：用特别愤怒的语气说（仅本地模型支持）"
                />
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item label="输入文本">
            <el-input
              v-model="ttsText"
              type="textarea"
              :rows="4"
              placeholder="请输入要转换的文字，例如：你好，欢迎来到元视界AI妙妙屋！"
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
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'

const router = useRouter()

const remote_tts_env = import.meta.env.VITE_QWEN3_TTS_ENV === 'aliyun'

const aliyunVoices = [
  { name: 'cherry', displayName: '芊悦', description: '阳光积极、亲切自然小姐姐', icon: '👩', scenarios: '活力旁白、短视频、对话', lang: '多语言' },
  { name: 'serena', displayName: '苏瑶', description: '温柔小姐姐', icon: '🌙', scenarios: '暖心解说、有声书、客服', lang: '多语言' },
  { name: 'ethan', displayName: '晨煦', description: '阳光、温暖、活力、朝气（北方口音）', icon: '👦', scenarios: '生活Vlog、朝气男声、解说', lang: '多语言' },
  { name: 'chelsie', displayName: '千雪', description: '二次元虚拟女友', icon: '❄️', scenarios: '动漫配音、虚拟助理', lang: '多语言' },
  { name: 'momo', displayName: '茉兔', description: '撒娇搞怪，逗你开心', icon: '🐰', scenarios: '萌系配音、短视频', lang: '多语言' },
  { name: 'vivian', displayName: '十三', description: '拽拽的、可爱的小暴躁', icon: '👧', scenarios: '个性旁白、互动问答', lang: '多语言' },
  { name: 'moon', displayName: '月白', description: '率性帅气的月白', icon: '🌙', scenarios: '冷酷男声、时尚解说', lang: '多语言' },
  { name: 'maia', displayName: '四月', description: '知性与温柔的碰撞', icon: '🌸', scenarios: '散文读办、知性广告', lang: '多语言' },
  { name: 'kai', displayName: '凯', description: '耳朵的一场SPA', icon: '🧔', scenarios: '磁性男声、助眠播报', lang: '多语言' },
  { name: 'nofish', displayName: '不吃鱼', description: '不会翘舌音的设计师男声', icon: '🐟', scenarios: '自然口音、生活记录', lang: '多语言' },
  { name: 'bella', displayName: '萌宝', description: '喝酒不打醉拳的小萝莉', icon: '👧', scenarios: '萌系动画、儿童音色', lang: '多语言' },
  { name: 'jennifer', displayName: '詹妮弗', description: '品牌级、电影质感般美语女声', icon: '🎬', scenarios: '电影解说、高端广告', lang: '多语言' },
  { name: 'ryan', displayName: '甜茶', description: '节奏拉满，戏感炸裂的男声', icon: '🎸', scenarios: '富有感染力的配音', lang: '多语言' },
  { name: 'katerina', displayName: '卡捷琳娜', description: '御姐音色，韵律回味十足', icon: '👠', scenarios: '成熟女声、高端解说', lang: '多语言' },
  { name: 'aiden', displayName: '艾登', description: '精通厨艺的美语大男孩', icon: '👨', scenarios: '美食Vlog、美式男声', lang: '多语言' },
  { name: 'jada', displayName: '上海-阿珍', description: '风风火火的沪上阿姐', icon: '🥟', scenarios: '上海话解说、方言特色', lang: '中文 (上海话)' },
  { name: 'dylan', displayName: '北京-晓东', description: '北京胡同里长大的少年', icon: '👦', scenarios: '北京话对话、京味解说', lang: '中文 (北京话)' },
  { name: 'eric', displayName: '四川-程川', description: '一个跳脱市井的四川成都男子', icon: '🍵', scenarios: '四川话解说、幽默对话', lang: '中文 (四川话)' },
  { name: 'sunny', displayName: '四川-晴儿', description: '甜到你心里的川妹子', icon: '🌶️', scenarios: '四川话配音、萌系女声', lang: '中文 (四川话)' },
  { name: 'rocky', displayName: '粤语-阿强', description: '幽默风趣的阿强，在线陪聊', icon: '🕶️', scenarios: '粤语脱口秀、风趣旁白', lang: '中文 (粤语)' },
  { name: 'kiki', displayName: '粤语-阿清', description: '甜美的港妹闺蜜', icon: '👗', scenarios: '粤语配音、生活Vlog', lang: '中文 (粤语)' }
]

const localVoices = [
  { name: 'vivian', displayName: 'Vivian', description: '有点急躁的年轻女声', icon: '👩', scenarios: '场景配音、情绪化表达', lang: '中文' },
  { name: 'serena', displayName: 'Serena', description: '温柔知性的年轻女声', icon: '🌙', scenarios: '暖心解说、有声书、客服', lang: '中文' },
  { name: 'uncle_fu', displayName: 'Uncle_Fu', description: '低沉浑厚的成熟男声', icon: '🧔‍♂️', scenarios: '纪录片、故事讲述、稳重旁白', lang: '中文' },
  { name: 'dylan', displayName: 'Dylan', description: '清朗自然的北京少男', icon: '👦', scenarios: '生活Vlog、京味儿对话、朝气男声', lang: '中文 (北京话)' },
  { name: 'eric', displayName: 'Eric', description: '活泼微哑的成都男声', icon: '🍵', scenarios: '四川话配音、地道解说、个性化内容', lang: '中文 (四川话)' },
  { name: 'ryan', displayName: 'Ryan', description: '富有节奏驱动感的男声', icon: '🎸', scenarios: '动感广告、热场配音、英文旁白', lang: '英语' },
  { name: 'aiden', displayName: 'Aiden', description: '阳光清亮的美国男声', icon: '👨', scenarios: '美式配音、英语教学、活力旁白', lang: '英语' },
  { name: 'ono_anna', displayName: 'Ono_Anna', description: '俏皮灵动的日本女声', icon: '🌸', scenarios: '动漫配音、日式广告、对话', lang: '日语' },
  { name: 'sohee', displayName: 'Sohee', description: '情感丰富的温暖韩语女声', icon: '🍯', scenarios: '韩语配音、剧情解说、柔美旁白', lang: '韩语' }
]

const officialVoices = ref(remote_tts_env ? aliyunVoices : localVoices)

const selectedVoice = ref('')
const ttsText = ref('')
const ttsInstruct = ref('')
const audioUrl = ref('')
const synthesizing = ref(false)

const selectedVoiceInfo = computed(() => {
  return officialVoices.value.find(v => v.name === selectedVoice.value)
})

const createWavUrl = (chunks) => {
  const gain = 5.0
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
  wav.set(new Uint8Array(pcm.buffer) , 44)
  return URL.createObjectURL(new Blob([wav], { type: 'audio/wav' }))
}

const goBack = () => {
  router.push('/')
}

const selectVoice = (voice) => {
  selectedVoice.value = voice.name
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
        voice_type: 'official',
        voice_name: selectedVoice.value
      }))

      setTimeout(() => {
        ws.send(JSON.stringify({
          action: 'synthesize',
          text: ttsText.value,
          instruct: ttsInstruct.value
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

    ws.onclose = (event) => {
      if (synthesizing.value) {
        ElMessage.error('WebSocket连接已断开')
        synthesizing.value = false
      }
    }

  } catch (error) {
    ElMessage.error('语音合成失败: ' + error.message)
    synthesizing.value = false
  }
}
</script>

<style scoped>
.official-voice-container {
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

.selection-section,
.details-section,
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

.voices-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
}

.voice-card {
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  padding: 10px 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: white;
}

.voice-card:hover {
  border-color: #ff8c00;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 140, 0, 0.2);
}

.voice-card.active {
  border-color: #ff8c00;
  background: #fff8e1;
}

.voice-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.voice-icon-wrapper {
  font-size: 24px;
}

.voice-header h3 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.voice-desc {
  font-size: 13px;
  color: #666;
  margin: 0;
  line-height: 1.4;
}

.details-section {
  display: flex;
  flex-direction: column;
}

.voice-detail-card {
  background: rgba(255, 255, 255, 0.6);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid rgba(255, 140, 0, 0.1);
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.detail-icon {
  font-size: 48px;
}

.detail-titles h3 {
  margin: 0 0 5px 0;
  font-size: 24px;
  color: #3a2d18;
}

.detail-desc {
  margin: 0;
  color: #7a4f1b;
  font-size: 16px;
}

.detail-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-item {
  display: flex;
  font-size: 15px;
}

.info-item .label {
  font-weight: bold;
  color: #3a2d18;
  width: 80px;
}

.info-item .value {
  color: #666;
  flex: 1;
}

.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  font-size: 16px;
}

.audio-player {
  margin-top: 20px;
}

.audio-player audio {
  width: 100%;
}
</style>
