import pandas as pd
import numpy as np

# 读取CSV文件，指定正确的文件路径和编码
input_path = r"E:\水电202303班\大二（下期）\平时课件及作业\工程水文学\实践课程\1994典型洪水过程.csv"

# 尝试不同的编码方式
try:
    df = pd.read_csv(input_path, header=None, skiprows=2, names=['年月日', '时', 'Q'], encoding='latin1')
except Exception as e:
    print(f"尝试latin1编码失败: {e}")
    try:
        df = pd.read_csv(input_path, header=None, skiprows=2, names=['年月日', '时', 'Q'], encoding='gbk')
    except Exception as e:
        print(f"尝试gbk编码失败: {e}")
        df = pd.read_csv(input_path, header=None, skiprows=2, names=['年月日', '时', 'Q'], encoding='utf-8')

# 将“年月日”列转换为日期格式
df['年月日'] = pd.to_datetime(df['年月日'])

# 创建一个新的DataFrame，用于存储插值后的数据
df_interp = pd.DataFrame()

# 设置插值间隔（例如：每1小时一个点）
freq = '1H'  # 可以根据需要调整# 可以根据需要调整（30T：30分钟间隔）

# 生成完整的时间索引
start_time = df['年月日'].min()
end_time = df['年月日'].max()
full_time_index = pd.date_range(start=start_time, end=end_time, freq=freq)

# 创建一个临时的完整时间索引的DataFrame，并与原始数据合并
df_full = pd.DataFrame({'时间': full_time_index})
df['时间'] = df['年月日'] + pd.to_timedelta(df['时'], unit='h')
df_full = df_full.merge(df, on='时间', how='left')

# 按照时间进行排序，并进行插值
df_full = df_full.sort_values('时间')
df_full['Q'] = df_full['Q'].interpolate(method='linear', limit_direction='both')  # 双向插值

# 如果仍有缺失值，使用前向填充和后向填充
df_full['Q'] = df_full['Q'].ffill().bfill()

# 将时间拆分为“年”、“月”、“日”、“时”字段
df_full['年'] = df_full['时间'].dt.year
df_full['月'] = df_full['时间'].dt.month
df_full['日'] = df_full['时间'].dt.day
df_full['时'] = df_full['时间'].dt.hour

# 提取需要的列并重新排序
df_result = df_full[['年', '月', '日', '时', 'Q']]

# 将结果保存为CSV文件
output_path = r"E:\水电202303班\大二（下期）\平时课件及作业\工程水文学\实践课程\1994典型洪水过程_插值后.csv"
df_result.to_csv(output_path, index=False)

print(f"插值后的数据已保存到{output_path}文件中")