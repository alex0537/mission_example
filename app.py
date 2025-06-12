import streamlit as st
import time
import random

# --------------------------------------------------------------------------
# 1. 模拟后端逻辑
# --------------------------------------------------------------------------

# --- 设备状态模拟 ---
DEVICE_NAMES = ["机器人", "设备1", "设备2", "设备3", "设备4"]
POSSIBLE_STATUSES = {
    "空闲": "success", "运行中": "info", "维护中": "warning", "故障": "error"
}

def get_all_device_statuses():
    """模拟获取所有设备的状态。"""
    statuses = []
    for name in DEVICE_NAMES:
        status_key = random.choice(list(POSSIBLE_STATUSES.keys()))
        statuses.append({
            "name": name, "status": status_key, "type": POSSIBLE_STATUSES[status_key],
            "value": round(random.uniform(0, 100), 2)
        })
    return statuses

# --- 新增：任务状态模拟 ---
TASK_STEPS = ["等待指令", "抓取物料", "移动至设备1", "执行加工", "移动至设备2", "放置物料", "任务完成"]

def get_current_task_status():
    """模拟获取当前活动任务的状态。"""
    # 模拟有时没有任务的情况
    if random.random() < 0.2:
        return None

    current_step_index = random.randint(1, len(TASK_STEPS) - 2)
    total_seconds = random.randint(30, 300)
    step_seconds = random.randint(5, total_seconds if total_seconds > 5 else 6)

    return {
        "material_info": f"物料批次 #{random.randint(202500, 202599)}",
        "prev_step": TASK_STEPS[current_step_index - 1],
        "current_step": TASK_STEPS[current_step_index],
        "next_step": TASK_STEPS[current_step_index + 1],
        "total_time": total_seconds,
        "step_time": step_seconds
    }

def send_task_command(task_name, target_device, params, command):
    """模拟发送任务指令。"""
    print(f"指令已发送: [命令: {command}] -> [目标: {target_device}] -> [任务: {task_name}] -> [参数: {params}]")
    time.sleep(0.5)
    return (True, f"指令 '{command}' 已成功发送！") if random.random() > 0.1 else (False, "指令发送失败！")

# --------------------------------------------------------------------------
# 2. UI 辅助函数
# --------------------------------------------------------------------------

def format_seconds_to_ms(seconds):
    """将秒格式化为 MM:SS 格式。"""
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}:{secs:02d}"

def display_device_status(device_info):
    """渲染一个设备状态卡片。"""
    internal_status_type = device_info.get("type", "info")
    status_map = {"info": "running", "success": "complete", "warning": "complete", "error": "error"}
    st_status_state = status_map.get(internal_status_type, "running")

    st.metric(
        label=f"**{device_info['name']}**", value=device_info['status'],
        delta=f"利用率: {device_info.get('value', 'N/A')}%", delta_color="off"
    )
    with st.status(f"详细信息", state=st_status_state, expanded=False):
        st.write(f"最后更新: {time.strftime('%H:%M:%S')}")
        st.write(f"模式: 自动")

# --------------------------------------------------------------------------
# 3. 主应用逻辑
# --------------------------------------------------------------------------

st.set_page_config(layout="wide", page_title="设备监控与任务下发系统")
st.title("🤖 设备监控和任务下发系统")
st.markdown("---")

# --- 新增：第一部分: 任务实时状态 ---
st.header("任务实时状态")

# 获取当前任务状态
task_status = get_current_task_status()

# 使用带边框的容器来包裹任务状态，使其更突出
with st.container(border=True):
    if task_status:
        # 第一行：物料信息
        st.info(f"**当前物料信息**: {task_status['material_info']}", icon="📦")

        # 第二行：任务流程和计时
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("##### 任务流程")
            st.markdown(
                f"<span style='color: gray;'>{task_status['prev_step']}</span> → "
                f"**<span style='font-size: 1.1em;'>{task_status['current_step']}</span>** → "
                f"<span style='color: gray;'>{task_status['next_step']}</span>",
                unsafe_allow_html=True
            )
        with col2:
            st.metric(
                label="总用时",
                value=format_seconds_to_ms(task_status['total_time'])
            )
        with col3:
            st.metric(
                label="当前步骤用时",
                value=format_seconds_to_ms(task_status['step_time'])
            )
    else:
        st.info("当前无活动任务。", icon="💤")

st.markdown("---")


# --- 第二部分: 设备状态监控 ---
st.header("设备状态监控")

current_statuses = get_all_device_statuses()
columns = st.columns(len(DEVICE_NAMES))

for i, col in enumerate(columns):
    with col:
        display_device_status(current_statuses[i])

st.markdown("---")


# --- 第三部分: 任务下发控制 ---
st.header("任务下发控制")

col1, col2 = st.columns(2)
with col1:
    task_name_input = st.text_input("任务名称", placeholder="例如：执行A物料搬运")
with col2:
    target_device_input = st.selectbox("选择目标设备", options=DEVICE_NAMES)
task_params_input = st.slider("任务参数 (示例)", min_value=1, max_value=10, value=5)

btn_col1, btn_col2, btn_col3, _ = st.columns([1, 1, 1, 3])
with btn_col1:
    if st.button("🚀 下发任务", use_container_width=True, type="primary"):
        if task_name_input:
            success, message = send_task_command(task_name_input, target_device_input, task_params_input, "START")
            st.toast(f"✅ {message}" if success else f"❌ {message}", icon="✅" if success else "❌")
        else:
            st.warning("请输入任务名称！")
with btn_col2:
    if st.button("⏸️ 暂停任务", use_container_width=True):
        success, message = send_task_command("N/A", target_device_input, "N/A", "PAUSE")
        st.toast(f"⏸️ {message}" if success else f"❌ {message}", icon="⏸️" if success else "❌")
with btn_col3:
    if st.button("⏹️ 停止任务", use_container_width=True):
        success, message = send_task_command("N/A", target_device_input, "N/A", "STOP")
        st.toast(f"⏹️ {message}" if success else f"❌ {message}", icon="⏹️" if success else "❌")

# --- 侧边栏 ---
with st.sidebar:
    st.info("这是一个模拟系统。点击下方按钮手动刷新状态。")
    if st.button("🔄 刷新状态"):
        st.rerun()