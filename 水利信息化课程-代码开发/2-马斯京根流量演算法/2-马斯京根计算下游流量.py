# -*- coding: utf-8 -*-
from __future__ import division
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import warnings
warnings.filterwarnings('ignore')
# 设置中文字体，例如使用方正姚体字体
# 设置中文字体，使用绝对路径
font_path = r'D:\Python pro\水文计算\水利信息化课程-代码开发\2-马斯京根流量演算法\FZYTK.TTF'
font = FontProperties(fname=font_path, size=14)
# ==============================
# 马斯京根流量演算法参数设置
# ==============================

# 马斯京根法系数
# C0, C1, C2 是通过K和X计算得到的参数
# 公式: C0 + C1 + C2 = 1
K = 1.1002  # 马斯京根法K系数 - 河道传播时间 (小时)
X = 0.27    # 马斯京根法X系数 - 流量比重因子 (0-0.5)

# 计算马斯京根法参数
# 注意：这里直接给出了C0, C1, C2，但通常它们是通过K和X以及时间步长Δt计算得到
C0 = 0.27   # 上游流量权重系数
C1 = 1.1002 # 下游流量权重系数 (这里可能与K值混淆了)
C2 = 0.27   # 前期流量权重系数

# 上游断面流量数据 (单位: m³/s)
# 时间序列的入流数据
I = np.array([250, 310, 500, 1560, 1680, 1360, 1090, 870, 730, 640, 560, 500])

# ==============================
# 马斯京根流量演算计算
# ==============================

# 初始化下游流量数组
Q = np.empty(len(I))

# 设置初始下游流量值
# 注意：这里的初始值22800与上游流量量级不匹配，可能存在单位错误
Q[0] = 350  # 初始下游流量

# 马斯京根流量演算公式：
# Q[i] = C0 * I[i] + C1 * I[i-1] + C2 * Q[i-1]
# 其中：
# Q[i] - 当前时刻下游流量
# I[i] - 当前时刻上游流量
# I[i-1] - 前一时刻上游流量
# Q[i-1] - 前一时刻下游流量

print("开始进行马斯京根流量演算...")
print(f"参数设置: C0={C0}, C1={C1}, C2={C2}")
print(f"参数验证: C0+C1+C2 = {C0+C1+C2}")

# 马斯京根法流量演算循环
for i in range(1, len(I)):
    Q[i] = C0 * I[i] + C1 * I[i-1] + C2 * Q[i-1]
    print(f"时段 {i}: Q[{i}] = {C0}×{I[i]} + {C1}×{I[i-1]} + {C2}×{Q[i-1]:.1f} = {Q[i]:.1f}")

# 输出结果
print("\n马斯京根流量演算结果:")
print("=" * 50)
print("时段\t上游流量I\t下游流量Q")
print("-" * 50)
for i in range(len(I)):
    print(f"{i}\t{I[i]}\t\t{Q[i]:.1f}")

# ==============================
# 结果可视化
# ==============================

plt.figure(figsize=(12, 8))
# 全局设置字体
plt.rcParams['font.family'] = font.get_name()
plt.rcParams['font.size'] = font.get_size()
# 绘制入流和出流过程线
plt.plot(I, '--*', markersize=10, linewidth=2, label='上游入流 (Inflow)')
plt.plot(Q, '--s', markersize=8, linewidth=2, label='下游出流 (Outflow)')

# 设置图形属性
plt.xlabel('时间 (时段)', fontsize=14)
plt.ylabel('流量 (m³/s)', fontsize=14)
plt.title('马斯京根法流量演算结果', fontsize=16)

# 添加网格和图例
plt.grid(True, alpha=0.3)
plt.legend(fontsize=12)

# 在图上添加参数信息
plt.text(0.02, 0.98, f'马斯京根法参数:\nC0={C0}, C1={C1}, C2={C2}\nK={K}, X={X}',
         transform=plt.gca().transAxes, fontsize=10,
         verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

# 保存图形
plt.tight_layout()
plt.savefig(r'D:\Python pro\水文计算\水利信息化课程-代码开发\2-马斯京根流量演算法/下游流量计算.png', dpi=300, bbox_inches='tight')

# 显示图形
plt.show()

print(fr"\n图形已保存至: D:\\Python pro\\水文计算\\水利信息化课程-代码开发\\2-马斯京根流量演算法/下游流量计算.png")