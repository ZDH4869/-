#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV 多列插值工具  v2.0
1. 以指定自变量列为基准，按固定间隔插值所有因变量列；
2. 支持 linear / nearest / polynomial / spline / log  共 5 种方法；
3. 原始满足间隔的因变量点 **不被修改**（先保留原始点，再插值缺失点）；
4. 自变量、因变量小数精度可分别设置；
5. 带进度条；输出列顺序 = [自变量, 因变量1, 因变量2, …]；
6. 全部可调参数集中放在“用户参数区”。
"""
import os
import pandas as pd
import numpy as np
from tqdm import tqdm
from scipy.interpolate import interp1d

# ============== 用户参数区（仅需修改这里） ==============
PARAM = {
    'input_csv':  r'E:\水电202303班\大三（上期）\课程报告或小组作业\防洪概论（调洪计算）\代码开发\原始曲线\3h入库流量过程线.csv',   # ① 输入文件
    'output_csv': r'E:\水电202303班\大三（上期）\课程报告或小组作业\防洪概论（调洪计算）\代码开发\曲线插值\插值1h入库流量过程线.csv',  # ② 输出文件
    'x_col':      '时间t/h',          # ③ 自变量列名 水位Z/m  时间t/h
    'x_step':     0.1,          # ④ 自变量插值间隔（浮点）
    'methods':    None,         # ⑤ 指定插值方法列表，None=全部
    # 可选: ['linear', 'nearest', 'polynomial', 'spline', 'log']
    'poly_order': 3,            # ⑥ 多项式阶数（仅 polynomial 有效）
    'spline_k':   3,            # ⑦ 样条阶数（仅 spline 有效）
    'encoding':   'gbk',        # ⑧ 文件编码 'gbk' 'utf-8' 'latin1'
    'x_precision': 0,           # ⑨ 自变量保留小数位
    'y_precision': 0,           # ⑩ 因变量保留小数位
}
# =========================================================

METHODS_ALL = ['linear', 'nearest', 'polynomial', 'spline', 'log']

def interpolate_df(df, x_col, x_new, methods, poly_order=3, spline_k=3, x_prec=1, y_prec=2):
    """
    对 df 做多列插值，返回 dict{method: DataFrame}。
    策略：先保留原始点（满足间隔的），再插值缺失点。
    """
    x_raw = df[x_col].values.astype(float)
    res = {}
    y_cols = [c for c in df.columns if c != x_col]

    for method in methods:
        interp_dfs = []
        for y_col in tqdm(y_cols, desc=f'Interpolating ({method})', leave=False):
            y_raw = df[y_col].values.astype(float)

            # 1) 先保留原始点（与 x_new 差值 < 1e-12 视为同点）
            mask_keep = np.isclose(x_raw[:, None], x_new[None, :], rtol=1e-12, atol=1e-12).any(axis=1)
            x_keep, y_keep = x_raw[mask_keep], y_raw[mask_keep]

            # 2) 需要插值的点
            x_miss = x_new[~np.isclose(x_new[:, None], x_keep[None, :], rtol=1e-12, atol=1e-12).any(axis=1)]

            # 3) 构造插值函数
            if method == 'log':
                # 对数插值：log(y) 线性插值后再指数还原
                log_y = np.log(y_raw + 1e-12)  # 防 0
                f_log = interp1d(x_raw, log_y, kind='linear', bounds_error=False, fill_value='extrapolate')
                y_miss = np.exp(f_log(x_miss))
            elif method == 'linear':
                f = interp1d(x_raw, y_raw, kind='linear', bounds_error=False, fill_value='extrapolate')
                y_miss = f(x_miss)
            elif method == 'nearest':
                f = interp1d(x_raw, y_raw, kind='nearest', bounds_error=False, fill_value='extrapolate')
                y_miss = f(x_miss)
            elif method == 'polynomial':
                p = np.poly1d(np.polyfit(x_raw, y_raw, poly_order))
                y_miss = p(x_miss)
            elif method == 'spline':
                f = interp1d(x_raw, y_raw, kind=f'cubic', bounds_error=False, fill_value='extrapolate')
                y_miss = f(x_miss)
            else:
                raise ValueError(f'Unsupported method: {method}')

            # 4) 合并：保留点 + 插值点
            x_comb = np.concatenate([x_keep, x_miss])
            y_comb = np.concatenate([y_keep, y_miss])
            # 按 x 排序
            order = np.argsort(x_comb)
            x_comb, y_comb = x_comb[order], y_comb[order]

            # 5) 精度控制
            x_comb = np.round(x_comb, x_prec)
            y_comb = np.round(y_comb, y_prec)

            interp_dfs.append(pd.Series(y_comb, name=y_col))

        out = pd.DataFrame({x_col: x_comb})
        out = pd.concat([out] + interp_dfs, axis=1)
        res[method] = out
    return res

def main():
    param = PARAM
    if not os.path.isfile(param['input_csv']):
        raise FileNotFoundError(param['input_csv'])

    methods = param['methods'] or METHODS_ALL
    methods = [m for m in methods if m in METHODS_ALL]

    df = pd.read_csv(param['input_csv'], encoding=param['encoding'])
    if param['x_col'] not in df.columns:
        raise KeyError(f'自变量列 "{param["x_col"]}" 不存在！')

    x_min, x_max = df[param['x_col']].min(), df[param['x_col']].max()
    x_new = np.arange(x_min, x_max + param['x_step'], param['x_step'])

    print(f'>>> 开始插值，方法：{methods}，范围：[{x_min:.3f}, {x_max:.3f}]，步长：{param["x_step"]}')
    results = interpolate_df(df, param['x_col'], x_new, methods,
                             poly_order=param['poly_order'],
                             spline_k=param['spline_k'],
                             x_prec=param['x_precision'],
                             y_prec=param['y_precision'])

    # 输出文件：若只一种方法直接写；多种方法则写多个文件（后缀区分）
    output_path = param['output_csv']
    base, ext = os.path.splitext(output_path)

    for method, out_df in results.items():
        if len(results) > 1:
            out_file = f'{base}_{method}{ext}'
        else:
            out_file = output_path
        out_df.to_csv(out_file, index=False, encoding='utf-8-sig')
        print(f'<<< 已保存：{out_file}  （行数：{len(out_df)}）')

if __name__ == '__main__':
    main()