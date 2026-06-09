<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import type { VideoStreamConfig } from '@/api/video'
import { buildVideoAssetUrl, getVideoConfig } from '@/api/video'
import type { CvTrackResult } from '@/api/cv'
import TwinScene from '@/components/TwinScene.vue'

const props = defineProps<{
  experimentId?: number
  cvTrack?: CvTrackResult | null
  running?: boolean
  position: { x: number; y: number }
  heading: number
  tracks: { x: number; y: number }[]
  highlight?: boolean
  speed?: number
  battery?: number
}>()

const config = ref<VideoStreamConfig | null>(null)
const videoMode = ref<'canvas' | 'mjpeg' | 'file'>('canvas')
const videoRef = ref<HTMLVideoElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)
let animId = 0
let localPhase = 0
let frameCount = 0
let lastFpsTime = performance.now()
const fps = ref(0)
const hudTime = ref('')

const videoSrc = computed(() => {
  if (!config.value || !props.experimentId) return ''
  if (videoMode.value === 'file' && config.value.fileUrl) {
    return buildVideoAssetUrl(`/api/video/${props.experimentId}/demo-file`)
  }
  if (videoMode.value === 'mjpeg' && config.value.mjpegUrl) {
    const base = import.meta.env.VITE_API_BASE_URL || ''
    return `${base}${config.value.mjpegUrl}`
  }
  return ''
})

const confidence = computed(() => props.cvTrack?.confidence ?? 0.87)
const bboxStyle = computed(() => {
  const t = props.cvTrack
  if (!t || t.bbox.length < 4 || videoMode.value === 'canvas') return null
  const [x, y, w, h] = t.bbox
  return {
    left: `${(x / 640) * 100}%`,
    top: `${(y / 360) * 100}%`,
    width: `${(w / 640) * 100}%`,
    height: `${(h / 360) * 100}%`,
  }
})

function drawGrid(ctx: CanvasRenderingContext2D, w: number, h: number) {
  ctx.strokeStyle = 'rgba(147, 197, 253, 0.15)'
  ctx.lineWidth = 1
  const step = 40
  for (let x = 0; x <= w; x += step) {
    ctx.beginPath()
    ctx.moveTo(x, 0)
    ctx.lineTo(x, h)
    ctx.stroke()
  }
  for (let y = 0; y <= h; y += step) {
    ctx.beginPath()
    ctx.moveTo(0, y)
    ctx.lineTo(w, y)
    ctx.stroke()
  }
}

function drawCanvas() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  const w = canvas.width
  const h = canvas.height
  frameCount++
  const now = performance.now()
  if (now - lastFpsTime >= 1000) {
    fps.value = frameCount
    frameCount = 0
    lastFpsTime = now
  }
  hudTime.value = new Date().toLocaleTimeString('zh-CN', { hour12: false })

  localPhase += props.running ? 0.02 : 0

  const grad = ctx.createLinearGradient(0, 0, 0, h)
  grad.addColorStop(0, '#1e3a5f')
  grad.addColorStop(0.6, '#1e40af')
  grad.addColorStop(1, '#1d4ed8')
  ctx.fillStyle = grad
  ctx.fillRect(0, 0, w, h)
  drawGrid(ctx, w, h)

  // 扫描线
  const scanY = (localPhase * 80) % h
  ctx.fillStyle = 'rgba(37, 99, 235, 0.08)'
  ctx.fillRect(0, scanY, w, 3)

  ctx.fillStyle = 'rgba(20, 80, 100, 0.5)'
  ctx.fillRect(0, h - 32, w, 32)

  let cx: number
  let cy: number
  let bw = 60
  let bh = 32
  if (props.cvTrack) {
    cx = (props.cvTrack.centerX / 640) * w
    cy = (props.cvTrack.centerY / 360) * h
    if (props.cvTrack.bbox.length >= 4) {
      bw = (props.cvTrack.bbox[2] / 640) * w
      bh = (props.cvTrack.bbox[3] / 360) * h
    }
  } else {
    cx = w * (0.3 + 0.4 * (0.5 + 0.5 * Math.sin(localPhase)))
    cy = h * (0.5 + 0.2 * Math.cos(localPhase * 0.7))
  }

  ctx.fillStyle = 'rgba(0, 200, 255, 0.85)'
  ctx.fillRect(cx - bw / 2 + 2, cy - bh / 2 + 2, bw - 4, bh - 4)
  ctx.strokeStyle = '#fbbf24'
  ctx.lineWidth = 2
  ctx.strokeRect(cx - bw / 2, cy - bh / 2, bw, bh)
  ctx.fillStyle = '#fbbf24'
  ctx.font = '11px monospace'
  ctx.fillText(`SHIP ${(confidence.value * 100).toFixed(0)}%`, cx - bw / 2, cy - bh / 2 - 4)

  animId = requestAnimationFrame(drawCanvas)
}

async function loadConfig() {
  if (!props.experimentId) return
  const { data } = await getVideoConfig(props.experimentId)
  config.value = data.data!
}

watch(() => props.experimentId, () => loadConfig())

watch(videoMode, (mode) => {
  cancelAnimationFrame(animId)
  if (mode === 'canvas') drawCanvas()
  else if (videoRef.value && videoSrc.value && mode === 'file') {
    videoRef.value.load()
    if (props.running) videoRef.value.play().catch(() => {})
  }
})

watch(
  () => props.running,
  (run) => {
    if (run && videoRef.value && videoMode.value === 'file') {
      videoRef.value.play().catch(() => {})
    }
  },
)

onMounted(() => {
  loadConfig()
  drawCanvas()
})

onUnmounted(() => cancelAnimationFrame(animId))
</script>

<template>
  <div class="video-twin-panel">
    <!-- 视频区 -->
    <div class="panel-section video-section">
      <div class="section-head">
        <span class="head-title">视频感知</span>
        <el-radio-group v-model="videoMode" size="small">
          <el-radio-button value="canvas" label="canvas">模拟画面</el-radio-button>
          <el-radio-button value="mjpeg" label="mjpeg">MJPEG</el-radio-button>
          <el-radio-button value="file" label="file" :disabled="!config?.fileUrl">本地 MP4</el-radio-button>
        </el-radio-group>
      </div>
      <div class="video-viewport">
        <canvas
          v-if="videoMode === 'canvas'"
          ref="canvasRef"
          width="640"
          height="280"
          class="viewport-el"
        />
        <video
          v-else-if="videoMode === 'file' && videoSrc"
          ref="videoRef"
          :src="videoSrc"
          muted
          loop
          playsinline
          class="viewport-el"
        />
        <img
          v-else-if="videoSrc"
          :src="videoSrc"
          alt="实时视频"
          class="viewport-el"
        />
        <div v-else class="viewport-placeholder">视频源加载中…</div>

        <!-- HUD 浮层 -->
        <div class="hud hud-tl">
          <span class="hud-tag live">● LIVE</span>
          <span>CAM-001</span>
          <span class="hud-sep">|</span>
          <span>OpenCV Tracking</span>
        </div>
        <div v-if="bboxStyle" class="cv-box" :style="bboxStyle">
          <span class="cv-label">{{ confidence.toFixed(2) }}</span>
        </div>
        <div class="hud hud-br">
          <span>{{ fps }} FPS</span>
          <span class="hud-sep">|</span>
          <span>置信度 {{ (confidence * 100).toFixed(0) }}%</span>
          <span class="hud-sep">|</span>
          <span>{{ hudTime || cvTrack?.timestamp?.slice(11) || '--:--:--' }}</span>
        </div>
      </div>
    </div>

    <!-- 联动指示 -->
    <div class="link-bar">
      <span class="link-arrow">↕</span>
      <span>视频识别 ↔ 数字孪生联动</span>
      <span v-if="cvTrack" class="link-coord">
        水池 ({{ cvTrack.poolX }}, {{ cvTrack.poolY }})
      </span>
    </div>

    <!-- 孪生区 -->
    <div class="panel-section twin-section">
      <div class="section-head">
        <span class="head-title">数字孪生水池</span>
        <span class="head-scale">40 m × 20 m</span>
      </div>
      <div class="twin-viewport">
        <TwinScene
          :position="position"
          :heading="heading"
          :tracks="tracks"
          :highlight="highlight"
          class="twin-scene-inner"
        />
        <div class="twin-hud">
          <div class="hud-row"><span>速度</span><strong>{{ speed?.toFixed(1) ?? '—' }} m/s</strong></div>
          <div class="hud-row"><span>航向</span><strong>{{ heading?.toFixed(0) ?? '—' }}°</strong></div>
          <div class="hud-row"><span>电量</span><strong>{{ battery?.toFixed(0) ?? '—' }}%</strong></div>
          <div class="hud-row"><span>坐标</span><strong>{{ position.x.toFixed(1) }}, {{ position.y.toFixed(1) }}</strong></div>
        </div>
        <div class="device-markers">
          <span class="marker cam" title="摄像头">📷</span>
          <span class="marker wave" title="造波机">🌊</span>
          <span class="marker imu" title="IMU">📡</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.video-twin-panel {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.panel-section {
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
  background: #fff;
}
.twin-section {
  background: #fff;
}
.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #fafafa;
  border-bottom: 1px solid #e5e7eb;
}
.head-title {
  font-size: 13px;
  font-weight: 600;
  color: #111827;
}
.head-scale {
  font-size: 11px;
  color: #6b7280;
  font-family: monospace;
}
.video-viewport,
.twin-viewport {
  position: relative;
}
.video-viewport {
  aspect-ratio: 16 / 9;
  min-height: 220px;
  background: #111827;
}
.viewport-el {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.viewport-placeholder {
  width: 100%;
  height: 100%;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  font-size: 13px;
}
.hud {
  position: absolute;
  font-size: 11px;
  font-family: ui-monospace, monospace;
  color: #e0f2fe;
  background: rgba(15, 23, 42, 0.72);
  padding: 4px 8px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 6px;
  pointer-events: none;
  backdrop-filter: blur(4px);
}
.hud-tl {
  top: 8px;
  left: 8px;
}
.hud-br {
  bottom: 8px;
  right: 8px;
}
.hud-tag.live {
  color: #60a5fa;
  font-weight: 700;
}
.hud-sep {
  opacity: 0.4;
}
.cv-box {
  position: absolute;
  border: 2px solid #fbbf24;
  box-shadow: 0 0 12px rgba(251, 191, 36, 0.5);
  pointer-events: none;
}
.cv-label {
  position: absolute;
  top: -18px;
  left: 0;
  background: #fbbf24;
  color: #1e293b;
  font-size: 10px;
  padding: 1px 5px;
  border-radius: 3px;
  font-weight: 700;
}
.link-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 6px 12px;
  font-size: 12px;
  color: #6b7280;
  background: #eff6ff;
  border: 1px solid #dbeafe;
  border-radius: 4px;
}
.link-arrow {
  color: #2563eb;
  font-weight: 700;
}
.link-coord {
  font-family: monospace;
  color: #1d4ed8;
  font-weight: 600;
}
.twin-viewport {
  position: relative;
  min-height: 280px;
}
.twin-viewport :deep(.twin-scene) {
  height: 280px;
  border-radius: 0;
}
.twin-hud {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  padding: 6px 10px;
  font-size: 11px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  pointer-events: none;
}
.hud-row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 2px;
}
.hud-row span {
  color: #6b7280;
}
.hud-row strong {
  color: #1d4ed8;
  font-family: monospace;
}
.device-markers {
  position: absolute;
  bottom: 8px;
  left: 8px;
  display: flex;
  gap: 6px;
  pointer-events: none;
}
.marker {
  font-size: 14px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 4px;
  padding: 2px 5px;
  border: 1px solid #e5e7eb;
  line-height: 1;
}
</style>
