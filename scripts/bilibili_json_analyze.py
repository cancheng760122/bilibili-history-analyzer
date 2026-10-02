"""
B站观看历史JSON分析脚本
读取B站导出的JSON格式历史记录，生成统计图表和报告

使用方法:
    python bilibili_json_analyze.py

依赖:
    pip install pandas matplotlib jieba
"""

import json
import os
import base64
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from collections import Counter

plt.rcParams["font.sans-serif"] = ["SimHei", "WenQuanYi Micro Hei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# -------------------------- 路径配置 --------------------------
JSON_FILE_PATH = "bilibili-history-backup.json"
date_str = datetime.now().strftime("%Y-%m-%d")
OUTPUT_DIR = f"output/{date_str}_history_json"
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "bilibili_history_from_json.csv")
REPORT_TXT = os.path.join(OUTPUT_DIR, "watch_report.txt")

IMG_DAILY = os.path.join(OUTPUT_DIR, "01_daily_watch.png")
IMG_HOUR = os.path.join(OUTPUT_DIR, "02_hour_dist.png")
IMG_WEEK = os.path.join(OUTPUT_DIR, "03_week_dist.png")
IMG_TOPUP = os.path.join(OUTPUT_DIR, "04_top_up.png")
IMG_WORDS = os.path.join(OUTPUT_DIR, "05_title_word_freq.png")

SAVE_CSV = True
# --------------------------------------------------------------


def timestamp_sec_to_datetime(ts):
    """秒级时间戳转本地时间"""
    try:
        return datetime.fromtimestamp(int(ts))
    except Exception:
        return None


def get_word_frequency(title_series):
    """标题词频统计"""
    try:
        import jieba
        stop_words = {"的", "了", "是", "在", "和", "有", "就", "都", "而", "及", "与", "之", "也",
                      "不", "很", "还", "这", "那", "我", "你", "他", "她", "它", "什么", "怎么",
                      "一个", "一点", "全部", "看看", "视频", "B站", "bilibili"}
        all_words = []
        for title in title_series:
            words = jieba.lcut(str(title))
            for w in words:
                if len(w) > 1 and w not in stop_words:
                    all_words.append(w)
        counter = Counter(all_words)
        return counter.most_common(30)
    except ImportError:
        print("⚠️  未安装jieba，跳过词频分析。执行: pip install jieba")
        return []


def load_bilibili_json(filepath):
    """加载并解析B站JSON历史记录"""
    with open(filepath, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    # 自动寻找记录数组
    item_list = None
    if isinstance(raw_data, dict):
        if "history" in raw_data and isinstance(raw_data["history"], list):
            item_list = raw_data["history"]
        elif "data" in raw_data and isinstance(raw_data["data"], list):
            item_list = raw_data["data"]
        else:
            for k in raw_data:
                if isinstance(raw_data[k], list):
                    item_list = raw_data[k]
                    print(f"✅ 在字段 [{k}] 中找到记录数组")
                    break
    elif isinstance(raw_data, list):
        item_list = raw_data

    if item_list is None:
        raise ValueError("未能在JSON中找到记录数组")

    print(f"✅ 找到记录数组，长度={len(item_list)}")

    records = []
    for item in item_list:
        if not isinstance(item, dict):
            continue
        # 观看时间: view_at (秒级时间戳)
        dt = timestamp_sec_to_datetime(item.get("view_at") or item.get("viewAt"))
        row = {
            "标题": item.get("title", ""),
            "作者": item.get("author_name", item.get("author", "")),
            "观看时间": dt,
            "BV号": item.get("bvid", ""),
            "封面": item.get("cover", ""),
            "视频时长(秒)": item.get("duration", 0),
            "类型": item.get("business", "视频"),
            "view_at时间戳": item.get("view_at", "")
        }
        records.append(row)

    df = pd.DataFrame(records)
    print(f"✅ 读取完成，共 {len(df)} 条观看记录")
    return df


def main():
    # 创建输出文件夹
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"📁 自动创建文件夹: {OUTPUT_DIR}")

    # 检查文件是否存在
    if not os.path.exists(JSON_FILE_PATH):
        print(f"❌ 找不到文件: {JSON_FILE_PATH}")
        print("请将B站导出的JSON文件放在脚本同目录，并命名为 bilibili-history-backup.json")
        print("或修改脚本中的 JSON_FILE_PATH 变量")
        return

    df = load_bilibili_json(JSON_FILE_PATH)

    if SAVE_CSV:
        df.to_csv(OUTPUT_CSV, index=False, encoding="utf_8_sig")
        print(f"✅ 已导出CSV：{OUTPUT_CSV}")

    # 时间清洗
    df["观看时间"] = pd.to_datetime(df["观看时间"], errors="coerce")
    df_valid = df.dropna(subset=["观看时间"])
    print(f"✅ 有效时间记录：{len(df_valid)}")

    if len(df_valid) == 0:
        print("❌ 没有有效时间记录，无法生成统计")
        return

    # 衍生字段
    df_valid["观看日期"] = df_valid["观看时间"].dt.date
    df_valid["小时"] = df_valid["观看时间"].dt.hour
    df_valid["星期"] = df_valid["观看时间"].dt.dayofweek

    daily_count = df_valid.groupby("观看日期").size()
    top_authors = df_valid["作者"].value_counts().head(15)
    hour_count = df_valid.groupby("小时").size()
    week_map = {0: "周一", 1: "周二", 2: "周三", 3: "周四", 4: "周五", 5: "周六", 6: "周日"}
    df_valid["星期名"] = df_valid["星期"].map(week_map)
    week_count = df_valid.groupby("星期名").size().reindex(
        ["周一", "周二", "周三", "周四", "周五", "周六", "周日"])

    # ========== 绘图 ==========

    # 图1 每日趋势
    plt.figure(figsize=(14, 5))
    daily_count.plot(kind="line", color="#fb7299", marker="o", markersize=3)
    plt.title("B站每日观看视频数量", fontsize=14)
    plt.xlabel("日期")
    plt.ylabel("观看条数")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(IMG_DAILY, dpi=150)
    plt.close()

    # 图2 小时分布
    plt.figure(figsize=(12, 4))
    colors = ["#fb7299" if h == hour_count.idxmax() else "#23ade5" for h in hour_count.index]
    hour_count.plot(kind="bar", color=colors)
    plt.title("24小时观看分布（几点刷B站最多）", fontsize=14)
    plt.xlabel("小时")
    plt.ylabel("视频条数")
    plt.tight_layout()
    plt.savefig(IMG_HOUR, dpi=150)
    plt.close()

    # 图3 星期分布
    plt.figure(figsize=(9, 4))
    week_count.plot(kind="bar", color="#2ca02c")
    plt.title("星期观看数量分布", fontsize=14)
    plt.xlabel("星期")
    plt.ylabel("视频条数")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(IMG_WEEK, dpi=150)
    plt.close()

    # 图4 TOP UP主
    plt.figure(figsize=(10, 6))
    top_authors.sort_values().plot(kind="barh", color="#d62728")
    plt.title("观看最多的15位UP主", fontsize=14)
    plt.xlabel("观看视频条数")
    plt.tight_layout()
    plt.savefig(IMG_TOPUP, dpi=150)
    plt.close()

    # 图5 词频
    word_freq = get_word_frequency(df_valid["标题"])
    if word_freq:
        words = [item[0] for item in word_freq]
        counts = [item[1] for item in word_freq]
        plt.figure(figsize=(12, 8))
        plt.barh(words[::-1], counts[::-1], color="#9467bd")
        plt.title("视频标题关键词TOP30", fontsize=14)
        plt.xlabel("出现次数")
        plt.tight_layout()
        plt.savefig(IMG_WORDS, dpi=150)
        plt.close()

    print("\n✅ 全部图表保存至", OUTPUT_DIR)

    # ========== 额外统计（用于AI深度总结） ==========
    # 观看时长统计
    total_duration = df_valid["视频时长(秒)"].sum()
    avg_duration = df_valid["视频时长(秒)"].mean()
    total_hours = total_duration / 3600

    # 视频类型分布
    type_count = df_valid["类型"].value_counts()

    # 周末vs工作日
    df_valid["是否周末"] = df_valid["星期"].isin([5, 6])
    weekend_avg = df_valid[df_valid["是否周末"]].groupby("观看日期").size().mean()
    weekday_avg = df_valid[~df_valid["是否周末"]].groupby("观看日期").size().mean()

    # 观看频率
    days_watched = df_valid["观看日期"].nunique()
    total_days = (df_valid["观看日期"].max() - df_valid["观看日期"].min()).days + 1
    watch_rate = days_watched / total_days * 100

    # 最活跃的一周
    df_valid["周数"] = df_valid["观看时间"].dt.isocalendar().week
    weekly_count = df_valid.groupby("周数").size()
    max_week = weekly_count.idxmax()
    max_week_cnt = weekly_count.max()

    # ========== 生成文本报告 ==========
    max_day = daily_count.idxmax()
    max_day_cnt = daily_count.max()
    max_hour = hour_count.idxmax()
    max_hour_cnt = hour_count.max()

    report = f"""
================ B站观看行为分析报告【JSON版本】 ================
总有效观看记录：{len(df_valid)} 条
统计时间范围：{df_valid['观看日期'].min()} ~ {df_valid['观看日期'].max()}，共 {df_valid['观看日期'].nunique()} 天

1. 每日统计
观看最多的一天：{max_day}，共观看 {max_day_cnt} 个视频

2. 时段统计
一天内看视频最多的时刻：{max_hour}点，共 {max_hour_cnt} 条记录

3. 星期分布
{week_count.to_string()}

4. TOP 15 UP主（观看条数）
{top_authors.to_string()}

5. 标题关键词TOP30
"""
    for word, cnt in word_freq:
        report += f"{word}：{cnt}次\n"
    report += "===================================================="

    with open(REPORT_TXT, "w", encoding="utf-8") as f:
        f.write(report)
    print(report)
    print(f"\n✅ 文本报告保存至：{REPORT_TXT}")

    # ========== 生成ECharts交互式HTML报告 ==========
    import json

    # 准备图表数据
    daily_data = [{"date": str(d), "count": int(c)} for d, c in daily_count.items()]
    hour_data = [{"hour": f"{h}时", "count": int(c)} for h, c in hour_count.items()]
    week_data = [{"day": d, "count": int(c) if pd.notna(c) else 0} for d, c in week_count.items()]
    author_data = [{"name": str(a), "count": int(c)} for a, c in top_authors.items()]
    word_data = [{"name": w, "value": int(c)} for w, c in word_freq[:30]]
    type_data = [{"name": str(t), "count": int(c)} for t, c in type_count.items()]

    # AI深度总结
    # 兴趣标签生成
    interest_tags = []
    game_words = ["鸣潮", "战双", "异环", "游戏", "Steam", "神作", "攻略", "角色"]
    tech_words = ["AI", "手机", "iPhone", "NFC", "门禁卡", "教程", "使用"]
    study_words = ["建模", "数学", "国赛", "数模"]
    if any(w in [x[0] for x in word_freq[:20]] for w in game_words):
        interest_tags.append("🎮 游戏爱好者")
    if any(w in [x[0] for x in word_freq[:20]] for w in tech_words):
        interest_tags.append("📱 科技数码控")
    if any(w in [x[0] for x in word_freq[:20]] for w in study_words):
        interest_tags.append("📚 学习上进型")

    # 观看习惯总结
    if max_hour < 6:
        time_pattern = "🌙 夜猫子型（凌晨活跃）"
    elif max_hour < 12:
        time_pattern = "🌅 早起型（上午活跃）"
    elif max_hour < 18:
        time_pattern = "☀️ 白天型（下午活跃）"
    else:
        time_pattern = "🌆 晚间型（晚上活跃）"

    if weekend_avg > weekday_avg * 1.5:
        weekend_pattern = "🎉 周末狂欢型（周末观看量是工作日的1.5倍以上）"
    elif weekday_avg > weekend_avg * 1.5:
        weekend_pattern = "💼 工作日摸鱼型（工作日观看量远高于周末）"
    else:
        weekend_pattern = "⚖️ 均衡型（工作日和周末观看量差不多）"

    # 生成深度总结文本
    summary_text = f"""
    <p>在过去的 <strong>{total_days}</strong> 天里，你一共观看了 <strong>{len(df_valid)}</strong> 个视频，总观看时长约 <strong>{total_hours:.1f}</strong> 小时，平均每天看 <strong>{len(df_valid)/total_days:.1f}</strong> 个视频。</p>
    <p>你的观看活跃度为 <strong>{watch_rate:.1f}%</strong>（{days_watched}/{total_days}天有观看记录）。最疯狂的一天是 <strong>{max_day}</strong>，一口气看了 <strong>{max_day_cnt}</strong> 个视频！</p>
    <p>从时间分布来看，你属于<strong>{time_pattern}</strong>，最活跃的时段是 <strong>{max_hour}点</strong>。从星期分布来看，你是<strong>{weekend_pattern}</strong>，最活跃的一天是 <strong>{week_count.idxmax()}</strong>。</p>
    <p>兴趣方面，你最关注的关键词是 <strong>{word_freq[0][0]}</strong>（{word_freq[0][1]}次），其次是 <strong>{word_freq[1][0]}</strong>（{word_freq[1][1]}次）和 <strong>{word_freq[2][0]}</strong>（{word_freq[2][1]}次）。最常看的UP主是 <strong>{top_authors.index[0]}</strong>（{int(top_authors.iloc[0])}个视频）。</p>
    """

    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>B站观看历史深度分析报告</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; color: #333; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 30px 20px; }}
        .header {{ background: linear-gradient(135deg, #fb7299, #23ade5); color: white; padding: 50px 40px; border-radius: 20px; margin-bottom: 30px; text-align: center; box-shadow: 0 10px 40px rgba(0,0,0,0.2); }}
        .header h1 {{ font-size: 36px; margin-bottom: 15px; text-shadow: 2px 2px 4px rgba(0,0,0,0.2); }}
        .header p {{ font-size: 18px; opacity: 0.95; }}
        .tags {{ display: flex; justify-content: center; gap: 12px; margin-top: 20px; flex-wrap: wrap; }}
        .tag {{ background: rgba(255,255,255,0.25); backdrop-filter: blur(10px); padding: 8px 20px; border-radius: 20px; font-size: 14px; font-weight: 500; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .stat-card {{ background: white; padding: 25px 20px; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); text-align: center; transition: transform 0.3s, box-shadow 0.3s; }}
        .stat-card:hover {{ transform: translateY(-5px); box-shadow: 0 8px 30px rgba(0,0,0,0.15); }}
        .stat-card .number {{ font-size: 32px; font-weight: bold; background: linear-gradient(135deg, #fb7299, #23ade5); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }}
        .stat-card .label {{ font-size: 13px; color: #888; margin-top: 8px; }}
        .summary-card {{ background: white; padding: 35px; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); margin-bottom: 30px; }}
        .summary-card h2 {{ font-size: 22px; margin-bottom: 20px; color: #333; border-left: 4px solid #fb7299; padding-left: 15px; }}
        .summary-card p {{ line-height: 1.8; color: #555; margin-bottom: 12px; font-size: 15px; }}
        .chart-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 25px; margin-bottom: 30px; }}
        .chart-card {{ background: white; padding: 25px; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
        .chart-card.full {{ grid-column: 1 / -1; }}
        .chart-card h3 {{ font-size: 18px; margin-bottom: 15px; color: #444; }}
        .chart {{ width: 100%; height: 350px; }}
        .chart.tall {{ height: 450px; }}
        .footer {{ text-align: center; padding: 30px; color: rgba(255,255,255,0.8); font-size: 13px; }}
        @media (max-width: 768px) {{ .chart-grid {{ grid-template-columns: 1fr; }} .header h1 {{ font-size: 24px; }} }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 B站观看历史深度分析报告</h1>
            <p>统计时间：{df_valid['观看日期'].min()} ~ {df_valid['观看日期'].max()} | 共 {total_days} 天</p>
            <div class="tags">
                {"".join(f'<span class="tag">{tag}</span>' for tag in interest_tags)}
                <span class="tag">{time_pattern}</span>
                <span class="tag">{weekend_pattern}</span>
            </div>
        </div>

        <div class="stats">
            <div class="stat-card"><div class="number">{len(df_valid)}</div><div class="label">总观看视频</div></div>
            <div class="stat-card"><div class="number">{total_hours:.1f}h</div><div class="label">总观看时长</div></div>
            <div class="stat-card"><div class="number">{watch_rate:.0f}%</div><div class="label">观看活跃度</div></div>
            <div class="stat-card"><div class="number">{max_day_cnt}</div><div class="label">单日最多观看</div></div>
            <div class="stat-card"><div class="number">{max_hour}时</div><div class="label">高峰时段</div></div>
            <div class="stat-card"><div class="number">{week_count.idxmax()}</div><div class="label">最活跃星期</div></div>
        </div>

        <div class="summary-card">
            <h2>🤖 AI深度总结</h2>
            {summary_text}
        </div>

        <div class="chart-grid">
            <div class="chart-card full">
                <h3>📈 每日观看趋势</h3>
                <div id="dailyChart" class="chart"></div>
            </div>
            <div class="chart-card">
                <h3>⏰ 24小时观看分布</h3>
                <div id="hourChart" class="chart"></div>
            </div>
            <div class="chart-card">
                <h3>📅 星期观看分布</h3>
                <div id="weekChart" class="chart"></div>
            </div>
            <div class="chart-card full">
                <h3>👥 最常观看的UP主 TOP15</h3>
                <div id="authorChart" class="chart tall"></div>
            </div>
            <div class="chart-card">
                <h3>🔤 标题关键词 TOP30</h3>
                <div id="wordChart" class="chart tall"></div>
            </div>
            <div class="chart-card">
                <h3>📺 视频类型分布</h3>
                <div id="typeChart" class="chart"></div>
            </div>
        </div>

        <div class="footer">
            <p>报告生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | 由B站历史分析工具生成 | 数据仅供个人参考</p>
        </div>
    </div>

    <script>
        const dailyData = {json.dumps(daily_data, ensure_ascii=False)};
        const hourData = {json.dumps(hour_data, ensure_ascii=False)};
        const weekData = {json.dumps(week_data, ensure_ascii=False)};
        const authorData = {json.dumps(author_data, ensure_ascii=False)};
        const wordData = {json.dumps(word_data, ensure_ascii=False)};
        const typeData = {json.dumps(type_data, ensure_ascii=False)};

        // 每日趋势
        const dailyChart = echarts.init(document.getElementById('dailyChart'));
        dailyChart.setOption({{
            tooltip: {{ trigger: 'axis' }},
            xAxis: {{ type: 'category', data: dailyData.map(d => d.date), axisLabel: {{ rotate: 45 }} }},
            yAxis: {{ type: 'value', name: '观看条数' }},
            series: [{{ data: dailyData.map(d => d.count), type: 'line', smooth: true, areaStyle: {{ color: 'rgba(251,114,153,0.3)' }}, itemStyle: {{ color: '#fb7299' }} }}],
            grid: {{ left: '3%', right: '4%', bottom: '15%', containLabel: true }}
        }});

        // 时段分布
        const hourChart = echarts.init(document.getElementById('hourChart'));
        hourChart.setOption({{
            tooltip: {{ trigger: 'axis' }},
            xAxis: {{ type: 'category', data: hourData.map(d => d.hour) }},
            yAxis: {{ type: 'value' }},
            series: [{{ data: hourData.map(d => d.count), type: 'bar', itemStyle: {{ color: new echarts.graphic.LinearGradient(0,0,0,1,[{{offset:0,color:'#23ade5'}},{{offset:1,color:'#fb7299'}}]) }} }}],
            grid: {{ left: '3%', right: '4%', bottom: '10%', containLabel: true }}
        }});

        // 星期分布
        const weekChart = echarts.init(document.getElementById('weekChart'));
        weekChart.setOption({{
            tooltip: {{ trigger: 'axis' }},
            xAxis: {{ type: 'category', data: weekData.map(d => d.day) }},
            yAxis: {{ type: 'value' }},
            series: [{{ data: weekData.map(d => d.count), type: 'bar', itemStyle: {{ color: '#2ca02c', borderRadius: [4,4,0,0] }} }}],
            grid: {{ left: '3%', right: '4%', bottom: '10%', containLabel: true }}
        }});

        // TOP UP主
        const authorChart = echarts.init(document.getElementById('authorChart'));
        authorChart.setOption({{
            tooltip: {{ trigger: 'axis' }},
            xAxis: {{ type: 'value' }},
            yAxis: {{ type: 'category', data: authorData.map(d => d.name).reverse(), axisLabel: {{ width: 120, overflow: 'truncate' }} }},
            series: [{{ data: authorData.map(d => d.count).reverse(), type: 'bar', itemStyle: {{ color: new echarts.graphic.LinearGradient(0,0,1,0,[{{offset:0,color:'#fb7299'}},{{offset:1,color:'#ff9a9e'}}]) }} }}],
            grid: {{ left: '20%', right: '5%', bottom: '5%', top: '5%', containLabel: true }}
        }});

        // 关键词
        const wordChart = echarts.init(document.getElementById('wordChart'));
        wordChart.setOption({{
            tooltip: {{ trigger: 'axis' }},
            xAxis: {{ type: 'value' }},
            yAxis: {{ type: 'category', data: wordData.map(d => d.name).reverse(), axisLabel: {{ fontSize: 11 }} }},
            series: [{{ data: wordData.map(d => d.value).reverse(), type: 'bar', itemStyle: {{ color: new echarts.graphic.LinearGradient(0,0,1,0,[{{offset:0,color:'#9467bd'}},{{offset:1,color:'#c39bd3'}}]) }} }}],
            grid: {{ left: '15%', right: '5%', bottom: '5%', top: '5%', containLabel: true }}
        }});

        // 类型分布
        const typeChart = echarts.init(document.getElementById('typeChart'));
        typeChart.setOption({{
            tooltip: {{ trigger: 'item' }},
            series: [{{ type: 'pie', radius: ['40%', '70%'], data: typeData, itemStyle: {{ borderRadius: 8, borderColor: '#fff', borderWidth: 2 }}, label: {{ formatter: '{{b}}: {{c}} ({{d}}%)' }} }}]
        }});

        window.addEventListener('resize', () => {{
            dailyChart.resize(); hourChart.resize(); weekChart.resize();
            authorChart.resize(); wordChart.resize(); typeChart.resize();
        }});
    </script>
</body>
</html>"""

    html_path = os.path.join(OUTPUT_DIR, "report.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"\n✅ HTML报告保存至：{html_path}")
    print("   用浏览器打开即可查看交互式报告（动态图表+AI深度总结）")


if __name__ == "__main__":
    main()
