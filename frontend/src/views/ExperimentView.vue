<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  archiveExperiment,
  finishExperiment,
  listExperiments,
  markReady,
  startExperiment,
  type ExperimentTask,
} from '@/api/experiment'
import { statusLabel, statusTagType } from '@/utils/format'

const loading = ref(false)
const tableData = ref<ExperimentTask[]>([])
const total = ref(0)
const query = reactive({ status: '', page: 1, pageSize: 10 })

async function load() {
  loading.value = true
  try {
    const { data } = await listExperiments({ ...query })
    tableData.value = data.data!.items
    total.value = data.data!.total
  } finally {
    loading.value = false
  }
}

async function action(fn: (id: number) => ReturnType<typeof markReady>, row: ExperimentTask, msg: string) {
  await fn(row.id)
  ElMessage.success(msg)
  load()
}

onMounted(load)
</script>

<template>
  <el-card shadow="never">
    <div class="toolbar">
      <el-select v-model="query.status" placeholder="任务状态" clearable style="width: 160px">
        <el-option label="待准备" value="PENDING_PREPARE" />
        <el-option label="已准备" value="READY" />
        <el-option label="执行中" value="RUNNING" />
        <el-option label="已完成" value="COMPLETED" />
        <el-option label="已归档" value="ARCHIVED" />
      </el-select>
      <el-button type="primary" @click="load">查询</el-button>
    </div>

    <el-table v-loading="loading" :data="tableData" stripe>
      <el-table-column prop="taskNo" label="任务单号" width="180" />
      <el-table-column prop="expName" label="试验名称" />
      <el-table-column prop="reservationId" label="预约ID" width="90" />
      <el-table-column label="状态" width="110">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.status)">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="320" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="row.status === 'PENDING_PREPARE'"
            link
            type="primary"
            @click="action(markReady, row, '已标记准备完成')"
          >
            准备完成
          </el-button>
          <el-button
            v-if="row.status === 'READY'"
            link
            type="success"
            @click="action(startExperiment, row, '试验已启动')"
          >
            启动试验
          </el-button>
          <el-button
            v-if="row.status === 'RUNNING'"
            link
            type="warning"
            @click="action(finishExperiment, row, '试验已完成')"
          >
            完成试验
          </el-button>
          <el-button
            v-if="row.status === 'COMPLETED'"
            link
            @click="action(archiveExperiment, row, '已归档')"
          >
            归档
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
</template>

<style scoped>
.toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}
.pager {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>
