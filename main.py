# main.py

import uvicorn
from fastapi import FastAPI, HTTPException, status, Body
from typing import List, Optional
import uuid
import random
import time
from pydantic import BaseModel, Field, model_validator
from enum import Enum

# --- 1. Pydantic 数据模型 (从 schemas.py 导入) ---
# (为了方便，直接将上面定义的模型粘贴在这里)
# --- 设备模型 ---
class DeviceStatus(BaseModel):
    name: str = Field(..., description="设备名称", examples=["机器人"])
    status: str = Field(..., description="可读的状态", examples=["运行中"])
    type: str = Field(..., description="用于前端判断的状态类型", examples=["info"])
    value: float = Field(..., description="设备利用率或其他数值", examples=[75.5])

# --- 任务状态枚举 ---
class TaskState(str, Enum):
    PAUSED = "paused"
    STOPPED = "stopped"
    RUNNING = "running"

# --- 任务模型 ---
class ActiveTask(BaseModel):
    task_id: str = Field(..., description="任务的唯一ID", examples=[str(uuid.uuid4())])
    material_info: str = Field(..., description="当前物料信息", examples=["物料批次 #202533"])
    prev_step: str
    current_step: str
    next_step: str
    total_time: int = Field(..., description="总运行时长 (秒)")
    step_time: int = Field(..., description="当前步骤用时 (秒)")

class TaskInfo(ActiveTask):
    state: TaskState
    task_name: str
    target_device: str

# --- API 请求体模型 ---
class TaskCreate(BaseModel):
    task_name: str = Field(..., min_length=1, examples=["执行A物料搬运"])
    target_device: str = Field(..., examples=["设备1"])
    params: int = Field(..., examples=[5])

class TaskStateUpdate(BaseModel):
    state: TaskState

    @model_validator(mode='after')
    def check_state(self):
        if self.state not in [TaskState.PAUSED, TaskState.STOPPED]:
            raise ValueError("State must be either 'paused' or 'stopped'")
        return self


# --- 2. 模拟数据库和业务逻辑 ---
# 使用一个简单的字典来模拟数据库和当前状态
DB = {
    "active_task": None,  # 存储当前唯一的活动任务
    "devices": [
        {"name": "机器人", "status": "空闲", "type": "success", "value": 10.5},
        {"name": "设备1", "status": "空闲", "type": "success", "value": 5.2},
        {"name": "设备2", "status": "空闲", "type": "success", "value": 0.0},
        {"name": "设备3", "status": "空闲", "type": "success", "value": 1.2},
        {"name": "设备4", "status": "空闲", "type": "success", "value": 0.5},
    ]
}
TASK_STEPS = ["等待指令", "抓取物料", "移动至设备1", "执行加工", "移动至设备2", "放置物料", "任务完成"]

def update_db_states():
    """一个模拟器，随机更新设备和任务状态，让GET请求看起来是动态的"""
    # 随机更新设备状态
    for device in DB["devices"]:
        if random.random() < 0.2: # 20%概率改变状态
             statuses = {"空闲": "success", "运行中": "info", "故障": "error"}
             key = random.choice(list(statuses.keys()))
             device["status"] = key
             device["type"] = statuses[key]
        device["value"] = round(random.uniform(0, 100), 1)

    # 如果有活动任务，更新其时间
    if DB["active_task"] and DB["active_task"]["state"] == TaskState.RUNNING:
        DB["active_task"]["total_time"] += 1
        DB["active_task"]["step_time"] += 1


# --- 3. FastAPI 应用和路由定义 ---
app = FastAPI(
    title="设备监控与任务下发 API",
    description="一个用于设备监控和任务管理的RESTful API。",
    version="1.0.0",
)

@app.get("/api/v1/devices/", response_model=List[DeviceStatus], summary="获取所有设备状态")
def get_all_devices():
    """
    检索系统中所有设备的当前状态列表。
    这个数据用于前端的状态显示面板。
    """
    update_db_states() # 模拟实时变化
    return DB["devices"]

@app.get("/api/v1/tasks/active/", response_model=TaskInfo, summary="获取当前活动任务的状态")
def get_active_task():
    """
    获取当前正在活动（运行或暂停）的任务的详细信息。
    如果当前没有活动任务，则返回 404 Not Found。
    """
    update_db_states() # 模拟实时变化
    if DB["active_task"]:
        return DB["active_task"]
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="当前无活动任务")


@app.post("/api/v1/tasks/", response_model=TaskInfo, status_code=status.HTTP_201_CREATED, summary="下发一个新任务")
def create_task(task: TaskCreate):
    """
    创建一个新的任务。如果已有活动任务，会返回 409 Conflict。
    成功后，返回新创建任务的完整信息。
    """
    if DB["active_task"]:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="已有活动任务正在进行中，请先停止当前任务。")

    new_task = {
        "task_id": str(uuid.uuid4()),
        "task_name": task.task_name,
        "target_device": task.target_device,
        "material_info": f"物料批次 #{random.randint(202500, 202599)}",
        "prev_step": "开始",
        "current_step": TASK_STEPS[1],
        "next_step": TASK_STEPS[2],
        "total_time": 0,
        "step_time": 0,
        "state": TaskState.RUNNING,
    }
    DB["active_task"] = new_task
    return new_task


@app.patch("/api/v1/tasks/{task_id}/state/", response_model=TaskInfo, summary="更新任务状态 (暂停/停止)")
def update_task_state(task_id: str, state_update: TaskStateUpdate):
    """
    根据任务ID更新任务的状态。目前只支持更新为 'paused' 或 'stopped'。
    - **暂停 (paused)**: 任务计时将暂停。
    - **停止 (stopped)**: 任务将从活动任务中移除。
    """
    if not DB["active_task"] or DB["active_task"]["task_id"] != task_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"ID为 {task_id} 的任务不存在或不活动")

    if state_update.state == TaskState.PAUSED:
        DB["active_task"]["state"] = TaskState.PAUSED
        return DB["active_task"]
    elif state_update.state == TaskState.STOPPED:
        stopped_task = DB["active_task"].copy()
        stopped_task["state"] = TaskState.STOPPED
        DB["active_task"] = None  # 从活动任务中移除
        return stopped_task

# --- 4. 运行服务器 ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)