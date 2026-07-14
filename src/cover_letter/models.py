from pydantic import BaseModel , Field


class JDParsedResult(BaseModel):
    project_title:   str        = Field(description="Title or role of the project/job")
    required_skills: list[str]  = Field(description="Technologies, tools, frameworks, languages mentioned")
    scope_of_work:   list[str]  = Field(description="Expected tasks, deliverables, responsibilities")
    industry_domain: str        = Field(default="", description="Industry sector (healthcare, fintech, e-commerce, etc.)")
    pain_points:     list[str]  = Field(description="Problems or challenges the client wants solved")
    confidence:      float      = Field(ge=0.0, le=1.0, default=1.0)