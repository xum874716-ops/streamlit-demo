"""数据输入页面"""
import streamlit as st
from config import RESOURCE_GROUPS


def input_page():
    """输入界面"""
    st.title("📝 数据输入")
    st.markdown("---")

    # 选择资源能力组
    selected_group = st.selectbox(
        "📂 选择资源能力组",
        list(RESOURCE_GROUPS.keys())
    )
    source_file = RESOURCE_GROUPS[selected_group]

    st.info(f"当前选择的资源组文件：{source_file}")

    # 添加文件上传功能
    uploaded = st.file_uploader(
        f"上传 {selected_group} 的CSV文件",
        type=["csv"],
        key=f"upload_input_{selected_group}"
    )
    if uploaded:
        with open(source_file, 'wb') as f:
            f. write(uploaded.getvalue())
        st.success(f"✅ 文件已保存为：{source_file}")
        st.rerun()