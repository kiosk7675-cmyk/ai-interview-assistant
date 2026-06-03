"""面试流程管理服务 - 四分支出题策略（八股文/场景题/项目深挖/算法题）"""

import json
import random
import uuid
from typing import Dict, Any, Optional, List
from textwrap import dedent
from datetime import datetime
from pathlib import Path

from loguru import logger
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import config
from app.models.interview import (
    InterviewSession, InterviewQuestion, AnswerRecord,
    QuestionType, DifficultyLevel
)
from app.models.resume import ResumeParseResult
from app.models.report import (
    InterviewReport, QuestionReview, ScoreBreakdown,
    ImprovementSuggestion
)

# LeetCode Hot 100 题库路径（项目根目录下 data/）
_PROJECT_ROOT = Path(__file__).parent.parent.parent
LEETCODE_DB_PATH = _PROJECT_ROOT / "data" / "leetcode_hot100.json"


class InterviewService:
    """面试流程管理服务 - 四分支出题策略"""

    _sessions: Dict[str, InterviewSession] = {}

    # ---- 出题比例常量 ----
    BAGU_COUNT = 3       # 八股文（1-3题）
    SCENARIO_COUNT = 2   # 场景题（4-5题）
    PROJECT_COUNT = 3    # 项目深挖（6-8题）
    ALGORITHM_COUNT = 2  # 算法题（9-10题）

    def __init__(self):
        self.model = ChatOpenAI(
            model="deepseek-chat",
            api_key=config.dashscope_api_key,
            base_url=config.dashscope_api_base or "https://api.deepseek.com/v1",
            temperature=0.85,
        )
        # 加载 LeetCode Hot 100 题库
        self.leetcode_db = self._load_leetcode_db()

        # ---- 八股文出题 prompt（纯RAG，不允许自由发挥）----
        self.bagu_prompt = dedent("""
            你是一个专业的技术面试官，正在出「八股文」基础理论题。

            【核心规则 - 必须严格遵守】
            1. 题目必须基于「相关面经参考」中的内容出题，不允许脱离面经自由发挥
            2. 你可以从面经中提取具体的知识点，变换角度提问（如面经写了答案，你从原理角度反问）
            3. 如果面经参考中没有足够的材料，可以结合该岗位最核心的基础知识补充出题
            4. 题目应开放性强，能考察理解深度而非死记硬背
            5. 必须与「已出题目列表」中的题目完全不同，考察不同知识点
            6. 难度与指定级别一致

            输出 JSON：
            {
                "question": "题目内容",
                "hints": ["提示1"],
                "knowledge_points": ["知识点1"],
                "reference_answer": "参考答案要点"
            }
            只返回 JSON。
        """).strip()

        # ---- 项目深挖出题 prompt ----
        self.project_prompt = dedent("""
            你是一个专业的技术面试官，正在针对候选人的项目经历进行深挖出题。

            要求：
            1. 题目必须与候选人简历中的具体项目相关
            2. 考察候选人对项目技术选型、架构设计、难点解决的理解
            3. 可以问：为什么选这个技术？遇到过什么坑？如果重新设计会怎么改？
            4. 必须与「已出题目列表」中的题目完全不同
            5. 每道题应聚焦一个项目的不同方面，尽量覆盖多个项目

            输出 JSON：
            {
                "question": "题目内容",
                "hints": ["提示1"],
                "knowledge_points": ["知识点1"],
                "reference_answer": "参考答案要点"
            }
            只返回 JSON。
        """).strip()

        # ---- 场景题出题 prompt ----
        self.scenario_prompt = dedent("""
            你是一个专业的技术面试官，正在出「场景设计题」。

            【核心规则 - 必须严格遵守】
            1. 题目必须是一个实际工作中会遇到的场景，要求候选人给出解决方案
            2. 场景应结合面经参考中的知识点，但以实际应用场景包装
            3. 常见场景类型：
               - 「系统设计」：如何设计一个短链接服务/秒杀系统/消息推送系统
               - 「故障排查」：线上接口突然变慢/内存持续增长/Redis缓存雪崩如何排查
               - 「技术选型」：为什么选 MySQL 而非 MongoDB / 为什么用 Kafka 而非 RabbitMQ
               - 「架构演进」：单体→微服务如何拆分 / 数据库分库分表方案
               - 「性能优化」：接口响应从2s优化到200ms的思路
            4. 必须与「已出题目列表」中的题目完全不同
            5. 难度与指定级别一致

            输出 JSON：
            {
                "question": "题目内容（包含场景描述和具体问题）",
                "hints": ["提示1"],
                "knowledge_points": ["知识点1"],
                "reference_answer": "参考答案要点"
            }
            只返回 JSON。
        """).strip()

        # ---- 评分 prompt（不变）----
        self.evaluation_prompt = dedent("""
            你是一个专业的技术面试官，对候选人回答评分。

            评分维度：准确性40%、深度30%、完整性20%、表达10%。总分0-100。

            【核心规则 - 必须严格遵守】
            1. 你收到的 prompt 中一定包含「候选人回答：」字段，该字段内容一定不为空
            2. 如果你认为回答为空，请重新检查 prompt —— 回答就在「候选人回答：」后面
            3. feedback 中必须逐字引用候选人的至少一个回答要点
            4. 禁止在 feedback/strengths/weaknesses 中出现以下措辞：
               "未提交回答"、"回答为空"、"无法评估"、"未提供回答"、"无回答内容"

            正确示例（当候选人回答很短时）：
            {"score": 20, "feedback": "候选人仅回答了'进程'两个字，未能展开说明进程的概念、类型或管理方式，理解非常肤浅。", "strengths": [], "weaknesses": ["回答过于简略，缺乏实质性内容"]}

            输出 JSON：
            {
                "score": 85,
                "feedback": "对候选人回答的评价，必须引用回答中的具体内容",
                "strengths": ["优点1"],
                "weaknesses": ["不足1"]
            }
            只返回 JSON。
        """).strip()

        # ---- 报告 prompt（不变）----
        self.report_prompt = dedent("""
            你是一个专业的技术面试官，根据面试记录生成评分报告。

            【核心规则 - 必须严格遵守】
            1. 每位候选人的回答都在「回答:」字段中，内容一定不为空
            2. 逐题回顾时，必须引用候选人的实际回答要点进行分析
            3. 禁止在报告中出现以下措辞：
               "回答为空"、"未提交回答"、"疑为系统异常"、"无法评估"、"未提供回答"
            4. 如果某题标记为「回答: [未回答]」，在逐题回顾中直接省略该题即可

            输出 JSON：
            {
                "overall_score": 82,
                "score_breakdown": {
                    "technical_knowledge": 85,
                    "problem_solving": 80,
                    "communication": 78,
                    "depth_of_knowledge": 83
                },
                "strengths": ["优势1"],
                "areas_for_improvement": ["改进点1"],
                "improvement_suggestions": [
                    {"category": "技术知识", "priority": "高", "suggestion": "建议内容", "resources": ["资源1"]}
                ],
                "report_markdown": "完整的Markdown格式报告（包含总分、分项评分、逐题回顾、优势分析、改进建议）"
            }
            只返回 JSON。report_markdown 应为格式良好的 Markdown。
        """).strip()

        logger.info(f"InterviewService 初始化完成，LeetCode 题库加载 {len(self.leetcode_db)} 题")

    # ========================================================
    # 公开接口
    # ========================================================

    async def start_interview(
        self,
        resume: ResumeParseResult,
        job_title: str,
        interview_type: QuestionType = QuestionType.TECHNICAL,
        difficulty: DifficultyLevel = DifficultyLevel.MEDIUM,
        total_questions: int = 10
    ) -> Optional[InterviewSession]:
        """开始面试：RAG 检索面经 + 只生成第一道题（快速响应）"""
        try:
            logger.info(f"开始面试: job={job_title}, type={interview_type}")

            # 从 ChromaDB 检索相关面经
            rag_context = await self._retrieve_context(job_title)

            # 构建简历摘要
            resume_summary = self._build_resume_summary(resume)

            # 生成第一道题（八股文）
            first_question = await self._generate_bagu_question(
                resume_summary, job_title, difficulty, rag_context,
                question_number=1, previous_questions=[]
            )
            if not first_question:
                logger.error("第一题生成失败")
                return None

            interview_id = f"interview-{uuid.uuid4().hex[:8]}"
            session = InterviewSession(
                interview_id=interview_id,
                resume_id=resume.resume_id,
                job_title=job_title,
                interview_type=interview_type,
                difficulty=difficulty,
                total_questions=total_questions,
                questions=[first_question],
            )
            # 保存内部状态
            session._rag_context = rag_context
            session._resume_summary = resume_summary
            session._used_leetcode_ids = []
            self._sessions[interview_id] = session
            logger.info(f"面试创建成功: {interview_id}, 第1题(八股文)已生成")
            return session

        except Exception as e:
            logger.error(f"开始面试失败: {e}")
            return None

    async def submit_answer(
        self, interview_id: str, question_id: str,
        answer: str, time_spent: int = 0
    ) -> Optional[Dict[str, Any]]:
        """提交回答并评分，同时生成下一题"""
        try:
            session = self._sessions.get(interview_id)
            if not session:
                logger.warning(f"提交失败: 面试会话 {interview_id} 不存在（服务可能已重启）")
                return None
            if session.status != "in_progress":
                logger.warning(f"提交失败: 面试 {interview_id} 状态为 {session.status}，非 in_progress")
                return None

            # 检测跳过标记
            is_skipped = answer.strip() == "[SKIP]"
            if is_skipped:
                answer = "[未回答]"

            if not answer or not answer.strip():
                logger.warning("提交失败: 回答内容为空")
                return {"error": "empty_answer"}

            logger.info(f"收到回答: interview_id={interview_id}, q={question_id}, "
                        f"answer_len={len(answer)}, skipped={is_skipped}")

            current_q = session.questions[session.current_index]
            if current_q.question_id != question_id:
                logger.warning(f"提交失败: question_id={question_id} 不匹配当前题目 {current_q.question_id}")
                return {"error": "question_mismatch"}

            # 评分：跳过直接0分，不调LLM
            if is_skipped:
                evaluation = {
                    "score": 0,
                    "feedback": "该题已跳过，未作答。",
                    "strengths": [],
                    "weaknesses": ["跳过未作答"],
                }
                logger.info(f"题目已跳过，直接0分: {question_id}")
            else:
                evaluation = await self._evaluate_answer(current_q, answer)
                if not evaluation:
                    evaluation = {"score": 0, "feedback": "评分服务暂时不可用，请继续下一题", "strengths": [], "weaknesses": []}

            record = AnswerRecord(
                question_id=question_id,
                answer=answer,
                time_spent=time_spent,
                score=evaluation.get("score", 0),
                feedback=evaluation.get("feedback", ""),
            )
            session.answers.append(record)

            result: Dict[str, Any] = {
                "evaluation": {
                    "score": evaluation.get("score", 0),
                    "feedback": evaluation.get("feedback", "评价生成异常"),
                    "strengths": evaluation.get("strengths", []),
                    "weaknesses": evaluation.get("weaknesses", []),
                }
            }

            if session.current_index < session.total_questions - 1:
                session.current_index += 1
                next_num = session.current_index + 1
                logger.info(f"正在生成第 {next_num} 题...")

                # 根据题号决定出题类型
                next_q = await self._generate_next_question(
                    session, next_num
                )
                if next_q:
                    session.questions.append(next_q)
                    result["next_question"] = {
                        "id": next_q.question_id,
                        "type": next_q.type.value,
                        "category": next_q.category,
                        "question": next_q.question,
                        "leetcode_link": next_q.leetcode_link,
                    }
                else:
                    fallback = InterviewQuestion(
                        question_id=f"q-{uuid.uuid4().hex[:6]}",
                        type=QuestionType.TECHNICAL,
                        question="请介绍一下你对上一题相关技术的理解。",
                        hints=[],
                        knowledge_points=[],
                        reference_answer="根据候选人回答综合评价。",
                        category="技术题",
                    )
                    session.questions.append(fallback)
                    result["next_question"] = {
                        "id": fallback.question_id,
                        "type": fallback.type.value,
                        "category": fallback.category,
                        "question": fallback.question,
                        "leetcode_link": None,
                    }
                result["progress"] = {
                    "current": session.current_index + 1,
                    "total": session.total_questions,
                }
            else:
                session.status = "completed"
                session.completed_at = datetime.now()
                result["interview_completed"] = True

            return result

        except Exception as e:
            logger.error(f"提交回答失败: {e}")
            return None

    async def generate_report(self, interview_id: str) -> Optional[InterviewReport]:
        """生成面试报告"""
        try:
            session = self._sessions.get(interview_id)
            if not session or session.status != "completed":
                return None

            context = self._build_report_context(session)
            data = await self._generate_report_llm(context)
            if not data:
                return None

            question_reviews = []
            for i, rec in enumerate(session.answers):
                q = session.questions[i]
                question_reviews.append(QuestionReview(
                    question_id=q.question_id,
                    question=q.question,
                    answer=rec.answer,
                    score=rec.score or 0,
                    feedback=rec.feedback or "",
                ))

            breakdown_data = data.get("score_breakdown", {})
            report_id = f"report-{uuid.uuid4().hex[:8]}"
            report = InterviewReport(
                report_id=report_id,
                interview_id=interview_id,
                resume_id=session.resume_id,
                job_title=session.job_title,
                overall_score=data.get("overall_score", 0),
                score_breakdown=ScoreBreakdown(
                    technical_knowledge=breakdown_data.get("technical_knowledge", 0),
                    problem_solving=breakdown_data.get("problem_solving", 0),
                    communication=breakdown_data.get("communication", 0),
                    depth_of_knowledge=breakdown_data.get("depth_of_knowledge", 0),
                ),
                question_reviews=question_reviews,
                strengths=data.get("strengths", []),
                areas_for_improvement=data.get("areas_for_improvement", []),
                improvement_suggestions=[
                    ImprovementSuggestion(**s) for s in data.get("improvement_suggestions", [])
                ],
                report_markdown=data.get("report_markdown", ""),
            )
            logger.info(f"报告生成成功: {report_id}")
            return report

        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            return None

    def get_session(self, interview_id: str) -> Optional[InterviewSession]:
        return self._sessions.get(interview_id)

    # ========================================================
    # 四分支出题策略
    # ========================================================

    def _get_question_type_by_number(self, question_number: int) -> QuestionType:
        """根据题号决定出题类型：1-3八股文, 4-5场景题, 6-8项目深挖, 9-10算法题"""
        if question_number <= self.BAGU_COUNT:
            return QuestionType.BAGU
        elif question_number <= self.BAGU_COUNT + self.SCENARIO_COUNT:
            return QuestionType.SCENARIO
        elif question_number <= self.BAGU_COUNT + self.SCENARIO_COUNT + self.PROJECT_COUNT:
            return QuestionType.PROJECT
        else:
            return QuestionType.ALGORITHM

    async def _generate_next_question(
        self, session: InterviewSession, question_number: int
    ) -> Optional[InterviewQuestion]:
        """根据题号路由到不同的出题策略"""
        q_type = self._get_question_type_by_number(question_number)
        logger.info(f"第{question_number}题 类型={q_type.value}")

        if q_type == QuestionType.BAGU:
            return await self._generate_bagu_question(
                session._resume_summary,
                session.job_title,
                session.difficulty,
                session._rag_context,
                question_number,
                session.questions,
            )
        elif q_type == QuestionType.SCENARIO:
            return await self._generate_scenario_question(
                session._resume_summary,
                session.job_title,
                session.difficulty,
                session._rag_context,
                question_number,
                session.questions,
            )
        elif q_type == QuestionType.PROJECT:
            return await self._generate_project_question(
                session._resume_summary,
                session.job_title,
                session.difficulty,
                session._rag_context,
                question_number,
                session.questions,
            )
        else:
            return self._generate_algorithm_question(
                session.job_title,
                session.difficulty,
                session._used_leetcode_ids,
            )

    # ---- 八股文出题 ----
    async def _generate_bagu_question(
        self, resume_summary: str, job_title: str,
        difficulty: DifficultyLevel, rag_context: str,
        question_number: int, previous_questions: list
    ) -> Optional[InterviewQuestion]:
        """LLM 生成八股文基础理论题"""
        try:
            previous = previous_questions or []
            prev_list = "\n".join(f"- {q.question[:60]}..." for q in previous) if previous else "（暂无）"

            user_prompt = f"""
简历摘要：{resume_summary}
目标岗位：{job_title}
难度：{difficulty.value}
当前是第 {question_number} 题（八股文基础理论题）。

【已出题目列表 - 必须避开这些知识点出题】
{prev_list}

【相关面经参考 - 必须基于以下内容出题，不允许脱离面经自由发挥】
{rag_context or "（暂无面经参考，请结合该岗位最核心的基础知识出题）"}

请只生成 1 道八股文基础理论题，要求：
- 必须基于上方面经参考内容出题，从面经中提取知识点变换角度提问
- 如果面经参考内容丰富，优先考察面经中的重点知识点
- 如果面经参考较少，可以结合该岗位最核心的基础知识补充
- 题目开放性强，能考察理解深度而非死记硬背
- 必须与已出题目完全不同
"""
            response = await self.model.ainvoke([
                SystemMessage(content=self.bagu_prompt),
                HumanMessage(content=user_prompt),
            ])
            text = response.content if hasattr(response, "content") else str(response)
            q = json.loads(self._extract_json(text))

            # 兼容：如果返回的是 {"questions": [...]} 格式
            if "questions" in q and len(q["questions"]) > 0:
                q = q["questions"][0]

            return InterviewQuestion(
                question_id=f"q-{uuid.uuid4().hex[:6]}",
                type=QuestionType.BAGU,
                question=q["question"],
                hints=q.get("hints", []),
                knowledge_points=q.get("knowledge_points", []),
                reference_answer=q.get("reference_answer", ""),
                category="八股文",
            )
        except Exception as e:
            logger.error(f"生成八股文题失败: {e}")
            return None

    # ---- 场景题出题 ----
    async def _generate_scenario_question(
        self, resume_summary: str, job_title: str,
        difficulty: DifficultyLevel, rag_context: str,
        question_number: int, previous_questions: list
    ) -> Optional[InterviewQuestion]:
        """LLM 生成场景设计题"""
        try:
            previous = previous_questions or []
            prev_list = "\n".join(f"- {q.question[:60]}..." for q in previous) if previous else "（暂无）"

            user_prompt = f"""
简历摘要：{resume_summary}
目标岗位：{job_title}
难度：{difficulty.value}
当前是第 {question_number} 题（场景设计题）。

【已出题目列表 - 必须避开这些知识点出题】
{prev_list}

【相关面经参考 - 场景题应结合面经中的知识点来设计】
{rag_context or "（暂无面经参考，请结合该岗位常见实际场景出题）"}

请只生成 1 道场景设计题，要求：
- 必须是一个真实工作中会遇到的场景，要求候选人给出解决方案
- 场景类型可以是：系统设计、故障排查、技术选型、架构演进、性能优化等
- 优先结合面经参考中的知识点来设计场景
- 题目应描述具体场景和需要解决的问题
- 必须与已出题目完全不同
"""
            response = await self.model.ainvoke([
                SystemMessage(content=self.scenario_prompt),
                HumanMessage(content=user_prompt),
            ])
            text = response.content if hasattr(response, "content") else str(response)
            q = json.loads(self._extract_json(text))

            if "questions" in q and len(q["questions"]) > 0:
                q = q["questions"][0]

            return InterviewQuestion(
                question_id=f"q-{uuid.uuid4().hex[:6]}",
                type=QuestionType.SCENARIO,
                question=q["question"],
                hints=q.get("hints", []),
                knowledge_points=q.get("knowledge_points", []),
                reference_answer=q.get("reference_answer", ""),
                category="场景题",
            )
        except Exception as e:
            logger.error(f"生成场景题失败: {e}")
            return None

    # ---- 项目深挖出题 ----
    async def _generate_project_question(
        self, resume_summary: str, job_title: str,
        difficulty: DifficultyLevel, rag_context: str,
        question_number: int, previous_questions: list
    ) -> Optional[InterviewQuestion]:
        """LLM 生成项目深挖题"""
        try:
            previous = previous_questions or []
            prev_list = "\n".join(f"- {q.question[:60]}..." for q in previous) if previous else "（暂无）"

            user_prompt = f"""
简历摘要：{resume_summary}
目标岗位：{job_title}
难度：{difficulty.value}
当前是第 {question_number} 题（项目深挖题）。

【已出题目列表 - 必须避开这些知识点出题】
{prev_list}

相关面经参考：
{rag_context or "（暂无）"}

请只生成 1 道项目深挖题，要求：
- 必须与候选人简历中的具体项目经历相关
- 考察项目的技术选型、架构设计、难点解决、性能优化等方面
- 可以问：为什么选这个技术？遇到过什么坑？如何解决的？如果重新设计会怎么改？
- 必须与已出题目完全不同
- 尽量覆盖不同项目，避免反复追问同一项目同一方面
"""
            response = await self.model.ainvoke([
                SystemMessage(content=self.project_prompt),
                HumanMessage(content=user_prompt),
            ])
            text = response.content if hasattr(response, "content") else str(response)
            q = json.loads(self._extract_json(text))

            if "questions" in q and len(q["questions"]) > 0:
                q = q["questions"][0]

            return InterviewQuestion(
                question_id=f"q-{uuid.uuid4().hex[:6]}",
                type=QuestionType.PROJECT,
                question=q["question"],
                hints=q.get("hints", []),
                knowledge_points=q.get("knowledge_points", []),
                reference_answer=q.get("reference_answer", ""),
                category="项目深挖",
            )
        except Exception as e:
            logger.error(f"生成项目深挖题失败: {e}")
            return None

    # ---- 算法题出题（从 Hot 100 题库随机抽取）----
    def _generate_algorithm_question(
        self, job_title: str,
        difficulty: DifficultyLevel,
        used_leetcode_ids: Optional[list] = None,
    ) -> Optional[InterviewQuestion]:
        """从 LeetCode Hot 100 题库中随机抽取算法题"""
        try:
            used_ids = set(used_leetcode_ids or [])
            # 按难度筛选
            diff_map = {
                DifficultyLevel.EASY: ["easy"],
                DifficultyLevel.MEDIUM: ["medium", "easy"],
                DifficultyLevel.HARD: ["hard", "medium"],
            }
            allowed_diff = diff_map.get(difficulty, ["medium", "easy"])

            candidates = [
                p for p in self.leetcode_db
                if p["difficulty"] in allowed_diff and p["id"] not in used_ids
            ]

            if not candidates:
                # 降级：不限难度
                candidates = [p for p in self.leetcode_db if p["id"] not in used_ids]

            if not candidates:
                logger.warning("LeetCode 题库已用尽，回退到通用算法题")
                return InterviewQuestion(
                    question_id=f"q-{uuid.uuid4().hex[:6]}",
                    type=QuestionType.ALGORITHM,
                    question="请手写一个快速排序算法，并分析其时间和空间复杂度。",
                    hints=["考虑基准元素选择", "注意递归终止条件"],
                    knowledge_points=["排序算法", "分治"],
                    reference_answer="快速排序：选基准、分区、递归。平均O(nlogn)，最坏O(n^2)，空间O(logn)。",
                    category="算法题",
                    leetcode_link=None,
                )

            # 随机选一道
            problem = random.choice(candidates)
            used_ids.add(problem["id"])
            if used_leetcode_ids is not None:
                used_leetcode_ids.append(problem["id"])

            question_text = (
                f"【手撕算法】{problem['title_cn']}（LeetCode #{problem['id']}）\n\n"
                f"{problem['description']}\n\n"
                f"请给出你的解题思路和代码实现。"
            )

            return InterviewQuestion(
                question_id=f"q-{uuid.uuid4().hex[:6]}",
                type=QuestionType.ALGORITHM,
                question=question_text,
                hints=[problem["solution_hint"]],
                knowledge_points=problem["tags"],
                reference_answer=problem["solution_hint"],
                category="算法题",
                leetcode_link=problem["link"],
                leetcode_id=problem["id"],
            )
        except Exception as e:
            logger.error(f"生成算法题失败: {e}")
            return None

    # ========================================================
    # 内部方法
    # ========================================================

    def _load_leetcode_db(self) -> List[dict]:
        """加载 LeetCode Hot 100 题库"""
        try:
            if LEETCODE_DB_PATH.exists():
                with open(LEETCODE_DB_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                logger.warning(f"LeetCode 题库文件不存在: {LEETCODE_DB_PATH}")
                return []
        except Exception as e:
            logger.error(f"加载 LeetCode 题库失败: {e}")
            return []

    async def _retrieve_context(self, job_title: str, n_results: int = 8) -> str:
        """从 ChromaDB RAG 检索相关面经"""
        try:
            from app.core.chroma_client import chroma_manager
            collection = chroma_manager.get_collection()
            from app.services.vector_embedding_service import vector_embedding_service
            query_embedding = vector_embedding_service.embed_query(f"{job_title} 技术面经 面试题 八股文")
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["documents"],
            )
            if not results or not results["documents"] or not results["documents"][0]:
                return ""
            return "\n\n".join(
                f"【面经{i+1}】{doc}" for i, doc in enumerate(results["documents"][0])
            )
        except Exception as e:
            logger.error(f"RAG 检索失败: {e}")
            return ""

    async def _evaluate_answer(self, question: InterviewQuestion, answer: str) -> Optional[dict]:
        """LLM 评分（带幻觉检测 + 自动重试）"""
        FORBIDDEN_PHRASES = ["回答为空", "未提交回答", "无法评估", "未提供回答", "无回答内容", "没有回答"]

        user_prompt = f"""
【题目】{question.question}

【参考答案要点】{question.reference_answer or "无"}

【候选人回答】
{answer}
（上方为候选人的完整回答，内容一定不为空，请据此评分）

请严格按照 JSON 格式输出评分结果。"""

        logger.info(f"LLM评分请求: answer_len={len(answer)}, prompt_len={len(user_prompt)}")

        for attempt in range(2):
            try:
                response = await self.model.ainvoke([
                    SystemMessage(content=self.evaluation_prompt),
                    HumanMessage(content=user_prompt),
                ])
                text = response.content if hasattr(response, "content") else str(response)
                raw = json.loads(self._extract_json(text))

                safe = {
                    "score": int(raw.get("score", 0)),
                    "feedback": str(raw.get("feedback", raw.get("comment", "评价生成异常"))),
                    "strengths": [str(s) for s in raw.get("strengths", [])],
                    "weaknesses": [str(w) for w in raw.get("weaknesses", raw.get("areas_for_improvement", []))],
                }
                safe["score"] = max(0, min(100, safe["score"]))

                combined = safe["feedback"] + " ".join(safe["strengths"]) + " ".join(safe["weaknesses"])
                if any(phrase in combined for phrase in FORBIDDEN_PHRASES):
                    logger.warning(f"评分幻觉检测命中 (attempt {attempt+1}): feedback 含违禁词，将重试")
                    if attempt == 0:
                        user_prompt += "\n\n【再次强调】候选人的回答就在上方「候选人回答」标签内，绝对不为空。请务必引用其内容来评分，不要再声称回答为空。"
                        continue
                    else:
                        logger.warning("评分幻觉重试仍失败，强制覆盖 feedback")
                        safe["feedback"] = f"候选人回答了 {len(answer)} 个字符，但评分模型未能正确分析。建议人工复核。"
                        safe["score"] = max(0, min(50, safe["score"]))

                return safe
            except Exception as e:
                logger.error(f"评分失败 (attempt {attempt+1}): {e}")
                if attempt == 1:
                    return None
        return None

    async def _generate_report_llm(self, context: str) -> Optional[dict]:
        """LLM 生成报告（带幻觉检测）"""
        FORBIDDEN = ["回答为空", "未提交回答", "疑为系统异常", "无法评估", "未提供回答"]
        try:
            response = await self.model.ainvoke([
                SystemMessage(content=self.report_prompt),
                HumanMessage(content=context),
            ])
            text = response.content if hasattr(response, "content") else str(response)
            data = json.loads(self._extract_json(text))

            markdown = data.get("report_markdown", "")
            for phrase in FORBIDDEN:
                if phrase in markdown:
                    logger.warning(f"报告幻觉检测: report_markdown 含违禁词「{phrase}」，已清理")
                    markdown = markdown.replace(phrase, "[内容待补充]")
            data["report_markdown"] = markdown

            return data
        except Exception as e:
            logger.error(f"报告 LLM 失败: {e}")
            return None

    def _build_resume_summary(self, resume: ResumeParseResult) -> str:
        parts = []
        if resume.name:
            parts.append(f"姓名: {resume.name}")
        if resume.skills:
            parts.append(f"技能: {', '.join(resume.skills)}")
        if resume.education:
            parts.append(f"教育: {', '.join(f'{e.school} {e.major}' for e in resume.education)}")
        if resume.projects:
            project_details = []
            for p in resume.projects:
                detail = f"{p.name}（{p.role}）"
                if p.technologies:
                    detail += f" - 技术栈: {', '.join(p.technologies)}"
                if p.description:
                    detail += f" - {p.description[:100]}"
                project_details.append(detail)
            parts.append(f"项目经历:\n" + "\n".join(f"  - {d}" for d in project_details))
        return "\n".join(parts)

    def _build_report_context(self, session: InterviewSession) -> str:
        parts = [f"目标岗位: {session.job_title}", f"面试难度: {session.difficulty.value}"]
        for i, q in enumerate(session.questions):
            category_label = f" [{q.category}]" if q.category else ""
            if i < len(session.answers):
                rec = session.answers[i]
                parts.append(f"\n--- 第{i+1}题{category_label} ---\n题目: {q.question}\n回答: {rec.answer}\n得分: {rec.score}")
            else:
                parts.append(f"\n--- 第{i+1}题{category_label} ---\n题目: {q.question}\n回答: [未回答]\n得分: 0")
        return "\n".join(parts)

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


interview_service = InterviewService()
