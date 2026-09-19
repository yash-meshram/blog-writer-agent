from unittest.mock import Base
from pydantic import BaseModel, Field
from typing import Annotated, List, Literal, TypedDict, Optional, Tuple
import operator

class RouterDecision(BaseModel):
    needs_research: bool
    research_type: Literal["closed_book", "hybrid", "open_book"] = "closed_book"
    queries: List[str] = Field(default_factory = list)
    
class Task(BaseModel):
    id: str
    title: str
    brief: str = Field(..., description = "What to cover")
    goal: str = Field(..., description = "One sentense describing what the reader should do/understand by reading this section.")
    bullets: List[str] = Field(
        ...,
        min_length = 3,
        max_length = 5,
        description = "3-5 concrete and non-overlapping subpoints to be cover in this section."
    )
    tags: List[str] = Field(default_factory = list)
    requires_research: bool = False
    requires_citation: bool = False
    requires_code: bool = False
    
class Plan(BaseModel):
    blog_title: str
    tasks: List[Task]
    audience: str = Field(..., description = "Who this blog is for.")
    blog_type: Literal["explainer", "tutorial", "news_roundup", "comparision", "system_design"] = "explainer"
    tone: str
    constrains: List[str] = Field(default_factory = list)
    
class EvidenceItem(BaseModel):
    title: str
    url: str
    content: Optional[str] = None
    published_at: Optional[str] = None
    source: Optional[str] = None
    
class EvidencePack(BaseModel):
    evidence: List[EvidenceItem] = Field(default_factory = list)
    
class ImageSpec(BaseModel):
    placeholder: str = Field(..., description = "eg. [[Image_1]]")
    filename: str = Field(..., description = "eg. flow_diagram.png")
    alt: str
    caption: str
    prompt: str = Field(..., description = "Prompt to send to the image model.")
    size: Literal["1024x1024", "1024x1536", "1536x1024"] = "1024x1024"
    quality: Literal["low", "medium", "high"] = "medium"

class GlobalImagePlan(BaseModel):
    blog_with_placeholder: str
    images: List[ImageSpec] = Field(default_factory = list)
    
class State(TypedDict):
    topic: str
    needs_reserach: bool
    mode: str
    queries: List[str]
    evidence: List[EvidenceItem]
    plan: Optional[Plan]
    sections: Annotated[List[Tuple[int, str]], operator.add]
    blog_content: str
    blog_with_placeholder: str
    image_specs: List[ImageSpec]
    final: str
    