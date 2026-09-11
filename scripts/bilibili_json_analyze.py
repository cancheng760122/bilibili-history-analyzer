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
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from collections import Counter

plt.rcParams["font.sans-serif"] = ["SimHei", "WenQuanYi Micro Hei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# -------------------------- 路径配置 --------------------------
JSON_FILE_PATH = "bilibili-history-backup.json"
OUTPUT_DIR = "output_json"
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

    # ========== 生成报告 ==========
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


if __name__ == "__main__":
    main()
