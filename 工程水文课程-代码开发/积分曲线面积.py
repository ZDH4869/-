import pandas as pd
import numpy as np
from scipy import integrate
from scipy.interpolate import interp1d
import csv

# 读取CSV文件
df = pd.read_csv("C:/Users/张德海（Jack）/Desktop/第二次作业.txt")  # 替换为你的文件路径

# 假设数据文件有三列：'日', '时', '流量(m³/s)'
df['时间'] = df['日'] + df['时'] / 24  # 将时间和日合并为一个时间轴（单位：日）

# 提取x和y值
x = df['时间'].values
y = df['流量(m³/s)'].values

# 定义起始时间
start_time_total = 11 + 4 / 24  # 11日4时

# 定义一个函数将时间转换为“xx日xx时”格式
def format_time(time_value):
    days = int(time_value)
    fractional_time = time_value - days
    hours = int(fractional_time * 24)
    hours = hours if 0 <= hours <= 23 else 23
    return f"{days}日{hours}时"

# 定义要计算的时间段（天数）
days_list = [4/24,1, 3, 5]

try:
    # 创建输出CSV文件
    with open('C:/Users/张德海（Jack）/Desktop/验证面积积分.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['时间天数', '积分区间开始', '积分区间结束', '梯形法则面积', '辛普森法则面积', '插值函数面积'])

        for n_days in days_list:
            max_trapezoid = 0
            max_simpson = 0
            max_interpolation = 0
            max_start = ""
            max_end = ""

            # 计算每个可能的n天窗口的最大值
            for start_index in range(len(x)):
                current_time = x[start_index]
                end_time = current_time + n_days
                end_index = start_index

                # 找到结束时间对应的索引
                while end_index < len(x) and x[end_index] < end_time:
                    end_index += 1

                # 如果结束时间超出数据范围，跳过
                if end_index >= len(x):
                    continue

                # 提取积分区间内的x和y值
                x_integral = x[start_index:end_index + 1]
                y_integral = y[start_index:end_index + 1]

                # 将时间差转换为秒
                time_diff_seconds = (x_integral - x_integral[0]) * 24 * 3600

                # 计算梯形法则积分
                trapezoid_integral = integrate.trapezoid(y_integral, time_diff_seconds)

                # 计算辛普森法则积分
                if len(x_integral) >= 2:
                    simpson_integral = integrate.simpson(y_integral, time_diff_seconds)
                else:
                    simpson_integral = None

                # 创建插值函数并计算积分
                if len(x_integral) >= 4:  # 确保有足够的点用于插值
                    f = interp1d(x_integral, y_integral, kind='cubic')  # 使用三次样条插值
                    x_smooth = np.linspace(x_integral[0], x_integral[-1], 1000)
                    time_diff_seconds_smooth = (x_smooth - x_integral[0]) * 24 * 3600
                    y_smooth = f(x_smooth)
                    interpolation_integral = integrate.trapezoid(y_smooth, time_diff_seconds_smooth)
                else:
                    interpolation_integral = None

                # 格式化时间
                formatted_start = format_time(x[start_index])
                formatted_end = format_time(x[end_index])

                # 更新最大值
                if trapezoid_integral > max_trapezoid:
                    max_trapezoid = trapezoid_integral
                    max_simpson = simpson_integral if simpson_integral is not None else max_simpson
                    max_interpolation = interpolation_integral if interpolation_integral is not None else max_interpolation
                    max_start = formatted_start
                    max_end = formatted_end

            # 写入最大值结果到CSV文件
            writer.writerow([
                f"{n_days}天",
                max_start, max_end,
                max_trapezoid,
                max_simpson,
                max_interpolation
            ])

    print("积分结果已保存到面积积分.csv文件中")

except PermissionError:
    print("无法写入文件，请确保文件未被其他程序占用，并且程序有权限写入目标文件夹。")