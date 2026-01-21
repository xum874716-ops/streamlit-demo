"""CSV数据加载和处理工具"""
import pandas as pd
import numpy as np
import os
from typing import Dict, List, Tuple


def _read_csv_with_encodings(path: str) -> pd.DataFrame:
    """尝试多种编码读取 CSV"""
    last_err = None
    for enc in ("utf-8-sig", "utf-8", "gbk", "cp936", "latin1"):
        try:
            return pd.read_csv(path, header=None, dtype=str, encoding=enc)
        except Exception as e:
            last_err = e
    raise RuntimeError(f"无法读取文件：{path}，最后错误：{last_err}")


def _compose_month_labels(row_years: pd.Series, row_suffix: pd.Series, start_col: int = 2) -> Tuple[List[str], List[int]]:
    """组合两行表头生成月份标签与对应的列下标"""
    month_labels:  List[str] = []
    month_cols: List[int] = []
    for j in range(start_col, len(row_suffix)):
        y_raw = (row_years. iloc[j] if j < len(row_years) else "")
        s_raw = row_suffix.iloc[j]
        if pd.isna(s_raw):
            continue
        suffix = str(s_raw).strip()

        year = ""
        if not pd.isna(y_raw):
            y = str(y_raw).strip()
            if y: 
                try:
                    year = str(int(float(y)))
                except Exception:
                    year = y. split(".", 1)[0].strip()

        # 处理 AP 前缀
        suffix_clean = suffix.replace('AP', '').strip()
        label = f"{year}_AP{suffix_clean}" if year else suffix
        month_labels.append(label)
        month_cols.append(j)

    return month_labels, month_cols


def _find_row_index(df: pd.DataFrame, key: str) -> int:
    """在第0列中查找等于 key 的行索引"""
    matches = df.index[df. iloc[:, 0] == key]. tolist()
    return matches[0] if matches else -1


def _coerce_numeric(arr) -> np.ndarray:
    """将一组字符串数值安全转换为 float"""
    return pd.to_numeric(pd.Series(arr), errors="coerce").to_numpy(dtype=float)


def _extract_shift_resource(df: pd.DataFrame, month_cols: List[int]) -> Dict[str, np.ndarray]:
    """提取每班次工作资源能力数量"""
    res:  Dict[str, np.ndarray] = {}
    start = _find_row_index(df, "每班次工作资源能力数量")
    if start < 0:
        return res

    r = start
    while r < len(df):
        c0 = str(df. iat[r, 0]) if not pd.isna(df. iat[r, 0]) else ""
        c1 = str(df.iat[r, 1]) if not pd.isna(df.iat[r, 1]) else ""
        if c0.startswith("注：") or c0 in ("班次", "基础产能（小时）", "合格率", "生产效率"):
            break
        if c1 and c1 in ("一班", "二班", "三班", "四班"):
            vals = [df.iat[r, j] if j < df.shape[1] else np.nan for j in month_cols]
            res[c1] = _coerce_numeric(vals)
        r += 1
    return res


def _extract_shift_time_and_days(df: pd.DataFrame, month_cols: List[int]) -> Tuple[Dict[str, float], Dict[str, np.ndarray]]:
    """提取班次工作时间和月工作天数"""
    hours_map:  Dict[str, float] = {}
    days_map: Dict[str, np.ndarray] = {}

    start = _find_row_index(df, "班次")
    if start < 0:
        return hours_map, days_map

    r = start + 1
    while r < len(df):
        c0 = str(df.iat[r, 0]) if not pd.isna(df.iat[r, 0]) else ""
        if not c0 or c0 in ("加班", "基础产能（小时）", "合格率", "生产效率", "产能裕度", "峰值产能"):
            if not c0:
                r += 1
                continue
            break

        shift_name = c0
        hours_str = df.iat[r, 1]
        try:
            hours = float(hours_str) if hours_str not in (None, "", np.nan) else np.nan
        except Exception:
            hours = np.nan

        days_vals = [df.iat[r, j] if j < df. shape[1] else np.nan for j in month_cols]
        hours_map[shift_name] = 0.0 if np.isnan(hours) else hours
        days_map[shift_name] = _coerce_numeric(days_vals)
        r += 1

    return hours_map, days_map


def _extract_row_series(df: pd.DataFrame, row_name: str, month_cols: List[int]) -> np.ndarray:
    """按行名提取一行的各月数值"""
    idx = _find_row_index(df, row_name)
    if idx < 0:
        return None
    vals = [df.iat[idx, j] if j < df. shape[1] else np.nan for j in month_cols]
    return _coerce_numeric(vals)


def load_capacity_from_csv(csv_path: str) -> Tuple[Dict[str, pd.Series], pd.DataFrame]:
    """
    读取 CSV 并计算所有指标
    返回：(变量字典, 原始DataFrame用于显示)
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"未找到文件：{csv_path}")

    raw = _read_csv_with_encodings(csv_path)

    # 组合月份列标签与列下标
    month_labels, month_cols = _compose_month_labels(raw. iloc[0, :], raw.iloc[1, :], start_col=2)
    if not month_labels:
        raise ValueError("未解析到有效的月份列")

    # 提取班次资源数量
    shift_res = _extract_shift_resource(raw, month_cols)

    # 提取班次工时和工作天数
    shift_hours, shift_days = _extract_shift_time_and_days(raw, month_cols)

    # 计算基础产能
    base_capacity = np.zeros(len(month_cols), dtype=float)
    for shift in set(shift_res.keys()) | set(shift_hours.keys()) | set(shift_days.keys()):
        res_arr = shift_res.get(shift, np.zeros_like(base_capacity))
        hrs = shift_hours.get(shift, 0.0)
        days_arr = shift_days.get(shift, np.zeros_like(base_capacity))
        res_arr = np.nan_to_num(res_arr, nan=0.0)
        days_arr = np.nan_to_num(days_arr, nan=0.0)
        if not np.isnan(hrs):
            base_capacity += res_arr * hrs * days_arr

    # 读取表中直接给定的行
    base_capacity_row = _extract_row_series(raw, "基础产能（小时）", month_cols)
    if base_capacity_row is not None:
        mask = ~np.isnan(base_capacity_row)
        base_capacity[mask] = base_capacity_row[mask]

    # 读取基础参数
    yield_rate = _extract_row_series(raw, "合格率", month_cols)
    efficiency = _extract_row_series(raw, "生产效率", month_cols)
    margin = _extract_row_series(raw, "产能裕度", month_cols)
    demand = _extract_row_series(raw, "基本需求（小时）", month_cols)

    # 默认值填充
    if yield_rate is None:
        yield_rate = np.ones(len(month_cols), dtype=float)
    if efficiency is None: 
        efficiency = np.full(len(month_cols), 0.85, dtype=float)
    if margin is None:
        margin = np.full(len(month_cols), 0.2, dtype=float)
    if demand is None:
        demand = np.zeros(len(month_cols), dtype=float)

    # 计算各项指标
    effective_capacity = base_capacity * yield_rate * efficiency
    peak_capacity = effective_capacity * (1.0 + margin)
    diff_hours = effective_capacity - demand
    cum_diff_hours = np.cumsum(diff_hours)
    with np.errstate(divide="ignore", invalid="ignore"):
        diff_pct = np.where(demand > 0, diff_hours / demand, np.nan)
    capacity_gap = np.where(cum_diff_hours > 0, 0, cum_diff_hours)

    # 打包为 Series
    idx = pd.Index(month_labels, name="日期")

    variables = {
        "基础产能（小时）":  pd.Series(base_capacity, index=idx),
        "合格率": pd.Series(yield_rate, index=idx),
        "生产效率": pd. Series(efficiency, index=idx),
        "有效产能":  pd.Series(effective_capacity, index=idx),
        "产能裕度": pd.Series(margin, index=idx),
        "峰值产能":  pd.Series(peak_capacity, index=idx),
        "基本需求（小时）":  pd.Series(demand, index=idx),
        "产能差异（小时）": pd.Series(diff_hours, index=idx),
        "产能差异（%）": pd.Series(diff_pct, index=idx),
        "累计产能差异（小时）": pd.Series(cum_diff_hours, index=idx),
        "产能缺口（小时）": pd.Series(capacity_gap, index=idx),
    }

    return variables, raw


def variables_to_dataframe(variables: Dict[str, pd. Series]) -> pd.DataFrame:
    """将变量字典合并为 DataFrame"""
    df = pd.DataFrame(variables)
    df. index. name = "日期"
    df = df.reset_index()
    return df