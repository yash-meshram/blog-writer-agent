from schemas.schema import EvidencePack, GlobalImagePlan, RouterDecision, State, Plan
from models.llm import get_model, get_image_model
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.types import Send
from pathlib import Path
import re
from typing import List
from langchain_tavily import TavilySearch
from config.config import settings
from google.genai import types

llm = get_model()


def router(state: State) -> dict:
    topic = state["topic"]
    decider = llm.with_structured_output(RouterDecision)
    decision = decider.invoke(
        [
            SystemMessage(
                content = """
                You are a routing module for a technical blog planner.
                Decide whether web research is needed BEFORE planning.
                Modes:
                - closed_book (needs_research=false):
                Evergreen topics where correctness does not depend on recent facts (concepts, fundamentals).
                - hybrid (needs_research=true):
                Mostly evergreen but needs up-to-date examples/tools/models to be useful.
                - open_book (needs_research=true):
                Mostly volatile: weekly roundups, "this week", "latest", rankings, pricing, policy/regulation.
                If needs_research=true:
                - Output 3–10 high-signal queries.
                - Queries should be scoped and specific (avoid generic queries like just "AI" or "LLM").
                - If user asked for "last week/this week/latest", reflect that constraint IN THE QUERIES.
                """
            ),
            HumanMessage(
                content = f"Topic: {topic}"
            )
        ]
    )
    
    return {
        "needs_reserach": decision.needs_research,
        "research_type": decision.research_type,
        "queries": decision.queries
    }
    
    
def route_next(state: State) -> str:
    return "researcher" if state["needs_reserach"] else "orchestrator"


def _tavily_search(query: str, max_results: int = 5) -> List[dict]:
    tool = TavilySearch(
        tavily_api_key = settings.TAVILY_API_KEY,
        max_results = max_results
    )
    results = tool.invoke(
        {
            "query": query
        }
    )["results"]
    results_list: List[dict] = []
    for result in results or []:
        results_list.append(
            {
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "content": result.get("content", ""),
                "published_at": result.get("published_at", ""),
                "source": result.get("source", "")
            }
        )
    
    return results_list


def researcher(state: State) -> dict:
    queries = state["queries"]
    max_results = 3
    results: List[dict] = []
    
    for query in queries:
        results.append(
            _tavily_search(query = query, max_results = max_results)
        )
        
    if not results:
        return {"evidence": []}
    
    research = llm.with_structured_output(EvidencePack)
    reserached_data = research.invoke(
        [
            SystemMessage(
                content = """
                You are a research synthesizer for technical writing.
                Given raw web search results, produce a deduplicated list of EvidenceItem objects.
                Rules:
                - Only include items with a non-empty url.
                - Prefer relevant + authoritative sources (company blogs, docs, reputable outlets).
                - If a published date is explicitly present in the result payload, keep it as YYYY-MM-DD.
                If missing or unclear, set published_at=null. Do NOT guess.
                - Keep snippets short.
                - Deduplicate by URL.
                """
            ),
            HumanMessage(content = f"results: \n{results}")
        ]
    )
    
    return {"evidence": [evidence for evidence in reserached_data]}


def orchestrator(state: State) -> dict:
    print("================================================================================")
    print(state)
    print("================================================================================")
    topic = state["topic"]
    mode = state.get("mode", "closed_book")
    evidence = state.get("evidence", [])
    
    planner = llm.with_structured_output(Plan)
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
                content = (
                    f"Topic: {topic}"
                    f"Mode: {mode}"
                    f"Evidence (if empty ignore it): {evidence}"
                )
            )
        ]   
    )
    
    # Saving state in state.json file
    # with open("state_orchestrator.json", "w", encoding="utf-8") as f:
    #     json.dump(state, f, indent=4, default=str)
    #
    
    return {"plan": plan}


def fanout(state: State):
    return [
        Send(
            "worker",
            {
                "task": task,
                "topic": state["topic"],
                "mode": state.get("mode", "closed_book"),
                "plan": state["plan"],
                "evidence": state["evidence"]
            }
        )
        for task in state["plan"].tasks
    ]
    

def worker(payload: dict) -> dict:
    task = payload["task"]
    topic = payload["topic"]
    mode = payload.get("mode", "closed_book")
    plan = payload["plan"]
    evidence = payload.get("evidence", [])
    
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
                - Add source wherever required.
                """
            ),
            HumanMessage(
                content = f"""
                Blog: {plan.blog_title}
                Blog type: {plan.blog_type}
                Audience: {plan.audience}
                Constrains: {plan.constrains}
                Topic: {topic}
                Mode: {mode}
                Section: {task.title}
                Brief: {task.brief}
                Bullets: {bullet_text}
                Goal: {task.goal}
                Tone: {plan.tone}
                Tag: {task.tags}
                Requires research: {task.requires_research}
                Requires Citation: {task.requires_citation}
                Requires Code: {task.requires_code}
                Evidence (if empty igmore): {evidence}
                Return only the section content in markdown.
                """
            )
        ]
    ).content.strip()
    
    return {"sections": [(task.id, section_content)]}

_INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*]')
def _blog_foldername(title: str) -> str:
    slug = title.lower().replace(" ", "_")
    slug = _INVALID_FILENAME_CHARS.sub("", slug)
    slug = re.sub(r"_+", "_", slug).strip("_")
    return f"{slug}"

# def reducer(state: State) -> dict:
#     title = state["plan"].blog_title
#     ordered_sections = [section for _, section in sorted(state["sections"], key = lambda x: x[0])]
#     body = "\n\n".join(ordered_sections).strip()
    
#     final = f"# {title}\n\n{body}\n"
    
#     output_path = Path("data") / _blog_filename(title)
#     output_path.parent.mkdir(parents = True, exist_ok = True)
#     output_path.write_text(final, encoding = "utf-8")
    
#     return {"final": final}


def merge_content(state: State) -> dict:
    title = state["plan"].blog_title
    ordered_sections = [section for _, section in sorted(state["sections"], key = lambda x: x[0])]
    body = "\n\n".join(ordered_sections).strip()
    blog_content = f"# {title}\n\n{body}\n"
    
    return {"blog_content": blog_content}


def decide_images(state: State) -> dict:
    image_planner = llm.with_structured_output(GlobalImagePlan)
    blog_content = state["blog_content"]
    plan = state["plan"]
    
    image_plan = image_planner.invoke(
        [
            SystemMessage(
                content = """
                You are an expert technical editor.
                Decide if images/diagrams are needed for THIS blog.

                Rules:
                - Max 3 images total.
                - Each image must materially improve understanding (diagram/flow/table-like visual).
                - Insert placeholders exactly: [[IMAGE_1]], [[IMAGE_2]], [[IMAGE_3]].
                - If no images needed: md_with_placeholders must equal input and images=[].
                - Avoid decorative images; prefer technical diagrams with short labels.
                Return strictly GlobalImagePlan.
                """
            ),
            HumanMessage(
                content = f"""
                Blog type: {plan.blog_type}
                Topic: {state['topic']}
                Blog content: {blog_content}
                
                Insert placeholders + propose image prompts.
                """
            )
        ]
    )
    
    return {
        "blog_with_placeholder": image_plan.blog_with_placeholder,
        "image_specs": image_plan.images
    }

# import json
def generate_and_place_images(state: State) -> dict:
    
    # Saving state in state.json file
    # with open("state.json", "w", encoding="utf-8") as f:
    #     json.dump(state, f, indent=4, default=str)
    #
        
    plan = state["plan"]
    
    content = state.get("blog_with_placeholder", "") or state["blog_content"]
    image_specs = state.get("image_specs", []) or []
    
    blog_title = _blog_foldername(plan.blog_title)
    
    output_path = Path(f"data/{blog_title}/{blog_title}.md")
    output_path.parent.mkdir(parents = True, exist_ok = True)
            
    if not image_specs:
        output_path.write_text(content, encoding = "utf-8")
        return {"final": content}
    
    for image in image_specs:
        placeholder = image["placeholder"]
        filename = image["filename"]
        image_output_path = Path(f"data/{blog_title}/{filename}")
        
        if not image_output_path.exists():
            try:
                image_llm = get_image_model()
                image_bytes = image_llm.models.generate_content(
                    model="gemini-2.5-flash-image",
                    contents = image["prompt"],
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE"],
                        safety_settings=[
                            types.SafetySetting(
                                category="HARM_CATEGORY_DANGEROUS_CONTENT",
                                threshold="BLOCK_ONLY_HIGH",
                            )
                        ],
                    ),
                )
                image_output_path.write_bytes(image_bytes)
            except Exception as e:
                prompt_block = (
                    f"> **[IMAGE GENERATION FAILED]** {image.get('caption','')}\n>\n"
                    f"> **Alt:** {image.get('alt','')}\n>\n"
                    f"> **Prompt:** {image.get('prompt','')}\n>\n"
                    f"> **Error:** {e}\n"
                )
                content = content.replace(placeholder, prompt_block)
                continue
            
        img_md = f"![{image['alt']}](data/ {blog_title} / {filename})\n*{image['caption']}*"
        content = content.replace(placeholder, img_md)
    
    output_path.write_text(content, encoding = "utf-8")
    return {"final": content}
                