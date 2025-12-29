"""
从历史事件时间线JSON生成GeoJSON文件
将 1812_campaign_timeline.json 转换为标准GeoJSON格式供前端使用
"""

import json
from pathlib import Path
from datetime import datetime

# 文件路径
DATA_DIR = Path(__file__).parent.parent / "data"
INPUT_FILE = DATA_DIR / "1812_campaign_timeline.json"
OUTPUT_DIR = DATA_DIR / "geojson"
OUTPUT_FILE = OUTPUT_DIR / "events.geojson"

# 确保输出目录存在
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_timeline_data() -> dict:
    """加载时间线JSON数据"""
    print(f"读取数据: {INPUT_FILE}")

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"✅ 读取成功")
    return data


def convert_event_to_feature(event: dict) -> dict:
    """
    将单个事件转换为GeoJSON Feature

    Args:
        event: 事件对象

    Returns:
        GeoJSON Feature对象
    """
    # 提取位置信息
    location = event.get('location', {})

    # 创建GeoJSON Feature
    feature = {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [
                location.get('lon'),
                location.get('lat')
            ]
        },
        "properties": {}
    }

    # 复制所有属性到properties
    properties = feature['properties']

    # 基础信息
    properties['id'] = event.get('id')
    properties['name'] = event.get('name')
    properties['name_zh'] = event.get('name_zh')
    properties['date'] = event.get('date')
    properties['type'] = event.get('type')

    # 位置信息
    properties['location_name'] = location.get('name')
    properties['country'] = location.get('country')

    # 描述
    properties['description'] = event.get('description')
    properties['description_zh'] = event.get('description_zh')

    # 参与者信息
    participants = event.get('participants', {})

    # 法军信息
    if 'french' in participants:
        french = participants['french']
        properties['french_troops'] = french.get('troops')
        properties['french_commanders'] = french.get('commanders', [])
        if 'artillery' in french:
            properties['french_artillery'] = french['artillery']

    # 俄军信息
    if 'russian' in participants:
        russian = participants['russian']
        properties['russian_troops'] = russian.get('troops')
        properties['russian_commanders'] = russian.get('commanders', [])
        if 'artillery' in russian:
            properties['russian_artillery'] = russian['artillery']

    # 奥地利/联军信息
    if 'austrian' in participants:
        austrian = participants['austrian']
        properties['austrian_troops'] = austrian.get('troops')
        properties['austrian_commanders'] = austrian.get('commanders', [])

    if 'coalition' in participants:
        coalition = participants['coalition']
        properties['coalition_austrian'] = coalition.get('austrian')
        properties['coalition_saxon'] = coalition.get('saxon')
        properties['coalition_commanders'] = coalition.get('commanders', [])

    # 伤亡信息
    casualties = event.get('casualties', {})

    if 'french' in casualties:
        french_cas = casualties['french']
        properties['french_killed'] = french_cas.get('killed')
        properties['french_wounded'] = french_cas.get('wounded')
        properties['french_captured'] = french_cas.get('captured')
        properties['french_dead'] = french_cas.get('dead')
        properties['french_casualties_total'] = french_cas.get('total')
        properties['french_casualties_reason'] = french_cas.get('reason')

    if 'russian' in casualties:
        russian_cas = casualties['russian']
        properties['russian_killed'] = russian_cas.get('killed')
        properties['russian_wounded'] = russian_cas.get('wounded')
        properties['russian_casualties_total'] = russian_cas.get('total')

    if 'coalition' in casualties:
        properties['coalition_casualties_total'] = casualties['coalition'].get('total')

    if 'campaign_total' in casualties:
        properties['campaign_casualties'] = casualties['campaign_total']

    # 其他信息
    properties['result'] = event.get('result')
    properties['impact'] = event.get('impact')
    properties['significance'] = event.get('significance')
    properties['confidence'] = event.get('confidence')

    # 天气信息（如有）
    if 'weather' in event:
        weather = event['weather']
        properties['weather_temperature'] = weather.get('temperature')
        properties['weather_conditions'] = weather.get('conditions')

    return feature


def generate_events_geojson(timeline_data: dict) -> dict:
    """
    生成完整的events GeoJSON

    Args:
        timeline_data: 时间线数据

    Returns:
        GeoJSON FeatureCollection
    """
    print("\n开始转换事件为GeoJSON...")

    features = []

    # 转换主要事件
    main_events = timeline_data.get('events', [])
    print(f"处理主要事件: {len(main_events)} 个")

    for event in main_events:
        try:
            feature = convert_event_to_feature(event)
            features.append(feature)
        except Exception as e:
            print(f"⚠️  转换事件失败 {event.get('id')}: {e}")

    # 转换Schwarzenberg行动
    schwarzenberg_ops = timeline_data.get('schwarzenberg_operations', {})
    schwarzenberg_events = schwarzenberg_ops.get('events', [])

    if schwarzenberg_events:
        print(f"处理Schwarzenberg事件: {len(schwarzenberg_events)} 个")

        for event in schwarzenberg_events:
            try:
                feature = convert_event_to_feature(event)
                features.append(feature)
            except Exception as e:
                print(f"⚠️  转换事件失败 {event.get('id')}: {e}")

    # 创建GeoJSON FeatureCollection
    geojson = {
        "type": "FeatureCollection",
        "metadata": {
            "title": "Napoleon's 1812 Russian Campaign - Events",
            "title_zh": "1812年拿破仑东征俄罗斯 - 事件",
            "description": "Historical events from Napoleon's 1812 invasion of Russia",
            "campaign": timeline_data.get('campaign'),
            "date_range": timeline_data.get('date_range'),
            "total_events": len(features),
            "source": timeline_data.get('source'),
            "generated_at": datetime.now().isoformat(),
            "coordinate_system": "WGS84",
            "schema": {
                "geometry": "Point",
                "properties": {
                    "id": "string - Event ID",
                    "name": "string - Event name (English)",
                    "name_zh": "string - Event name (Chinese)",
                    "date": "ISO8601 date",
                    "type": "string - battle|movement|occupation|disaster|political|weather",
                    "location_name": "string - Location name",
                    "country": "string - Country",
                    "description": "string - English description",
                    "description_zh": "string - Chinese description",
                    "significance": "string - low|medium|high|critical",
                    "confidence": "number - 0-1",
                    "french_troops": "number - French troop count",
                    "russian_troops": "number - Russian troop count",
                    "result": "string - Battle result"
                }
            }
        },
        "features": features
    }

    print(f"✅ 转换完成: {len(features)} 个事件")

    return geojson


def save_geojson(geojson: dict, output_path: Path):
    """保存GeoJSON到文件"""
    print(f"\n保存GeoJSON: {output_path}")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)

    # 计算文件大小
    file_size = output_path.stat().st_size / 1024  # KB

    print(f"✅ 保存成功")
    print(f"文件大小: {file_size:.1f} KB")


def validate_geojson(geojson: dict):
    """验证GeoJSON格式"""
    print("\n验证GeoJSON格式...")

    issues = []

    # 检查基本结构
    if geojson.get('type') != 'FeatureCollection':
        issues.append("类型必须是 'FeatureCollection'")

    features = geojson.get('features', [])
    if not features:
        issues.append("没有features")

    # 检查每个feature
    for i, feature in enumerate(features):
        if feature.get('type') != 'Feature':
            issues.append(f"Feature {i}: 类型必须是 'Feature'")

        geometry = feature.get('geometry', {})
        if geometry.get('type') != 'Point':
            issues.append(f"Feature {i}: geometry类型必须是 'Point'")

        coords = geometry.get('coordinates', [])
        if len(coords) != 2:
            issues.append(f"Feature {i}: coordinates必须是[lon, lat]")
        elif coords[0] is None or coords[1] is None:
            issues.append(f"Feature {i}: 缺少坐标")

        properties = feature.get('properties', {})
        if not properties.get('id'):
            issues.append(f"Feature {i}: 缺少id")
        if not properties.get('date'):
            issues.append(f"Feature {i}: 缺少date")

    if issues:
        print("⚠️  发现问题:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ GeoJSON格式正确")

    return len(issues) == 0


def print_statistics(geojson: dict):
    """打印统计信息"""
    print("\n" + "=" * 70)
    print("统计信息")
    print("=" * 70)

    features = geojson.get('features', [])

    # 按类型统计
    type_counts = {}
    for feature in features:
        event_type = feature['properties'].get('type', 'unknown')
        type_counts[event_type] = type_counts.get(event_type, 0) + 1

    print(f"\n总事件数: {len(features)}")
    print("\n按类型统计:")
    for event_type, count in sorted(type_counts.items()):
        print(f"  - {event_type}: {count}")

    # 按重要性统计
    significance_counts = {}
    for feature in features:
        sig = feature['properties'].get('significance', 'unknown')
        significance_counts[sig] = significance_counts.get(sig, 0) + 1

    print("\n按重要性统计:")
    for sig, count in sorted(significance_counts.items()):
        print(f"  - {sig}: {count}")

    # 时间范围
    dates = []
    for feature in features:
        date_str = feature['properties'].get('date')
        if date_str:
            try:
                dates.append(datetime.fromisoformat(date_str))
            except:
                pass

    if dates:
        dates.sort()
        print(f"\n时间范围:")
        print(f"  开始: {dates[0].strftime('%Y-%m-%d')}")
        print(f"  结束: {dates[-1].strftime('%Y-%m-%d')}")
        print(f"  持续: {(dates[-1] - dates[0]).days} 天")

    # 坐标范围
    lats = []
    lons = []
    for feature in features:
        coords = feature['geometry']['coordinates']
        if coords[0] is not None and coords[1] is not None:
            lons.append(coords[0])
            lats.append(coords[1])

    if lats and lons:
        print(f"\n地理范围:")
        print(f"  纬度: {min(lats):.2f}° - {max(lats):.2f}°")
        print(f"  经度: {min(lons):.2f}° - {max(lons):.2f}°")


def main():
    print("=" * 70)
    print("Events GeoJSON生成器")
    print("1812拿破仑东征项目")
    print("=" * 70)

    try:
        # 1. 加载数据
        timeline_data = load_timeline_data()

        # 2. 转换为GeoJSON
        geojson = generate_events_geojson(timeline_data)

        # 3. 验证
        validate_geojson(geojson)

        # 4. 保存
        save_geojson(geojson, OUTPUT_FILE)

        # 5. 统计
        print_statistics(geojson)

        print("\n" + "=" * 70)
        print("✅ 生成完成!")
        print("=" * 70)
        print(f"输出文件: {OUTPUT_FILE}")
        print(f"可在前端使用以下代码加载:")
        print(f"  fetch('/data/geojson/events.geojson')")
        print(f"    .then(res => res.json())")
        print(f"    .then(data => map.addSource('events', {{ type: 'geojson', data }}))")

    except FileNotFoundError:
        print(f"\n❌ 错误: 找不到输入文件 {INPUT_FILE}")
        print("请确保已运行数据收集脚本")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
