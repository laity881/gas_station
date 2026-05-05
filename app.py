import os
import streamlit as st
from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from agent_tools import (
    ALL_TOOLS,
    list_categories_raw,
    list_notes_raw,
    read_note_raw,
    search_notes_raw,
    NOTES_ROOT,
)

load_dotenv()

# ---------- 页面配置 ----------
st.set_page_config(page_title="⛽ Gas Station", page_icon="⛽", layout="wide")
st.title("⛽ Gas Station - 智能知识管家")
st.markdown("*随时速记，AI 自动纠错、分类、保存。你的个人加油站。*")

# ---------- 初始化 Agent ----------
@st.cache_resource
def load_agent():
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        st.error("未找到 DEEPSEEK_API_KEY，请在 .env 文件中设置或手动输入。")
        st.stop()

    llm = ChatOpenAI(
        model="deepseek-chat",
        openai_api_key=api_key,
        openai_api_base="https://api.deepseek.com/v1",
        temperature=0.1,
        max_tokens=2000,
    )

    system_message = (
        "你是一个名为“Gas Station 管家”的个人知识助手。"
        "你的职责是将用户随意记录的“速记”处理成一则规范的 Markdown 笔记并保存。\n\n"
        "**工作流程：**\n"
        "1. 仔细阅读用户输入，提炼核心思想和关键信息。\n"
        "2. 纠正错别字、口语化表达，使语句通顺、要点清晰。\n"
        "3. 生成一个简洁的标题（10字以内）和完整的 Markdown 正文，可适当扩展但忠于原意。\n"
        "4. 根据内容主题确定一个分类，已有分类：{categories}。若都不合适，可创建新分类（文件夹名）。\n"
        "5. 调用 `save_note` 工具保存，参数 category、title、content（均为字符串）。\n"
        "6. 保存成功后，回复用户一句鼓励的话，并告知已保存到哪个分类。"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, ALL_TOOLS, prompt)
    return AgentExecutor(agent=agent, tools=ALL_TOOLS, verbose=True, handle_parsing_errors=True)

agent_executor = load_agent()

# ---------- 主布局 ----------
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📝 自由速记")
    user_input = st.text_area(
        "在这里随意写下你的灵感、经验、资源...",
        placeholder="例：今天学到一个很牛的 Git 技巧，git bisect 可以用二分法定位引入 bug 的提交，太高效了！",
        height=150,
        key="note_input"
    )

    if st.button("⛽ 加满智慧", type="primary"):
        if not user_input.strip():
            st.warning("请先输入一些内容～")
        else:
            with st.spinner("AI 管家正在整理你的笔记..."):
                try:
                    categories = list_categories_raw()   # ✅ 使用 raw 函数
                    context = {
                        "input": user_input,
                        "categories": ", ".join(categories) if categories else "暂无"
                    }
                    result = agent_executor.invoke(context)
                    output = result.get("output", "处理完成，但未收到回复。")
                    st.success(output)
                except Exception as e:
                    st.error(f"处理出错：{str(e)}")
                    st.info("若问题持续，请检查网络连接和 API Key 是否正确。")

    st.divider()
    st.subheader("🔍 知识检索")
    search_query = st.text_input("搜索你的笔记库", placeholder="输入关键词...")
    if search_query:
        results = search_notes_raw(search_query)   # ✅ 使用 raw 函数
        st.markdown(results)

with col2:
    st.subheader("📂 笔记分类浏览")
    categories = list_categories_raw()   # ✅ 使用 raw 函数
    if not categories:
        st.info("尚无笔记分类。快去记录第一条灵感吧！")
    else:
        selected_category = st.selectbox("选择分类", categories)
        notes = list_notes_raw(selected_category)   # ✅ 使用 raw 函数
        if notes:
            selected_note = st.selectbox("选择笔记", notes)
            if selected_note:
                with st.expander(f"📄 {selected_note}", expanded=True):
                    content = read_note_raw(selected_category, selected_note)   # ✅ 使用 raw 函数
                    st.markdown(content)
        else:
            st.info("该分类下还没有笔记。")

    st.divider()
    st.subheader("📊 统计")
    total_notes = sum(len(list_notes_raw(cat)) for cat in categories) if categories else 0
    st.metric("总笔记数", total_notes)
    st.metric("分类数", len(categories))
    