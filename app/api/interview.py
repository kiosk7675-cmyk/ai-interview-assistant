"""面试备考 API 路由 - 简历上传/解析/岗位匹配/面试/报告"""

import json
import uuid
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, File, HTTPException, UploadFile
from loguru import logger
from pydantic import BaseModel, Field

from app.models.resume import ResumeParseResult
from app.models.interview import QuestionType, DifficultyLevel
from app.services.resume_parser_service import resume_parser_service
from app.services.job_match_service import job_match_service
from app.services.interview_service import interview_service

router = APIRouter()

UPLOAD_DIR = Path("./uploads/resumes")
ALLOWED_EXTENSIONS = {"pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# 内存存储简历解析结果（按 resume_id）
_resumes: dict = {}


# ---- 请求体模型 ----
class ResumeParseReq(BaseModel):
    file_path: str


class JobMatchReq(BaseModel):
    resume_id: str
    target_industry: Optional[str] = None
    preferred_roles: Optional[List[str]] = None


class StartInterviewReq(BaseModel):
    resume_id: str
    job_title: str
    interview_type: str = "technical"
    difficulty: str = "medium"
    total_questions: int = 10


class SubmitAnswerReq(BaseModel):
    interview_id: str
    question_id: str
    answer: str
    time_spent: int = 0


class EndInterviewReq(BaseModel):
    interview_id: str


@router.post("/resume/upload")
async def upload_resume(file: UploadFile = File(...)):
    """上传 PDF 简历"""
    # 校验文件名
    if not file.filename:
        raise HTTPException(400, detail="文件名不能为空")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, detail="仅支持 PDF 格式")

    # 校验大小
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, detail="文件大小不能超过 10MB")

    # 保存
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = file.filename.replace(" ", "_")
    file_path = UPLOAD_DIR / safe_name
    if file_path.exists():
        file_path.unlink()
    file_path.write_bytes(content)

    return {
        "code": 200,
        "message": "success",
        "data": {
            "file_id": f"{uuid.uuid4().hex[:8]}-{safe_name}",
            "filename": file.filename,
            "file_path": str(file_path),
            "size": len(content),
        }
    }


@router.post("/resume/parse")
async def parse_resume(req: ResumeParseReq):
    """解析简历并提取结构化信息"""
    result = await resume_parser_service.parse_resume(req.file_path)
    if not result:
        raise HTTPException(500, detail="简历解析失败")
    _resumes[result.resume_id] = result
    return {"code": 200, "message": "success", "data": result.model_dump()}


@router.post("/job/match")
async def match_jobs(req: JobMatchReq):
    """基于简历推荐岗位"""
    resume = _resumes.get(req.resume_id)
    if not resume:
        raise HTTPException(404, detail="简历不存在，请先上传并解析")
    result = await job_match_service.match_jobs(resume, req.target_industry, req.preferred_roles)
    if not result:
        raise HTTPException(500, detail="岗位匹配失败")
    return {"code": 200, "message": "success", "data": result.model_dump()}


@router.post("/start")
async def start_interview(req: StartInterviewReq):
    """开始面试"""
    resume = _resumes.get(req.resume_id)
    if not resume:
        raise HTTPException(404, detail="简历不存在")

    try:
        q_type = QuestionType(req.interview_type)
    except ValueError:
        q_type = QuestionType.TECHNICAL

    try:
        diff = DifficultyLevel(req.difficulty)
    except ValueError:
        diff = DifficultyLevel.MEDIUM

    session = await interview_service.start_interview(
        resume=resume,
        job_title=req.job_title,
        interview_type=q_type,
        difficulty=diff,
        total_questions=min(max(req.total_questions, 3), 20),
    )
    if not session:
        raise HTTPException(500, detail="面试创建失败")

    first_q = session.questions[0]
    return {
        "code": 200,
        "message": "success",
        "data": {
            "interview_id": session.interview_id,
            "total_questions": session.total_questions,
            "current_question": 1,
            "question": {
                "id": first_q.question_id,
                "type": first_q.type.value,
                "category": first_q.category,
                "question": first_q.question,
                "leetcode_link": first_q.leetcode_link,
            },
            # 出题策略说明
            "question_plan": {
                "bagu": {"count": 3, "range": "1-3", "label": "八股文"},
                "scenario": {"count": 2, "range": "4-5", "label": "场景题"},
                "project": {"count": 3, "range": "6-8", "label": "项目深挖"},
                "algorithm": {"count": 2, "range": "9-10", "label": "算法题(Hot100)"},
            },
        }
    }


@router.post("/answer")
async def submit_answer(req: SubmitAnswerReq):
    """提交回答"""
    result = await interview_service.submit_answer(
        interview_id=req.interview_id,
        question_id=req.question_id,
        answer=req.answer,
        time_spent=req.time_spent,
    )
    if not result:
        raise HTTPException(400, detail="面试会话不存在或已结束，请刷新页面重新开始面试")
    if "error" in result:
        error_map = {
            "empty_answer": "回答内容不能为空，请输入答案后再提交",
            "question_mismatch": "题目不匹配，请刷新页面后重试",
        }
        raise HTTPException(400, detail=error_map.get(result["error"], "提交失败，请重试"))
    return {"code": 200, "message": "success", "data": result}


@router.post("/end")
async def end_interview(req: EndInterviewReq):
    """结束面试并生成报告"""
    report = await interview_service.generate_report(req.interview_id)
    if not report:
        raise HTTPException(500, detail="报告生成失败")
    return {"code": 200, "message": "success", "data": report.model_dump()}
