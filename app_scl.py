import streamlit as st
import time
import json
import sys
import random
import os
from openai import OpenAI

# --- 1. 核心配置与环境检查 ---
ADMIN_PASSWORD = "admin" 
DATA_DIR = "experiment_data" 

# DeepSeek 配置
API_KEY = "sk" 
BASE_URL = "https://api.deepseek.com"

# 初始化 DeepSeek 客户端 (使用 OpenAI SDK 兼容模式)
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# 创建数据文件夹
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

if not st.runtime.exists():
    st.error("请在终端使用 `streamlit run plt_lab.py` 命令来启动此程序。")
    st.stop()

st.set_page_config(page_title="Writing Platform", layout="wide")

# --- 2. 角色权限判断 ---
# 管理员入口隐藏：通过 URL 参数 ?admin=true 开启
query_params = st.query_params
is_admin_mode = query_params.get("admin") == "true"

# --- 3. 题库配置 ---
TASK_POOL = [
    {"id": "task1", "content": "Some people think that it is more effective for students to study in a group while others believe that it is better for them to study alone."},
    {"id": "task2", "content": "Some people think technology mostly benefits our lives, while others believe it brings more disadvantages."},
    {"id": "task3", "content": "Government should protect culture. Therefore, some people believe that new buildings should be built in traditional styles."}
]

# --- 4. 界面样式 ---
st.markdown("""
    <style>
    .section-header {
        background-color: #f0f2f6;
        padding: 6px 12px;
        border-radius: 5px;
        margin-bottom: 8px;
        border-left: 5px solid #4CAF50;
    }
    .section-header h4 {
        font-size: 1.1rem !important;
        margin: 0;
        line-height: 1.2;
    }
    .stChatMessage { width: fit-content; max-width: 80%; margin-bottom: 10px; }
    div[data-testid="stChatMessage"]:has(div[aria-label="Chat message from user"]) {
        margin-left: auto; background-color: #e3f2fd; border-radius: 15px 15px 0 15px;
    }
    div[data-testid="stChatMessage"]:has(div[aria-label="Chat message from assistant"]) {
        margin-right: auto; background-color: #f1f8e9; border-radius: 15px 15px 15px 0;
    }
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 5. 初始化 Session ---
if "started" not in st.session_state:
    st.session_state.started = False
if "participant_id" not in st.session_state:
    st.session_state.participant_id = ""
if "condition" not in st.session_state:
    st.session_state.condition = "条件1" # 默认条件1  
if "current_task" not in st.session_state:
    st.session_state.current_task = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "essay_text" not in st.session_state:
    st.session_state.essay_text = ""
if "notes_text" not in st.session_state:
    st.session_state.notes_text = ""
if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False

# --- 6. 登录界面 ---
if not st.session_state.started:
    st.title("你好！")
    st.write("欢迎参加本次写作课程。请在下方输入您的信息。")
    
    col1, col2 = st.columns(2)
    with col1:
        pid = st.text_input("请输入编号:", value=st.session_state.participant_id)
    with col2:
        condition = st.selectbox("请选择组别:", ["组1", "组2", "组3"])
        
    if st.button("下一页", use_container_width=True):
        if pid.strip() == "":
            st.warning("请输入有效的编号。")
        else:
            st.session_state.participant_id = pid
            st.session_state.condition = condition
            # 随机抽取题目
            st.session_state.current_task = random.choice(TASK_POOL)
            st.session_state.started = True
            st.rerun()
    st.stop()

# --- 7. 侧边栏 (权限控制) ---
with st.sidebar:
    st.title("System Information")
    st.write(f"Current ID: {st.session_state.participant_id}")
    st.write(f"Condition: {st.session_state.condition}")
    
    # 管理员入口隐藏：仅在 URL 包含 ?admin=true 时显示
    if is_admin_mode:
        st.divider()
        with st.expander("管理入口"):
            pwd = st.text_input("输入管理密码", type="password")
            if pwd == ADMIN_PASSWORD:
                st.session_state.admin_authenticated = True
                st.success("管理模式已开启")
            elif pwd != "":
                st.error("密码错误")

        if st.session_state.admin_authenticated:
            st.subheader("管理操作")
            files = [f for f in os.listdir(DATA_DIR) if f.endswith('.json')]
            st.write(f"已收集记录: {len(files)} 份")
            
            if len(files) > 0:
                for filename in files:
                    with open(os.path.join(DATA_DIR, filename), "r", encoding="utf-8") as f:
                        st.download_button(label=f"下载: {filename}", data=f.read(), file_name=filename, key=filename, mime="application/json")
            
            if st.button("清空 Session (重置)"):
                st.session_state.clear()
                st.rerun()
    else:
        st.write("---")
        st.caption("课程进行中")

# --- 8. 主界面布局 ---
if st.session_state.condition == "Condition 1":
    # 条件1：上面 1/3 题目，下面 2/3 写作区
    st.markdown('<div class="section-header"><h4>写作题目</h4></div>', unsafe_allow_html=True)
    with st.container(height=200):
        if st.session_state.current_task:
            st.markdown(st.session_state.current_task['content'])
        else:
            st.warning("未找到写作任务，请重新进入实验。")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-header"><h4>笔记</h4></div>', unsafe_allow_html=True)
    st.session_state.essay_text = st.text_area("essay", value=st.session_state.essay_text, height=500, key="e_in_c1", placeholder="", label_visibility="collapsed")

    if st.button("结束课程", type="primary", use_container_width=True):
        save_data = {
            "participant_id": st.session_state.participant_id,
            "condition": st.session_state.condition,
            "task": st.session_state.current_task,
            "essay": st.session_state.essay_text,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        file_path = os.path.join(DATA_DIR, f"result_{st.session_state.participant_id}_{int(time.time())}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        st.balloons()
        st.success(f"提交成功！数据已存档。")

else:
    # 条件2 & 3：左上题目，右上写作区，下方 AI 对话区
    col_top_left, col_top_right = st.columns(2)
    
    with col_top_left:
        st.markdown('<div class="section-header"><h4>写作题目</h4></div>', unsafe_allow_html=True)
        with st.container(height=200):
            if st.session_state.current_task:
                st.markdown(st.session_state.current_task['content'])
    
    with col_top_right:
        st.markdown('<div class="section-header"><h4>笔记</h4></div>', unsafe_allow_html=True)
        st.session_state.essay_text = st.text_area("essay", value=st.session_state.essay_text, height=200, key="e_in_c23", placeholder="", label_visibility="collapsed")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-header"><h4>AI 对话</h4></div>', unsafe_allow_html=True)
    
    chat_container = st.container(height=600)
    with chat_container:
        for m in st.session_state.chat_history:
            if m["role"] != "system":
                with st.chat_message(m["role"]):
                    st.markdown(m["content"])

    if prompt := st.chat_input("向 AI 提问..."):
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        try:
            # 根据条件设置 System Prompt
            if st.session_state.condition == "组2":
                sys_prompt = "你是一位写作助手。你不能提供文章完整内容，只能提供建议、启发或局部修改意见。"
            else: # 条件3
                sys_prompt = "你是一位写作助手。你直接提供一篇文章供被试参考。"
                
            messages = [{"role": "system", "content": sys_prompt}] + st.session_state.chat_history

            response = client.chat.completions.create(
                model="gpt-4o", # 使用 GPT-4o
                messages=messages,
                stream=True
            )
            
            with chat_container:
                with st.chat_message("assistant"):
                    response_placeholder = st.empty()
                    full_response = ""
                    for chunk in response:
                        if chunk.choices[0].delta.content is not None:
                            full_response += chunk.choices[0].delta.content
                            response_placeholder.markdown(full_response + "▌")
                    response_placeholder.markdown(full_response)
            
            st.session_state.chat_history.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"AI 连接出错: {str(e)}")

    if st.button("结束写作", type="primary", use_container_width=True):
        save_data = {
            "participant_id": st.session_state.participant_id,
            "condition": st.session_state.condition,
            "task": st.session_state.current_task,
            "essay": st.session_state.essay_text,
            "chat": st.session_state.chat_history,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        file_path = os.path.join(DATA_DIR, f"result_{st.session_state.participant_id}_{int(time.time())}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        st.balloons()
        st.success(f"提交成功！数据已存档。")


