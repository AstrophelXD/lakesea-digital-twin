<script setup lang="ts">
import { statusLabel, statusTagType } from '@/utils/format'
import { ALARM_TYPE_LABELS, type AlarmRecord } from '@/api/alarm'

defineProps<{
  alarms: AlarmRecord[]
  compact?: boolean
}>()
</script>

<template>
  <el-empty v-if="!alarms.length" description="暂无告警" />
  <el-timeline v-else>
    <el-timeline-item
      v-for="a in alarms"
      :key="a.id"
      :timestamp="a.createTime"
      placement="top"
      :type="a.alarmLevel === 'HIGH' ? 'danger' : 'warning'"
    >
      <div class="alarm-item">
        <el-tag size="small" type="danger">{{ ALARM_TYPE_LABELS[a.alarmType] || a.alarmType }}</el-tag>
        <span>{{ a.alarmMessage }}</span>
        <el-tag v-if="!compact" size="small" :type="statusTagType(a.handleStatus)">
          {{ statusLabel(a.handleStatus) }}
        </el-tag>
      </div>
    </el-timeline-item>
  </el-timeline>
</template>

<style scoped>
.alarm-item {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  font-size: 13px;
}
</style>
