<script setup lang="ts">
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
</script>

<template>
  <div class="dashboard">
    <el-card shadow="never">
      <template #header>
        <span>欢迎，{{ userStore.user?.realName }}</span>
      </template>
      <p>校园湖海试验场数字孪生全景监控与数据管理系统</p>
      <el-divider />
      <el-descriptions :column="2" border>
        <el-descriptions-item label="用户名">
          {{ userStore.user?.username }}
        </el-descriptions-item>
        <el-descriptions-item label="角色">
          <el-tag
            v-for="role in userStore.user?.roles"
            :key="role"
            size="small"
            style="margin-right: 4px"
          >
            {{ role }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>
      <el-alert
        class="tip"
        title="骨架已就绪"
        type="info"
        :closable="false"
        description="后续阶段将实现：试验预约主从表、资源管理、数字孪生监控、WebSocket 实时数据与 DeepSeek AI 分析。"
        show-icon
      />
    </el-card>
  </div>
</template>

<style scoped>
.dashboard {
  max-width: 960px;
}

.tip {
  margin-top: 20px;
}
</style>
