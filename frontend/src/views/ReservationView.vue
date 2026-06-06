<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listResources, type Resource } from '@/api/resource'
import {
  cancelReservation,
  checkConflicts,
  createReservation,
  directorApprove,
  getReservation,
  listReservations,
  submitReservation,
  teacherReview,
  updateReservation,
  type Reservation,
  type ReservationResource,
} from '@/api/reservation'
import { listTeachers, type TeacherOption } from '@/api/user'
import { useUserStore } from '@/stores/user'
import { statusLabel, statusTagType, toApiDateTime } from '@/utils/format'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const tableData = ref<Reservation[]>([])
const total = ref(0)
const query = reactive({ status: '', keyword: '', page: 1, pageSize: 10 })

const allResources = ref<Resource[]>([])
const teachers = ref<TeacherOption[]>([])

const formVisible = ref(false)
const detailVisible = ref(false)
const approvalVisible = ref(false)
const approvalMode = ref<'teacher' | 'director'>('teacher')
const editingId = ref<number | null>(null)
const currentDetail = ref<Reservation | null>(null)

const approvalForm = reactive({ approved: true, comment: '' })

const form = reactive({
  expName: '',
  expType: '阻力试验',
  teacherId: undefined as number | undefined,
  startTime: '',
  endTime: '',
  purpose: '',
  planSummary: '',
  resources: [] as ReservationResource[],
})

function emptyResource(): ReservationResource {
  return {
    resourceId: 0,
    resourceType: '',
    quantity: 1,
    startTime: '',
    endTime: '',
    remark: '',
  }
}

async function load() {
  loading.value = true
  try {
    const { data } = await listReservations({ ...query })
    tableData.value = data.data!.items
    total.value = data.data!.total
  } finally {
    loading.value = false
  }
}

async function loadOptions() {
  const [res, tea] = await Promise.all([
    listResources({ pageSize: 100, status: 'AVAILABLE' }),
    listTeachers(),
  ])
  allResources.value = res.data.data!.items
  teachers.value = tea.data.data!
  if (teachers.value.length && !form.teacherId) {
    form.teacherId = teachers.value[0].id
  }
}

function openCreate() {
  editingId.value = null
  const now = new Date()
  const end = new Date(now.getTime() + 2 * 3600 * 1000)
  Object.assign(form, {
    expName: '',
    expType: '阻力试验',
    teacherId: teachers.value[0]?.id,
    startTime: toApiDateTime(now).slice(0, 16),
    endTime: toApiDateTime(end).slice(0, 16),
    purpose: '',
    planSummary: '',
    resources: [emptyResource()],
  })
  syncResourceTimes()
  formVisible.value = true
}

async function openEdit(row: Reservation) {
  const { data } = await getReservation(row.id)
  const d = data.data!
  editingId.value = d.id
  Object.assign(form, {
    expName: d.expName,
    expType: d.expType || '',
    teacherId: d.teacherId,
    startTime: d.startTime?.slice(0, 16),
    endTime: d.endTime?.slice(0, 16),
    purpose: d.purpose || '',
    planSummary: d.planSummary || '',
    resources: (d.resources || []).map((r) => ({
      resourceId: r.resourceId,
      resourceType: r.resourceType || '',
      quantity: r.quantity,
      startTime: r.startTime?.slice(0, 16) || '',
      endTime: r.endTime?.slice(0, 16) || '',
      remark: r.remark || '',
    })),
  })
  if (!form.resources.length) form.resources.push(emptyResource())
  formVisible.value = true
}

async function openDetail(row: Reservation) {
  const { data } = await getReservation(row.id)
  currentDetail.value = data.data!
  detailVisible.value = true
}

function syncResourceTimes() {
  const s = form.startTime ? `${form.startTime}:00` : ''
  const e = form.endTime ? `${form.endTime}:00` : ''
  form.resources.forEach((r) => {
    r.startTime = s
    r.endTime = e
  })
}

function onResourcePick(row: ReservationResource) {
  const res = allResources.value.find((x) => x.id === row.resourceId)
  if (res) row.resourceType = res.resourceType
}

function buildPayload() {
  syncResourceTimes()
  return {
    expName: form.expName,
    expType: form.expType,
    teacherId: form.teacherId,
    startTime: toApiDateTime(`${form.startTime}:00`),
    endTime: toApiDateTime(`${form.endTime}:00`),
    purpose: form.purpose,
    planSummary: form.planSummary,
    resources: form.resources
      .filter((r) => r.resourceId)
      .map((r) => ({
        resourceId: r.resourceId,
        resourceType: r.resourceType,
        quantity: r.quantity,
        startTime: toApiDateTime(r.startTime.length === 16 ? `${r.startTime}:00` : r.startTime),
        endTime: toApiDateTime(r.endTime.length === 16 ? `${r.endTime}:00` : r.endTime),
        remark: r.remark,
      })),
  }
}

async function saveDraft() {
  if (!form.resources.some((r) => r.resourceId)) {
    ElMessage.warning('请添加资源明细')
    return
  }
  const payload = buildPayload()
  if (editingId.value) {
    await updateReservation(editingId.value, payload)
  } else {
    await createReservation(payload)
  }
  ElMessage.success('草稿已保存')
  formVisible.value = false
  load()
}

async function onSubmit(row: Reservation) {
  const { data: conflictData } = await checkConflicts(row.id)
  if (conflictData.data!.hasConflict) {
    const list = conflictData.data!.conflicts
      .map((c) => `「${c.resourceName}」与 ${c.conflictReservationNo}（${c.conflictExpName}）冲突`)
      .join('\n')
    await ElMessageBox.alert(`检测到资源冲突：\n${list}`, '冲突检测', { type: 'warning' })
    return
  }
  await ElMessageBox.confirm('冲突检测通过。确认提交预约？提交后将进入教师审核。', '提示')
  await submitReservation(row.id)
  ElMessage.success('已提交')
  load()
}

async function onCancel(row: Reservation) {
  await ElMessageBox.confirm('确认取消该预约？', '提示', { type: 'warning' })
  await cancelReservation(row.id)
  ElMessage.success('已取消')
  load()
}

function openApproval(row: Reservation, mode: 'teacher' | 'director') {
  currentDetail.value = row
  approvalMode.value = mode
  approvalForm.approved = true
  approvalForm.comment = ''
  approvalVisible.value = true
}

async function submitApproval() {
  if (!approvalForm.approved && !approvalForm.comment) {
    ElMessage.warning('驳回须填写意见')
    return
  }
  const id = currentDetail.value!.id
  if (approvalMode.value === 'teacher') {
    await teacherReview(id, approvalForm.approved, approvalForm.comment)
  } else {
    await directorApprove(id, approvalForm.approved, approvalForm.comment)
  }
  ElMessage.success('审批完成')
  approvalVisible.value = false
  load()
}

const canCreate = () =>
  userStore.hasRole('STUDENT', 'TEACHER', 'ADMIN')

const canEdit = (row: Reservation) =>
  row.status === 'DRAFT' || row.status === 'REJECTED'

const canSubmit = (row: Reservation) =>
  (row.status === 'DRAFT' || row.status === 'REJECTED') &&
  (row.applicantId === userStore.user?.id || userStore.hasRole('ADMIN'))

const canCancel = (row: Reservation) =>
  ['PENDING_TEACHER', 'PENDING_DIRECTOR'].includes(row.status) &&
  (row.applicantId === userStore.user?.id || userStore.hasRole('ADMIN'))

const approvalSteps = computed(() => {
  if (!currentDetail.value) return []
  const d = currentDetail.value
  const steps: { title: string; status: 'finish' | 'wait' | 'error'; time: string }[] = [
    { title: '草稿', status: 'finish', time: d.createTime || '' },
    { title: '已提交', status: d.submitTime ? 'finish' : 'wait', time: d.submitTime || '' },
    { title: '教师审核', status: 'wait', time: '' },
    { title: '主任审批', status: 'wait', time: '' },
    { title: '生成任务', status: 'wait', time: '' },
  ]
  if (['PENDING_TEACHER', 'PENDING_DIRECTOR', 'APPROVED', 'COMPLETED', 'ARCHIVED'].includes(d.status)) {
    steps[1].status = 'finish'
  }
  if (['PENDING_DIRECTOR', 'APPROVED', 'COMPLETED', 'ARCHIVED'].includes(d.status)) {
    steps[2].status = 'finish'
  }
  if (['APPROVED', 'COMPLETED', 'ARCHIVED'].includes(d.status)) {
    steps[3].status = 'finish'
    steps[4].status = 'finish'
  }
  if (d.status === 'REJECTED') {
    steps[2].status = d.approvalLogs?.some((l) => l.stepType === 'TEACHER_REVIEW') ? 'error' : 'wait'
    steps[3].status = d.approvalLogs?.some((l) => l.stepType === 'DIRECTOR_APPROVAL') ? 'error' : 'wait'
  }
  return steps
})

onMounted(async () => {
  await loadOptions()
  await load()
})
</script>

<template>
  <el-card shadow="never">
    <div class="toolbar">
      <el-input v-model="query.keyword" placeholder="试验名称" clearable style="width: 180px" />
      <el-select v-model="query.status" placeholder="状态" clearable style="width: 150px">
        <el-option label="草稿" value="DRAFT" />
        <el-option label="待教师审核" value="PENDING_TEACHER" />
        <el-option label="待主任审批" value="PENDING_DIRECTOR" />
        <el-option label="已通过" value="APPROVED" />
        <el-option label="已驳回" value="REJECTED" />
      </el-select>
      <el-button type="primary" @click="load">查询</el-button>
      <el-button v-if="canCreate()" type="success" @click="openCreate">新建预约</el-button>
    </div>

    <el-table v-loading="loading" :data="tableData" stripe>
      <el-table-column prop="reservationNo" label="预约单号" width="170" />
      <el-table-column prop="expName" label="试验名称" />
      <el-table-column prop="applicantName" label="申请人" width="100" />
      <el-table-column prop="teacherName" label="指导教师" width="100" />
      <el-table-column label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.status)">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="计划时间" width="200">
        <template #default="{ row }">
          {{ row.startTime?.slice(0, 16) }} ~ {{ row.endTime?.slice(11, 16) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="340" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)">详情</el-button>
          <el-button v-if="canEdit(row)" link @click="openEdit(row)">编辑</el-button>
          <el-button v-if="canSubmit(row)" link type="success" @click="onSubmit(row)">提交</el-button>
          <el-button v-if="canCancel(row)" link type="warning" @click="onCancel(row)">取消</el-button>
          <el-button
            v-if="row.status === 'PENDING_TEACHER' && userStore.hasRole('TEACHER', 'ADMIN')"
            link
            type="primary"
            @click="openApproval(row, 'teacher')"
          >
            教师审核
          </el-button>
          <el-button
            v-if="row.status === 'PENDING_DIRECTOR' && userStore.hasRole('DIRECTOR', 'ADMIN')"
            link
            type="primary"
            @click="openApproval(row, 'director')"
          >
            主任审批
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

  <!-- 新建/编辑 -->
  <el-dialog v-model="formVisible" :title="editingId ? '编辑预约' : '新建预约'" width="720px">
    <el-form label-width="100px">
      <el-form-item label="试验名称" required>
        <el-input v-model="form.expName" />
      </el-form-item>
      <el-form-item label="试验类型">
        <el-input v-model="form.expType" />
      </el-form-item>
      <el-form-item label="指导教师" required>
        <el-select v-model="form.teacherId" style="width: 100%">
          <el-option
            v-for="t in teachers"
            :key="t.id"
            :label="t.realName"
            :value="t.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="开始时间" required>
        <el-date-picker
          v-model="form.startTime"
          type="datetime"
          value-format="YYYY-MM-DDTHH:mm"
          style="width: 100%"
          @change="syncResourceTimes"
        />
      </el-form-item>
      <el-form-item label="结束时间" required>
        <el-date-picker
          v-model="form.endTime"
          type="datetime"
          value-format="YYYY-MM-DDTHH:mm"
          style="width: 100%"
          @change="syncResourceTimes"
        />
      </el-form-item>
      <el-form-item label="试验目的">
        <el-input v-model="form.purpose" type="textarea" />
      </el-form-item>
      <el-form-item label="方案摘要">
        <el-input v-model="form.planSummary" type="textarea" />
      </el-form-item>
      <el-form-item label="资源明细" required>
        <el-button size="small" @click="form.resources.push(emptyResource())">添加资源</el-button>
        <el-table :data="form.resources" size="small" class="res-table">
          <el-table-column label="资源" width="200">
            <template #default="{ row }">
              <el-select
                v-model="row.resourceId"
                filterable
                placeholder="选择资源"
                @change="onResourcePick(row)"
              >
                <el-option
                  v-for="r in allResources"
                  :key="r.id"
                  :label="r.resourceName"
                  :value="r.id"
                />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="数量" width="80">
            <template #default="{ row }">
              <el-input-number v-model="row.quantity" :min="1" size="small" />
            </template>
          </el-table-column>
          <el-table-column label="备注">
            <template #default="{ row }">
              <el-input v-model="row.remark" size="small" />
            </template>
          </el-table-column>
          <el-table-column label="" width="60">
            <template #default="{ $index }">
              <el-button
                link
                type="danger"
                :disabled="form.resources.length <= 1"
                @click="form.resources.splice($index, 1)"
              >
                删
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="formVisible = false">取消</el-button>
      <el-button type="primary" @click="saveDraft">保存草稿</el-button>
    </template>
  </el-dialog>

  <!-- 详情：主表 + 从表 -->
  <el-dialog v-model="detailVisible" title="预约详情（主从表）" width="780px">
    <template v-if="currentDetail">
      <el-card shadow="never" class="master-card">
        <template #header>主表 EXP_RESERVATION</template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="单号">{{ currentDetail.reservationNo }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusTagType(currentDetail.status)">
              {{ statusLabel(currentDetail.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="试验名称" :span="2">{{ currentDetail.expName }}</el-descriptions-item>
          <el-descriptions-item label="申请人">{{ currentDetail.applicantName }}</el-descriptions-item>
          <el-descriptions-item label="教师">{{ currentDetail.teacherName }}</el-descriptions-item>
          <el-descriptions-item label="计划时间" :span="2">
            {{ currentDetail.startTime?.slice(0, 16) }} ~ {{ currentDetail.endTime?.slice(0, 16) }}
          </el-descriptions-item>
          <el-descriptions-item v-if="currentDetail.rejectReason" label="驳回原因" :span="2">
            {{ currentDetail.rejectReason }}
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <el-card shadow="never" class="detail-card">
        <template #header>从表 EXP_RESERVATION_RESOURCE（{{ currentDetail.resources?.length || 0 }} 条明细）</template>
        <el-table :data="currentDetail.resources" size="small" border>
          <el-table-column prop="resourceName" label="资源" />
          <el-table-column prop="resourceType" label="类型" width="90" />
          <el-table-column prop="quantity" label="数量" width="70" />
          <el-table-column label="占用时段" width="200">
            <template #default="{ row }">
              {{ row.startTime?.slice(0, 16) }} ~ {{ row.endTime?.slice(11, 16) }}
            </template>
          </el-table-column>
          <el-table-column prop="remark" label="备注" />
        </el-table>
      </el-card>

      <h4>审批流程</h4>
      <el-steps :active="approvalSteps.filter((s) => s.status === 'finish').length" finish-status="success" align-center>
        <el-step
          v-for="step in approvalSteps"
          :key="step.title"
          :title="step.title"
          :status="step.status"
        />
      </el-steps>

      <h4 v-if="currentDetail.approvalLogs?.length">审批日志 EXP_APPROVAL_LOG</h4>
      <el-timeline v-if="currentDetail.approvalLogs?.length">
        <el-timeline-item
          v-for="log in currentDetail.approvalLogs"
          :key="log.id"
          :timestamp="log.actionTime"
          :type="log.result === 'APPROVED' ? 'success' : 'danger'"
        >
          {{ log.approverName }} — {{ log.result === 'APPROVED' ? '通过' : '驳回' }}：{{ log.comment || '无' }}
        </el-timeline-item>
      </el-timeline>

      <el-button
        v-if="currentDetail.experimentTaskId"
        type="primary"
        @click="router.push({ name: 'experiments', query: { highlight: String(currentDetail.experimentTaskId) } })"
      >
        查看生成的试验任务 #{{ currentDetail.experimentTaskId }}
      </el-button>
    </template>
  </el-dialog>

  <!-- 审批 -->
  <el-dialog
    v-model="approvalVisible"
    :title="approvalMode === 'teacher' ? '教师审核' : '主任审批'"
    width="420px"
  >
    <el-form label-width="80px">
      <el-form-item label="结果">
        <el-radio-group v-model="approvalForm.approved">
          <el-radio :value="true">通过</el-radio>
          <el-radio :value="false">驳回</el-radio>
        </el-radio-group>
      </el-form-item>
      <el-form-item label="意见">
        <el-input v-model="approvalForm.comment" type="textarea" placeholder="驳回时必填" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="approvalVisible = false">取消</el-button>
      <el-button type="primary" @click="submitApproval">提交</el-button>
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
.res-table {
  margin-top: 8px;
  width: 100%;
}
.master-card,
.detail-card {
  margin-bottom: 12px;
}
h4 {
  margin: 16px 0 8px;
  font-size: 14px;
  color: #374151;
}
</style>
