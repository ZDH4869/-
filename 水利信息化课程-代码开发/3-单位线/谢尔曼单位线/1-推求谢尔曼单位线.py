import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体，使用绝对路径
font_path = r'D:\Python pro\水文计算\水利信息化课程-代码开发\2-马斯京根流量演算法\FZYTK.TTF'
font = FontProperties(fname=font_path, size=14)

# ==============================
# 输入数据
# ==============================
# 地面径流量序列 (单位：m³/s 或 径流深 mm，根据具体情况)
rs = [0, 120, 275, 737, 1085, 840, 575, 389, 261, 180, 128, 95, 73, 55, 40, 29, 12, 6, 1, 0]
# 流域面积 (单位：km²)
F_area = 8080
# 净雨量 (单位：mm)
# PE[0] = 第一时段净雨量，PE[1] = 第二时段净雨量
PE = [15.7, 5.9]
# 时间间隔 (单位：小时)
h = 12

def calculate_un_and_q(rs, PE, h, F_area, adjustment_factor):
    """
    计算谢尔曼单位线的un序列和q值

    参数:
    rs -- 地面径流量序列
    PE -- 净雨量 [第一时段, 第二时段]
    h -- 时间间隔 (小时)
    F_area -- 流域面积 (km²)
    adjustment_factor -- 调整系数

    返回:
    un -- 单位线纵坐标序列
    q -- 单位线总量检验值
    """
    un = []  # 存储单位线纵坐标
    un1 = 0  # 中间计算变量

    # 遍历地面径流量序列
    for i in range(len(rs)):
        if i == 0:
            # 第一个时段：直接计算
            # 公式：un1 = 径流量 / 第一时段净雨量 × 10
            un1 = rs[i] / PE[0] * 10
        else:
            if rs[i] == 0:
                # 如果径流量为0，则单位线值为0
                un1 = 0
            else:
                # 后续时段：考虑前后时段的影响
                # 公式：un1 = (当前径流量 - 前一时段单位线值 × 第二时段净雨量/10) / 第一时段净雨量 × 10
                un1 = (rs[i] - un1 * PE[1] / 10) / PE[0] * 10

        # 应用调整系数
        un1 *= adjustment_factor

        # 将计算值添加到序列中
        un.append(un1)

    # 计算单位线总量检验值q
    # 公式：q = sum(un) × 时间间隔 × 3.6 / 流域面积
    # 3.6是单位转换系数，将mm·km²/h转换为m³/s
    q = sum(un) * h * 3.6 / F_area

    return un, q


# ==============================
# 参数调整过程
# ==============================

# 初始化调整系数为1（无调整）
adjustment_factor = 1.0

# 首次计算un序列和q值
un, q = calculate_un_and_q(rs, PE, h, F_area, adjustment_factor)

print(f"初始计算: q值 = {q:.4f}")

# 迭代调整：如果q与10的差距大于0.1，则进行调整
# 目标：使q值接近10（单位线的标准化条件）
while abs(q - 10) > 0.1:
    # 通过试错法调整un1的值，以接近q值为10
    if q > 10:
        # 如果q值大于10，则减小调整系数
        adjustment_factor -= 0.001
    else:
        # 如果q值小于10，则增大调整系数
        adjustment_factor += 0.001

    # 使用新的调整系数重新计算
    un, q = calculate_un_and_q(rs, PE, h, F_area, adjustment_factor)

# ==============================
# 结果输出
# ==============================

print("\n谢尔曼单位线计算结果:")
print("序列号\t单位线纵坐标(un)")
print("-" * 30)

# 打印调整后的un值和对应的序列号
for index, value in enumerate(un):
    print(f"序列 {index + 1}: {value:.2f}")

# ==============================
# 可视化
# ==============================

# 全局设置字体
plt.rcParams['font.family'] = font.get_name()
plt.rcParams['font.size'] = font.get_size()

# 创建图形
plt.figure(figsize=(12, 6))  # 设置画布大小

# 绘制单位线曲线
plt.plot(range(1, len(rs) + 1), un, marker="o", linewidth=2, markersize=6,
         color='blue', markerfacecolor='red', markeredgecolor='red')

# 设置图形属性
plt.title('谢尔曼单位线推求结果', fontproperties=font, fontsize=16)
plt.xlabel('时段序列', fontproperties=font, fontsize=12)
plt.ylabel('单位线流量(m³/s)', fontproperties=font, fontsize=12)

# 添加网格线
plt.grid(True, alpha=0.3, linestyle='--')

# 添加关键参数标注
plt.text(0.02, 0.98, f'流域面积: {F_area} km²\n'
                     f'净雨量: {PE[0]}/{PE[1]} mm\n'
                     f'时间间隔: {h} 小时\n'
                     f'调整系数: {adjustment_factor:.4f}\n'
                     f'最终q值: {q:.4f}',
         transform=plt.gca().transAxes, fontsize=10,
         verticalalignment='top',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

# 保存图片
plt.tight_layout()
plt.savefig('推求谢尔曼单位线.png', dpi=300, bbox_inches='tight')

# 显示图形
plt.show()

# ==============================
# 最终结果输出
# ==============================

print(f"\n最终结果:")
print(f"调整系数: {adjustment_factor:.4f}")
print(f"最终q值: {q:.4f}")
print(f"单位线峰值: {max(un):.2f} (出现在第{un.index(max(un)) + 1}时段)")
print(f"单位线总历时: {len(un)} 个时段")

print(f"\n图形已保存至: 推求谢尔曼单位线.png")