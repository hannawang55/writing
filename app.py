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
API_KEY = "sk-f116ae9291604da5a741413c458de349" 
BASE_URL = "https://api.deepseek.com"

# 初始化 DeepSeek 客户端 (使用 OpenAI SDK 兼容模式)
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# 创建数据文件夹
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

if not st.runtime.exists():
    st.error("请在终端使用 `streamlit run app.py` 命令来启动此程序。")
    st.stop()

st.set_page_config(page_title="写作测试平台", layout="wide")

# --- 2. 角色权限判断 ---
query_params = st.query_params
is_admin_link = query_params.get("role") == "admin"

# --- 3. 题库配置 ---
TASK_POOL = [
    {"id": "A", "content": "Some people think that it is more effective for students to study in a group while others believe that it is better for them to study alone. \n\n**Task:** Discuss both views and give your own opinion.\n*Word limit: 250-300 words.*"},
    {"id": "B", "content": "Some people believe that technology has made education more accessible and effective, while others argue it distracts students. \n\n**Task:** Discuss both views and give your own opinion.\n*Word limit: 250-300 words.*"},
    {"id": "C", "content": "The trend of working from home has become popular. Some say it increases productivity, while others claim it leads to isolation. \n\n**Task:** Discuss both views and give your own opinion.\n*Word limit: 250-300 words.*"}
]

# --- 4. 界面样式 ---
st.markdown("""
    <style>
    .section-header {
        background-color: #f0f2f6;
        padding: 8px 12px;
        border-radius: 5px;
        margin-bottom: 10px;
        border-left: 5px solid #4CAF50;
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
    st.write("欢迎报名本次写作测试。如果您同意参加本次测试，请在下方输入您的编号。")
    pid = st.text_input("请输入编号:", value=st.session_state.participant_id)
    if st.button("进入实验"):
        if pid.strip() == "":
            st.warning("请输入有效的编号。")
        else:
            st.session_state.participant_id = pid
            st.session_state.current_task = random.choice(TASK_POOL)
            st.session_state.started = True
            st.rerun()
    st.stop()

# --- 7. 侧边栏 (权限控制) ---
with st.sidebar:
    st.title("系统信息")
    st.write(f"当前编号: {st.session_state.participant_id}")
    
    if is_admin_link:
        with st.expander("管理入口"):
            pwd = st.text_input("输入管理密码", type="password")
            if pwd == ADMIN_PASSWORD:
                st.session_state.admin_authenticated = True
                st.success("管理模式已开启")
            elif pwd != "":
                st.error("密码错误")

        if st.session_state.admin_authenticated:
            st.divider()
            st.subheader("管理操作")
            
            files = [f for f in os.listdir(DATA_DIR) if f.endswith('.json')]
            st.write(f"已收集记录: {len(files)} 份")
            
            if len(files) > 0:
                for filename in files:
                    with open(os.path.join(DATA_DIR, filename), "r", encoding="utf-8") as f:
                        st.download_button(label=f"下载: {filename}", data=f.read(), file_name=filename, mime="application/json")
            
            if st.button("重置当前页面"):
                st.session_state.clear()
                st.rerun()
    else:
        st.write("---")
        st.caption("实验进行中")

# --- 8. 主界面布局 ---
col_left, col_right = st.columns(2)

# 左侧
with col_left:
    st.markdown('<div class="section-header"><h4>笔记</h4></div>', unsafe_allow_html=True)
    st.session_state.notes_text = st.text_area("notes", value=st.session_state.notes_text, height=180, key="n_in", label_visibility="collapsed", placeholder="在此记录灵感或提纲...")

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown('<div class="section-header"><h4>AI对话</h4></div>', unsafe_allow_html=True)
    chat_container = st.container(height=450)
    with chat_container:
        for m in st.session_state.chat_history:
            if m["role"] != "system":
                with st.chat_message(m["role"]):
                    st.markdown(m["content"])

    if prompt := st.chat_input("向 AI 提问..."):
        # 1. 显示并保存用户消息
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        # 2. 调用 DeepSeek API
        try:
            messages = [
                {"role": "system", "content": "你是一位专业的写作助手。你的任务是启发式地引导学生，提供写作建议、语法纠错或逻辑润色，但不要直接帮学生写出整段作文。请使用中文交流。"} #修改写作条件的prompt
            ] + st.session_state.chat_history

            response = client.chat.completions.create(
                model="deepseek-chat", # 在此更改聊天模型
                messages=messages,
                stream=True,
                # 根据 DeepSeek 特色参数进行配置
                extra_body={
                    "thinking": {"type": "enabled"} 
                } if "thinking" in prompt else {} # 仅当用户提到思维或需要深度思考时开启
            )
            
            # 3. 流式显示 AI 回复
            with chat_container:
                with st.chat_message("assistant"):
                    response_placeholder = st.empty()
                    full_response = ""
                    for chunk in response:
                        if chunk.choices[0].delta.content is not None:
                            full_response += chunk.choices[0].delta.content
                            response_placeholder.markdown(full_response + "▌")
                    response_placeholder.markdown(full_response)
            
            # 4. 保存 AI 回复
            st.session_state.chat_history.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"AI 连接出错: {str(e)}")

# 右侧
with col_right:
    st.markdown('<div class="section-header"><h4>写作任务</h4></div>', unsafe_allow_html=True)
    with st.container(height=160):
        st.markdown(st.session_state.current_task['content'])

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown('<div class="section-header"><h4>作文撰写</h4></div>', unsafe_allow_html=True)
    
    if st.button("暂存作文", use_container_width=True):
        st.success("已暂存当前进度")

    st.write(f"当前字数: {len(st.session_state.essay_text.split())}")
    
    st.session_state.essay_text = st.text_area("essay", value=st.session_state.essay_text, height=450, key="e_in", placeholder="在这里开始写作...", label_visibility="collapsed")
    
    if st.button("提交作文", type="primary", use_container_width=True):
        save_data = {
            "participant_id": st.session_state.participant_id,
            "task": st.session_state.current_task,
            "notes": st.session_state.notes_text,
            "essay": st.session_state.essay_text,
            "chat": st.session_state.chat_history,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        file_path = os.path.join(DATA_DIR, f"result_{st.session_state.participant_id}_{int(time.time())}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        
        st.balloons()
        st.success(f"提交成功！数据已存档。")
