<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { getAuditMeta, listOperationLogs, type OperationLog } from '@/api/audit'

const loading = ref(false)
const tableData = ref<OperationLog[]>([])
const total = ref(0)
const moduleOptions = ref<{ value: string; label: string }[]>([])
const actionOptions = ref<{ value: string; label: string }[]>([])

const query = reactive({
  module: '',
  action: '',
  keyword: '',
  success: '' as '' | 'true' | 'false',
  page: 1,
  pageSize: 20,
})

async function loadMeta() {
  const { data } = await getAuditMeta()
  moduleOptions.value = data.data!.modules
  actionOptions.value = data.data!.actions
}

async function load() {
  loading.value = true
  try {
    const params: Record<string, unknown> = {
      page: query.page,
      pageSize: query.pageSize,
    }
    if (query.module) params.module = query.module
    if (query.action) params.action = query.action
    if (query.keyword) params.keyword = query.keyword
    if (query.success !== '') params.success = query.success === 'true'

    const { data } = await listOperationLogs(params)
    tableData.value = data.data!.items
    total.value = data.data!.total
  } finally {
    loading.value = false
  }
}

function onSearch() {
  query.page = 1
  load()
}

onMounted(async () => {
  await loadMeta()
  await load()
})
</script>

<template>
  <div>
    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" @submit.prevent="onSearch">
        <el-form-item label="模块">
          <el-select v-model="query.module" clearable placeholder="全部" style="width: 140px">
            <el-option
              v-for="opt in moduleOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="操作">
          <el-select v-model="query.action" clearable placeholder="全部" style="width: 140px">
            <el-option
              v-for="opt in actionOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="结果">
          <el-select v-model="query.success" clearable placeholder="全部" style="width: 100px">
            <el-option label="成功" value="true" />
            <el-option label="失败" value="false" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input
            v-model="query.keyword"
            placeholder="用户名 / 详情"
            clearable
            style="width: 180px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="onSearch">查询</el-button>
          <el-button @click="() => { query.module=''; query.action=''; query.keyword=''; query.success=''; onSearch() }">
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <el-table v-loading="loading" :data="tableData" size="small" stripe>
        <el-table-column prop="createTime" label="时间" width="170" />
        <el-table-column prop="username" label="用户" width="110" />
        <el-table-column label="模块" width="110">
          <template #default="{ row }">{{ row.moduleLabel || row.module }}</template>
        </el-table-column>
        <el-table-column label="操作" width="110">
          <template #default="{ row }">{{ row.actionLabel || row.action }}</template>
        </el-table-column>
        <el-table-column label="目标" width="140">
          <template #default="{ row }">
            <span v-if="row.targetType">{{ row.targetType }}#{{ row.targetId }}</span>
            <span v-else>—</span>
          </template>
        </el-table-column>
        <el-table-column prop="detail" label="详情" min-width="180" show-overflow-tooltip />
        <el-table-column prop="ipAddress" label="IP" width="120" />
        <el-table-column label="结果" width="80">
          <template #default="{ row }">
            <el-tag :type="row.success ? 'success' : 'danger'" size="small">
              {{ row.success ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>

      <div class="pager">
        <el-pagination
          v-model:current-page="query.page"
          v-model:page-size="query.pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="load"
          @size-change="() => { query.page = 1; load() }"
        />
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.filter-card {
  margin-bottom: 12px;
}
.pager {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
