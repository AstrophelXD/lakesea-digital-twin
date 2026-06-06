<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import * as THREE from 'three'

const POOL_W = 40
const POOL_H = 20

const props = defineProps<{
  position: { x: number; y: number }
  heading: number
  tracks: { x: number; y: number }[]
  highlight?: boolean
}>()

const containerRef = ref<HTMLDivElement | null>(null)
let renderer: THREE.WebGLRenderer | null = null
let scene: THREE.Scene | null = null
let camera: THREE.OrthographicCamera | null = null
let shipMesh: THREE.Mesh | null = null
let shipMat: THREE.MeshBasicMaterial | null = null
let trailLine: THREE.Line | null = null
let animId = 0

function init() {
  if (!containerRef.value) return
  const w = containerRef.value.clientWidth
  const h = containerRef.value.clientHeight || 360

  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x0c4a6e)

  const aspect = w / h
  const viewH = POOL_H + 4
  const viewW = viewH * aspect
  camera = new THREE.OrthographicCamera(
    -viewW / 2,
    viewW / 2,
    viewH / 2,
    -viewH / 2,
    0.1,
    100,
  )
  camera.position.set(POOL_W / 2, POOL_H / 2, 50)
  camera.lookAt(POOL_W / 2, POOL_H / 2, 0)

  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(w, h)
  containerRef.value.innerHTML = ''
  containerRef.value.appendChild(renderer.domElement)

  const poolGeo = new THREE.PlaneGeometry(POOL_W, POOL_H)
  const poolMat = new THREE.MeshBasicMaterial({ color: 0x0284c7, transparent: true, opacity: 0.85 })
  const pool = new THREE.Mesh(poolGeo, poolMat)
  pool.position.set(POOL_W / 2, POOL_H / 2, 0)
  scene.add(pool)

  const border = new THREE.LineSegments(
    new THREE.EdgesGeometry(new THREE.PlaneGeometry(POOL_W, POOL_H)),
    new THREE.LineBasicMaterial({ color: 0x7dd3fc }),
  )
  border.position.set(POOL_W / 2, POOL_H / 2, 0.1)
  scene.add(border)

  const shipGeo = new THREE.ConeGeometry(0.8, 2, 3)
  shipMat = new THREE.MeshBasicMaterial({ color: 0xfbbf24 })
  shipMesh = new THREE.Mesh(shipGeo, shipMat)
  scene.add(shipMesh)

  const trailMat = new THREE.LineBasicMaterial({ color: 0xa7f3d0 })
  const trailGeo = new THREE.BufferGeometry()
  trailLine = new THREE.Line(trailGeo, trailMat)
  scene.add(trailLine)

  updateShip()
  animate()
}

function updateShip() {
  if (!shipMesh || !trailLine) return
  shipMesh.position.set(props.position.x, props.position.y, 0.5)
  shipMesh.rotation.z = -((props.heading * Math.PI) / 180) + Math.PI / 2

  const pts = props.tracks.map((p) => new THREE.Vector3(p.x, p.y, 0.2))
  if (pts.length > 1) {
    trailLine.geometry.dispose()
    trailLine.geometry = new THREE.BufferGeometry().setFromPoints(pts)
  }
}

function animate() {
  animId = requestAnimationFrame(animate)
  renderer?.render(scene!, camera!)
}

function onResize() {
  if (!containerRef.value || !renderer || !camera) return
  const w = containerRef.value.clientWidth
  const h = containerRef.value.clientHeight || 360
  renderer.setSize(w, h)
  const aspect = w / h
  const viewH = POOL_H + 4
  const viewW = viewH * aspect
  camera.left = -viewW / 2
  camera.right = viewW / 2
  camera.top = viewH / 2
  camera.bottom = -viewH / 2
  camera.updateProjectionMatrix()
}

watch(() => [props.position, props.heading, props.tracks], updateShip, { deep: true })

watch(
  () => props.highlight,
  (on) => {
    if (shipMat) shipMat.color.setHex(on ? 0xef4444 : 0xfbbf24)
  },
)

onMounted(() => {
  init()
  window.addEventListener('resize', onResize)
})

onUnmounted(() => {
  cancelAnimationFrame(animId)
  window.removeEventListener('resize', onResize)
  renderer?.dispose()
})
</script>

<template>
  <div ref="containerRef" class="twin-scene" />
</template>

<style scoped>
.twin-scene {
  width: 100%;
  height: 360px;
  border-radius: 8px;
  overflow: hidden;
}
</style>
