<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createUser,
  listUsers,
  resetUserPassword,
  toggleUserStatus,
  updateUser,
  type UserItem,
} from '@/api/user'
import { roleLabel } from '@/utils/format'

const loading = ref(false)
const tableData = ref<UserItem[]>([])
const total = ref(0)
const query = reactive({ keyword: '', status: '', page: 1, pageSize: 10 })

const dialogVisible = ref(false)
const pwdDialogVisible = ref(false)
const editingId = ref<number | null>(null)
const pwdUserId = ref(0)

const form = reactive({
  username: '',
  password: '',
  realName: '',
  phone: '',
  email: '',
  roleCode: 'STUDENT',
})

const pwdForm = reactive({ password: '123456' })

const roleOptions = [
  { value: 'ADMIN', label: '系统管理员' },
  { value: 'DIRECTOR', label: '试验场主任' },
  { value: 'TEACHER', label: '指导教师' },
  { value: 'STUDENT', label: '学生/研究员' },
  { value: 'MAINTAINER', label: '设备维护人员' },
]

async function load() {
  loading.value = true
  try {
    const { data } = await listUsers({ ...query })
    tableData.value = data.data!.items
    total.value = data.data!.total
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  Object.assign(form, {
    username: '',
    password: '123456',
    realName: '',
    phone: '',
    email: '',
    roleCode: 'STUDENT',
  })
  dialogVisible.value = true
}

function openEdit(row: UserItem) {
  editingId.value = row.id
  Object.assign(form, {
    username: row.username,
    password: '',
    realName: row.realName,
    phone: row.phone || '',
    email: row.email || '',
    roleCode: row.roles[0] || 'STUDENT',
  })
  dialogVisible.value = true
}

async function save() {
  if (editingId.value) {
    await updateUser(editingId.value, {
      realName: form.realName,
      phone: form.phone || undefined,
      email: form.email || undefined,
      roleCode: form.roleCode,
    })
    ElMessage.success('用户已更新')
  } else {
    await createUser({
      username: form.username,
      password: form.password,
      realName: form.realName,
      phone: form.phone || undefined,
      email: form.email || undefined,
      roleCode: form.roleCode,
    })
    ElMessage.success('用户已创建')
  }
  dialogVisible.value = false
  await load()
}

function openResetPwd(row: UserItem) {
  pwdUserId.value = row.id
  pwdForm.password = '123456'
  pwdDialogVisible.value = true
}

async function savePwd() {
  await resetUserPassword(pwdUserId.value, pwdForm.password)
  ElMessage.success('密码已重置')
  pwdDialogVisible.value = false
}

async function toggleStatus(row: UserItem) {
  const action = row.status === 'ACTIVE' ? '禁用' : '启用'
  await ElMessageBox.confirm(`确定${action}用户「${row.realName}」？`, '提示', {
    type: 'warning',
  })
  await toggleUserStatus(row.id)
  ElMessage.success(`已${action}`)
  await load()
}

onMounted(load)
</script>

<template>
  <div class="user-manage">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>用户管理</span>
          <el-button type="primary" @click="openCreate">新增用户</el-button>
        </div>
      </template>

      <el-form :inline="true" class="filter-form">
        <el-form-item label="关键词">
          <el-input v-model="query.keyword" placeholder="用户名/姓名" clearable @clear="load" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="query.status" clearable placeholder="全部" @change="load">
            <el-option label="正常" value="ACTIVE" />
            <el-option label="禁用" value="DISABLED" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="load">查询</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="tableData" stripe>
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="realName" label="姓名" width="120" />
        <el-table-column label="角色" width="140">
          <template #default="{ row }">
            <el-tag v-for="r in row.roles" :key="r" size="small" style="margin-right: 4px">
              {{ roleLabel(r) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="手机" width="130" />
        <el-table-column prop="email" label="邮箱" min-width="160" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 'ACTIVE' ? 'success' : 'danger'" size="small">
              {{ row.status === 'ACTIVE' ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="warning" @click="openResetPwd(row)">重置密码</el-button>
            <el-button
              link
              :type="row.status === 'ACTIVE' ? 'danger' : 'success'"
              @click="toggleStatus(row)"
            >
              {{ row.status === 'ACTIVE' ? '禁用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="query.page"
        v-model:page-size="query.pageSize"
        :total="total"
        layout="total, prev, pager, next"
        class="pager"
        @current-change="load"
        @size-change="load"
      />
    </el-card>

    <el-dialog
      v-model="dialogVisible"
      :title="editingId ? '编辑用户' : '新增用户'"
      width="480px"
    >
      <el-form label-width="80px">
        <el-form-item label="用户名" required>
          <el-input v-model="form.username" :disabled="!!editingId" />
        </el-form-item>
        <el-form-item v-if="!editingId" label="密码" required>
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="姓名" required>
          <el-input v-model="form.realName" />
        </el-form-item>
        <el-form-item label="角色" required>
          <el-select v-model="form.roleCode" style="width: 100%">
            <el-option
              v-for="opt in roleOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="手机">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="pwdDialogVisible" title="重置密码" width="400px">
      <el-form label-width="80px">
        <el-form-item label="新密码" required>
          <el-input v-model="pwdForm.password" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pwdDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="savePwd">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.filter-form {
  margin-bottom: 12px;
}

.pager {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>
