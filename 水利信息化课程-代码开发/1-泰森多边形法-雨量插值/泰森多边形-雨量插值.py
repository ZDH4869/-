# -*- coding: utf-8 -*-
import numpy as np
from shapely.geometry import Point, Polygon
import geopandas as gpd
from shapely.ops import unary_union
import matplotlib.pyplot as plt
from scipy.spatial import Voronoi
import warnings

warnings.filterwarnings('ignore')

# ==============================
# 用户可配置参数区域
# ==============================

# 1. 文件路径设置
BASIN_SHP_PATH = r'D:\Python pro\水文计算\水利信息化课程-代码开发\1-泰森多边形法-雨量插值\区域数据\降雨区域.shp'  # 雨量区域面shape文件路径
STATIONS_SHP_PATH = r'D:\Python pro\水文计算\水利信息化课程-代码开发\1-泰森多边形法-雨量插值\区域数据\雨量站.shp'  # 雨量站点shape文件路径

# 2. 坐标系设置
INPUT_CRS = "EPSG:4490"  # 输入数据的坐标系 (CGCS2000地理坐标系) 4490(CGCS2000) 4326(WGS84) 4610(Xian 1980) 4214(Beijing 1954)
TARGET_CRS = "EPSG:4519"  # 计算泰森多边形时使用的投影坐标系 (CGCS2000 / 3-degree Gauss-Kruger CM 111E) 32649(UTM Zone 49N)

# 3. 字段名称设置
STATION_NAME_FIELD = "站名"  # 站点名称字段
RAINFALL_FIELD = "雨量"  # 雨量数据字段

# 4. 可视化设置
OUTPUT_IMAGE_PATH = "泰森多边形权重分析结果.png"
IMAGE_DPI = 300
PLOT_SIZE = (16, 10)


# ==============================
# 主程序开始
# ==============================

def fix_geometry(geom):
    """
    修复几何图形，确保多边形闭合
    """
    if geom.is_empty:
        return geom

    if geom.geom_type == 'Polygon':
        exterior_coords = list(geom.exterior.coords)
        if exterior_coords[0] != exterior_coords[-1]:
            exterior_coords.append(exterior_coords[0])

        interiors = []
        for interior in geom.interiors:
            interior_coords = list(interior.coords)
            if interior_coords[0] != interior_coords[-1]:
                interior_coords.append(interior_coords[0])
            interiors.append(interior_coords)

        return Polygon(exterior_coords, interiors)

    return geom


def create_voronoi_polygons(points_gdf, boundary):
    """
    创建泰森多边形 - 改进版本
    """
    # 获取点坐标
    points = [point for point in points_gdf.geometry]
    coords = [(point.x, point.y) for point in points]

    # 添加边界点以确保Voronoi图覆盖整个区域
    bounds = boundary.bounds
    # 在边界周围添加额外的点
    padding = max(bounds[2] - bounds[0], bounds[3] - bounds[1]) * 0.1  # 10%的边界扩展
    extra_points = [
        (bounds[0] - padding, bounds[1] - padding),
        (bounds[0] - padding, bounds[3] + padding),
        (bounds[2] + padding, bounds[1] - padding),
        (bounds[2] + padding, bounds[3] + padding)
    ]

    all_coords = coords + extra_points

    # 创建Voronoi图
    vor = Voronoi(all_coords)

    # 创建Voronoi多边形
    voronoi_polys = []
    for i in range(len(points)):
        region_index = vor.point_region[i]
        region = vor.regions[region_index]
        if not -1 in region and len(region) > 0:
            polygon = Polygon([vor.vertices[j] for j in region])
            # 用边界裁剪多边形
            clipped_polygon = polygon.intersection(boundary)
            voronoi_polys.append(clipped_polygon)
        else:
            # 对于无限区域，创建一个空多边形
            voronoi_polys.append(Polygon())

    return gpd.GeoDataFrame(geometry=voronoi_polys, crs=points_gdf.crs)


def clip_points(shp, clip_obj):
    """
    使用裁剪对象裁剪点要素
    """
    poly = clip_obj.geometry.unary_union
    return shp.geometry.intersects(poly)


def main():
    """
    主函数
    """
    print("=" * 60)
    print("泰森多边形权重计算与可视化")
    print("=" * 60)

    # 显示当前配置
    print(f"雨量区域面文件: {BASIN_SHP_PATH}")
    print(f"雨量站点文件: {STATIONS_SHP_PATH}")
    print(f"输入坐标系: {INPUT_CRS}")
    print(f"目标投影坐标系: {TARGET_CRS}")
    print(f"站点名称字段: {STATION_NAME_FIELD}")
    print(f"雨量字段: {RAINFALL_FIELD}")
    print()

    # 1. 读取雨量区域面数据
    try:
        basin_area = gpd.read_file(BASIN_SHP_PATH)
        # 如果数据没有坐标系信息，设置坐标系
        if basin_area.crs is None:
            basin_area = basin_area.set_crs(INPUT_CRS)
            print(f"已为雨量区域面设置坐标系: {INPUT_CRS}")
        else:
            print(f"雨量区域面坐标系: {basin_area.crs}")

        # 修复几何图形
        basin_area['geometry'] = basin_area['geometry'].apply(fix_geometry)
        print(f"成功读取雨量区域面，包含 {len(basin_area)} 个要素")

    except Exception as e:
        print(f"读取雨量区域面时出错: {e}")
        return

    # 2. 读取雨量站点数据
    try:
        rainfall_stations = gpd.read_file(STATIONS_SHP_PATH)
        # 如果数据没有坐标系信息，设置坐标系
        if rainfall_stations.crs is None:
            rainfall_stations = rainfall_stations.set_crs(INPUT_CRS)
            print(f"已为雨量站点设置坐标系: {INPUT_CRS}")
        else:
            print(f"雨量站点坐标系: {rainfall_stations.crs}")

        print(f"成功读取雨量站点，包含 {len(rainfall_stations)} 个站点")

        # 检查必要的字段是否存在
        available_fields = rainfall_stations.columns.tolist()
        print(f"雨量站点字段: {available_fields}")

        if STATION_NAME_FIELD not in available_fields:
            print(f"警告: 未找到站点名称字段 '{STATION_NAME_FIELD}'")
            # 创建默认站点名称
            rainfall_stations[STATION_NAME_FIELD] = [f"站点{i + 1}" for i in range(len(rainfall_stations))]

        if RAINFALL_FIELD not in available_fields:
            print(f"警告: 未找到雨量字段 '{RAINFALL_FIELD}'，将使用模拟数据")
            np.random.seed(42)
            rainfall_stations[RAINFALL_FIELD] = np.random.uniform(20, 50, len(rainfall_stations))

    except Exception as e:
        print(f"读取雨量站点时出错: {e}")
        return

    # 3. 坐标系转换
    print("\n正在进行坐标系转换...")
    try:
        # 转换为目标投影坐标系
        basin_area_proj = basin_area.to_crs(TARGET_CRS)
        rainfall_stations_proj = rainfall_stations.to_crs(TARGET_CRS)
        print(f"已成功转换为目标坐标系: {TARGET_CRS}")
    except Exception as e:
        print(f"坐标系转换时出错: {e}")
        return

    # 4. 筛选在雨量区域面内的站点
    print("\n正在筛选在雨量区域面内的站点...")
    in_basin = clip_points(rainfall_stations_proj, basin_area_proj)
    gdf_filtered = rainfall_stations_proj[in_basin]

    if len(gdf_filtered) == 0:
        print("警告：没有站点在雨量区域面内，使用所有站点")
        gdf_filtered = rainfall_stations_proj

    print(f"用于分析的站点数量: {len(gdf_filtered)}")

    # 5. 创建泰森多边形
    print("\n正在创建泰森多边形...")
    boundary_shape = unary_union(basin_area_proj.geometry).buffer(1000)  # 增加缓冲区到1000米

    # 检查边界形状是否有效
    if boundary_shape.is_empty:
        print("错误：边界形状为空，无法创建泰森多边形")
        return

    voronoi_gdf = create_voronoi_polygons(gdf_filtered, boundary_shape)

    # 6. 计算权重
    print("\n正在计算权重...")
    voronoi_gdf['area'] = voronoi_gdf.area
    region_areas = voronoi_gdf['area'].values

    # 检查是否有有效的泰森多边形
    valid_polygons = sum(area > 0 for area in region_areas)
    print(f"有效的泰森多边形数量: {valid_polygons}/{len(region_areas)}")

    # 准备结果数据
    results = []
    for k in range(len(gdf_filtered)):
        point = gdf_filtered.geometry.iloc[k]
        station_name = gdf_filtered[STATION_NAME_FIELD].values[k]
        rainfall = gdf_filtered[RAINFALL_FIELD].values[k]

        # 计算面积（转换为平方公里）
        area_km2 = round(region_areas[k] * 0.000001, 2)

        # 计算总面积
        total_area = round(sum(region_areas) * 0.000001, 2)

        # 计算权重
        if total_area > 0:
            weight = round(area_km2 / total_area, 3)
        else:
            weight = 0

        # 获取原始坐标（用于显示）
        orig_point = rainfall_stations.geometry.iloc[k]
        lon = orig_point.x
        lat = orig_point.y

        results.append({
            "index": k,
            "station_name": station_name,
            "rainfall": rainfall,
            "area_km2": area_km2,
            "total_area_km2": total_area,
            "weight": weight,
            "lon": lon,
            "lat": lat,
            "x": point.x,
            "y": point.y,
        })

    # 7. 输出结果
    print("\n" + "=" * 60)
    print("泰森多边形权重计算结果")
    print("=" * 60)
    for res in results:
        print(
            f"站点 {res['station_name']}: 雨量={res['rainfall']:.1f}mm, 控制面积={res['area_km2']} km², 权重={res['weight']}")

    # 计算流域平均雨量
    if len(results) > 0:
        weighted_rainfall = sum(res["rainfall"] * res["weight"] for res in results)
        arithmetic_mean = sum(res["rainfall"] for res in results) / len(results)

        print(f"\n流域平均雨量:")
        print(f"  泰森多边形法: {weighted_rainfall:.2f} mm")
        print(f"  算术平均法: {arithmetic_mean:.2f} mm")
        print(f"  差异: {weighted_rainfall - arithmetic_mean:.2f} mm")

    # 8. 可视化
    print("\n正在生成可视化图形...")
    fig, ax = plt.subplots(1, 1, figsize=PLOT_SIZE)

    # 绘制泰森多边形
    voronoi_gdf.plot(ax=ax, alpha=0.3, edgecolor='blue', facecolor='lightblue')

    # 绘制站点位置，根据雨量大小着色
    scatter = ax.scatter(
        [res['x'] for res in results],
        [res['y'] for res in results],
        c=[res['rainfall'] for res in results],
        s=100, cmap='RdYlBu', edgecolor='black'
    )

    # 添加颜色条
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('雨量 (mm)')

    # 添加站点标注
    for res in results:
        ax.annotate(f"{res['station_name']}\n雨量:{res['rainfall']:.1f}mm\n权重:{res['weight']}",
                    xy=(res['x'], res['y']),
                    xytext=(10, 10),
                    textcoords="offset points",
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.8),
                    arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0"))

    # 绘制流域边界
    basin_area_proj.boundary.plot(ax=ax, color='black', linewidth=2)

    # 设置标题和标签
    ax.set_title('泰森多边形权重分析与雨量插值', fontsize=14)
    ax.set_xlabel('东坐标 (m)')
    ax.set_ylabel('北坐标 (m)')
    ax.grid(True, alpha=0.3)

    # 添加结果摘要
    if len(results) > 0:
        fig.text(0.02, 0.02,
                 f"流域平均雨量: {weighted_rainfall:.2f} mm\n"
                 f"算术平均雨量: {arithmetic_mean:.2f} mm\n"
                 f"差异: {weighted_rainfall - arithmetic_mean:.2f} mm",
                 bbox=dict(boxstyle="round,pad=0.5", fc="lightyellow", alpha=0.8),
                 fontsize=10)

    plt.tight_layout()

    # 保存图形
    plt.savefig(OUTPUT_IMAGE_PATH, dpi=IMAGE_DPI, bbox_inches='tight')
    print(f"图形已保存至: {OUTPUT_IMAGE_PATH}")

    # 显示图形
    plt.show()

    print("\n程序执行完成!")


if __name__ == "__main__":
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']

    # 执行主程序
    main()