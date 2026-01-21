"""AI分析页面"""
import streamlit as st
from datetime import datetime
import os

from openai import OpenAI

from config import RESOURCE_GROUPS, DEEPSEEK_API_KEY
from utils import load_capacity_from_csv, variables_to_dataframe


def ai_page():
    """AI分析界面"""
    st.title("🤖 AI智能分析")
    st.markdown("基于DeepSeek AI的智能产能分析与建议")
    st.markdown("---")

    # 资源能力组选择
    selected_group = st.selectbox(
        "📂 选择分析的资源能力组",
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

    # 准备数据摘要
    summary = _generate_summary(df, selected_group)

    with st.expander("📋 查看数据摘要", expanded=True):
        st.text(summary)

    api_key = st.text_input(
        "DeepSeek API Key",
        value=DEEPSEEK_API_KEY if DEEPSEEK_API_KEY != "your-api-key-here" else "",
        type="password",
        help="请输入您的DeepSeek API Key"
    )

    analysis_type = st.selectbox(
        "选择分析类型",
        ["综合分析与建议", "产能优化建议", "风险预警分析", "增产方案建议"]
    )

    # 添加流式输出选项
    use_stream = st.checkbox("启用流式输出", value=True, help="实时显示AI生成的内容")

    if st.button("🚀 开始AI分析", use_container_width=True):
        if not api_key:
            st. error("请输入DeepSeek API Key")
            return

        _run_ai_analysis(api_key, analysis_type, summary, df, selected_group, use_stream)


def _generate_summary(df, selected_group:  str) -> str:
    """生成数据摘要"""
    return f"""
    产能数据分析摘要（{selected_group}）：

    1. 数据范围：{df['日期'].iloc[0]} 至 {df['日期'].iloc[-1]}，共 {len(df)} 个月

    2. 产能概况：
       - 平均基础产能：{df['基础产能（小时）'].mean():.2f} 小时
       - 平均有效产能：{df['有效产能']. mean():.2f} 小时
       - 平均峰值产能：{df['峰值产能'].mean():.2f} 小时

    3. 效率指标：
       - 平均合格率：{df['合格率'].mean()*100:.2f}%
       - 平均生产效率：{df['生产效率'].mean()*100:.2f}%

    4. 需求与缺口：
       - 平均基本需求：{df['基本需求（小时）'].mean():.2f} 小时
       - 总产能缺口：{df['产能缺口（小时）'].sum():.2f} 小时
       - 存在缺口的月份：{len(df[df['产能缺口（小时）'] > 0])} 个月
       - 最大单月缺口：{df['产能缺口（小时）'].max():.2f} 小时

    5. 产能利用率：{(df['基本需求（小时）']. sum() / df['有效产能'].sum()) * 100:.2f}%
    """


def _get_prompts(summary: str) -> dict:
    """获取分析提示词"""
    return {
        "综合分析与建议": f"请根据以下产能数据，进行综合分析，并提出改进建议：\n\n{summary}\n\n请从以下几个方面进行分析：\n1. 产能现状评估\n2. 效率分析\n3. 存在的问题\n4. 改进建议\n5. 未来预测",
        "产能优化建议": f"请根据以下产能数据，提出产能优化的具体建议：\n\n{summary}\n\n请重点关注：\n1. 如何提高合格率\n2. 如何提高生产效率\n3. 如何减少产能缺口\n4. 设备和人员优化建议",
        "风险预警分析": f"请根据以下产能数据，进行风险预警分析：\n\n{summary}\n\n请分析：\n1. 当前存在的风险\n2. 潜在风险预警\n3. 风险等级评估\n4. 风险应对措施",
        "增产方案建议": f"请根据以下产能数据，提出增产方案：\n\n{summary}\n\n请提供：\n1. 短期增产方案（1-3个月）\n2. 中期增产方案（3-6个月）\n3. 长期增产方案（6个月以上）\n4. 投资回报分析"
    }


def _run_ai_analysis(api_key:  str, analysis_type: str, summary: str, df, selected_group: str, use_stream: bool = True):
    """执行AI分析"""
    prompts = _get_prompts(summary)

    try:
        # 创建 OpenAI 客户端（使用 DeepSeek API）
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )

        messages = [
            {
                "role": "system",
                "content": "你是一位专业的生产管理和产能分析专家，擅长分析生产数据并提出专业建议。请用中文回答，结构清晰，建议具体可行。"
            },
            {
                "role": "user",
                "content": prompts[analysis_type]
            }
        ]

        if use_stream:
            # 流式输出
            _run_stream_analysis(client, messages, analysis_type, selected_group)
        else:
            # 非流式输出
            _run_normal_analysis(client, messages, analysis_type, selected_group)

    except Exception as e:
        st.error(f"发生错误：{str(e)}")
        st.info("💡 由于API暂时不可用，以下显示模拟分析结果：")
        mock_response = _generate_mock_analysis(analysis_type, df, selected_group)
        st.markdown(mock_response)


def _run_stream_analysis(client:  OpenAI, messages: list, analysis_type: str, selected_group: str):
    """流式输出分析"""
    st.markdown("---")
    st.markdown("### 🤖 AI分析结果")

    # 创建占位符用于流式显示
    response_placeholder = st.empty()
    full_response = ""

    with st.spinner("AI正在分析中..."):
        response = client.chat.completions. create(
            model="deepseek-chat",
            messages=messages,
            stream=True,
            temperature=0.7,
            max_tokens=2000
        )

        for chunk in response:
            if chunk.choices[0].delta. content is not None:
                full_response += chunk.choices[0].delta.content
                response_placeholder.markdown(full_response + "▌")

        # 移除光标，显示最终结果
        response_placeholder.markdown(full_response)

    st.success("✅ 分析完成！")

    # 下载按钮
    _show_download_button(full_response, analysis_type, selected_group)


def _run_normal_analysis(client: OpenAI, messages: list, analysis_type: str, selected_group: str):
    """非流式输出分析"""
    with st.spinner("AI正在分析中，请稍候..."):
        response = client. chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            stream=False,
            temperature=0.7,
            max_tokens=2000
        )

        ai_response = response.choices[0].message.content

        st.success("✅ 分析完成！")
        st.markdown("---")
        st.markdown("### 🤖 AI分析结果")
        st.markdown(ai_response)

        # 下载按钮
        _show_download_button(ai_response, analysis_type, selected_group)


def _show_download_button(content: str, analysis_type: str, selected_group: str):
    """显示下载按钮"""
    st.download_button(
        label="📥 下载分析报告",
        data=f"产能分析报告（{selected_group}）\n分析类型：{analysis_type}\n分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n{content}",
        file_name=f"AI分析报告_{selected_group}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain"
    )


def _generate_mock_analysis(analysis_type: str, df, group_name: str) -> str:
    """生成模拟分析结果"""
    avg_utilization = (df['基本需求（小时）'].sum() / df['有效产能'].sum()) * 100
    gap_months = len(df[df['产能缺口（小时）'] > 0])

    if analysis_type == "综合分析与建议": 
        return f"""
### 📊 产能现状评估（{group_name}）

根据数据分析，当前产能利用率为 **{avg_utilization:.1f}%**，整体处于{'较高' if avg_utilization > 85 else '适中'}水平。

### ⚡ 效率分析

- 平均合格率：{df['合格率'].mean()*100:.1f}%（{'良好' if df['合格率'].mean() > 0.95 else '需要提升'}）
- 平均生产效率：{df['生产效率'].mean()*100:.1f}%（{'良好' if df['生产效率'].mean() > 0.85 else '需要优化'}）

### ⚠️ 存在的问题

1. 共有 **{gap_months}** 个月存在产能缺口
2. 最大缺口达到 **{df['产能缺口（小时）'].max():.1f}** 小时

### 💡 改进建议

1. **短期**：优化排产计划，提高设备利用率
2. **中期**：引入精益生产，减少浪费
3. **长期**：考虑扩产或增加班次

### 📈 未来预测

基于当前趋势，建议在需求高峰期前 **提前2-3个月** 做好产能储备。
"""
    else: 
        return f"""
### 🔍 分析结果（{group_name}）

基于当前数据分析：
- 产能利用率：{avg_utilization:.1f}%
- 缺口月份：{gap_months} 个月
- 建议重点关注效率提升和需求预测准确性

请配置正确的API Key以获取更详细的分析结果。
"""