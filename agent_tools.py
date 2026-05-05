import os
import re
from datetime import datetime
from pathlib import Path
from typing import List
from langchain.tools import tool

NOTES_ROOT = Path("gas_station_notes")
NOTES_ROOT.mkdir(exist_ok=True)

# ========== 原始函数（供界面直接调用）==========
def save_note_raw(category: str, title: str, content: str) -> str:
    """保存一篇笔记为 Markdown 文件，需要提供分类、标题和内容。"""
    safe_category = re.sub(r'[\\/*?:"<>|]', "", category).strip()
    safe_title = re.sub(r'[\\/*?:"<>|]', "", title).strip()
    if not safe_category or not safe_title:
        return "错误：分类和标题不能为空。"
    category_dir = NOTES_ROOT / safe_category
    category_dir.mkdir(exist_ok=True)
    filename = f"{safe_title}.md"
    filepath = category_dir / filename
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    frontmatter = f"""---
title: {safe_title}
category: {safe_category}
date: {now}
---

"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(frontmatter + content)
    return f"笔记已保存到: {filepath}"

def list_categories_raw() -> List[str]:
    """列出所有已有的笔记分类（文件夹名）。"""
    if not NOTES_ROOT.exists():
        return []
    return [d.name for d in NOTES_ROOT.iterdir() if d.is_dir()]

def list_notes_raw(category: str) -> List[str]:
    """列出指定分类下的所有笔记文件名。"""
    category_dir = NOTES_ROOT / category
    if not category_dir.exists():
        return []
    return [f.name for f in category_dir.iterdir() if f.is_file() and f.suffix == '.md']

def read_note_raw(category: str, filename: str) -> str:
    """读取指定笔记的完整内容。"""
    filepath = NOTES_ROOT / category / filename
    if not filepath.exists():
        return "笔记不存在。"
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def search_notes_raw(keyword: str) -> str:
    """在所有笔记中搜索关键词，返回匹配的片段。"""
    results = []
    for root, dirs, files in os.walk(NOTES_ROOT):
        for file in files:
            if file.endswith(".md"):
                filepath = Path(root) / file
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    if keyword.lower() in content.lower():
                        idx = content.lower().find(keyword.lower())
                        start = max(0, idx - 50)
                        end = min(len(content), idx + len(keyword) + 50)
                        snippet = content[start:end].replace('\n', ' ')
                        rel_path = filepath.relative_to(NOTES_ROOT)
                        results.append(f"**{rel_path}** → ...{snippet}...")
    if not results:
        return "未找到匹配的笔记。"
    return "\n\n".join(results)

# ========== 工具对象（供 Agent 使用）==========
save_note_tool = tool(save_note_raw)
list_categories_tool = tool(list_categories_raw)
list_notes_tool = tool(list_notes_raw)
read_note_tool = tool(read_note_raw)
search_notes_tool = tool(search_notes_raw)

ALL_TOOLS = [
    save_note_tool,
    list_categories_tool,
    list_notes_tool,
    read_note_tool,
    search_notes_tool,
]

