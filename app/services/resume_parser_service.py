"""简历解析服务 - pdfplumber 提取文字 + LLM 结构化"""

import json
import uuid
from typing import Optional
from textwrap import dedent

import pdfplumber
from loguru import logger
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import config
from app.models.resume import ResumeParseResult


class ResumeParserService:
    """简历解析服务"""

    def __init__(self):
        self.model = ChatOpenAI(
            model="deepseek-chat",
            api_key=config.dashscope_api_key,
            base_url=config.dashscope_api_base or "https://api.deepseek.com/v1",
            temperature=0.3,
        )
        self.system_prompt = dedent("""
            你是一个专业的简历解析助手。从PDF简历文本中提取结构化信息，以JSON格式返回。

            提取字段：
            1. name: 姓名
            2. email: 邮箱
            3. phone: 电话
            4. location: 所在地
            5. years_of_experience: 工作年限（数字，如 2.0）
            6. skills: 技能列表（数组）
            7. skill_categories: 技能分类（字典，如 {"后端": ["Python", "FastAPI"]}）
            8. education: 教育经历数组，每个含 school, degree, major, start_date, end_date, gpa(可选)
            9. work_experience: 工作经历数组，每个含 company, position, start_date, end_date, description, achievements(可选)
            10. projects: 项目经历数组，每个含 name, role, duration(可选), description, technologies(可选), achievements(可选)
            11. certifications: 证书列表（可选）
            12. summary: 自我评价（可选）

            注意：不存在的字段设为 null 或空数组 []，只返回 JSON 不要附带其他文本。
        """).strip()
        logger.info("ResumeParserService 初始化完成")

    async def parse_resume(self, file_path: str) -> Optional[ResumeParseResult]:
        """解析 PDF 简历"""
        try:
            logger.info(f"开始解析简历: {file_path}")
            raw_text = self._extract_text_from_pdf(file_path)
            if not raw_text:
                logger.error(f"无法提取 PDF 文本: {file_path}")
                return None

            logger.info(f"PDF 文本提取成功，长度: {len(raw_text)}")
            structured_data = await self._structure_with_llm(raw_text)
            if not structured_data:
                logger.error("LLM 结构化失败")
                return None

            resume_id = f"resume-{uuid.uuid4().hex[:8]}"
            result = ResumeParseResult(
                resume_id=resume_id,
                raw_text=raw_text[:500],
                **structured_data
            )
            logger.info(f"简历解析成功: resume_id={resume_id}, name={result.name}")
            return result

        except Exception as e:
            logger.error(f"简历解析失败: {e}")
            return None

    def _extract_text_from_pdf(self, file_path: str) -> Optional[str]:
        """使用 pdfplumber 提取 PDF 文本"""
        try:
            with pdfplumber.open(file_path) as pdf:
                pages = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        pages.append(text)
                return "\n\n".join(pages).strip() or None
        except Exception as e:
            logger.error(f"PDF 提取失败: {e}")
            return None

    async def _structure_with_llm(self, raw_text: str) -> Optional[dict]:
        """使用 LLM 将原始文本结构化"""
        try:
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=f"请解析以下简历文本：\n\n{raw_text}")
            ]
            response = await self.model.ainvoke(messages)
            response_text = response.content if hasattr(response, "content") else str(response)
            json_str = self._extract_json(response_text)
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}")
            return None
        except Exception as e:
            logger.error(f"LLM 结构化失败: {e}")
            return None

    @staticmethod
    def _extract_json(text: str) -> str:
        """从 LLM 响应中提取 JSON 字符串"""
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            return text[start:end].strip()
        if "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            return text[start:end].strip()
        return text.strip()


resume_parser_service = ResumeParserService()
