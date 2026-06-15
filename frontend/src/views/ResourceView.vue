<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  createResource,
  deleteResource,
  listResources,
  updateResource,
  updateResourceStatus,
  type Resource,
} from '@/api/resource'
import { useUserStore } from '@/stores/user'
import { resourceTypeLabel, statusLabel, statusTagType } from '@/utils/format'

const userStore = useUserStore()
const loading = ref(false)
const tableData = ref<Resource[]>([])
const total = ref(0)
const query = reactive({ keyword: '', status: '', page: 1, pageSize: 10 })

const dialogVisible = ref(false)
const statusDialogVisible = ref(false)
const detailVisible = ref(false)
const editingId = ref<number | null>(null)
const detailRow = ref<Resource | null>(null)
const form = reactive({
  resourceCode: '',
  resourceName: '',
  resourceType: 'POOL',
  location: '',
  description: '',
  maxQuantity: 1,
})
const statusForm = reactive({ id: 0, status: 'MAINTENANCE', comment: '' })

const canEdit = () => userStore.hasRole('ADMIN', 'MAINTAINER')

const statusSummary = computed(() => {
  const summary = { available: 0, reserved: 0, inUse: 0, other: 0 }
  for (const row of tableData.value) {
    if (row.status === 'AVAILABLE') summary.available += 1
    else if (row.status === 'RESERVED') summary.reserved += 1
    else if (row.status === 'IN_USE') summary.inUse += 1
    else summary.other += 1
  }
  return summary
})

async function load() {
  loading.value = true
  try {
    const { data } = await listResources({ ...query, pageSize: query.pageSize })
    tableData.value = data.data!.items
    total.value = data.data!.total
  } finally {
    loading.value = false
  }
}

function openDetail(row: Resource) {
  detailRow.value = row
  detailVisible.value = true
}

function openCreate() {
  editingId.value = null
  Object.assign(form, {
    resourceCode: '',
    resourceName: '',
    resourceType: 'POOL',
    location: '',
    description: '',
    maxQuantity: 1,
  })
  dialogVisible.value = true
}

function openEdit(row: Resource) {
  editingId.value = row.id
  Object.assign(form, {
    resourceCode: row.resourceCode,
    resourceName: row.resourceName,
    resourceType: row.resourceType,
    location: row.location || '',
    description: row.description || '',
    maxQuantity: row.maxQuantity ?? 1,
  })
  dialogVisible.value = true
}

async function save() {
  if (editingId.value) {
    await updateResource(editingId.value, {
      resourceName: form.resourceName,
      resourceType: form.resourceType,
      location: form.location,
      description: form.description,
      maxQuantity: form.maxQuantity,
    })
    ElMessage.success('已更新')
  } else {
    await createResource({ ...form })
    ElMessage.success('已创建')
  }
  dialogVisible.value = false
  load()
}

function openStatus(row: Resource) {
  statusForm.id = row.id
  statusForm.status = 'MAINTENANCE'
  statusForm.comment = ''
  statusDialogVisible.value = true
}

async function saveStatus() {
  await updateResourceStatus(statusForm.id, statusForm.status, statusForm.comment)
  ElMessage.success('状态已更新')
  statusDialogVisible.value = false
  load()
}

async function onDelete(row: Resource) {
  await deleteResource(row.id)
  ElMessage.success('已停用')
  load()
}

onMounted(load)
</script>

<template>
  <el-card shadow="never">
    <div class="summary-row">
      <el-tag type="success">可用 {{ statusSummary.available }}</el-tag>
      <el-tag type="warning">已预约 {{ statusSummary.reserved }}</el-tag>
      <el-tag>使用中 {{ statusSummary.inUse }}</el-tag>
      <el-tag v-if="statusSummary.other" type="info">其他 {{ statusSummary.other }}</el-tag>
    </div>

    <div class="toolbar">
      <el-input v-model="query.keyword" placeholder="搜索名称/编码" clearable style="width: 200px" />
      <el-select v-model="query.status" placeholder="状态" clearable style="width: 140px">
        <el-option label="可用" value="AVAILABLE" />
        <el-option label="已预约" value="RESERVED" />
        <el-option label="使用中" value="IN_USE" />
        <el-option label="维护中" value="MAINTENANCE" />
        <el-option label="故障" value="FAULT" />
        <el-option label="停用" value="DISABLED" />
      </el-select>
      <el-button type="primary" @click="load">查询</el-button>
      <el-button v-if="canEdit()" type="success" @click="openCreate">新增资源</el-button>
    </div>

    <el-table v-loading="loading" :data="tableData" stripe>
      <el-table-column prop="resourceCode" label="编码" width="110" />
      <el-table-column prop="resourceName" label="名称" min-width="160" show-overflow-tooltip />
      <el-table-column label="类型" width="100">
        <template #default="{ row }">
          {{ resourceTypeLabel(row.resourceType) }}
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.status)" size="small">
            {{ statusLabel(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="location" label="位置" min-width="120" show-overflow-tooltip />
      <el-table-column label="可预约上限" width="110" align="center">
        <template #default="{ row }">{{ row.maxQuantity ?? 1 }}</template>
      </el-table-column>
      <el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip />
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)">详情</el-button>
          <el-button v-if="canEdit()" link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button v-if="canEdit()" link @click="openStatus(row)">改状态</el-button>
          <el-button v-if="userStore.hasRole('ADMIN')" link type="danger" @click="onDelete(row)">
            停用
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

  <el-dialog v-model="detailVisible" title="资源详情" width="520px">
    <el-descriptions v-if="detailRow" :column="1" border size="small">
      <el-descriptions-item label="编码">{{ detailRow.resourceCode }}</el-descriptions-item>
      <el-descriptions-item label="名称">{{ detailRow.resourceName }}</el-descriptions-item>
      <el-descriptions-item label="类型">
        {{ resourceTypeLabel(detailRow.resourceType) }}（{{ detailRow.resourceType }}）
      </el-descriptions-item>
      <el-descriptions-item label="状态">
        <el-tag :type="statusTagType(detailRow.status)" size="small">
          {{ statusLabel(detailRow.status) }}
        </el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="位置">{{ detailRow.location || '—' }}</el-descriptions-item>
      <el-descriptions-item label="可预约上限">{{ detailRow.maxQuantity ?? 1 }}</el-descriptions-item>
      <el-descriptions-item label="描述">{{ detailRow.description || '—' }}</el-descriptions-item>
      <el-descriptions-item v-if="detailRow.createTime" label="录入时间">
        {{ detailRow.createTime?.slice(0, 19).replace('T', ' ') }}
      </el-descriptions-item>
    </el-descriptions>
  </el-dialog>

  <el-dialog v-model="dialogVisible" :title="editingId ? '编辑资源' : '新增资源'" width="480px">
    <el-form label-width="90px">
      <el-form-item label="编码" required>
        <el-input v-model="form.resourceCode" :disabled="!!editingId" />
      </el-form-item>
      <el-form-item label="名称" required>
        <el-input v-model="form.resourceName" />
      </el-form-item>
      <el-form-item label="类型">
        <el-select v-model="form.resourceType" style="width: 100%">
          <el-option label="水池" value="POOL" />
          <el-option label="模型船" value="SHIP" />
          <el-option label="传感器" value="SENSOR" />
          <el-option label="摄像头" value="CAMERA" />
          <el-option label="拖车" value="TOWING" />
        </el-select>
      </el-form-item>
      <el-form-item label="位置">
        <el-input v-model="form.location" />
      </el-form-item>
      <el-form-item label="可预约上限">
        <el-input-number v-model="form.maxQuantity" :min="1" :max="999" style="width: 100%" />
      </el-form-item>
      <el-form-item label="描述">
        <el-input v-model="form.description" type="textarea" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" @click="save">保存</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="statusDialogVisible" title="更新资源状态" width="400px">
    <el-form label-width="80px">
      <el-form-item label="状态">
        <el-select v-model="statusForm.status" style="width: 100%">
          <el-option label="可用" value="AVAILABLE" />
          <el-option label="维护中" value="MAINTENANCE" />
          <el-option label="故障" value="FAULT" />
          <el-option label="停用" value="DISABLED" />
        </el-select>
      </el-form-item>
      <el-form-item label="备注">
        <el-input v-model="statusForm.comment" type="textarea" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="statusDialogVisible = false">取消</el-button>
      <el-button type="primary" @click="saveStatus">确定</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.summary-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}
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
