"""
B站观看记录数据分析脚本
适配字段：标题,观看时间,类型,链接,封面,作者,作者主页
"""
import pandas as pd
import matplotlib.pyplot as plt
import os

# ========== 配置区 ==========
# 把你的csv文件名放这里，和脚本放同一个文件夹
CSV_PATH = "bilibili-history-2026-09-11.csv"
# ============================

# 设置中文显示（防止图里中文变成方框）
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False

# 创建输出文件夹，存放生成的图表
os.makedirs("output", exist_ok=True)

# ========== 1. 读取数据 ==========
df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
print("=" * 50)
print("【数据概览】")
print(f"总观看记录：{len(df)} 条")
print(f"字段数量：{df.shape[1]} 个")
print(f"字段列表：{df.columns.tolist()}")
print(f"时间范围：{df['观看时间'].min()}  ~  {df['观看时间'].max()}")

# ========== 2. 缺失值检查 ==========
print("\n" + "=" * 50)
print("【缺失值统计】")
print(df.isnull().sum())

# ========== 3. 时间处理（核心！UTC转北京时间，提取小时/星期/日期）==========
# 观看时间是 UTC 时区（末尾带Z），转成北京时间 UTC+8
df["观看时间"] = pd.to_datetime(df["观看时间"], utc=True)
df["北京时间"] = df["观看时间"].dt.tz_convert("Asia/Shanghai")

# 提取时间维度
df["小时"] = df["北京时间"].dt.hour
df["星期"] = df["北京时间"].dt.dayofweek  # 0=周一, 6=周日
df["日期"] = df["北京时间"].dt.date
df["月份"] = df["北京时间"].dt.to_period("M")

weekday_map = {0: "周一", 1: "周二", 2: "周三", 3: "周四", 4: "周五", 5: "周六", 6: "周日"}
df["星期名"] = df["星期"].map(weekday_map)

print("\n" + "=" * 50)
print("【时间处理完成】已转换为北京时间，并提取：小时、星期、日期、月份")

# ========== 4. 观看最多的UP主 TOP15 ==========
print("\n" + "=" * 50)
print("【观看最多的UP主 TOP15】")
top_authors = df["作者"].value_counts().head(15)
print(top_authors)

# 绘图：UP主TOP15横向柱状图
plt.figure(figsize=(10, 6))
top_authors.sort_values().plot(kind="barh", color="#4A90D9")
plt.title("观看最多的UP主 TOP15", fontsize=14)
plt.xlabel("观看次数")
plt.ylabel("UP主")
plt.tight_layout()
plt.savefig("output/top_authors.png", dpi=150)
plt.close()
print("✅ 图表已保存：output/top_authors.png")

# ========== 5. 一天中各时段观看分布 ==========
print("\n" + "=" * 50)
print("【各时段观看次数】")
hour_dist = df["小时"].value_counts().sort_index()
print(hour_dist)

# 绘图：小时分布柱状图
plt.figure(figsize=(12, 5))
hour_dist.plot(kind="bar", color="#50C878")
plt.title("一天中各时段观看次数分布", fontsize=14)
plt.xlabel("小时（北京时间）")
plt.ylabel("观看次数")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig("output/hour_distribution.png", dpi=150)
plt.close()
print("✅ 图表已保存：output/hour_distribution.png")

# ========== 6. 星期分布 ==========
print("\n" + "=" * 50)
print("【星期观看分布】")
weekday_order = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
weekday_dist = df["星期名"].value_counts().reindex(weekday_order)
print(weekday_dist)

# 绘图：星期分布
plt.figure(figsize=(8, 5))
weekday_dist.plot(kind="bar", color="#FFB347")
plt.title("一周各天观看次数分布", fontsize=14)
plt.xlabel("星期")
plt.ylabel("观看次数")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig("output/weekday_distribution.png", dpi=150)
plt.close()
print("✅ 图表已保存：output/weekday_distribution.png")

# ========== 7. 按日期观看趋势 ==========
print("\n" + "=" * 50)
print("【每日观看次数（最近30天）】")
daily_dist = df.groupby("日期").size().sort_index()
print(daily_dist.tail(30))

# 绘图：每日趋势折线图
plt.figure(figsize=(14, 5))
daily_dist.plot(kind="line", marker="o", color="#E74C3C", markersize=3)
plt.title("每日观看次数趋势", fontsize=14)
plt.xlabel("日期")
plt.ylabel("观看次数")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("output/daily_trend.png", dpi=150)
plt.close()
print("✅ 图表已保存：output/daily_trend.png")

# ========== 8. 内容类型分布 ==========
print("\n" + "=" * 50)
print("【内容类型分布】")
type_dist = df["类型"].value_counts()
print(type_dist)

# 绘图：类型饼图
plt.figure(figsize=(6, 6))
type_dist.plot(kind="pie", autopct="%1.1f%%", startangle=90)
plt.title("观看内容类型占比", fontsize=14)
plt.ylabel("")
plt.tight_layout()
plt.savefig("output/type_distribution.png", dpi=150)
plt.close()
print("✅ 图表已保存：output/type_distribution.png")

# ========== 9. 生成文字版分析报告 ==========
report = f"""
{'='*60}
                B站观看记录分析报告
{'='*60}

📊 基本信息
  - 总观看记录：{len(df)} 条
  - 时间范围：{df['北京时间'].min().strftime('%Y-%m-%d')} 至 {df['北京时间'].max().strftime('%Y-%m-%d')}
  - 涉及UP主数量：{df['作者'].nunique()} 位

👤 观看最多的UP主 TOP5
{top_authors.head(5).to_string()}

⏰ 观看习惯
  - 最活跃时段：{hour_dist.idxmax()} 点（共 {hour_dist.max()} 次）
  - 最活跃星期：{weekday_dist.idxmax()}（共 {weekday_dist.max()} 次）
  - 单日最多观看：{daily_dist.max()} 条（{daily_dist.idxmax()}）

📺 内容类型
{type_dist.to_string()}

{'='*60}
"""
print(report)

# 保存报告到文件
with open("output/analysis_report.txt", "w", encoding="utf-8") as f:
    f.write(report)
print("✅ 文字报告已保存：output/analysis_report.txt")
print("\n🎉 全部分析完成！图表和报告都在 output 文件夹里。")
