# 复盘报告 {{ report_date }}

**复盘范围：** {{ scope }}
**扫描文章数：** {{ article_count }}
**扫描卡片数：** {{ card_count }}
**发现问题数：** {{ issue_count }}

---

## 📊 统计摘要
| 问题类型 | 数量 | 已处理 | 待处理 |
|:--------|:----:|:------:|:------:|
| 重复定义 | {{ duplicate_count }} | | |
| 结论冲突 | {{ conflict_count }} | | |
| 内容冗余 | {{ redundant_count }} | | |
| 知识盲区 | {{ gap_count }} | | |

---

## 🔍 问题详情

{% for issue in issues %}
### 问题 #{{ issue.id }}：{{ issue.title }}
**类型：** {{ issue.type }}
**严重程度：** {{ issue.severity }}

{{ issue.description }}

**涉及文件：**
{% for file in issue.files %}
- [[{{ file }}]]
{% endfor %}

**建议处理方案：**
{{ issue.suggestion }}

---
{% endfor %}

## 📝 复盘结论
{{ conclusion }}
