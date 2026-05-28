<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
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
import { statusLabel, statusTagType } from '@/utils/format'

const userStore = useUserStore()
const loading = ref(false)
const tableData = ref<Resource[]>([])
const total = ref(0)
const query = reactive({ keyword: '', status: '', page: 1, pageSize: 10 })

const dialogVisible = ref(false)
const statusDialogVisible = ref(false)
const editingId = ref<number | null>(null)
const form = reactive({
  resourceCode: '',
  resourceName: '',
  resourceType: 'POOL',
  location: '',
  description: '',
})
const statusForm = reactive({ id: 0, status: 'MAINTENANCE', comment: '' })

const canEdit = () =>
  userStore.hasRole('ADMIN', 'MAINTAINER')

async function load() {
  loading.value = true
  try {
    const { data } = await listResources({ ...query })
    tableData.value = data.data!.items
    total.value = data.data!.total
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  Object.assign(form, {
    resourceCode: '',
    resourceName: '',
    resourceType: 'POOL',
    location: '',
    description: '',
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
    <div class="toolbar">
      <el-input v-model="query.keyword" placeholder="搜索名称/编码" clearable style="width: 200px" />
      <el-select v-model="query.status" placeholder="状态" clearable style="width: 140px">
        <el-option label="可用" value="AVAILABLE" />
        <el-option label="维护中" value="MAINTENANCE" />
        <el-option label="故障" value="FAULT" />
        <el-option label="停用" value="DISABLED" />
      </el-select>
      <el-button type="primary" @click="load">查询</el-button>
      <el-button v-if="canEdit()" type="success" @click="openCreate">新增资源</el-button>
    </div>

    <el-table v-loading="loading" :data="tableData" stripe>
      <el-table-column prop="resourceCode" label="编码" width="120" />
      <el-table-column prop="resourceName" label="名称" />
      <el-table-column prop="resourceType" label="类型" width="100" />
      <el-table-column label="状态" width="110">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.status)">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="location" label="位置" />
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
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
