import numpy as np
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体，例如使用方正姚体字体
# 设置中文字体，使用绝对路径
font_path = r'D:\Python pro\水文计算\水利信息化课程-代码开发\2-马斯京根流量演算法\FZYTK.TTF'
font = FontProperties(fname=font_path, size=14)
# 数据准备
delta_T = 1  # 时间间隔deltaT
'''时段,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18
上游站流量,75,407,1693,2320,2363,1867,1220,830,610,480,390,330,300,260,230,200,180,xx
下游站流量,xx,80,440,1680,2150,2280,1680,1270,880,680,550,450,400,340,290,250,220,200
'''
# 上游实测流量数据Q上
I_data = [75,407,1693,2320,2363,1867,1220,830,610,480,390,330,300,260,230,200,180]
I_data = I_data[1:]  # 去掉第一个数据

# 下游实测流量数据Q下
Q_data = [80,440,1680,2150,2280,1680,1270,880,680,550,450,400,340,290,250,220,200]
Q_data = Q_data[:-1]  # 去掉最后一个数据

# 计算过程
# 1、河段蓄水量S的计算
delta_S = np.zeros(len(I_data))
for i in range(len(I_data) - 1):
    delta_S[i + 1] = (0.5 * (I_data[i] + I_data[i + 1]) * delta_T -
                      0.5 * (Q_data[i] + Q_data[i + 1]) * delta_T)

S = np.cumsum(delta_S)
print("蓄水量S:", S)

# 2、流量Q的计算
best_cor = 0  # 存储拟合最好的相关系数
best_x = 0  # 存储拟合最好的x
best_Q = None

for x_val in range(0, 51):
    x = x_val / 100  # x的取值范围是0到0.5，步长是0.01
    Q_calc = np.zeros(len(I_data))

    for i in range(len(I_data)):
        Q_calc[i] = x * I_data[i] + (1 - x) * Q_data[i]

    # 计算相关系数，因为S(0)的数据未知，所以从第二项开始拟合
    corr_matrix = np.corrcoef(S[1:], Q_calc[1:])
    temp_cor = corr_matrix[0, 1]

    if temp_cor > best_cor:
        best_cor = temp_cor
        best_x = x
        best_Q = Q_calc.copy()

print(f"最佳x值: {best_x}, 最佳相关系数: {best_cor}")

# 3、画出蓄水曲线和用S-KQ求出K值
p = np.polyfit(best_Q[1:], S[1:], 1)
K = p[0]

# 绘制图形
plt.figure(figsize=(8, 6))
# 全局设置字体
plt.rcParams['font.family'] = font.get_name()
plt.rcParams['font.size'] = font.get_size()
plt.plot(S[1:], best_Q[1:], 'bo-', label='S-Q关系曲线')
plt.plot(S[1:], np.polyval(p, best_Q[1:]), 'r-', label=f'拟合直线 (K={K:.4f})')
plt.title('马斯京根法蓄量-流量关系曲线', fontproperties=font)
plt.xlabel('蓄水量 S (m³)', fontproperties=font)
plt.ylabel('流量 Q (m³/s)', fontproperties=font)
plt.legend()
plt.grid(True)
plt.savefig('计算X、K.png', bbox_inches='tight', dpi=300)
plt.show()

print(f"计算结果 - K值: {K:.4f}, 最佳x值: {best_x:.2f}")