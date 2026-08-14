# 求职全链路智能管理系统 (job-tracker)

数据驱动的求职管理系统：`采集 JD → AI 打分 → 结构化入库 → 投递状态跟踪 → 可视化看板` 全链路闭环，用 Dashboard 一屏替代碎片化的手动记录。

## ✨ 核心能力

- **浏览器自动化采集**：基于 MCP 协议 + Playwright，反检测 / 随机延迟 / 持久化登录态，单轮 40 条结构化 JD
- **AI 六维打分引擎**：三层关键词匹配（硬伤否决 → 正向加权 → 反向覆盖率校验）+ 六维评分 + 城市加分
- **全栈跟踪应用**：FastAPI + React 18 + TypeScript，13 种状态流转 + ECharts 雷达图 / 漏斗图
- **工程化部署**：SQLite WAL + 幂等迁移 + Docker Compose + Nginx

## 🏗️ 架构

```
采集（Playwright MCP）→ 打分（jd_matcher + batch_score）→ 入库（FastAPI + SQLite）→ 跟踪看板（React）
```

## 🛠️ 技术栈

- **后端**：FastAPI / SQLite (WAL) / Pydantic v2
- **前端**：React 18 / TypeScript / Vite / ECharts
- **采集**：Playwright / MCP 协议
- **部署**：Docker Compose / Nginx

## 📁 目录结构

```
.
├── backend/              # FastAPI 后端（数据库 + REST API）
│   ├── main.py           # 入口
│   ├── database.py       # SQLite 层（WAL + 外键）
│   ├── models.py         # Pydantic 模型
│   └── routes/           # jobs / stats / import_jobs
├── frontend/             # React 18 + TS + Vite 前端
│   └── src/
│       ├── components/   # 雷达图 / 漏斗图 / 状态时间线等
│       └── pages/        # Dashboard / JobList / JobDetail
├── batch_score_v2.py     # 六维打分脚本
├── jd_matcher.py         # JD 三层匹配引擎
├── convert_for_import.py # 爬虫 JSON → 导入格式
├── 爬虫json/             # 采集脚本（liepin_extract.js / merge.py）
├── docker-compose.yml
└── start.bat             # Windows 本地一键启动
```

## 🚀 快速开始

### Docker（推荐）

```bash
docker-compose up -d
# 后端 http://localhost:8004 ｜ 前端 http://localhost:5173
```

### 本地开发

```bash
# 后端
cd backend && pip install -r requirements.txt && python main.py

# 前端（另开终端）
cd frontend && npm install && npm run dev
```

## 📊 打分流程

```bash
# 1) 去重（读 爬虫json/猎聘-*.json，输出 猎聘-合并_去重.json）
cd 爬虫json && python merge.py

# 2) 打分（输出 import_ready_v2.json）
cd .. && python batch_score_v2.py 爬虫json/猎聘-合并_去重.json -o 爬虫json/import_ready_v2.json

# 3) 导入：前端上传 import_ready_v2.json，或调用 POST /api/import/batch
```

采集环节的完整说明见 [爬虫json/README.md](爬虫json/README.md)。

## 🔒 隐私说明

- 数据库 `tracker.db` 与爬取数据 `爬虫json/*.json` 已通过 `.gitignore` 排除，不进入仓库
- `jd_matcher.py` 的能力矩阵默认使用内置精简版，不含个人求职策略（薪资 / 城市 / 年限等）
