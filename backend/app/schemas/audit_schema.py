from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

MODULE_LABELS = {
    "AUTH": "认证",
    "USER": "用户管理",
    "RESOURCE": "资源设备",
    "RESERVATION": "试验预约",
    "EXPERIMENT": "试验任务",
    "MONITOR": "数字孪生监控",
    "ALARM": "告警管理",
    "AI": "AI 分析",
}

ACTION_LABELS = {
    "LOGIN": "登录",
    "LOGOUT": "退出",
    "CREATE": "创建",
    "UPDATE": "更新",
    "DELETE": "删除",
    "SUBMIT": "提交",
    "APPROVE": "审批通过",
    "REJECT": "驳回",
    "CANCEL": "取消",
    "READY": "准备完成",
    "START": "启动",
    "FINISH": "完成",
    "ARCHIVE": "归档",
    "HANDLE": "处理",
    "GENERATE": "生成",
    "RESET_PASSWORD": "重置密码",
    "DISABLE": "禁用",
    "ENABLE": "启用",
}


class OperationLogOut(BaseModel):
    id: int
    user_id: Optional[int] = Field(None, serialization_alias="userId")
    username: Optional[str] = None
    module: str
    module_label: Optional[str] = Field(None, serialization_alias="moduleLabel")
    action: str
    action_label: Optional[str] = Field(None, serialization_alias="actionLabel")
    target_type: Optional[str] = Field(None, serialization_alias="targetType")
    target_id: Optional[int] = Field(None, serialization_alias="targetId")
    detail: Optional[str] = None
    ip_address: Optional[str] = Field(None, serialization_alias="ipAddress")
    success: bool
    create_time: datetime = Field(serialization_alias="createTime")

    model_config = {"from_attributes": True, "populate_by_name": True}
