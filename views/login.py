"""登录页面"""
import streamlit as st
from config import USERS


def login_page():
    """登录界面"""
    st.title("🏭 产能测算系统")
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.subheader("🔐 用户登录")

        with st.form("login_form"):
            username = st.text_input("用户名", placeholder="请输入用户名")
            password = st.text_input("密码", type="password", placeholder="请输入密码")
            submit = st.form_submit_button("登录", use_container_width=True)

            if submit:
                if username in USERS and USERS[username]["password"] == password:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.role = USERS[username]["role"]
                    st.session_state.current_page = "产能数据表"
                    st. success(f"登录成功！欢迎 {username}")
                    st.rerun()
                else:
                    st.error("用户名或密码错误！")

        st.markdown("---")
        st.info("💡 测试账号：admin / admin123")