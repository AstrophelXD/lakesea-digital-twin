<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { ALARM_TYPE_LABELS, handleAlarm, listAlarms, type AlarmRecord } from '@/api/alarm'
import { listExperiments, type ExperimentTask } from '@/api/experiment'
import { useUserStore } from '@/stores/user'
import { statusLabel, statusTagType } from '@/utils/format'

const userStore = useUserStore()
const loading = ref(false)
const tableData = ref<AlarmRecord[]>([])
const total = ref(0)
const experiments = ref<ExperimentTask[]>([])
const query = reactive({
  experimentId: undefined as number | undefined,
  handleStatus: '',
  page: 1,
  pageSize: 15,
})

const handleVisible = ref(false)
const currentAlarm = ref<AlarmRecord | null>(null)
const handleForm = reactive({ handleStatus: 'RESOLVED', comment: '' })

const canHandle = () => userStore.hasRole('MAINTAINER', 'ADMIN', 'DIRECTOR')

async function load() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { page: query.page, pageSize: query.pageSize }
    if (query.experimentId) params.experimentId = query.experimentId
    if (query.handleStatus) params.handleStatus = query.handleStatus
    const { data } = await listAlarms(params)
    tableData.value = data.data!.items
    total.value = data.data!.total
  } finally {
    loading.value = false
  }
}

async function loadExperiments() {
  const { data } = await listExperiments({ pageSize: 100 })
  experiments.value = data.data!.items
}

function openHandle(row: AlarmRecord) {
  currentAlarm.value = row
  handleForm.handleStatus = 'RESOLVED'
  handleForm.comment = ''
  handleVisible.value = true
}

async function submitHandle() {
  if (!currentAlarm.value) return
  await handleAlarm(currentAlarm.value.id, handleForm.handleStatus, handleForm.comment)
  ElMessage.success('已处理')
  handleVisible.value = false
  load()
}

onMounted(async () => {
  await loadExperiments()
  await load()
})
</script>

<template>
  <el-card shadow="never">
    <div class="toolbar">
      <el-select v-model="query.experimentId" placeholder="试验任务" clearable style="width: 220px">
        <el-option
          v-for="e in experiments"
          :key="e.id"
          :label="`${e.taskNo} - ${e.expName}`"
          :value="e.id"
        />
      </el-select>
      <el-select v-model="query.handleStatus" placeholder="处理状态" clearable style="width: 140px">
        <el-option label="待处理" value="PENDING" />
        <el-option label="已处理" value="RESOLVED" />
        <el-option label="已忽略" value="IGNORED" />
      </el-select>
      <el-button type="primary" @click="load">查询</el-button>
    </div>

    <el-table v-loading="loading" :data="tableData" stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="experimentId" label="任务ID" width="90" />
      <el-table-column label="类型" width="120">
        <template #default="{ row }">
          {{ ALARM_TYPE_LABELS[row.alarmType] || row.alarmType }}
        </template>
      </el-table-column>
      <el-table-column prop="alarmMessage" label="内容" />
      <el-table-column label="等级" width="80">
        <template #default="{ row }">
          <el-tag :type="row.alarmLevel === 'HIGH' ? 'danger' : 'warning'" size="small">
            {{ row.alarmLevel }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.handleStatus)" size="small">
            {{ statusLabel(row.handleStatus) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="createTime" label="时间" width="170" />
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="canHandle() && row.handleStatus === 'PENDING'"
            link
            type="primary"
            @click="openHandle(row)"
          >
            处理
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="query.page"
      :page-size="query.pageSize"
      :total="total"
      layout="total, prev, pager, next"
      class="pager"
      @current-change="load"
    />
  </el-card>

  <el-dialog v-model="handleVisible" title="处理告警" width="400px">
    <el-form label-width="80px">
      <el-form-item label="状态">
        <el-select v-model="handleForm.handleStatus" style="width: 100%">
          <el-option label="已处理" value="RESOLVED" />
          <el-option label="处理中" value="PROCESSING" />
          <el-option label="已忽略" value="IGNORED" />
        </el-select>
      </el-form-item>
      <el-form-item label="说明">
        <el-input v-model="handleForm.comment" type="textarea" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="handleVisible = false">取消</el-button>
      <el-button type="primary" @click="submitHandle">确定</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.pager {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>
