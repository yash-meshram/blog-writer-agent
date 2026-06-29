from schemas.schema import State, Plan
from models.llm import get_model
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.types import Send
from pathlib import Path

llm = get_model()

def orchestrator(state: State) -> dict:
    plan = llm.with_structured_output(Plan).invoke(
        [
            SystemMessage(
                content = "Create a blog plan with 5-7 sections on the following topic."
            ),
            HumanMessage(
                content = f"Topic: {state["topic"]}"
            )
        ]   
    )
    return {"plan": plan}


def fanout(state: State):
    return [
        Send(
            "worker",
            {
                "task": task,
                "topic": state["topic"],
                "plan": state["plan"]
            }
        )
        for task in state["plan"].tasks
    ]
    

def worker(payload: dict) -> dict:
    task = payload["task"]
    topic = payload["topic"]
    plan = payload["plan"]
    blog_title = plan.blog_title
    
    section_content = llm.invoke(
        [
            SystemMessage(
                content = "Write one clean mardown section."
            ),
            HumanMessage(
                content = f"""
                Blog: {blog_title}
                Topic: {topic}
                Section: {task.title}
                Brief: {task.brief}
                Return only the section content in markdown.
                """
            )
        ]
    ).content.strip()
    
    return {"sections": [section_content]}


def reducer(state: State) -> dict:
    title = state["plan"].blog_title
    body = "\n\n".join(state["sections"]).strip()
    
    final = f"# {title}\n\n{body}\n"
    
    filename = title.lower().replace(" ", "_") + ".md"
    output_path = Path(f"data/{filename}")
    output_path.write_text(final, encoding = "utf-8")
    
    return {"final": final}