"""简历解析结果模型"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class Education(BaseModel):
    """教育经历"""
    school: str = Field(..., description="学校名称")
    degree: str = Field(..., description="学位")
    major: str = Field(..., description="专业")
    start_date: Optional[str] = Field(None, description="开始时间")
    end_date: Optional[str] = Field(None, description="结束时间")
    gpa: Optional[float] = Field(None, description="GPA")


class WorkExperience(BaseModel):
    """工作经历"""
    company: str = Field(..., description="公司名称")
    position: str = Field(..., description="职位")
    start_date: Optional[str] = Field(None, description="开始时间")
    end_date: Optional[str] = Field(None, description="结束时间")
    description: Optional[str] = Field(None, description="工作描述")
    achievements: Optional[List[str]] = Field(None, description="主要成就")


class ProjectExperience(BaseModel):
    """项目经历"""
    name: str = Field(..., description="项目名称")
    role: str = Field(..., description="担任角色")
    duration: Optional[str] = Field(None, description="项目周期")
    description: str = Field(..., description="项目描述")
    technologies: Optional[List[str]] = Field(None, description="使用技术")
    achievements: Optional[List[str]] = Field(None, description="项目成就")


class ResumeParseResult(BaseModel):
    """简历解析结果"""
    resume_id: str = Field(..., description="简历ID")
    name: Optional[str] = Field(None, description="姓名")
    email: Optional[str] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, description="电话")
    location: Optional[str] = Field(None, description="所在地")
    years_of_experience: Optional[float] = Field(None, description="工作年限")
    skills: List[str] = Field(default_factory=list, description="技能列表")
    skill_categories: Optional[dict] = Field(None, description="技能分类")
    education: List[Education] = Field(default_factory=list, description="教育经历")
    work_experience: List[WorkExperience] = Field(default_factory=list, description="工作经历")
    projects: List[ProjectExperience] = Field(default_factory=list, description="项目经历")
    certifications: Optional[List[str]] = Field(None, description="证书")
    languages: Optional[List[str]] = Field(None, description="语言能力")
    summary: Optional[str] = Field(None, description="自我评价")
    raw_text: Optional[str] = Field(None, description="原始文本摘要（调试用）")
    parsed_at: datetime = Field(default_factory=datetime.now, description="解析时间")
