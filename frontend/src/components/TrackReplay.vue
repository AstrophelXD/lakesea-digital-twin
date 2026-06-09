<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import TwinScene from './TwinScene.vue'

const props = withDefaults(
  defineProps<{
    tracks: { positionX: number; positionY: number; heading?: number }[]
    index?: number
    controlled?: boolean
    highlight?: boolean
  }>(),
  { controlled: false, highlight: false },
)

const emit = defineEmits<{
  'update:index': [value: number]
}>()

const playing = ref(false)
const localIndex = ref(0)
let timer: ReturnType<typeof setInterval> | null = null

const frameIndex = computed({
  get: () => (props.controlled ? (props.index ?? 0) : localIndex.value),
  set: (v: number) => {
    if (props.controlled) emit('update:index', v)
    else localIndex.value = v
  },
})

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
  }, 300)
}

function resetPlay() {
  stopPlay()
  frameIndex.value = 0
}

watch(
  () => props.tracks,
  () => {
    if (!props.controlled) {
      frameIndex.value = props.tracks.length ? props.tracks.length - 1 : 0
    }
    stopPlay()
  },
  { deep: true },
)

defineExpose({ togglePlay, stopPlay, resetPlay, playing })
</script>

<template>
  <div class="replay-wrap">
    <TwinScene
      :position="currentPos"
      :heading="currentHeading"
      :tracks="currentTrack"
      :highlight="highlight"
    />
    <div v-if="tracks.length && !controlled" class="controls">
      <el-button size="small" @click="togglePlay">{{ playing ? 'Pause' : 'Play' }}</el-button>
      <el-slider
        v-model="frameIndex"
        :min="0"
        :max="Math.max(0, tracks.length - 1)"
        :format-tooltip="(v: number) => `${v + 1}/${tracks.length}`"
        @change="stopPlay"
      />
    </div>
    <el-empty v-else-if="!tracks.length" description="No track data" />
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
