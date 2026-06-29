from pydantic import BaseModel, Field
from typing import Annotated, List, TypedDict
import operator

class Task(BaseModel):
    id: str
    title: str
    brief: str = Field(..., description = "What to cover")
    
class Plan(BaseModel):
    blog_title: str
    tasks: List[Task]
    
class State(TypedDict):
    topic: str
    plan: Plan
    sections: Annotated[List[str], operator.add]
    final: str