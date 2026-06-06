export const ROLE_LABELS: Record<string, string> = {
  ADMIN: '系统管理员',
  DIRECTOR: '试验场主任',
  TEACHER: '指导教师',
  STUDENT: '学生/研究员',
  MAINTAINER: '设备维护人员',
}

export const STATUS_LABELS: Record<string, string> = {
  DRAFT: '草稿',
  PENDING_TEACHER: '待教师审核',
  PENDING_DIRECTOR: '待主任审批',
  APPROVED: '已通过',
  REJECTED: '已驳回',
  CANCELLED: '已取消',
  COMPLETED: '已完成',
  ARCHIVED: '已归档',
  AVAILABLE: '可用',
  RESERVED: '已预约',
  IN_USE: '使用中',
  MAINTENANCE: '维护中',
  FAULT: '故障',
  DISABLED: '停用',
  PENDING_PREPARE: '待准备',
  READY: '已准备',
  RUNNING: '执行中',
  PENDING: '待处理',
  PROCESSING: '处理中',
  RESOLVED: '已处理',
  IGNORED: '已忽略',
}

export function statusLabel(status: string) {
  return STATUS_LABELS[status] || status
}

export function roleLabel(role: string) {
  return ROLE_LABELS[role] || role
}

export function statusTagType(status: string): '' | 'success' | 'warning' | 'danger' | 'info' {
  const map: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    DRAFT: 'info',
    PENDING_TEACHER: 'warning',
    PENDING_DIRECTOR: 'warning',
    APPROVED: 'success',
    REJECTED: 'danger',
    CANCELLED: 'info',
    RUNNING: 'success',
    READY: '',
    PENDING: 'warning',
    RESOLVED: 'success',
  }
  return map[status] || 'info'
}

/** 转为后端接受的 ISO 时间字符串 */
export function toApiDateTime(val: string | Date) {
  if (!val) return ''
  const d = typeof val === 'string' ? new Date(val) : val
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}
