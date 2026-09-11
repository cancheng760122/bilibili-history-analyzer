# 📊 B站观看历史分析看板

> 一个纯前端的B站观看历史可视化分析工具，上传文件即可生成全套交互式图表，数据仅在本地浏览器处理，不上传服务器。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

## 🖼️ 项目预览

![项目截图](assets/screenshot.png)

## ✨ 功能特性

- 📈 **每日趋势** — 每日观看视频数量折线图，支持缩放拖拽
- ⏰ **时段分布** — 24小时观看分布柱状图，自动高亮最活跃时段
- 📅 **星期分布** — 周一到周日观看数量对比
- 👤 **TOP UP主** — 观看最多的15位UP主横向排行
- 🏷️ **类型分布** — 视频类型占比饼图
- 🔤 **关键词词频** — 视频标题分词TOP30高频词分析
- 💡 **智能洞察** — 自动总结观看习惯、深夜占比、兴趣标签
- 🔒 **隐私安全** — 所有数据在本地浏览器处理，不上传任何服务器

## 🚀 快速开始

### 方式一：直接使用（推荐）

1. 下载本项目的 `index.html` 文件
2. 双击用浏览器打开（Chrome / Edge / Firefox 均可）
3. 点击上传区域，选择B站导出的历史记录文件（CSV或JSON）
4. 自动解析并生成可视化分析

> 也可以先点击「加载示例数据」预览效果

### 方式二：本地部署

```bash
# 克隆项目
git clone https://github.com/your-username/bilibili-history-analyzer.git
cd bilibili-history-analyzer

# 启动本地服务器（任选其一）
python3 -m http.server 8080
# 或
npx serve .
```

然后访问 `http://localhost:8080`

## 📁 支持的文件格式

### CSV 格式
B站网页端「历史记录」页面直接导出的CSV文件，包含以下字段：
- 标题、观看时间、类型、链接、封面、作者、作者主页

### JSON 格式
B站历史记录备份JSON文件，自动识别：
- 顶层 `history` 字段中的记录数组
- `view_at` 观看时间戳（秒级）
- `author_name` UP主名称
- `title` 视频标题

## 🛠️ 技术栈

| 技术 | 用途 |
|------|------|
| [ECharts 5](https://echarts.apache.org/) | 交互式图表渲染 |
| [PapaParse 5](https://www.papaparse.com/) | CSV文件解析 |
| 原生 JavaScript | 数据处理与中文分词（2-gram算法） |
| HTML5 + CSS3 | 页面结构与样式 |

> 所有依赖通过 CDN 加载，无需 npm install，单个 HTML 文件即可运行。

## 📂 项目结构

```
bilibili-history-analyzer/
├── index.html              # 主页面（核心功能，单文件即可运行）
├── README.md               # 项目说明文档
├── LICENSE                 # MIT 开源协议
├── .gitignore              # Git忽略配置
├── assets/
│   └── screenshot.png      # 项目截图
├── examples/
│   └── sample.csv          # 示例数据（可用于测试）
└── scripts/
    ├── bilibili_analysis.py       # CSV版本Python分析脚本
    └── bilibili_json_analyze.py   # JSON版本Python分析脚本
```

## 📊 分析维度说明

### 统计指标
- 总观看记录数
- 统计天数
- 时间范围
- 关注UP主数量
- 日均观看条数

### 智能洞察
- 观看最多的一天及数量
- 最活跃的时段
- 观看最多的星期
- 深夜时段（22:00-02:00）占比
- 最常看的UP主
- 最高频关键词

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的修改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

## 📝 更新日志

### v1.0.0
- 🎉 首次发布
- ✅ 支持CSV和JSON双格式解析
- ✅ 6大可视化分析维度
- ✅ 智能观看习惯洞察
- ✅ 纯前端实现，数据本地处理

## 📄 许可证

本项目基于 [MIT License](LICENSE) 开源协议。

## 🙏 致谢

- [ECharts](https://echarts.apache.org/) — 强大的图表库
- [PapaParse](https://www.papaparse.com/) — 强大的CSV解析库
- 所有为这个项目贡献代码的人

---

**如果这个项目对你有帮助，欢迎给个 ⭐ Star 支持一下！**
