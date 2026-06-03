"""面试状态模型"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class QuestionType(str, Enum):
    """问题类型（兼容旧值 + 新增分类）"""
    # 旧值（保留兼容）
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    COMPREHENSIVE = "comprehensive"
    # 新增：四分支出题策略
    BAGU = "bagu"           # 八股文（基础理论，纯RAG出题）
    SCENARIO = "scenario"   # 场景题（实际应用场景，RAG+岗位场景）
    PROJECT = "project"     # 项目深挖（简历项目相关，LLM自由发挥）
    ALGORITHM = "algorithm" # 手撕算法（LeetCode Hot 100）


class DifficultyLevel(str, Enum):
    """难度级别"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class InterviewQuestion(BaseModel):
    """面试题目"""
    question_id: str = Field(..., description="题目ID")
    type: QuestionType = Field(..., description="问题类型")
    question: str = Field(..., description="题目内容")
    context: Optional[str] = Field(None, description="RAG 面经上下文")
    hints: Optional[List[str]] = Field(None, description="提示")
    time_limit: Optional[int] = Field(None, description="时间限制（秒）")
    reference_answer: Optional[str] = Field(None, description="参考答案")
    knowledge_points: Optional[List[str]] = Field(None, description="考察知识点")
    # 新增字段
    category: Optional[str] = Field(None, description="题目分类标签（八股文/项目深挖/算法题）")
    leetcode_link: Optional[str] = Field(None, description="力扣题目链接（算法题专用）")
    leetcode_id: Optional[int] = Field(None, description="力扣题号（算法题专用）")


class AnswerRecord(BaseModel):
    """回答记录"""
    question_id: str = Field(..., description="题目ID")
    answer: str = Field(..., description="用户回答")
    time_spent: int = Field(..., description="用时（秒）")
    submitted_at: datetime = Field(default_factory=datetime.now, description="提交时间")
    score: Optional[float] = Field(None, description="得分")
    feedback: Optional[str] = Field(None, description="反馈")


class InterviewSession(BaseModel):
    """面试会话状态"""
    interview_id: str = Field(..., description="面试ID")
    resume_id: str = Field(..., description="简历ID")
    job_title: str = Field(..., description="目标岗位")
    interview_type: QuestionType = Field(default=QuestionType.TECHNICAL, description="面试类型")
    difficulty: DifficultyLevel = Field(default=DifficultyLevel.MEDIUM, description="难度")
    total_questions: int = Field(..., description="总题目数")
    current_index: int = Field(0, description="当前题目索引")
    questions: List[InterviewQuestion] = Field(default_factory=list, description="题目列表")
    answers: List[AnswerRecord] = Field(default_factory=list, description="回答记录")
    status: str = Field("in_progress", description="状态: in_progress / completed / abandoned")
    started_at: datetime = Field(default_factory=datetime.now, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    # 新增：出题策略内部字段
    _rag_context: Optional[str] = None
    _resume_summary: Optional[str] = None
    _used_leetcode_ids: Optional[list] = None  # 已出的算法题ID，避免重复

    class Config:
        arbitrary_types_allowed = True
