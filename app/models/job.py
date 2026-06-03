"""岗位匹配结果模型"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class JobRecommendation(BaseModel):
    """岗位推荐"""
    job_title: str = Field(..., description="岗位名称")
    match_score: float = Field(..., ge=0, le=1, description="匹配度 0-1")
    match_percentage: int = Field(..., ge=0, le=100, description="匹配百分比")
    reason: str = Field(..., description="推荐理由")
    required_skills: List[str] = Field(..., description="岗位要求技能")
    matching_skills: List[str] = Field(..., description="简历中匹配的技能")
    missing_skills: List[str] = Field(default_factory=list, description="缺失技能")
    interview_focus: List[str] = Field(..., description="面试重点方向")
    salary_range: Optional[str] = Field(None, description="薪资范围")
    demand_level: Optional[str] = Field(None, description="市场需求")


class JobMatchResult(BaseModel):
    """岗位匹配结果"""
    match_id: str = Field(..., description="匹配ID")
    resume_id: str = Field(..., description="简历ID")
    recommendations: List[JobRecommendation] = Field(..., description="推荐岗位列表")
    target_industry: Optional[str] = Field(None, description="目标行业")
    analysis_summary: Optional[str] = Field(None, description="整体分析总结")
    matched_at: datetime = Field(default_factory=datetime.now, description="匹配时间")
