# -*- coding: utf-8 -*-
import math
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
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

# 1. 瞬时单位线参数
N_VALUE = 1.5  # 瞬时单位线参数n (水库个数或调节次数)
K_VALUE = 5.68  # 瞬时单位线参数K (水库蓄量常数或汇流时间参数，小时)

# 2. 流域特征参数
BASIN_AREA = 349  # 流域面积 (km²)
TIME_INTERVAL = 3  # 时段长度 (小时)
NET_RAINFALL = 10  # 净雨量 (mm)

# 3. 计算时间范围设置
TIME_MIN = 0  # 最小计算时间 (小时)
TIME_MAX = 51  # 最大计算时间 (小时)

# 4. 标准曲线设置
STANDARD_CURVE_CSV = r'D:\Python pro\水文计算\水利信息化课程-代码开发\3-单位线\瞬时单位线\对比实际流量过程.csv'  # 标准曲线CSV文件路径
TIME_COLUMN = '时间（小时）'  # 时间列名
FLOW_COLUMN = '流量(m³/s)'  # 流量列名

# 5. 可视化设置
PLOT_SIZE = (12, 8)  # 图形尺寸 (宽, 高)
IMAGE_DPI = 300  # 输出图片分辨率
OUTPUT_IMAGE_NAME = '瞬时参数验证时段流量过程.png'  # 输出图片名称


# ==============================
# 函数定义区域
# ==============================

def iuh(t, n, K):
    """
    计算瞬时单位线值

    参数:
    t -- 时间 (小时)
    n -- 瞬时单位线参数n (水库个数或调节次数)
    K -- 瞬时单位线参数K (水库蓄量常数或汇流时间参数)

    返回:
    瞬时单位线值

    公式说明:
    u(t) = (t^(n-1) * e^(-t/K)) / (Γ(n) * K^n)
    其中Γ(n)是伽马函数，当n为正整数时，Γ(n) = (n-1)!
    """
    # 计算分子: t^(n-1) * e^(-t/K)
    numerator = (t ** (n - 1)) * math.exp(-t / K)

    # 计算分母: Γ(n) * K^n
    denominator = math.gamma(n) * (K ** n)

    # 返回瞬时单位线值
    return numerator / denominator


def s_curve(t, n, K):
    """
    计算S曲线值 (瞬时单位线的积分曲线)

    参数:
    t -- 时间 (小时)
    n -- 瞬时单位线参数n
    K -- 瞬时单位线参数K

    返回:
    S曲线值

    方法说明:
    通过对瞬时单位线从0到t进行数值积分得到S曲线
    使用步长为0.01小时的梯形法则进行近似计算
    """
    result = 0

    # 对t从0到t进行积分，步长为0.01
    for i in range(int(t * 100) + 1):
        # 计算瞬时单位线值
        iuh_value = iuh(i / 100, n, K)
        # 累加结果 (矩形法近似积分)
        result += iuh_value * 0.01

    return result


def duh(t, n, K, dt, p, F):
    """
    计算时段单位线值

    参数:
    t -- 时间 (小时)
    n -- 瞬时单位线参数n
    K -- 瞬时单位线参数K
    dt -- 时段长度 (小时)
    p -- 净雨量 (mm)
    F -- 流域面积 (km²)

    返回:
    时段单位线值 (m³/s)

    公式说明:
    Q(t) = [S(t) - S(t-dt)] * p * F / (dt * 3.6)
    其中:
    - S(t) 是t时刻的S曲线值
    - S(t-dt) 是t-dt时刻的S曲线值
    - p * F 是总水量 (mm * km²)
    - dt * 3.6 是单位转换系数，将mm·km²/h转换为m³/s
    """
    # 计算S曲线值
    s1 = s_curve(t, n, K)
    s2 = s_curve(t - dt, n, K) if t >= dt else 0

    # 计算时段单位线值
    duh_value = (s1 - s2) * p * F / (dt * 3.6)

    return duh_value


def read_standard_curve(csv_file):
    """
    从CSV文件读取标准曲线数据

    参数:
    csv_file -- CSV文件路径

    返回:
    time_data, flow_data -- 时间数据和流量数据
    """
    try:
        # 读取CSV文件
        df = pd.read_csv(csv_file)
        print(f"成功读取标准曲线文件: {csv_file}")

        # 检查必需的列是否存在
        if TIME_COLUMN not in df.columns or FLOW_COLUMN not in df.columns:
            print(f"错误: CSV文件中缺少必需的列 '{TIME_COLUMN}' 或 '{FLOW_COLUMN}'")
            return None, None

        # 提取数据
        time_data = df[TIME_COLUMN].values
        flow_data = df[FLOW_COLUMN].values

        print(f"标准曲线数据: 时间点={len(time_data)}, 流量点={len(flow_data)}")
        return time_data, flow_data

    except Exception as e:
        print(f"读取标准曲线文件时出错: {e}")
        return None, None


def main():
    """
    主函数：计算并绘制时段单位线
    """
    print("=" * 60)
    print("瞬时单位线转换为时段单位线计算")
    print("=" * 60)

    # 显示当前参数设置
    print(f"瞬时单位线参数: n={N_VALUE}, K={K_VALUE}")
    print(f"流域特征: 面积={BASIN_AREA} km², 时段长={TIME_INTERVAL}小时, 净雨量={NET_RAINFALL}mm")
    print(f"计算时间范围: {TIME_MIN}-{TIME_MAX}小时")
    print(f"标准曲线文件: {STANDARD_CURVE_CSV}")
    print()

    # 创建时间列表
    time_points = np.arange(TIME_MIN, TIME_MAX + TIME_INTERVAL, TIME_INTERVAL)

    # 计算每个时间点的时段单位线值
    print("正在计算时段单位线...")
    duh_values = []
    for t in time_points:
        value = duh(t, N_VALUE, K_VALUE, TIME_INTERVAL, NET_RAINFALL, BASIN_AREA)
        duh_values.append(value)

    # 输出结果
    print("\n时段单位线计算结果:")
    print("时间(小时)\t流量(m³/s)")
    print("-" * 30)
    for i, t in enumerate(time_points):
        print(f"{t:.1f}\t\t{duh_values[i]:.2f}")

    # 计算洪峰流量和出现时间
    peak_flow = max(duh_values)
    peak_time = time_points[duh_values.index(peak_flow)]
    print(f"\n洪峰流量: {peak_flow:.2f} m³/s, 出现时间: {peak_time}小时")

    # 读取标准曲线数据
    std_time, std_flow = read_standard_curve(STANDARD_CURVE_CSV)

    # 绘制图形
    plot_unit_hydrograph(time_points, duh_values, peak_flow, peak_time, std_time, std_flow)


def plot_unit_hydrograph(time_points, duh_values, peak_flow, peak_time, std_time=None, std_flow=None):
    """
    绘制时段单位线图形

    参数:
    time_points -- 时间点数组
    duh_values -- 时段单位线值数组
    peak_flow -- 洪峰流量
    peak_time -- 洪峰出现时间
    std_time -- 标准曲线时间数据
    std_flow -- 标准曲线流量数据
    """
    plt.figure(figsize=PLOT_SIZE)

    # 绘制计算得到的时段单位线
    plt.bar(time_points, duh_values, width=0.8 * TIME_INTERVAL,
            alpha=0.7, color='skyblue', edgecolor='blue', label='计算时段单位线')

    # 绘制计算流量过程线
    plt.plot(time_points, duh_values, 'ro-', markersize=4, linewidth=1.5, label='计算流量过程线')

    # 标记洪峰点
    plt.plot(peak_time, peak_flow, 's', markersize=10, color='red',
             label=f'计算洪峰({peak_flow:.1f}m³/s)')

    # 如果有标准曲线数据，绘制标准曲线
    if std_time is not None and std_flow is not None:
        plt.plot(std_time, std_flow, 'g^-', markersize=6, linewidth=2,
                 label='标准曲线', alpha=0.8)

        # 计算标准曲线的洪峰
        if len(std_flow) > 0:
            std_peak_flow = max(std_flow)
            std_peak_time = std_time[np.argmax(std_flow)]
            plt.plot(std_peak_time, std_peak_flow, 's', markersize=10, color='green',
                     label=f'标准洪峰({std_peak_flow:.1f}m³/s)')

            # 计算拟合误差
            mse = calculate_fit_error(time_points, duh_values, std_time, std_flow)
            print(f"计算曲线与标准曲线的均方根误差: {mse:.2f} m³/s")

    # 设置图形属性
    plt.title(
        f'瞬时单位线转换时段单位线\n(n={N_VALUE}, K={K_VALUE}, 时段长={TIME_INTERVAL}小时, 净雨量={NET_RAINFALL}mm)',
        fontsize=14)
    plt.xlabel('时间 (小时)', fontsize=12)
    plt.ylabel('流量 (m³/s)', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=10)

    # 设置x轴刻度
    plt.xticks(np.arange(0, TIME_MAX + 1, 6))

    # 添加参数信息框
    info_text = (f'流域面积: {BASIN_AREA} km²\n'
                 f'净雨量: {NET_RAINFALL} mm\n'
                 f'时段长: {TIME_INTERVAL} 小时\n'
                 f'洪峰流量: {peak_flow:.1f} m³/s\n'
                 f'洪峰时间: {peak_time} 小时')

    # 如果有标准曲线，添加拟合误差信息
    if std_time is not None and std_flow is not None and len(std_flow) > 0:
        mse = calculate_fit_error(time_points, duh_values, std_time, std_flow)
        info_text += f'\n均方根误差: {mse:.2f} m³/s'

    plt.text(0.02, 0.98, info_text,
             transform=plt.gca().transAxes, fontsize=10,
             verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    plt.tight_layout()
    plt.savefig(OUTPUT_IMAGE_NAME, dpi=IMAGE_DPI, bbox_inches='tight')
    plt.show()

    print(f"\n图形已保存至: {OUTPUT_IMAGE_NAME}")


def calculate_fit_error(calc_time, calc_flow, std_time, std_flow):
    """
    计算计算曲线与标准曲线的拟合误差

    参数:
    calc_time -- 计算曲线时间点
    calc_flow -- 计算曲线流量值
    std_time -- 标准曲线时间点
    std_flow -- 标准曲线流量值

    返回:
    rmse -- 均方根误差
    """
    # 创建标准曲线的插值函数
    from scipy import interpolate
    try:
        # 使用线性插值
        f_std = interpolate.interp1d(std_time, std_flow, bounds_error=False, fill_value=0)

        # 在计算曲线的时间点上评估标准曲线
        std_flow_interp = f_std(calc_time)

        # 计算均方根误差
        mse = np.mean((calc_flow - std_flow_interp) ** 2)
        rmse = np.sqrt(mse)

        return rmse
    except:
        # 如果插值失败，返回一个较大的误差值
        return 999.9


def example_calculation():
    """
    示例计算：使用不同的参数计算时段单位线
    """
    print("不同参数下的时段单位线比较:")

    # 参数组合
    parameters = [
        (2.0, 5.0, "n=2.0, K=5.0"),
        (1.5, 4.0, "n=1.5, K=4.0"),
        (2.5, 6.0, "n=2.5, K=6.0")
    ]

    # 固定参数
    F = 349  # 流域面积 (km²)
    dt = 3  # 时段长度 (小时)
    p = 10  # 净雨量 (mm)
    t_max = 51  # 最大时间 (小时)

    time_points = np.arange(0, t_max + dt, dt)

    plt.figure(figsize=(12, 8))

    for n, K, label in parameters:
        duh_values = []
        for t in time_points:
            value = duh(t, n, K, dt, p, F)
            duh_values.append(value)

        plt.plot(time_points, duh_values, 'o-', label=label, linewidth=2, markersize=4)

    plt.title('不同参数下的时段单位线比较', fontsize=14)
    plt.xlabel('时间 (小时)', fontsize=12)
    plt.ylabel('流量 (m³/s)', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.xticks(np.arange(0, t_max + 1, 6))
    plt.tight_layout()
    plt.savefig('comparison_unit_hydrograph.png', dpi=300)
    plt.show()


if __name__ == "__main__":
    # 全局设置字体
    plt.rcParams['font.family'] = font.get_name()
    plt.rcParams['font.size'] = font.get_size()

    # 执行主程序
    main()

    # 取消注释下面的行以查看不同参数的比较
    # example_calculation()