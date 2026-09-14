from pydantic import BaseModel, Field
from typing import Annotated, List, TypedDict
import operator

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
    
class Plan(BaseModel):
    blog_title: str
    tasks: List[Task]
    audience: str = Field(..., description = "Who this blog is for.")
    tone: str = Field(description = "writing tone (example: practical, professional, casual, etc.).")
    
class State(TypedDict):
    topic: str
    plan: Plan
    sections: Annotated[List[str], operator.add]
    final: str