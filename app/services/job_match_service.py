"""岗位匹配服务 - 基于简历推荐岗位方向"""

import json
import uuid
from typing import List, Optional
from textwrap import dedent

from loguru import logger
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import config
from app.models.resume import ResumeParseResult
from app.models.job import JobMatchResult, JobRecommendation


class JobMatchService:
    """岗位匹配服务"""

    def __init__(self):
        self.model = ChatOpenAI(
            model="deepseek-chat",
            api_key=config.dashscope_api_key,
            base_url=config.dashscope_api_base or "https://api.deepseek.com/v1",
            temperature=0.7,
        )
        self.system_prompt = dedent("""
            你是一个专业的职业规划与岗位匹配助手。根据候选人简历推荐最适合的岗位方向。

            分析维度：技能匹配度、经验匹配度、发展潜力、市场需求。

            输出 JSON 格式：
            {
                "recommendations": [
                    {
                        "job_title": "岗位名称",
                        "match_score": 0.92,
                        "reason": "推荐理由",
                        "required_skills": ["技能1"],
                        "matching_skills": ["匹配技能"],
                        "missing_skills": ["缺失技能"],
                        "interview_focus": ["面试重点"],
                        "salary_range": "薪资范围（可选）",
                        "demand_level": "高/中/低（可选）"
                    }
                ],
                "analysis_summary": "整体分析总结"
            }

            推荐 3-5 个岗位，按匹配度降序排列。只返回 JSON。
        """).strip()
        logger.info("JobMatchService 初始化完成")

    async def match_jobs(
        self,
        resume: ResumeParseResult,
        target_industry: Optional[str] = None,
        preferred_roles: Optional[List[str]] = None
    ) -> Optional[JobMatchResult]:
        """基于简历匹配岗位"""
        try:
            logger.info(f"开始岗位匹配: resume_id={resume.resume_id}")
            resume_summary = self._build_resume_summary(resume)
            match_data = await self._match_with_llm(resume_summary, target_industry, preferred_roles)
            if not match_data:
                logger.error("岗位匹配 LLM 返回为空")
                return None

            match_id = f"match-{uuid.uuid4().hex[:8]}"
            recommendations = [
                JobRecommendation(
                    job_title=rec["job_title"],
                    match_score=rec["match_score"],
                    match_percentage=int(rec["match_score"] * 100),
                    reason=rec["reason"],
                    required_skills=rec["required_skills"],
                    matching_skills=rec["matching_skills"],
                    missing_skills=rec.get("missing_skills", []),
                    interview_focus=rec["interview_focus"],
                    salary_range=rec.get("salary_range"),
                    demand_level=rec.get("demand_level")
                )
                for rec in match_data["recommendations"]
            ]

            result = JobMatchResult(
                match_id=match_id,
                resume_id=resume.resume_id,
                recommendations=recommendations,
                target_industry=target_industry,
                analysis_summary=match_data.get("analysis_summary")
            )
            logger.info(f"岗位匹配成功: {len(recommendations)} 个推荐")
            return result

        except Exception as e:
            logger.error(f"岗位匹配失败: {e}")
            return None

    def _build_resume_summary(self, resume: ResumeParseResult) -> str:
        """构建简历摘要文本"""
        parts = []
        if resume.name:
            parts.append(f"姓名: {resume.name}")
        if resume.years_of_experience:
            parts.append(f"工作年限: {resume.years_of_experience} 年")
        if resume.skills:
            parts.append(f"技能: {', '.join(resume.skills)}")
        if resume.education:
            edu = ", ".join(f"{e.school} {e.degree} {e.major}" for e in resume.education)
            parts.append(f"教育: {edu}")
        if resume.work_experience:
            work = ", ".join(f"{w.company} {w.position}" for w in resume.work_experience)
            parts.append(f"工作: {work}")
        if resume.projects:
            proj = ", ".join(f"{p.name} ({p.role})" for p in resume.projects)
            parts.append(f"项目: {proj}")
        return "\n".join(parts)

    async def _match_with_llm(
        self,
        resume_summary: str,
        target_industry: Optional[str],
        preferred_roles: Optional[List[str]]
    ) -> Optional[dict]:
        """使用 LLM 进行岗位匹配"""
        try:
            user_prompt = f"简历信息：\n{resume_summary}\n"
            if target_industry:
                user_prompt += f"目标行业: {target_industry}\n"
            if preferred_roles:
                user_prompt += f"期望岗位: {', '.join(preferred_roles)}\n"
            user_prompt += "\n请推荐最适合的岗位方向。"

            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=user_prompt)
            ]
            response = await self.model.ainvoke(messages)
            response_text = response.content if hasattr(response, "content") else str(response)
            json_str = self._extract_json(response_text)
            return json.loads(json_str)
        except Exception as e:
            logger.error(f"岗位匹配 LLM 失败: {e}")
            return None

    @staticmethod
    def _extract_json(text: str) -> str:
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            return text[start:end].strip()
        if "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            return text[start:end].strip()
        return text.strip()


job_match_service = JobMatchService()
