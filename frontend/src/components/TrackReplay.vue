<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import TwinScene from './TwinScene.vue'

const props = defineProps<{
  tracks: { positionX: number; positionY: number; heading?: number }[]
}>()

const playing = ref(false)
const frameIndex = ref(0)
let timer: ReturnType<typeof setInterval> | null = null

const currentTrack = computed(() => {
  const slice = props.tracks.slice(0, frameIndex.value + 1)
  return slice.map((t) => ({ x: t.positionX, y: t.positionY }))
})

const currentPos = computed(() => {
  const t = props.tracks[frameIndex.value]
  if (!t) return { x: 10, y: 10 }
  return { x: t.positionX, y: t.positionY }
})

const currentHeading = computed(() => props.tracks[frameIndex.value]?.heading ?? 0)

function stopPlay() {
  playing.value = false
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

function togglePlay() {
  if (playing.value) {
    stopPlay()
    return
  }
  if (!props.tracks.length) return
  playing.value = true
  timer = setInterval(() => {
    if (frameIndex.value >= props.tracks.length - 1) {
      stopPlay()
      return
    }
    frameIndex.value += 1
  }, 200)
}

watch(
  () => props.tracks,
  () => {
    frameIndex.value = props.tracks.length ? props.tracks.length - 1 : 0
    stopPlay()
  },
  { deep: true },
)
</script>

<template>
  <div class="replay-wrap">
    <TwinScene :position="currentPos" :heading="currentHeading" :tracks="currentTrack" />
    <div v-if="tracks.length" class="controls">
      <el-button size="small" @click="togglePlay">{{ playing ? '暂停' : '播放' }}</el-button>
      <el-slider
        v-model="frameIndex"
        :min="0"
        :max="Math.max(0, tracks.length - 1)"
        :format-tooltip="(v: number) => `${v + 1}/${tracks.length}`"
        @change="stopPlay"
      />
    </div>
    <el-empty v-else description="暂无轨迹数据，请先完成一次带监控的试验" />
  </div>
</template>

<style scoped>
.replay-wrap {
  width: 100%;
}
.controls {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 8px;
}
.controls .el-slider {
  flex: 1;
}
</style>
