# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import warnings
import os

warnings.filterwarnings('ignore')

# ==============================
# 用户可配置参数区域
# ==============================

# 1. 文件路径设置
CSV_FILE_PATH = r'D:\Python pro\水文计算\水利信息化课程-代码开发\3-单位线\谢尔曼单位线\净雨量单位线输入数据.csv'
COMPARISON_CSV_PATH = r'D:\Python pro\水文计算\水利信息化课程-代码开发\3-单位线\谢尔曼单位线\对比实际出口流量.csv'
OUTPUT_IMAGE_PATH = '谢尔曼出口流量曲线.png'
OUTPUT_CSV_PATH = '谢尔曼单位线出口流量计算.csv'  # 输出CSV文件路径

# 2. 数据列名设置
DAY_COLUMN = '日'
HOUR_COLUMN = '时'
RAINFALL_COLUMN = '净雨量(mm)'
UNIT_FLOW_COLUMN = '单位线(m3/s)'
COMPARISON_FLOW_COLUMN = '流量(实际)(m3/s)'

# 3. 流域参数设置
BASIN_AREA = 3400  # 流域面积 (km²)
TIME_INTERVAL = 6  # 时间间隔 (小时)

# 4. 可视化设置
PLOT_SIZE = (14, 10)
IMAGE_DPI = 300
ENABLE_COMPARISON = True  # 设为False可禁用对比数据显示

# 5. 字体设置
FONT_PATH = r'D:\Python pro\水文计算\水利信息化课程-代码开发\2-马斯京根流量演算法\FZYTK.TTF'


# ==============================
# 主程序开始
# ==============================

def read_data_from_csv(csv_file, rainfall_col, unit_flow_col):
    """
    从CSV文件读取净雨量和单位线数据
    """
    try:
        df = pd.read_csv(csv_file)
        print("成功读取CSV文件:")
        print(df.head())

        required_columns = [DAY_COLUMN, HOUR_COLUMN, rainfall_col, unit_flow_col]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            print(f"错误: CSV文件中缺少以下列: {missing_columns}")
            print(f"CSV文件中的列: {list(df.columns)}")
            return None, None

        excess_rain = df[rainfall_col].values
        unit_direct_runoff = df[unit_flow_col].values

        print(f"净雨量数据: {len(excess_rain)} 个时段")
        print(f"单位线数据: {len(unit_direct_runoff)} 个时段")

        return excess_rain, unit_direct_runoff

    except Exception as e:
        print(f"读取CSV文件时出错: {e}")
        return None, None


def read_comparison_data(csv_file, flow_col):
    """
    从CSV文件读取实际流量对比数据（仅用于可视化）
    """
    try:
        df = pd.read_csv(csv_file)
        print("成功读取对比数据文件（仅用于可视化）:")
        print(df.head())

        required_columns = [DAY_COLUMN, HOUR_COLUMN, flow_col]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            print(f"警告: 对比数据文件中缺少以下列: {missing_columns}")
            print(f"对比数据文件中的列: {list(df.columns)}")
            return None

        comparison_flow = df[flow_col].values

        print(f"实际流量数据: {len(comparison_flow)} 个时段")

        return comparison_flow

    except Exception as e:
        print(f"读取对比数据文件时出错: {e}")
        return None


def calculate_flow(excess_rain, unit_direct_runoff, basin_area, time_interval):
    """
    计算出口流量 - 基于单位线法的卷积计算

    根据您的数据分析，单位线对应的是1cm净雨量，而不是1mm
    """
    print("\n流量计算分析:")
    print("=" * 40)

    # 分析单位线数据
    unit_peak = np.max(unit_direct_runoff)
    unit_sum = np.sum(unit_direct_runoff)
    print(f"单位线峰值: {unit_peak:.1f} m³/s")
    print(f"单位线总和: {unit_sum:.1f} m³/s")

    # 计算单位线对应的径流深
    unit_volume = unit_sum * time_interval * 3600  # m³
    unit_runoff_depth = unit_volume / (basin_area * 1e6) * 1000  # mm

    print(f"单位线总水量: {unit_volume:.0f} m³")
    print(f"单位线对应径流深: {unit_runoff_depth:.2f} mm")

    # 关键修正：您的单位线对应1cm净雨量，而不是1mm
    # 因此需要将净雨量从mm转换为cm
    excess_rain_cm = excess_rain / 10.0
    print(f"净雨量转换为cm单位: {excess_rain_cm}")

    # 使用卷积计算总流量过程
    Q = np.convolve(excess_rain_cm, unit_direct_runoff)

    return Q


def save_results_to_csv(time_dr, Q, output_csv_path):
    """
    将计算结果保存到CSV文件中
    """
    results_df = pd.DataFrame({
        '时间': time_dr,
        '计算流量': Q
    })
    results_df.to_csv(output_csv_path, index=False)
    print(f"计算结果已保存到: {output_csv_path}")


def main():
    """
    主函数：读取数据并计算出口流量
    """
    print("=" * 50)
    print("谢尔曼单位线法 - 出口流量计算")
    print("=" * 50)

    print(f"数据文件: {CSV_FILE_PATH}")
    print(f"流域面积: {BASIN_AREA} km²")
    print(f"时间间隔: {TIME_INTERVAL} 小时")
    print()

    if not os.path.exists(CSV_FILE_PATH):
        print(f"错误: 文件 {CSV_FILE_PATH} 不存在")
        return

    excess_rain, unit_direct_runoff = read_data_from_csv(CSV_FILE_PATH, RAINFALL_COLUMN, UNIT_FLOW_COLUMN)

    if excess_rain is None or unit_direct_runoff is None:
        print("无法读取数据，程序终止")
        return

    # 读取对比数据（仅用于可视化）
    comparison_flow = None
    if ENABLE_COMPARISON and os.path.exists(COMPARISON_CSV_PATH):
        comparison_flow = read_comparison_data(COMPARISON_CSV_PATH, COMPARISON_FLOW_COLUMN)

    # 创建时间序列
    time_rain = np.arange(len(excess_rain))

    # 使用修正的流量计算方法
    Q = calculate_flow(excess_rain, unit_direct_runoff, BASIN_AREA, TIME_INTERVAL)

    # 创建流量时间序列
    time_dr = np.arange(len(Q))

    # 输出结果
    print("\n计算结果:")
    print("=" * 50)
    print(f"净雨量总和: {excess_rain.sum():.2f} mm")
    print(f"计算最大流量: {Q.max():.2f} m³/s")
    print(f"计算洪峰出现时间: {time_dr[Q.argmax()]} 时段")

    # 设置中文字体
    try:
        font = FontProperties(fname=FONT_PATH, size=14)
        plt.rcParams['font.family'] = font.get_name()
        plt.rcParams['font.size'] = font.get_size()
    except:
        print("警告: 无法加载指定字体，使用系统默认字体")
        plt.rcParams['font.sans-serif'] = ['SimHei']

    # 绘制图形
    plot_results(time_rain, excess_rain, time_dr, Q, unit_direct_runoff, comparison_flow)

    # 保存计算结果到CSV文件
    save_results_to_csv(time_dr, Q, OUTPUT_CSV_PATH)


def plot_results(time_rain, excess_rain, time_dr, Q, unit_direct_runoff, comparison_flow=None):
    """
    绘制计算结果图形
    """
    plt.figure(figsize=PLOT_SIZE)

    # 子图1: 净雨量
    plt.subplot(3, 1, 1)
    plt.bar(time_rain, excess_rain, align="edge", width=1.0,
            color='lightblue', edgecolor='blue', alpha=0.7)
    plt.ylabel("净雨量 (mm)", fontsize=12)
    plt.xlim(0, len(excess_rain))
    plt.ylim(0, max(excess_rain) * 1.2)
    plt.grid(True, alpha=0.3)
    plt.title("谢尔曼单位线法 - 出口流量计算", fontsize=14)

    # 添加净雨量标注
    for i, rain in enumerate(excess_rain):
        if rain > 0:
            plt.text(i + 0.5, rain + max(excess_rain) * 0.05, f'{rain}mm',
                     ha='center', va='bottom', fontsize=9)

    # 子图2: 流量过程线
    plt.subplot(3, 1, 2)

    # 绘制计算流量
    plt.plot(time_dr, Q, 'g-', linewidth=2, label='计算流量', alpha=0.8)

    # 标记计算洪峰
    calc_peak_idx = Q.argmax()
    calc_peak_value = Q.max()
    plt.plot(calc_peak_idx, calc_peak_value, 'go', markersize=8, label=f'计算洪峰: {calc_peak_value:.0f} m³/s')

    # 如果有对比数据，绘制实际流量（仅用于可视化）
    if comparison_flow is not None:
        comparison_time = np.arange(len(comparison_flow))
        plt.plot(comparison_time, comparison_flow, 'r-', linewidth=2,
                 label='实际流量', alpha=0.8)

        # 标记实际洪峰
        actual_peak_idx = np.argmax(comparison_flow)
        actual_peak_value = comparison_flow.max()
        plt.plot(actual_peak_idx, actual_peak_value, 'ro', markersize=8,
                 label=f'实际洪峰: {actual_peak_value:.0f} m³/s')

    plt.xlabel("时间 (时段)", fontsize=12)
    plt.ylabel("流量 (m³/s)", fontsize=12)

    # 设置Y轴范围
    y_max = max(Q.max(), comparison_flow.max() if comparison_flow is not None else Q.max())
    plt.ylim(0, y_max * 1.1)
    plt.xlim(0, max(len(time_dr), len(comparison_flow) if comparison_flow is not None else len(time_dr)))
    plt.grid(True, alpha=0.3)
    plt.legend()

    # 子图3: 单位线
    plt.subplot(3, 1, 3)
    plt.bar(range(len(unit_direct_runoff)), unit_direct_runoff,
            align="center", width=0.8, color='orange',
            edgecolor='red', alpha=0.7)
    plt.xlabel("时段", fontsize=12)
    plt.ylabel("单位线 (m³/s)", fontsize=12)
    plt.grid(True, alpha=0.3)

    # 添加单位线峰值标注
    unit_peak_idx = unit_direct_runoff.argmax()
    unit_peak_value = unit_direct_runoff.max()
    plt.annotate(f'峰值: {unit_peak_value:.0f} m³/s',
                 xy=(unit_peak_idx, unit_peak_value),
                 xytext=(unit_peak_idx + 1, unit_peak_value * 0.8),
                 arrowprops=dict(arrowstyle='->', color='red'),
                 fontsize=10, color='red')

    # 添加总体信息框
    info_text = (f'流域面积: {BASIN_AREA} km²\n'
                 f'时间间隔: {TIME_INTERVAL} 小时\n'
                 f'净雨量总和: {excess_rain.sum():.1f} mm\n'
                 f'计算洪峰流量: {Q.max():.1f} m³/s')

    # 如果有对比数据，添加对比信息
    if comparison_flow is not None:
        info_text += f'\n实际洪峰流量: {comparison_flow.max():.1f} m³/s'

    plt.figtext(0.02, 0.02, info_text,
                bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
                fontsize=10)

    plt.tight_layout()
    plt.savefig(OUTPUT_IMAGE_PATH, dpi=IMAGE_DPI, bbox_inches='tight')
    plt.show()

    print(f"\n图形已保存至: {OUTPUT_IMAGE_PATH}")


if __name__ == "__main__":
    main()