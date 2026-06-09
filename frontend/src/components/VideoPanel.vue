<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import type { VideoStreamConfig } from '@/api/video'
import { buildVideoAssetUrl, getVideoConfig } from '@/api/video'
import type { CvTrackResult } from '@/api/cv'

const props = defineProps<{
  experimentId?: number
  cvTrack?: CvTrackResult | null
  running?: boolean
}>()

const config = ref<VideoStreamConfig | null>(null)
const videoMode = ref<'canvas' | 'mjpeg' | 'file'>('canvas')
const videoRef = ref<HTMLVideoElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)
let animId = 0
let localPhase = 0

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

const overlayStyle = computed(() => {
  const t = props.cvTrack
  if (!t || t.bbox.length < 4) return null
  const [x, y, w, h] = t.bbox
  return {
    left: `${(x / 640) * 100}%`,
    top: `${(y / 360) * 100}%`,
    width: `${(w / 640) * 100}%`,
    height: `${(h / 360) * 100}%`,
  }
})

function drawCanvas() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  const w = canvas.width
  const h = canvas.height
  localPhase += props.running ? 0.02 : 0
  ctx.fillStyle = '#0c4a6e'
  ctx.fillRect(0, 0, w, h)
  ctx.fillStyle = '#14532d33'
  ctx.fillRect(0, h - 36, w, 36)
  ctx.fillStyle = '#c7eafe'
  ctx.font = '13px sans-serif'
  ctx.fillText('LakeSea 试验场 · 模拟视频感知', 12, h - 12)

  let cx: number
  let cy: number
  if (props.cvTrack) {
    cx = (props.cvTrack.centerX / 640) * w
    cy = (props.cvTrack.centerY / 360) * h
  } else {
    cx = w * (0.3 + 0.4 * (0.5 + 0.5 * Math.sin(localPhase)))
    cy = h * (0.5 + 0.2 * Math.cos(localPhase * 0.7))
  }
  ctx.fillStyle = '#00c8ff'
  ctx.fillRect(cx - 28, cy - 14, 56, 28)
  ctx.strokeStyle = '#fbbf24'
  ctx.lineWidth = 2
  ctx.strokeRect(cx - 30, cy - 16, 60, 32)
  animId = requestAnimationFrame(drawCanvas)
}

async function loadConfig() {
  if (!props.experimentId) return
  const { data } = await getVideoConfig(props.experimentId)
  config.value = data.data!
  if (data.data!.fileUrl) videoMode.value = 'canvas'
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
  <div class="video-panel">
    <div class="video-header">
      <span class="title">实时视频监控</span>
      <el-radio-group v-model="videoMode" size="small">
        <el-radio-button value="canvas" label="canvas">模拟画面</el-radio-button>
        <el-radio-button value="mjpeg" label="mjpeg">MJPEG 流</el-radio-button>
        <el-radio-button value="file" label="file" :disabled="!config?.fileUrl">本地 MP4</el-radio-button>
      </el-radio-group>
    </div>
    <div class="video-frame">
      <canvas
        v-if="videoMode === 'canvas'"
        ref="canvasRef"
        width="640"
        height="360"
        class="video-el"
      />
      <video
        v-else-if="videoMode === 'file' && videoSrc"
        ref="videoRef"
        :src="videoSrc"
        muted
        loop
        playsinline
        class="video-el"
      />
      <img
        v-else-if="videoSrc"
        :src="videoSrc"
        alt="实时视频"
        class="video-el"
      />
      <div
        v-if="overlayStyle && cvTrack && videoMode !== 'canvas'"
        class="cv-box"
        :style="overlayStyle"
      >
        <span class="cv-label">{{ cvTrack.confidence.toFixed(2) }}</span>
      </div>
    </div>
    <div v-if="cvTrack" class="cv-meta">
      识别源：{{ cvTrack.source }} · 水池坐标 ({{ cvTrack.poolX }}, {{ cvTrack.poolY }}) · 置信度 {{ cvTrack.confidence }}
    </div>
    <div v-else class="cv-meta">
      启动监控后将同步 OpenCV / 模拟识别框与孪生场景
    </div>
  </div>
</template>

<style scoped>
.video-panel {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.video-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}
.title {
  font-size: 13px;
  font-weight: 600;
}
.video-frame {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  background: #0c4a6e;
  border-radius: 8px;
  overflow: hidden;
}
.video-el {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.cv-box {
  position: absolute;
  border: 2px solid #fbbf24;
  box-shadow: 0 0 8px rgba(251, 191, 36, 0.6);
  pointer-events: none;
}
.cv-label {
  position: absolute;
  top: -20px;
  left: 0;
  background: rgba(251, 191, 36, 0.9);
  color: #1e293b;
  font-size: 11px;
  padding: 1px 4px;
  border-radius: 3px;
}
.cv-meta {
  font-size: 11px;
  color: #64748b;
}
</style>
