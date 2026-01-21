"""
产能测算系统 - 主程序入口
git init
git add .
git commit -m "init streamlit app"
git branch -M main
git remote add origin https://github.com/xum874716-ops/streamlit-demo.git
git push -u origin main

"""
import streamlit as st

from config import PAGE_CONFIG, PAGES, PAGE_ICONS
from views import (
    login_page,
    input_page,
    table_page,
    model_page,
    analysis_page,
    ai_page
)


# 页面配置
st.set_page_config(**PAGE_CONFIG)


def init_session_state():
    """初始化 session state"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = ""
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "登录"


def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        st. title("产能测算系统")
        st.markdown(f"👤 当前用户：**{st.session_state.username}**")
        st.markdown(f"🔑 角色：**{st.session_state.get('role', '普通用户')}**")
        st.markdown("---")

        for page in PAGES:
            icon = PAGE_ICONS. get(page, "")
            if st.button(
                f"{icon} {page}",
                use_container_width=True,
                type="primary" if st.session_state.current_page == page else "secondary"
            ):
                st. session_state.current_page = page
                st.rerun()

        st.markdown("---")
        if st.button("🚪 退出登录", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.current_page = "登录"
            st.rerun()

        st.markdown("---")
        st.caption("© 2026 产能测算系统 v1.2")


def route_page():
    """页面路由"""
    page_mapping = {
        "数据输入": input_page,
        "产能数据表": table_page,
        "产能模型": model_page,
        "产能分析": analysis_page,
        "AI分析": ai_page,
    }

    current = st.session_state.current_page
    page_func = page_mapping.get(current, table_page)
    page_func()


def main():
    """主函数"""
    init_session_state()

    if not st.session_state.logged_in:
        login_page()
        return

    render_sidebar()
    route_page()


if __name__ == "__main__":
    main()

