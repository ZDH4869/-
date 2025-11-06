# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from matplotlib.font_manager import FontProperties
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体，例如使用方正姚体字体
# 设置中文字体，使用绝对路径
font_path = r'D:\Python pro\水文计算\水利信息化课程-代码开发\2-马斯京根流量演算法\FZYTK.TTF'
font = FontProperties(fname=font_path, size=14)

# ==============================
# 用户可配置参数区域
# ==============================

# 1. 数据文件设置
CSV_FILE_PATH = r'D:\Python pro\水文计算\水利信息化课程-代码开发\3-单位线\瞬时单位线\降雨流量过程数据.csv'  # 输入数据CSV文件路径
OUTPUT_IMAGE_PATH = '瞬时单位线参数计算结果.png'  # 输出图片路径

# 2. 数据列名设置 (根据您的CSV文件列名调整)
TIME_COLUMN = 'Time'  # 时间列名
INPUT_COLUMN = 'R'  # 输入序列列名 (净雨过程或上游流量)
OUTPUT_COLUMN = 'Q'  # 输出序列列名 (出口断面流量过程)

# 3. 时间步长设置
TIME_STEP = 3  # 时间步长 (小时) - 根据您的数据，这是3小时

# 4. 可视化设置
PLOT_SIZE = (14, 8)  # 图形尺寸 (宽, 高)
IMAGE_DPI = 300  # 输出图片分辨率

# 5. 坐标轴设置
R_AXIS_LABEL = '净雨量 (mm)'  # 左侧Y轴标签 (输入序列)
Q_AXIS_LABEL = '流量 (m³/s)'  # 右侧Y轴标签 (输出序列)
R_COLOR = 'blue'  # 输入序列颜色
Q_COLOR = 'red'  # 输出序列颜色
TIME_INTERVAL = 6  # 时间轴刻度间隔 (小时)


# ==============================
# 主程序开始
# ==============================

def get_nk(r, qnq, dt):
    """
    计算瞬时单位线的N和K参数

    参数:
    r -- 输入数据序列 (净雨过程或上游流量过程)
    qnq -- 输出数据序列 (出口断面流量过程)
    dt -- 时间步长 (小时)

    返回:
    n, k -- 瞬时单位线的N和K参数
    n: 水库个数或调节次数
    k: 水库蓄量常数或汇流时间参数
    """
    nr = len(r)
    nq = len(qnq)

    print(f"输入数据: R序列长度={nr}, Q序列长度={nq}, 时间步长={dt}小时")

    # 计算输入序列的矩
    x1_r = np.sum(r * (2 * np.arange(1, nr + 1) - 1))
    x2_r = np.sum(r)
    x3_r = np.sum(r * (2 * np.arange(1, nr + 1) - 1) ** 2)

    # 计算输入序列的一阶矩和二阶矩
    mi1 = x1_r / x2_r * dt / 2
    mi2 = x3_r / x2_r * dt * dt / 4

    print(f"输入序列矩: mi1={mi1:.4f}, mi2={mi2:.4f}")

    # 计算输出序列的矩（使用梯形法则进行离散积分）
    xm = (qnq[:-1] + qnq[1:]) / 2
    x1_q = np.sum(xm * (2 * np.arange(1, nq) - 1))
    x2_q = np.sum(xm)
    x3_q = np.sum(xm * (2 * np.arange(1, nq) - 1) ** 2)

    # 计算输出序列的一阶矩和二阶矩
    mo1 = x1_q / x2_q * dt / 2
    mo2 = x3_q / x2_q * dt * dt / 4

    print(f"输出序列矩: mo1={mo1:.4f}, mo2={mo2:.4f}")

    # 计算方差
    ni2 = mi2 - mi1 ** 2
    no2 = mo2 - mo1 ** 2

    print(f"方差: ni2={ni2:.4f}, no2={no2:.4f}")

    # 计算N和K参数
    n = (mo1 - mi1) ** 2 / (no2 - ni2)
    k = (no2 - ni2) / (mo1 - mi1)

    print(f"中间参数: mo1={mo1:.4f}, mi1={mi1:.4f}, no2={no2:.4f}, ni2={ni2:.4f}")
    return n, k


def read_data_from_csv(csv_file):
    """
    从CSV文件读取数据

    参数:
    csv_file -- CSV文件路径

    返回:
    R, Q, dt -- 输入序列、输出序列和时间步长
    """
    try:
        df = pd.read_csv(csv_file)
        print("CSV文件内容:")
        print(df)

        # 检查必需的列是否存在
        required_columns = [TIME_COLUMN, INPUT_COLUMN, OUTPUT_COLUMN]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            print(f"错误: CSV文件中缺少以下列: {missing_columns}")
            return None, None, None

        # 提取数据
        R = df[INPUT_COLUMN].values
        Q = df[OUTPUT_COLUMN].values

        # 自动检测时间步长
        if len(df) > 1:
            auto_dt = df[TIME_COLUMN].iloc[1] - df[TIME_COLUMN].iloc[0]
            print(f"自动检测到时间步长: {auto_dt}小时")

            # 使用自动检测的时间步长，除非用户明确设置了不同的值
            if TIME_STEP != auto_dt:
                print(f"注意: 使用用户设置的时间步长 {TIME_STEP} 小时，而非自动检测的 {auto_dt} 小时")
                return R, Q, TIME_STEP
            else:
                return R, Q, auto_dt
        else:
            print(f"使用用户设置的时间步长: {TIME_STEP}小时")
            return R, Q, TIME_STEP

    except Exception as e:
        print(f"读取CSV文件时出错: {e}")
        return None, None, None


def main():
    """
    主函数：从文件读取数据并计算N、K参数
    """
    print("=" * 50)
    print("瞬时单位线N、K参数计算")
    print("=" * 50)

    # 显示当前配置
    print(f"数据文件: {CSV_FILE_PATH}")
    print(f"时间列: {TIME_COLUMN}")
    print(f"输入序列列: {INPUT_COLUMN}")
    print(f"输出序列列: {OUTPUT_COLUMN}")
    print(f"时间步长: {TIME_STEP}小时")
    print()

    # 检查文件是否存在
    if not os.path.exists(CSV_FILE_PATH):
        print(f"错误: 文件 {CSV_FILE_PATH} 不存在")
        print("请确保文件路径正确，或使用以下格式创建CSV文件:")
        print("Time,R,Q")
        print("5,19.4,0")
        print("8,59.4,180")
        print("11,42.4,700")
        print("...")
        return

    # 尝试从CSV文件读取数据
    R, Q, dt = read_data_from_csv(CSV_FILE_PATH)

    if R is not None:
        # 调用get_nk函数计算N、K参数
        N, K = get_nk(R, Q, dt)

        # 打印结果
        print("\n" + "=" * 50)
        print("瞬时单位线参数计算结果")
        print("=" * 50)
        print(f"N参数 (水库个数): {N:.4f}")
        print(f"K参数 (汇流时间): {K:.4f}")
        print(f"N: {N:.2f}, K: {K:.2f}")

        # 可视化输入输出过程线
        plot_hydrographs(R, Q, dt, N, K)

    else:
        print("无法读取数据文件，请检查文件格式")


def plot_hydrographs(R, Q, dt, N, K):
    """
    绘制输入输出过程线 - 使用双Y轴

    参数:
    R -- 输入序列
    Q -- 输出序列
    dt -- 时间步长
    N, K -- 瞬时单位线参数
    """
    fig, ax1 = plt.subplots(figsize=PLOT_SIZE)

    # 创建时间轴 - 使用实际时间值
    df = pd.read_csv(CSV_FILE_PATH)
    time_R = df[TIME_COLUMN].values[:len(R)]
    time_Q = df[TIME_COLUMN].values[:len(Q)]

    # 左侧Y轴 - 输入序列R
    color = R_COLOR
    ax1.set_xlabel('时间 (小时)', fontsize=12)
    ax1.set_ylabel(R_AXIS_LABEL, color=color, fontsize=12)
    line1 = ax1.plot(time_R, R, 'o-', color=color, linewidth=2, markersize=6, label='净雨过程 R')
    ax1.tick_params(axis='y', labelcolor=color)

    # 设置左侧Y轴范围和刻度
    r_max = max(R)
    r_interval = max(1, r_max // 10)  # 自动计算合适的刻度间隔
    ax1.set_ylim(0, r_max * 1.1)
    ax1.set_yticks(np.arange(0, r_max * 1.1, r_interval))

    # 右侧Y轴 - 输出序列Q
    ax2 = ax1.twinx()
    color = Q_COLOR
    ax2.set_ylabel(Q_AXIS_LABEL, color=color, fontsize=12)
    line2 = ax2.plot(time_Q, Q, 's-', color=color, linewidth=2, markersize=6, label='流量过程 Q')
    ax2.tick_params(axis='y', labelcolor=color)

    # 设置右侧Y轴范围和刻度
    q_max = max(Q)
    q_interval = max(100, q_max // 10)  # 自动计算合适的刻度间隔
    ax2.set_ylim(0, q_max * 1.1)
    ax2.set_yticks(np.arange(0, q_max * 1.1, q_interval))

    # 设置X轴范围和刻度
    time_min = min(time_R.min(), time_Q.min())
    time_max = max(time_R.max(), time_Q.max())
    ax1.set_xlim(time_min - dt, time_max + dt)
    ax1.set_xticks(np.arange(time_min, time_max + TIME_INTERVAL, TIME_INTERVAL))

    # 设置标题和网格
    plt.title(f'瞬时单位线参数计算\nN={N:.2f}, K={K:.2f}', fontsize=14)
    ax1.grid(True, alpha=0.3)

    # 合并图例
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper right', fontsize=12)

    # 添加参数信息
    plt.text(0.02, 0.98, f'时间步长: {dt}小时\nN={N:.3f}\nK={K:.3f}',
             transform=ax1.transAxes, fontsize=11,
             verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    fig.tight_layout()
    plt.savefig(OUTPUT_IMAGE_PATH, dpi=IMAGE_DPI, bbox_inches='tight')
    plt.show()

    print(f"图形已保存至: {OUTPUT_IMAGE_PATH}")


if __name__ == "__main__":
    # 全局设置字体
    plt.rcParams['font.family'] = font.get_name()
    plt.rcParams['font.size'] = font.get_size()

    # 执行主程序
    main()