"""产能模型页面"""
import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
import os
from datetime import datetime

from config import RESOURCE_GROUPS
from utils import load_capacity_from_csv, variables_to_dataframe


# 默认 Python 模型代码模板
DEFAULT_MODEL_CODE = '''"""
自定义产能计算模型

可用变量（DataFrame 列）：
- 基础产能（小时）
- 合格率
- 生产效率
- 有效产能
- 产能裕度
- 峰值产能
- 基本需求（小时）
- 产能差异（小时）
- 产能差异（%）
- 累计产能差异（小时）
- 产能缺口（小时）

返回：修改后的 DataFrame
"""

def custom_model(df:  pd.DataFrame) -> pd.DataFrame:
    """
    自定义模型函数
    
    参数: 
        df:  包含产能数据的 DataFrame
    
    返回: 
        处理后的 DataFrame
    """
    # 示例：计算新的指标
    
    # 1. 计算产能利用率
    df['产能利用率(%)'] = (df['基本需求（小时）'] / df['有效产能'] * 100).round(2)
    
    # 2. 计算产能富余
    df['产能富余（小时）'] = (df['有效产能'] - df['基本需求（小时）']).round(2)
    
    # 3. 计算综合效率 OEE
    df['综合效率OEE(%)'] = (df['合格率'] * df['生产效率'] * 100).round(2)
    
    # 4. 产能状态标记
    df['产能状态'] = df['产能利用率(%)'].apply(
        lambda x: '🔴 超负荷' if x > 100 else '🟡 高负荷' if x > 85 else '🟢 正常'
    )
    
    return df
'''

# Smart_AI API 配置模板
DEFAULT_API_CONFIG = {
    "name": "Smart_AI 产能预测模型",
    "url": "https://your-smart-ai-endpoint.com/api/workflow/run",
    "method": "POST",
    "headers": {
        "Content-Type": "application/json",
        "Authorization":  "Bearer your-api-key"
    },
    "body_template": {
        "workflow_id": "your-workflow-id",
        "inputs": {
            "capacity_data": "{{data}}"
        }
    }
}


def model_page():
    """产能模型界面"""
    st.title("🔧 产能模型")

    st.markdown("---")

    # 模型类型选择
    model_type = st.radio(
        "选择模型类型",
        ["📝 自定义模型", "🌐 调用模型 API（Smart_AI 等）"],
        horizontal=True
    )

    if model_type == "📝 自定义模型":
        _python_model_section()
    else:
        _api_model_section()


def _python_model_section():
    """自定义模型部分"""
    st.markdown("### 📝 自定义模型")
    st.info("编写 Python 代码来自定义产能计算逻辑，可以添加新的计算指标或修改现有计算方式。")

    # 资源组选择
    col1, col2 = st. columns([2, 1])
    with col1:
        selected_group = st.selectbox(
            "📂 选择资源能力组",
            list(RESOURCE_GROUPS.keys()),
            key="python_model_group"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        preview_data = st.checkbox("预览原始数据", value=False)

    source_file = RESOURCE_GROUPS[selected_group]

    # 加载数据
    df = None
    if os.path.exists(source_file):
        try:
            variables, _ = load_capacity_from_csv(source_file)
            df = variables_to_dataframe(variables)
            if preview_data:
                with st.expander("📊 原始数据预览", expanded=True):
                    st.dataframe(df, use_container_width=True, hide_index=True)
        except Exception as e:
            st. error(f"加载数据失败：{e}")
            return
    else:
        st.warning(f"⚠️ 文件不存在：{source_file}，请先在数据表页面上传")
        return

    # 代码编辑器
    st.markdown("#### 💻 模型代码编辑器")
    
    # 从 session_state 获取代码，如果没有则使用默认代码
    if 'model_code' not in st.session_state:
        st.session_state.model_code = DEFAULT_MODEL_CODE


    st.session_state. model_code = DEFAULT_MODEL_CODE

    model_code = st.text_area(
        "Python 代码",
        value=st.session_state.model_code,
        height=400,
        key="code_editor",
        help="编写自定义模型代码，必须定义 custom_model(df) 函数"
    )
    
    # 更新 session_state
    st.session_state.model_code = model_code

    # 执行模型
    col1, col2 = st. columns(2)
    with col1:
        if st.button("▶️ 运行模型", type="primary", use_container_width=True):
            _run_python_model(model_code, df, selected_group)
    with col2:
        if st.button("💾 保存模型代码", use_container_width=True):
            _save_model_code(model_code, selected_group)


def _api_model_section():
    """调用模型 API 部分"""
    st.markdown("### 🌐 调用模型 API")
    st.info("连接Smart_AI中模型 API，实现更复杂的产能分析和预测。")

    # API 配置
    tab1, tab2= st.tabs(["⚙️ API 配置", "📤 发送请求"])

    with tab1:
        _api_config_tab()

    with tab2:
        _api_request_tab()


def _api_config_tab():
    """API 配置标签页"""
    st.markdown("#### API 连接配置")

    # 从 session_state 加载配置
    if 'api_config' not in st. session_state:
        st. session_state.api_config = DEFAULT_API_CONFIG. copy()

    config = st.session_state.api_config

    col1, col2 = st. columns(2)
    
    with col1:
        config['name'] = st.text_input(
            "模型名称",
            value=config.get('name', ''),
            placeholder="例如：Smart_AI 产能预测模型"
        )
        
        config['url'] = st. text_input(
            "API 地址",
            value=config.get('url', ''),
            placeholder="https://your-api-endpoint.com/api/workflow/run"
        )
        
        config['method'] = st.selectbox(
            "请求方法",
            ["POST", "GET", "PUT"],
            index=["POST", "GET", "PUT"]. index(config. get('method', 'POST'))
        )

    with col2:
        # Headers 配置
        headers_str = json.dumps(config.get('headers', {}), indent=2, ensure_ascii=False)
        headers_input = st.text_area(
            "Headers (JSON 格式)",
            value=headers_str,
            height=150,
            help="JSON 格式的请求头配置"
        )
        try:
            config['headers'] = json.loads(headers_input)
        except json.JSONDecodeError:
            st.error("Headers 格式错误，请输入有效的 JSON")

    # Body 模板配置
    
    body_str = json.dumps(config.get('body_template', {}), indent=2, ensure_ascii=False)
    body_input = st.text_area(
        "Body Template (JSON 格式)",
        value=body_str,
        height=200,
        help="JSON 格式的请求体模板，{{data}} 会被替换为产能数据"
    )
    try:
        config['body_template'] = json.loads(body_input)
    except json.JSONDecodeError:
        st.error("Body 格式错误，请输入有效的 JSON")

    # 保存配置
    st.session_state.api_config = config

    col1, col2, col3 = st.columns(3)
    with col1:
        if st. button("💾 保存配置", use_container_width=True):
            _save_api_config(config)
            st.success("✅ 配置已保存")
    with col2:
        if st.button("🔄 重置配置", use_container_width=True):
            st.session_state.api_config = DEFAULT_API_CONFIG.copy()
            st.rerun()
    with col3:
        if st.button("📤 导出配置", use_container_width=True):
            config_json = json.dumps(config, indent=2, ensure_ascii=False)
            st.download_button(
                "下载配置文件",
                config_json,
                file_name="api_config.json",
                mime="application/json"
            )


def _api_request_tab():
    """API 请求标签页"""
    st.markdown("#### 发送 API 请求")

    # 资源组选择
    selected_group = st.selectbox(
        "📂 选择资源能力组",
        list(RESOURCE_GROUPS. keys()),
        key="api_model_group"
    )

    source_file = RESOURCE_GROUPS[selected_group]

    # 加载数据
    df = None
    if os.path.exists(source_file):
        try:
            variables, _ = load_capacity_from_csv(source_file)
            df = variables_to_dataframe(variables)
            
            with st.expander("📊 将发送的数据预览", expanded=False):
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.caption(f"共 {len(df)} 条记录")
        except Exception as e:
            st.error(f"加载数据失败：{e}")
            return
    else:
        st.warning(f"⚠️ 文件不存在：{source_file}")
        return

    # 显示当前配置
    config = st.session_state.get('api_config', DEFAULT_API_CONFIG)
    
    with st.expander("⚙️ 当前 API 配置", expanded=False):
        st.json(config)

    # 发送请求
    col1, col2 = st. columns(2)
    with col1:
        timeout = st.number_input("超时时间（秒）", min_value=5, max_value=300, value=60)
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        test_mode = st.checkbox("测试模式（不发送实际请求）", value=False)

    if st.button("🚀 发送请求", type="primary", use_container_width=True):
        _send_api_request(config, df, selected_group, timeout, test_mode)



def _run_python_model(code:  str, df: pd.DataFrame, group_name: str):
    """运行 Python 模型"""
    st.markdown("---")
    st.markdown("### 📊 模型运行结果")

    try:
        # 创建执行环境
        exec_globals = {
            'pd': pd,
            'np': np,
            'datetime': datetime,
        }
        exec_locals = {}

        # 执行代码
        exec(code, exec_globals, exec_locals)

        # 检查是否定义了 custom_model 函数
        if 'custom_model' not in exec_locals: 
            st.error("❌ 代码中未定义 `custom_model(df)` 函数")
            return

        # 运行模型
        with st.spinner("模型运行中..."):
            result_df = exec_locals['custom_model'](df.copy())

        if result_df is None:
            st.error("❌ 模型返回了 None，请检查代码")
            return

        if not isinstance(result_df, pd.DataFrame):
            st.error("❌ 模型必须返回 DataFrame 类型")
            return

        st.success("✅ 模型运行成功！")

        # 显示结果
        st.dataframe(result_df, use_container_width=True, hide_index=True)

        # 显示新增的列
        new_cols = set(result_df.columns) - set(df.columns)
        if new_cols:
            st.info(f"📌 新增指标列：{', '.join(new_cols)}")

        # 下载结果
        col1, col2 = st. columns(2)
        with col1:
            csv_data = result_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                "📥 下载结果 (CSV)",
                csv_data,
                file_name=f"模型结果_{group_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        with col2:
            excel_buffer = _df_to_excel(result_df)
            if excel_buffer:
                st. download_button(
                    "📥 下载结果 (Excel)",
                    excel_buffer,
                    file_name=f"模型结果_{group_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument. spreadsheetml.sheet",
                    use_container_width=True
                )

    except SyntaxError as e:
        st.error(f"❌ 语法错误：{e}")
        st.code(f"行 {e.lineno}: {e.text}")
    except Exception as e:
        st.error(f"❌ 运行错误：{type(e).__name__}: {e}")
        import traceback
        with st.expander("查看详细错误信息"):
            st.code(traceback.format_exc())


def _send_api_request(config: dict, df: pd.DataFrame, group_name: str, timeout: int, test_mode: bool):
    """发送 API 请求"""
    st.markdown("---")
    st.markdown("### 📬 API 响应")

    # 准备请求数据
    data_json = df.to_dict(orient='records')
    
    # 替换 body 模板中的占位符
    body = json.dumps(config.get('body_template', {}))
    body = body.replace('"{{data}}"', json.dumps(data_json))
    body = body.replace("'{{data}}'", json.dumps(data_json))
    
    try:
        body = json.loads(body)
    except json.JSONDecodeError:
        st.error("请求体构建失败")
        return

    # 显示将要发送的请求
    with st.expander("📤 请求详情", expanded=False):
        st.markdown(f"**URL:** `{config. get('url', '')}`")
        st.markdown(f"**Method:** `{config.get('method', 'POST')}`")
        st.markdown("**Headers:**")
        st.json(config.get('headers', {}))
        st.markdown("**Body:**")
        st.json(body)

    if test_mode:
        st. warning("⚠️ 测试模式：未发送实际请求")
        st.info("请求数据已准备就绪，取消勾选「测试模式」后点击发送")
        return

    # 发送请求
    try:
        with st.spinner("正在发送请求..."):
            response = requests.request(
                method=config.get('method', 'POST'),
                url=config.get('url', ''),
                headers=config.get('headers', {}),
                json=body,
                timeout=timeout
            )

        # 显示响应
        st.markdown(f"**状态码:** `{response.status_code}`")

        if response.status_code == 200:
            st.success("✅ 请求成功！")
            
            try:
                response_data = response.json()
                st.markdown("**响应数据:**")
                st.json(response_data)

                # 如果响应包含预测数据，尝试解析并显示
                if isinstance(response_data, dict):
                    _parse_api_response(response_data, group_name)

            except json.JSONDecodeError:
                st.markdown("**响应内容:**")
                st.text(response.text)
        else:
            st.error(f"❌ 请求失败")
            st.text(response.text)

    except requests. exceptions. Timeout:
        st.error(f"❌ 请求超时（{timeout}秒）")
    except requests.exceptions.ConnectionError:
        st.error("❌ 连接失败，请检查 API 地址是否正确")
    except Exception as e:
        st.error(f"❌ 请求错误：{e}")


def _parse_api_response(response_data: dict, group_name: str):
    """解析 API 响应数据"""
    # 尝试从响应中提取数据
    data_keys = ['data', 'result', 'output', 'predictions', 'forecast']
    
    for key in data_keys:
        if key in response_data:
            data = response_data[key]
            if isinstance(data, list) and len(data) > 0:
                try:
                    result_df = pd.DataFrame(data)
                    st.markdown("---")
                    st.markdown("### 📊 解析后的结果数据")
                    st.dataframe(result_df, use_container_width=True, hide_index=True)
                    
                    # 下载按钮
                    csv_data = result_df.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        "📥 下载结果 (CSV)",
                        csv_data,
                        file_name=f"API结果_{group_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                    return
                except Exception: 
                    pass


def _save_model_code(code: str, group_name: str):
    """保存模型代码"""
    filename = f"model_{group_name. replace(' ', '_')}.py"
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(code)
        st.success(f"✅ 代码已保存到：{filename}")
    except Exception as e:
        st.error(f"保存失败：{e}")


def _save_api_config(config: dict):
    """保存 API 配置"""
    try:
        with open('api_config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        st.error(f"保存失败：{e}")


def _df_to_excel(df:  pd.DataFrame):
    """将 DataFrame 转换为 Excel 字节流"""
    try:
        from io import BytesIO
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='模型结果')
        buffer.seek(0)
        return buffer.getvalue()
    except ImportError: 
        return None
    except Exception: 
        return None


def _get_forecast_model_template() -> str:
    """获取预测模型模板"""
    return '''"""
产能预测模型 - 基于移动平均的简单预测
"""

def custom_model(df: pd.DataFrame) -> pd.DataFrame:
    """
    使用移动平均进行产能预测
    """
    # 计算3期移动平均作为预测基准
    df['需求移动平均(3期)'] = df['基本需求（小时）']. rolling(window=3, min_periods=1).mean().round(2)
    
    # 计算需求环比增长率
    df['需求环比增长率(%)'] = (df['基本需求（小时）']. pct_change() * 100).round(2)
    
    # 计算趋势（基于线性回归斜率的简化版）
    df['需求趋势'] = df['基本需求（小时）']. diff().apply(
        lambda x: '📈 上升' if x > 0 else '📉 下降' if x < 0 else '➡️ 持平'
    )
    
    # 预测下期需求（简单外推）
    last_avg = df['需求移动平均(3期)'].iloc[-1]
    avg_growth = df['需求环比增长率(%)'].mean() / 100
    df['预测下期需求'] = np.nan
    df.loc[df. index[-1], '预测下期需求'] = round(last_avg * (1 + avg_growth), 2)
    
    # 产能充足性评估
    df['产能充足性'] = (df['有效产能'] - df['基本需求（小时）']).apply(
        lambda x: '✅ 充足' if x > 100 else '⚠️ 紧张' if x > 0 else '❌ 不足'
    )
    
    return df
'''


def _get_risk_model_template() -> str:
    """获取风险评估模型模板"""
    return '''"""
产能风险评估模型
"""

def custom_model(df: pd.DataFrame) -> pd.DataFrame:
    """
    多维度产能风险评估
    """
    # 1. 产能利用率风险
    df['产能利用率(%)'] = (df['基本需求（小时）'] / df['有效产能'] * 100).round(2)
    df['利用率风险'] = df['产能利用率(%)'].apply(
        lambda x: 3 if x > 95 else 2 if x > 85 else 1 if x > 70 else 0
    )
    
    # 2. 效率风险
    df['效率风险'] = df['生产效率']. apply(
        lambda x: 3 if x < 0.7 else 2 if x < 0.8 else 1 if x < 0.85 else 0
    )
    
    # 3. 质量风险
    df['质量风险'] = df['合格率'].apply(
        lambda x: 3 if x < 0.9 else 2 if x < 0.95 else 1 if x < 0.98 else 0
    )
    
    # 4. 缺口风险
    df['缺口风险'] = df['产能缺口（小时）'].apply(
        lambda x: 3 if x < -100 else 2 if x < -50 else 1 if x < 0 else 0
    )
    
    # 综合风险评分 (0-12分，越高风险越大)
    df['综合风险评分'] = df['利用率风险'] + df['效率风险'] + df['质量风险'] + df['缺口风险']
    
    # 风险等级
    df['风险等级'] = df['综合风险评分'].apply(
        lambda x: '🔴 高风险' if x >= 8 else '🟠 中高风险' if x >= 6 else '🟡 中风险' if x >= 4 else '🟢 低风险'
    )
    
    # 主要风险因素
    def get_main_risk(row):
        risks = {
            '利用率':  row['利用率风险'],
            '效率': row['效率风险'],
            '质量': row['质量风险'],
            '缺口':  row['缺口风险']
        }
        max_risk = max(risks.values())
        if max_risk == 0:
            return '无明显风险'
        return '、'.join([k for k, v in risks.items() if v == max_risk])
    
    df['主要风险因素'] = df.apply(get_main_risk, axis=1)
    
    return df
'''