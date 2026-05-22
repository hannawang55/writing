import streamlit as st
import time
import json
import sys
import random

# --- 核心配置 ---
ADMIN_PASSWORD = "wanghy0505$"  # 修改数据管理平台入口密码

# 检查运行环境
if not st.runtime.exists():
    st.error("请在终端使用 `streamlit run app.py` 命令来启动此程序。")
    st.stop()

st.set_page_config(page_title="写作实验平台", layout="wide")

# --- 题库配置 ---
TASK_POOL = [
    {
        "id": 1,
        "content": "Some people think that it is more effective for students to study in a group while others believe that it is better for them to study alone. Discuss both views and give your own opinion. \n\nWord limit: 250-300 words in English."
    },
    {
        "id": 2,
        "content": "Some people think technology mostly benefits our lives, while others believe it brings more disadvantages. Discuss both views and give your own opinion. \n\nWord limit: 250-300 words in English."
    },
    {
        "id": 3,
        "content": "The trend of working from home has become popular. Some say it increases productivity, while others claim it leads to isolation. Discuss both views and give your own opinion. \n\nWord limit: 250-300 words in English."
    }
]

# --- 样式 ---
st.markdown("""
    <style>
    .section-header {
        background-color: #f0f2f6;
        padding: 8px 12px;
        border-radius: 5px;
        margin-bottom: 10px;
        border-left: 5px solid #4CAF50;
    }
    .block-container { padding-top: 2rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 初始化 Session ---
if "started" not in st.session_state:
    st.session_state.started = False
if "participant_id" not in st.session_state:
    st.session_state.participant_id = ""
if "current_task" not in st.session_state:
    st.session_state.current_task = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "essay_text" not in st.session_state:
    st.session_state.essay_text = ""
if "notes_text" not in st.session_state:
    st.session_state.notes_text = ""
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

# --- 登录界面 ---
if not st.session_state.started:
    st.title("你好！")
    st.write("欢迎参加本次写作实验。请在下方输入您的编号。")
    
    pid = st.text_input("请输入编号:", value=st.session_state.participant_id)
    
    if st.button("开始"):
        if pid.strip() == "":
            st.warning("请输入有效的编号。")
        else:
            st.session_state.participant_id = pid
            st.session_state.current_task = random.choice(TASK_POOL)
            st.session_state.started = True
            st.rerun()
    st.stop()

# --- 侧边栏 (权限控制) ---
with st.sidebar:
    st.title("系统信息")
    st.write(f"当前编号: {st.session_state.participant_id}")
    
    # 管理员入口
    with st.expander("管理入口"):
        pwd = st.text_input("输入管理密码", type="password")
        if pwd == ADMIN_PASSWORD:
            st.session_state.is_admin = True
            st.success("管理模式已开启")
        elif pwd != "":
            st.error("密码错误")

    # 仅在管理模式下显示的按钮
    if st.session_state.is_admin:
        st.divider()
        st.subheader("管理操作")
        
        if st.button("清空当前数据"):
            st.session_state.chat_history = []
            st.session_state.essay_text = ""
            st.session_state.notes_text = ""
            st.rerun()

        if st.button("结束实验并返回主页"):
            st.session_state.clear() # 完全重置
            st.rerun()

        st.subheader("数据导出")
        export_data = {
            "participant_id": st.session_state.participant_id,
            "task": st.session_state.current_task,
            "notes": st.session_state.notes_text,
            "essay": st.session_state.essay_text,
            "chat": st.session_state.chat_history,
            "timestamp": time.time()
        }
        st.download_button(
            label="下载 JSON 数据",
            data=json.dumps(export_data, indent=2, ensure_ascii=False),
            file_name=f"result_{st.session_state.participant_id}.json",
            mime="application/json"
        )

# --- 主界面布局 ---
col_left, col_right = st.columns(2)

# 左侧
with col_left:
    st.markdown('<div class="section-header"><h4>笔记</h4></div>', unsafe_allow_html=True)
    st.session_state.notes_text = st.text_area("notes", value=st.session_state.notes_text, height=180, key="n_in", label_visibility="collapsed")

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown('<div class="section-header"><h4>AI 对话</h4></div>', unsafe_allow_html=True)
    chat_container = st.container(height=450)
    with chat_container:
        for m in st.session_state.chat_history:
            with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("向 AI 提问..."):
        with chat_container:
            with st.chat_message("user"): st.markdown(prompt)
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        # 模拟 AI 回复
        full_response = f"我是您的写作助手。针对您关于“{prompt}”的问题..."
        with chat_container:
            with st.chat_message("assistant"): st.write(full_response)
        st.session_state.chat_history.append({"role": "assistant", "content": full_response})

# 右侧
with col_right:
    st.markdown('<div class="section-header"><h4>写作任务</h4></div>', unsafe_allow_html=True)
    with st.container(height=160):
        st.markdown(st.session_state.current_task['content'])

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown('<div class="section-header"><h4>作文</h4></div>', unsafe_allow_html=True)
    st.write(f"当前字数: {len(st.session_state.essay_text.split())}")
    
    st.session_state.essay_text = st.text_area("essay", value=st.session_state.essay_text, height=500, key="e_in", label_visibility="collapsed")
    
    if st.button("暂存作文", use_container_width=True):
        st.success("保存成功")