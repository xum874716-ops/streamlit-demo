"""产能分析页面"""
import streamlit as st
import plotly.graph_objects as go
import os

from config import RESOURCE_GROUPS
from utils import load_capacity_from_csv, variables_to_dataframe


def analysis_page():
    """分析界面"""
    st. title("📈 产能分析")
    st.markdown("---")

    # 资源能力组选择
    selected_group = st.selectbox(
        "📂 选择资源能力组",
        list(RESOURCE_GROUPS.keys())
    )

    source_file = RESOURCE_GROUPS[selected_group]

    if not os.path.exists(source_file):
        st.warning(f"⚠️ 文件不存在：{source_file}，请先在数据表页面上传")
        return

    try:
        variables, _ = load_capacity_from_csv(source_file)
        df = variables_to_dataframe(variables)
    except Exception as e:
        st.error(f"读取文件失败：{e}")
        return

    # 按日期排序
    if '日期' in df.columns:
        try:
            df['sort_key'] = df['日期'].apply(
                lambda x: (int(str(x).split('_')[0]), int(str(x).split('_AP')[1])) if '_AP' in str(x) else (0, 0)
            )
            df = df.sort_values('sort_key').reset_index(drop=True)
            df = df.drop('sort_key', axis=1)
        except:
            pass

    # 图表选项
    col1, col2 = st. columns([1, 3])
    with col1:
        chart_type = st.radio(
            "选择图表类型",
            ["综合对比图", "产能缺口趋势", "效率分析", "产能利用率"]
        )

    with col2:
        fig = _create_chart(chart_type, df, selected_group)
        st.plotly_chart(fig, use_container_width=True)

    # 显示关键指标
    _show_key_metrics(df)


def _create_chart(chart_type:  str, df, selected_group: str) -> go.Figure:
    """创建图表"""
    fig = go.Figure()

    if chart_type == "综合对比图":
        if '产能缺口（小时）' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['日期'], y=df['产能缺口（小时）'],
                name='产能缺口（小时）',
                mode='lines+markers',
                line=dict(color='red', width=2),
                marker=dict(size=8)
            ))

        if '基本需求（小时）' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['日期'], y=df['基本需求（小时）'],
                name='需求工时',
                mode='lines+markers',
                line=dict(color='blue', width=2),
                marker=dict(size=8)
            ))

        if '有效产能' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['日期'], y=df['有效产能'],
                name='有效产能',
                mode='lines+markers',
                line=dict(color='green', width=2),
                marker=dict(size=8)
            ))

        if '峰值产能' in df.columns:
            fig.add_trace(go. Scatter(
                x=df['日期'], y=df['峰值产能'],
                name='峰值产能',
                mode='lines+markers',
                line=dict(color='orange', width=2, dash='dash'),
                marker=dict(size=8)
            ))

        fig.update_layout(
            title=f'{selected_group} - 产能综合对比分析',
            xaxis_title='日期',
            yaxis_title='小时',
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=500
        )

    elif chart_type == "产能缺口趋势":
        if '产能缺口（小时）' in df.columns:
            colors = ['red' if gap > 0 else 'green' for gap in df['产能缺口（小时）']]
            fig.add_trace(go.Bar(
                x=df['日期'],
                y=df['产能缺口（小时）'],
                name='产能缺口',
                marker_color=colors
            ))

        fig.update_layout(
            title=f'{selected_group} - 产能缺口趋势分析',
            xaxis_title='日期',
            yaxis_title='产能缺口（小时）',
            height=500
        )

    elif chart_type == "效率分析": 
        if '合格率' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['日期'], y=df['合格率'] * 100,
                name='合格率 (%)',
                mode='lines+markers',
                line=dict(color='blue', width=2)
            ))

        if '生产效率' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['日期'], y=df['生产效率'] * 100,
                name='生产效率 (%)',
                mode='lines+markers',
                line=dict(color='green', width=2)
            ))

        fig.update_layout(
            title=f'{selected_group} - 效率指标分析',
            xaxis_title='日期',
            yaxis_title='百分比 (%)',
            height=500
        )

    else:  # 产能利用率
        if '基本需求（小时）' in df.columns and '有效产能' in df.columns:
            df['利用率'] = (df['基本需求（小时）'] / df['有效产能']) * 100

            fig.add_trace(go. Scatter(
                x=df['日期'], y=df['利用率'],
                name='产能利用率',
                mode='lines+markers',
                fill='tozeroy',
                line=dict(color='purple', width=2)
            ))

            fig.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="满负荷")
            fig.add_hline(y=80, line_dash="dash", line_color="orange", annotation_text="高负荷警戒")

            fig.update_layout(
                title=f'{selected_group} - 产能利用率分析',
                xaxis_title='日期',
                yaxis_title='利用率 (%)',
                height=500
            )
        else:
            fig.update_layout(title="数据不足，无法计算利用率")

    return fig


def _show_key_metrics(df):
    """显示关键指标"""
    st.markdown("---")
    st.subheader("📊 关键指标统计")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if '产能缺口（小时）' in df.columns:
            gap_months = len(df[df['产能缺口（小时）'] > 0])
            st.metric("存在缺口月份数", f"{gap_months} 个月")

    with col2:
        if '产能缺口（小时）' in df.columns:
            max_gap = df['产能缺口（小时）'].max()
            if max_gap > 0:
                max_gap_date = df. loc[df['产能缺口（小时）']. idxmax(), '日期']
                st.metric("最大产能缺口", f"{max_gap:.2f} 小时", delta=f"发生在 {max_gap_date}")
            else:
                st.metric("最大产能缺口", "0 小时", delta="无缺口")

    with col3:
        if '基本需求（小时）' in df.columns and '有效产能' in df.columns:
            avg_utilization = (df['基本需求（小时）']. sum() / df['有效产能'].sum()) * 100
            st.metric("平均产能利用率", f"{avg_utilization:.2f}%")

    with col4:
        if '产能差异（小时）' in df.columns and len(df) >= 2:
            trend = df['产能差异（小时）'].iloc[-1] - df['产能差异（小时）'].iloc[0]
            st.metric("产能差异趋势", f"{trend:.2f}", delta="改善" if trend > 0 else "恶化")