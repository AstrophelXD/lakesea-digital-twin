<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const loading = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({
  username: 'student01',
  password: '123456',
})

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function onSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await userStore.login(form.username, form.password)
    ElMessage.success('登录成功')
    const redirect = (route.query.redirect as string) || '/dashboard'
    router.push(redirect)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <h1>湖海试验场数字孪生系统</h1>
      <p class="subtitle">校园湖海试验场全景监控与数据管理</p>
      <el-form ref="formRef" :model="form" :rules="rules" size="large" @submit.prevent="onSubmit">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名" prefix-icon="User" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            show-password
            prefix-icon="Lock"
            @keyup.enter="onSubmit"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" class="submit-btn" :loading="loading" @click="onSubmit">
            登 录
          </el-button>
        </el-form-item>
      </el-form>
      <div class="hint">
        <p>演示账号（密码均为 123456）：</p>
        <p>student01 · teacher01 · director01 · admin · maintainer01</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0f766e 0%, #134e4a 50%, #1e3a5f 100%);
}

.login-card {
  width: 420px;
  padding: 40px 36px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2);
}

h1 {
  margin: 0 0 8px;
  font-size: 22px;
  color: #0f766e;
  text-align: center;
}

.subtitle {
  margin: 0 0 28px;
  text-align: center;
  color: #6b7280;
  font-size: 13px;
}

.submit-btn {
  width: 100%;
}

.hint {
  margin-top: 16px;
  font-size: 12px;
  color: #9ca3af;
  line-height: 1.6;
  text-align: center;
}
</style>
