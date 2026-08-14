# 猎聘爬虫 · 完整操作手册

> 目的：爬取猎聘 AI 相关岗位，供 job-tracker 打分系统使用。
> 本手册 + 同目录脚本固化全部逻辑，下次照着做即可，不会忘。

---

## 0. 一句话流程

```
导航搜索页 → 跑提取脚本 → 保存 → sleep 45秒 → 下一关键词
  （5 个关键词都爬完）
→ 合并成 猎聘-8-13.json（raw）
→ 跑 merge.py 去重 → 猎聘-8-13_去重.json
→ 跑 batch_score_v2.py 打分 → import_ready_v2.json
→ 前端导入数据库
```

---

## 1. 文件规范

- **存放目录**：`E:\Trae CN\AI-Kart-Live\job-tracker\爬虫json\`
- **raw 文件名**：`猎聘-月-日.json`，例如 `猎聘-8-13.json`
  - ⚠️ **不能用 `/`**（如 `猎聘-8/13`），因为 `/` 是路径分隔符，会被当成「猎聘-8 目录下的 13 文件」
  - 想带年份可写 `猎聘-2026-8-13.json`
- **去重后**：`猎聘-8-13_去重.json`
- **打分后**：`import_ready_v2.json`（固定名，`batch_score_v2.py` 的输出）

一次爬取（5 个关键词）合并成一个 raw 文件，按当天日期命名。

---

## 2. 关键词清单（固定 5 个）

```
MCP
RAG
LLM
AI应用
AI工程师
```

⚠️ 注意：
- 不要用 `AI应用落地`（会返回空 / 失败），用 `AI应用`。

---

## 3. 搜索 URL

模板：`https://www.liepin.com/zhaopin/?key={关键词}`

例：`https://www.liepin.com/zhaopin/?key=MCP`

每页约 40-42 条，**每个关键词只爬第 1 页**即可（5 词 × 42 ≈ 210 条）。

---

## 4. 爬取字段（共 10 个）

卡片选择器：`.job-card-pc-container`（一页约 42 个卡片，每个卡片 = 一个岗位）

| # | 字段 | 说明 | 定位方式 |
|---|------|------|----------|
| 1 | `title` | 岗位标题 | `a[data-nick="job-detail-job-info"]` 内的 `div.ellipsis-1[title]` |
| 2 | `salary` | 薪资 | 岗位信息块第 1 个子 div 内，文本含 `k/元/薪/万` 的 span |
| 3 | `location` | 工作地点 | 岗位信息块第 1 个子 div 内的 `span.ellipsis-1`（【】包裹的那个） |
| 4 | `company` | 公司名 | `div[data-nick="job-detail-company-info"]` 内第一个 `span.ellipsis-1` |
| 5 | `industry` | 行业 | 公司信息块 3 个 span 中，**不含「人+数字」也不含「上市/融资/轮」**的那个 |
| 6 | `funding` | 融资阶段 | 含 `上市/融资/轮` 的那个 span |
| 7 | `scale` | 企业规模 | 含「人」且含数字的那个 span |
| 8 | `experience` | 经验要求 | 标签区（岗位信息块第 2 个子 div）的**第一个** span |
| 9 | `education` | 学历要求 | 标签区的**最后一个** span |
| 10 | `url` | 岗位链接 | `a[data-nick="job-detail-job-info"]` 的 href，**去掉 `?` 后的 query** |

> 合并时额外加 `keywords` 字段，标记该岗位来自哪些关键词（如 `["MCP","LLM"]`）。

### ⚠️ industry / funding / scale 的分类规则（最容易弄错）

公司信息块里有 **3 个 span**，但有些公司缺融资阶段、有些缺规模，所以**不能按位置取**，必须按文本特征分类：

```
"互联网港股上市2000-5000人"  →  互联网 | 港股上市 | 2000-5000人   (3 个 span 齐全)
"基金/证券/期货2000-5000人"  →  基金/证券/期货 | (空) | 2000-5000人 (缺 funding)
"其他商务服务业"             →  其他商务服务业 | (空) | (空)        (缺 funding+scale)
```

判断顺序（在 JS 里循环三个 span）：
1. 含 `人` 且含数字 → `scale`
2. 含 `上市 / 融资 / 轮` → `funding`
3. 其余 → `industry`

### ⚠️ JD 正文（详情页）

- **猎聘 JD 详情页已被反爬封禁**，不要尝试抓详情页正文（`jd_full`/`description`）。
- 因此打分时 JD 匹配维度（第⑦维）只能靠**标题**匹配，`jd_coverage` 部分岗位会是 0%，属正常现象，不是 bug。

---

## 5. 提取脚本

见同目录 **`liepin_extract.js`**。

- 每导航到一个关键词页面后，运行一次，得到该页 42 条数据。
- 保存时给每条打上 `keyword` 标记（当前关键词）。
- 校验：`title`、`company`、`url` 三者非空才保留。

---

## 6. 防反爬策略

- 每个关键词之间 **sleep 45 秒**。
- 顺序：`导航 → 提取 → 保存 → sleep 45s → 下一个关键词`。
- 只要间隔够，5 个词连续爬不会被风控（已验证）。

---

## 7. 后续流程（命令行）

```bash
# 1) 去重（读 爬虫json/猎聘-*.json，输出 猎聘-合并_去重.json）
cd "E:\Trae CN\AI-Kart-Live\job-tracker\爬虫json"
python merge.py

# 2) 打分（读去重文件，输出 import_ready_v2.json）
cd "E:\Trae CN\AI-Kart-Live\job-tracker"
python batch_score_v2.py "爬虫json/猎聘-合并_去重.json" -o "爬虫json/import_ready_v2.json"

# 3) 导入：启动后端 + 前端，在 http://localhost:5173 导入 import_ready_v2.json
```

---

## 8. 关键路径速查

| 东西 | 路径 |
|------|------|
| 爬虫文件目录 | `job-tracker\爬虫json\` |
| 提取脚本 | `job-tracker\爬虫json\liepin_extract.js` |
| 去重脚本 | `job-tracker\爬虫json\merge.py` |
| 打分脚本 | `job-tracker\batch_score_v2.py` |
| JD 匹配引擎 | `job-tracker\jd_matcher.py` |
| 能力矩阵 | `skills_matrix.json`（项目根目录） |
| 导入 API | `backend\routes\import_jobs.py` → `/api/import/batch` |
