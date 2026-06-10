<script setup lang="ts">
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'
import DOMPurify from 'dompurify'

const props = defineProps<{
  content: string
}>()

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
})

const html = computed(() => {
  const raw = props.content?.trim() || ''
  if (!raw) return ''
  return DOMPurify.sanitize(md.render(raw))
})
</script>

<template>
  <div v-if="html" class="markdown-body" v-html="html" />
  <span v-else class="empty">—</span>
</template>

<style scoped>
.markdown-body {
  line-height: 1.8;
  color: #374151;
  font-size: 14px;
}
.markdown-body :deep(p) {
  margin: 0.35rem 0 0.75rem;
}
.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin: 0.35rem 0 0.75rem;
  padding-left: 1.25rem;
}
.markdown-body :deep(li) {
  margin: 0.2rem 0;
}
.markdown-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 0.5rem 0 1rem;
  font-size: 13px;
}
.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid #e5e7eb;
  padding: 6px 10px;
  text-align: left;
}
.markdown-body :deep(th) {
  background: #f3f4f6;
  font-weight: 600;
}
.markdown-body :deep(code) {
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}
.markdown-body :deep(strong) {
  color: #111827;
}
.empty {
  color: #9ca3af;
}
</style>
