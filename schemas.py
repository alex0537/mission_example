'''
Description: 
Version: 1.0
Autor: wxchen
Date: 2025-06-12 23:43:17
LastEditTime: 2025-06-12 23:43:26
'''
# schemas.py

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
import uuid

# --- 设备模型 ---
class DeviceStatus(BaseModel):
    name: str = Field(..., description="设备名称", examples=["机器人"])
    status: str = Field(..., description="可读的状态", examples=["运行中"])
    type: str = Field(..., description="用于前端判断的状态类型", examples=["info"])
    value: float = Field(..., description="设备利用率或其他数值", examples=[75.5])

# --- 任务状态枚举 ---
class TaskState(str, Enum):
    """任务的控制状态"""
    PAUSED = "paused"
    STOPPED = "stopped"
    RUNNING = "running"


# --- 任务模型 ---
class ActiveTask(BaseModel):
    task_id: str = Field(..., description="任务的唯一ID", examples=[str(uuid.uuid4())])
    material_info: str = Field(..., description="当前物料信息", examples=["物料批次 #202533"])
    prev_step: str = Field(..., description="上一任务步骤")
    current_step: str = Field(..., description="当前任务步骤")
    next_step: str = Field(..., description="下一任务步骤")
    total_time: int = Field(..., description="总运行时长 (秒)")
    step_time: int = Field(..., description="当前步骤用时 (秒)")

class TaskInfo(ActiveTask):
    """任务的完整信息，包含控制状态"""
    state: TaskState = Field(..., description="任务的控制状态 (运行/暂停/停止)")
    task_name: str
    target_device: str

# --- API 请求体模型 ---
class TaskCreate(BaseModel):
    task_name: str = Field(..., min_length=1, description="任务的可读名称", examples=["执行A物料搬运"])
    target_device: str = Field(..., description="任务的目标设备名称", examples=["设备1"])
    params: int = Field(..., description="任务相关参数", examples=[5])

class TaskStateUpdate(BaseModel):
    # 使用 state: TaskState 可以在文档中生成下拉框，并且自动校验
    # 这里我们只允许暂停和停止操作
    state: TaskState = Field(..., description="要更新到的新状态 (只接受 'paused' 或 'stopped')")

    @model_validator(mode='after')
    def check_state(self):
        if self.state not in [TaskState.PAUSED, TaskState.STOPPED]:
            raise ValueError("State must be either 'paused' or 'stopped'")
        return self