"""数据表页面"""
import streamlit as st
import plotly.graph_objects as go
import os

from config import RESOURCE_GROUPS
from utils import load_capacity_from_csv, variables_to_dataframe


def table_page():
    """数据表界面"""
    st.title("📊 产能数据表")
    st.markdown("---")

    # 资源能力组选择
    col1, col2, col3 = st.columns([1.5, 1.5, 1])

    with col1:
        selected_group = st.selectbox(
            "📂 资源能力组",
            list(RESOURCE_GROUPS.keys()),
            help="选择要查看的资源能力组"
        )

    source_file = RESOURCE_GROUPS[selected_group]
    df = None
    raw_df = None

    # 加载数据
    if os.path.exists(source_file):
        try:
            variables, raw_df = load_capacity_from_csv(source_file)
            df = variables_to_dataframe(variables)
            st.success(f"✅ 已加载：{source_file}")
        except Exception as e:
            st. error(f"❌ 读取文件失败：{e}")
    else:
        st.warning(f"⚠️ 文件不存在：{source_file}")
        uploaded = st.file_uploader(
            f"上传 {selected_group} 的CSV文件",
            type=["csv"],
            key=f"upload_{selected_group}"
        )
        if uploaded:
            with open(source_file, 'wb') as f:
                f.write(uploaded.getvalue())
            st.success(f"✅ 文件已保存为：{source_file}")
            st.rerun()

    if df is not None:
        # 筛选功能
        with col2:
            if '日期' in df.columns:
                try:
                    years = sorted(list(set([str(d).split('_')[0] for d in df['日期'] if '_' in str(d)])))
                    selected_year = st.selectbox("筛选年份", ["全部"] + years)
                except: 
                    selected_year = "全部"
            else: 
                selected_year = "全部"

        with col3:
            if st.button("🔄 刷新数据"):
                st.rerun()

        # 筛选数据
        if selected_year != "全部" and '日期' in df.columns:
            df_filtered = df[df['日期'].astype(str).str.startswith(selected_year)]
        else:
            df_filtered = df

        # 显示数据表格
        st.markdown("### 📋 产能指标数据")
        st.dataframe(
            df_filtered,
            use_container_width=True,
            hide_index=True,
            column_config={
                "日期": st.column_config.TextColumn("日期", width="small"),
                "合格率": st.column_config.NumberColumn("合格率", format="%.4f"),
                "生产效率": st.column_config. NumberColumn("生产效率", format="%.4f"),
                "产能裕度": st.column_config.NumberColumn("产能裕度", format="%.4f"),
                "累计产能差异（%）": st.column_config. NumberColumn("累计产能差异（%）", format="%. 4f"),
            }
        )

        # 显示原始CSV数据
        if raw_df is not None: 
            with st.expander("📄 查看原始CSV数据", expanded=False):
                st.dataframe(raw_df, use_container_width=True, hide_index=True)

        # 快速图表
        st.markdown("---")
        st.markdown("### 📊 数据图")

        chart_metrics = st.multiselect(
            "选择要显示的指标",
            [col for col in df_filtered.columns if col != "日期"],
            default=["产能缺口（小时）", "基本需求（小时）", "有效产能", "峰值产能"]
            if "产能缺口（小时）" in df_filtered.columns else []
        )

        if chart_metrics and "日期" in df_filtered. columns:
            fig = go.Figure()
            x = df_filtered["日期"]

            for metric in chart_metrics: 
                # ① 柱状图（蓝色）
                if metric == "基本需求（小时）": 
                    fig.add_trace(go.Bar(
                        x=x,
                        y=df_filtered[metric],
                        name=metric,
                        marker=dict(color="rgba(30, 144, 255, 0.8)")
                    ))
                # ② 面积图（黄色）
                elif metric == "产能缺口（小时）":
                    fig.add_trace(go.Scatter(
                        x=x,
                        y=df_filtered[metric],
                        name=metric,
                        mode="lines",
                        fill="tozeroy",
                        fillcolor="rgba(255, 215, 0, 0.35)",
                        line=dict(color="gold", width=2)
                    ))
                # ③ 其余指标：折线图
                else:
                    fig.add_trace(go.Scatter(
                        x=x,
                        y=df_filtered[metric],
                        name=metric,
                        mode="lines+markers",
                        line=dict(width=2)
                    ))

            fig.update_layout(
                title=f"{selected_group} - 产能指标趋势",
                xaxis_title="日期",
                yaxis_title="数值",
                hovermode="x unified",
                height=600,
                barmode="overlay",
                template="plotly_white",
                legend=dict(orientation="h", yanchor="bottom", y=1.02)
            )

            st.plotly_chart(fig, use_container_width=True)