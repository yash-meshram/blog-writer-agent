from schemas.schema import State, Plan
from models.llm import get_model
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.types import Send
from pathlib import Path
import re

llm = get_model()

_INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*]')


def _blog_filename(title: str) -> str:
    slug = title.lower().replace(" ", "_")
    slug = _INVALID_FILENAME_CHARS.sub("", slug)
    slug = re.sub(r"_+", "_", slug).strip("_")
    return f"{slug}.md"

def orchestrator(state: State) -> dict:
    planner = llm.with_structured_output(
        Plan,
        method = "json_schema"
    )
    plan = planner.invoke(
        [
            SystemMessage(
                content = """
                You are a senior blog writer. Your job is to produce a highly actionable outline for a technical blog post.
                Hard requirements:
                - Create 5-7 sections (tasks) that fit a technical blog.
                - Each section must include:
                1) goal (1 sentence: what the reader can do/understand after the section)
                2) 3-5 bullets that are concrete, specific, and non-overlapping
                3) target word count (120-450)
                - Include EXACTLY ONE section with section_type='common_mistakes'.
                Make it technical (not generic):
                - Assume the reader is a technical person; use correct terminology.
                - Prefer design/engineering structure: problem → intuition → approach → implementation → trade-offs → testing/observability → conclusion.
                - Bullets must be actionable and testable (e.g., 'Show a minimal code snippet for X', 'Explain why Y fails under Z condition', 'Add a checklist for production readiness').
                - Explicitly include at least ONE of the following somewhere in the plan (as bullets):
                * a minimal working example (MWE) or code sketch
                * edge cases / failure modes
                * performance/cost considerations
                * security/privacy considerations (if relevant)
                * debugging tips / observability (logs, metrics, traces)
                - Avoid vague bullets like 'Explain X' or 'Discuss Y'. Every bullet should state what to build/compare/measure/verify.
                Ordering guidance:
                - Start with a crisp intro and problem framing.
                - Build core concepts before advanced details.
                - Include one section for common mistakes and how to avoid them.
                - End with a practical summary/checklist and next steps.
                Output must strictly match the Plan schema.
                """
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
    bullet_text = "\n- ".join(task.bullets)
    
    section_content = llm.invoke(
        [
            SystemMessage(
                content = """
                You are a senior technical writer and developer advocate. Write ONE section of a technical blog post in Markdown.
                Hard constraints:
                - Follow the provided Goal and cover ALL Bullets in order (do not skip or merge bullets).
                - Stay close to the Target words (±15%).
                - Output ONLY the section content in Markdown (no blog title H1, no extra commentary).
                Technical quality bar:
                - Be precise and implementation-oriented (developers should be able to apply it).
                - Prefer concrete details over abstractions: APIs, data structures, protocols, and exact terms.
                - When relevant, include at least one of:
                * a small code snippet (minimal, correct, and idiomatic)
                * a tiny example input/output
                * a checklist of steps
                * a diagram described in text (e.g., 'Flow: A -> B -> C')
                - Explain trade-offs briefly (performance, cost, complexity, reliability).
                - Call out edge cases / failure modes and what to do about them.
                - If you mention a best practice, add the 'why' in one sentence.
                Markdown style:
                - Start with a '## <Section Title>' heading.
                - Use short paragraphs, bullet lists where helpful, and code fences for code.
                - Avoid fluff. Avoid marketing language.
                - If you include code, keep it focused on the bullet being addressed.
                """
            ),
            HumanMessage(
                content = f"""
                Blog: {plan.blog_title}
                Topic: {topic}
                Section: {task.title}
                Brief: {task.brief}
                Bullets: {bullet_text}
                Goal: {task.goal}
                Tone: {plan.tone}
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
    
    output_path = Path("data") / _blog_filename(title)
    output_path.parent.mkdir(parents = True, exist_ok = True)
    output_path.write_text(final, encoding = "utf-8")
    
    return {"final": final}