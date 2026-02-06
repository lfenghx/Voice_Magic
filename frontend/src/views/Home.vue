<template>
  <div class="home-container">
    <div class="header">
      <h1 class="title">元视界AI妙妙屋</h1>
      <p class="subtitle">魔法语音</p>
    </div>

    <div class="content">
      <div class="mode-card" @click="goToVoiceDesign">
        <div class="card-icon">🎨</div>
        <h2 class="card-title">音色创造</h2>
        <p class="card-desc">通过文字描述创造个性化音色</p>
        <div class="card-arrow">→</div>
      </div>

      <div class="mode-card" @click="goToVoiceClone">
        <div class="card-icon">🎤</div>
        <h2 class="card-title">音色克隆</h2>
        <p class="card-desc">录制声音并克隆为专属音色</p>
        <div class="card-arrow">→</div>
      </div>

      <div class="mode-card" @click="goToOfficialVoice">
        <div class="card-icon">🎙️</div>
        <h2 class="card-title">官方音色</h2>
        <p class="card-desc">使用官方预置的专业音色</p>
        <div class="card-arrow">→</div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'


const router = useRouter()


const goToVoiceDesign = () => {
  router.push('/voice-design')
}

const goToVoiceClone = () => {
  router.push('/voice-clone')
}

const goToOfficialVoice = () => {
  router.push('/official-voice')
}


</script>

<style scoped>
.home-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: linear-gradient(135deg, #FFCF71 0%, #FF9A9E 100%);
}

.header {
  text-align: center;
  margin-bottom: 60px;
  color: white;
}

.title {
  font-size: 48px;
  font-weight: bold;
  margin-bottom: 10px;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
}

.subtitle {
  font-size: 36px;
  opacity: 0.9;
  font-weight: bold;
  color: rgb(255, 255, 255);
}

.content {
  display: flex;
  gap: 40px;
  flex-wrap: wrap;
  justify-content: center;
  max-width: 800px;
}

.mode-card {
  background: white;
  border-radius: 20px;
  padding: 40px;
  width: 300px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  position: relative;
  overflow: hidden;
}

.mode-card:hover {
  transform: translateY(-10px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}

.card-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.card-title {
  font-size: 28px;
  color: #333;
  margin-bottom: 10px;
}

.card-desc {
  font-size: 16px;
  color: #666;
  line-height: 1.5;
}

.card-arrow {
  position: absolute;
  right: 20px;
  bottom: 20px;
  font-size: 32px;
  color: #667eea;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.mode-card:hover .card-arrow {
  opacity: 1;
}

.footer {
  position: fixed;
  bottom: 30px;
  right: 30px;
}

.footer .el-button {
  width: 60px;
  height: 60px;
  font-size: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}
</style>
