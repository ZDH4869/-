import pandas as pd
import numpy as np
from scipy.interpolate import interp1d, splrep, splev, lagrange
from scipy.interpolate import NearestNDInterpolator
import os
from tqdm import tqdm
import warnings

warnings.filterwarnings('ignore')

# ================================
# 用户参数设置区域
# ================================

# 文件路径设置
input_file_path = r"E:\水电202303班\大三（上期）\课程报告或小组作业\防洪概论（调洪计算）\代码开发\原始曲线\3h入库流量过程线.csv"  # 输入CSV文件路径
output_folder_path = r"E:\水电202303班\大三（上期）\课程报告或小组作业\防洪概论（调洪计算）\代码开发\测试插值"  # 输出文件夹路径

# 插值参数设置
independent_column = "时间t/h"  # 自变量列名
interpolation_interval = 1  # 自变量插值间隔
interpolation_methods = []  # 特定的插值方法列表，为空则使用所有方法
# 可用的插值方法: ['nearest_two_point', 'linear', 'nearest', 'polynomial', 'spline', 'logarithmic']

# 文件编码设置
file_encoding = "utf-8"  # 读取CSV文件的编码格式

# 精度设置
independent_precision = 0  # 自变量小数位数
dependent_precision = 1  # 因变量小数位数


# ================================
# 插值函数定义
# ================================

def nearest_two_point_interpolation(x_original, y_original, x_new):
    """最邻近两点插值法"""
    y_new = []
    for x_val in x_new:
        # 找到最接近的两个点
        distances = np.abs(x_original - x_val)
        idx1 = np.argmin(distances)

        # 创建掩码排除第一个点
        mask = np.ones(len(distances), bool)
        mask[idx1] = False
        distances_masked = distances[mask]

        if len(distances_masked) > 0:
            idx2 = np.argmin(distances_masked)
            # 调整索引
            if idx2 >= idx1:
                idx2 += 1

            # 线性插值
            x1, x2 = x_original[idx1], x_original[idx2]
            y1, y2 = y_original[idx1], y_original[idx2]

            if x1 == x2:
                y_interp = y1
            else:
                y_interp = y1 + (y2 - y1) * (x_val - x1) / (x2 - x1)
        else:
            y_interp = y_original[idx1]

        y_new.append(y_interp)

    return np.array(y_new)


def linear_interpolation(x_original, y_original, x_new):
    """线性插值法"""
    interp_func = interp1d(x_original, y_original, kind='linear',
                           bounds_error=False, fill_value="extrapolate")
    return interp_func(x_new)


def nearest_interpolation(x_original, y_original, x_new):
    """最邻近插值法"""
    interp_func = interp1d(x_original, y_original, kind='nearest',
                           bounds_error=False, fill_value="extrapolate")
    return interp_func(x_new)


def polynomial_interpolation(x_original, y_original, x_new, degree=3):
    """多项式插值法"""
    try:
        # 使用拉格朗日插值
        poly = lagrange(x_original, y_original)
        return poly(x_new)
    except:
        # 如果失败，使用线性插值
        return linear_interpolation(x_original, y_original, x_new)


def spline_interpolation(x_original, y_original, x_new, degree=3):
    """样条插值法"""
    try:
        # 确保数据点足够
        if len(x_original) > degree:
            tck = splrep(x_original, y_original, k=degree, s=0)
            return splev(x_new, tck)
        else:
            return linear_interpolation(x_original, y_original, x_new)
    except:
        return linear_interpolation(x_original, y_original, x_new)


def logarithmic_interpolation(x_original, y_original, x_new):
    """对数插值法"""
    try:
        # 确保所有y值都为正数
        if np.all(y_original > 0):
            log_y = np.log(y_original)
            interp_func = interp1d(x_original, log_y, kind='linear',
                                   bounds_error=False, fill_value="extrapolate")
            log_y_new = interp_func(x_new)
            return np.exp(log_y_new)
        else:
            # 如果有非正数，使用线性插值
            return linear_interpolation(x_original, y_original, x_new)
    except:
        return linear_interpolation(x_original, y_original, x_new)


# 插值方法映射
INTERPOLATION_METHODS = {
    'nearest_two_point': {
        'function': nearest_two_point_interpolation,
        'name': '最邻近两点插值法'
    },
    'linear': {
        'function': linear_interpolation,
        'name': '线性插值法'
    },
    'nearest': {
        'function': nearest_interpolation,
        'name': '最邻近插值法'
    },
    'polynomial': {
        'function': polynomial_interpolation,
        'name': '多项式插值法'
    },
    'spline': {
        'function': spline_interpolation,
        'name': '样条插值法'
    },
    'logarithmic': {
        'function': logarithmic_interpolation,
        'name': '对数插值法'
    }
}


# ================================
# 主函数
# ================================

def interpolate_csv():
    """主函数：读取CSV文件并进行插值"""

    # 创建输出文件夹
    os.makedirs(output_folder_path, exist_ok=True)

    # 读取CSV文件
    try:
        df = pd.read_csv(input_file_path, encoding=file_encoding)
        print(f"成功读取文件: {input_file_path}")
        print(f"数据形状: {df.shape}")
        print(f"列名: {list(df.columns)}")
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return False

    # 检查自变量列是否存在
    if independent_column not in df.columns:
        print(f"错误: 自变量列 '{independent_column}' 不存在")
        print(f"可用的列: {list(df.columns)}")
        return False

    # 确定因变量列
    dependent_columns = [col for col in df.columns if col != independent_column]
    if not dependent_columns:
        print("错误: 没有找到因变量列")
        return False

    print(f"自变量列: {independent_column}")
    print(f"因变量列: {dependent_columns}")

    # 确定使用的插值方法
    if interpolation_methods:
        # 使用用户指定的方法
        available_methods = []
        for method in interpolation_methods:
            if method in INTERPOLATION_METHODS:
                available_methods.append(method)
            else:
                print(f"警告: 插值方法 '{method}' 不存在，已跳过")

        if not available_methods:
            print("错误: 没有可用的插值方法")
            return False
    else:
        # 使用所有方法
        available_methods = list(INTERPOLATION_METHODS.keys())

    print(f"使用的插值方法: {[INTERPOLATION_METHODS[m]['name'] for m in available_methods]}")

    # 准备数据
    x_original = df[independent_column].values
    y_originals = {col: df[col].values for col in dependent_columns}

    # 生成新的自变量值
    x_min, x_max = np.min(x_original), np.max(x_original)
    x_new = np.arange(x_min, x_max + interpolation_interval, interpolation_interval)
    x_new = np.round(x_new, independent_precision)

    print(f"原始数据点数: {len(x_original)}")
    print(f"插值后数据点数: {len(x_new)}")
    print(f"自变量范围: {x_min} ~ {x_max}")

    # 对每种方法进行插值
    results = {}

    for method in tqdm(available_methods, desc="插值方法进度"):
        method_name = INTERPOLATION_METHODS[method]['name']
        method_func = INTERPOLATION_METHODS[method]['function']

        print(f"\n正在使用 {method_name} 进行插值...")

        # 对每个因变量列进行插值
        method_results = {independent_column: x_new}

        for col in tqdm(dependent_columns, desc=f"{method_name}进度", leave=False):
            y_original = y_originals[col]

            try:
                # 执行插值
                if method in ['polynomial', 'spline']:
                    y_new = method_func(x_original, y_original, x_new)
                else:
                    y_new = method_func(x_original, y_original, x_new)

                # 设置精度
                y_new = np.round(y_new, dependent_precision)
                method_results[col] = y_new

            except Exception as e:
                print(f"警告: 对列 '{col}' 使用 {method_name} 插值时出错: {e}")
                # 使用线性插值作为备选
                y_new = linear_interpolation(x_original, y_original, x_new)
                y_new = np.round(y_new, dependent_precision)
                method_results[col] = y_new

        # 保存结果
        results[method] = pd.DataFrame(method_results)

    # 保存结果到文件
    base_name = os.path.splitext(os.path.basename(input_file_path))[0]

    for method, result_df in results.items():
        method_name_cn = INTERPOLATION_METHODS[method]['name']
        output_filename = f"{base_name}_{method}_插值结果.csv"
        output_path = os.path.join(output_folder_path, output_filename)

        try:
            # 确保列顺序：自变量列、因变量列
            column_order = [independent_column] + dependent_columns
            result_df = result_df[column_order]

            result_df.to_csv(output_path, index=False, encoding='utf-8-sig')
            print(f"已保存: {output_path}")
        except Exception as e:
            print(f"保存文件 {output_path} 时出错: {e}")

    # 生成汇总报告
    generate_summary_report(results, base_name)

    return True


def generate_summary_report(results, base_name):
    """生成插值结果汇总报告"""
    report_path = os.path.join(output_folder_path, f"{base_name}_插值报告.txt")

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("CSV文件插值处理报告\n")
        f.write("=" * 50 + "\n")
        f.write(f"输入文件: {input_file_path}\n")
        f.write(f"输出文件夹: {output_folder_path}\n")
        f.write(f"自变量列: {independent_column}\n")
        f.write(f"插值间隔: {interpolation_interval}\n")
        f.write(f"自变量精度: {independent_precision} 位小数\n")
        f.write(f"因变量精度: {dependent_precision} 位小数\n")
        f.write("\n使用的插值方法:\n")

        for method in results.keys():
            method_name_cn = INTERPOLATION_METHODS[method]['name']
            df = results[method]
            f.write(f"- {method_name_cn}: {len(df)} 行数据\n")

        f.write("\n生成的文件:\n")
        for method in results.keys():
            output_filename = f"{base_name}_{method}_插值结果.csv"
            f.write(f"- {output_filename}\n")

    print(f"已生成报告: {report_path}")


# ================================
# 参数验证函数
# ================================

def validate_parameters():
    """验证输入参数"""
    errors = []

    # 检查输入文件是否存在
    if not os.path.exists(input_file_path):
        errors.append(f"输入文件不存在: {input_file_path}")

    # 检查插值间隔
    if interpolation_interval <= 0:
        errors.append("插值间隔必须大于0")

    # 检查精度设置
    if independent_precision < 0 or independent_precision > 10:
        errors.append("自变量精度应在0-10之间")

    if dependent_precision < 0 or dependent_precision > 10:
        errors.append("因变量精度应在0-10之间")

    # 检查插值方法
    if interpolation_methods:
        for method in interpolation_methods:
            if method not in INTERPOLATION_METHODS:
                errors.append(f"不支持的插值方法: {method}")

    return errors


# ================================
# 主程序
# ================================

if __name__ == "__main__":
    print("CSV文件插值处理程序")
    print("=" * 50)

    # 验证参数
    validation_errors = validate_parameters()
    if validation_errors:
        print("参数验证错误:")
        for error in validation_errors:
            print(f"  - {error}")
        print("请修改参数后重新运行程序。")
    else:
        print("参数验证通过，开始处理...")
        success = interpolate_csv()

        if success:
            print("\n程序运行成功！")
        else:
            print("\n程序运行失败，请检查错误信息。")

    print("=" * 50)