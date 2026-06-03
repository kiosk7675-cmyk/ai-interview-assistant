"""评分报告模型"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class QuestionReview(BaseModel):
    """单题评分回顾"""
    question_id: str = Field(..., description="题目ID")
    question: str = Field(..., description="题目内容")
    answer: str = Field(..., description="用户回答")
    score: float = Field(..., description="得分")
    max_score: float = Field(100, description="满分")
    feedback: str = Field(..., description="反馈")
    strengths: List[str] = Field(default_factory=list, description="优点")
    weaknesses: List[str] = Field(default_factory=list, description="不足")


class ScoreBreakdown(BaseModel):
    """分项评分"""
    technical_knowledge: float = Field(..., description="技术知识 0-100")
    problem_solving: float = Field(..., description="问题解决 0-100")
    communication: float = Field(..., description="沟通表达 0-100")
    depth_of_knowledge: float = Field(..., description="知识深度 0-100")


class ImprovementSuggestion(BaseModel):
    """改进建议"""
    category: str = Field(..., description="类别")
    priority: str = Field(..., description="优先级: 高/中/低")
    suggestion: str = Field(..., description="建议内容")
    resources: Optional[List[str]] = Field(None, description="学习资源")


class InterviewReport(BaseModel):
    """面试评分报告"""
    report_id: str = Field(..., description="报告ID")
    interview_id: str = Field(..., description="面试ID")
    resume_id: str = Field(..., description="简历ID")
    job_title: str = Field(..., description="目标岗位")
    overall_score: float = Field(..., description="总分 0-100")
    score_breakdown: ScoreBreakdown = Field(..., description="分项评分")
    question_reviews: List[QuestionReview] = Field(default_factory=list, description="逐题回顾")
    strengths: List[str] = Field(default_factory=list, description="优势")
    areas_for_improvement: List[str] = Field(default_factory=list, description="改进领域")
    improvement_suggestions: List[ImprovementSuggestion] = Field(default_factory=list, description="改进建议")
    report_markdown: str = Field("", description="完整 Markdown 报告")
    generated_at: datetime = Field(default_factory=datetime.now, description="生成时间")
