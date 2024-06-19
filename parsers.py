from langchain_core.pydantic_v1 import BaseModel, Field


class ResumeEvaluation(BaseModel):
    evaluation: str = Field(description="evaluation of the resume according to job description")
    strengths: str = Field(description="strength of the candidate")
    weakness: str = Field(description="weakness of the candidate")
    verdict: str = Field(description="verdict on resume according to job description to select the candidate or not")
    rating: int = Field(description="rating of the resume according to job description on scale of 1-10")
