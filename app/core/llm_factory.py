"""LLM 工厂类

使用 LangChain ChatOpenAI 通过 OpenAI 兼容模式调用模型

支持的模型提供商（只需修改 base_url 和 api_key）：
- DeepSeek: https://api.deepseek.com/v1 (模型: deepseek-chat)
- 阿里云 DashScope: https://dashscope.aliyuncs.com/compatible-mode/v1
- OpenAI: https://api.openai.com/v1
"""

from langchain_openai import ChatOpenAI
from app.config import config
from loguru import logger


class LLMFactory:
    """LLM 工厂类 - 使用 OpenAI 兼容模式"""

    DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"

    @staticmethod
    def create_chat_model(
        model: str | None = None,
        temperature: float = 0.7,
        streaming: bool = True,
        base_url: str | None = None,
        api_key: str | None = None,
    ) -> ChatOpenAI:
        model = model or config.dashscope_model
        base_url = base_url or config.dashscope_api_base or LLMFactory.DEEPSEEK_BASE_URL
        api_key = api_key or config.dashscope_api_key

        llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            streaming=streaming,
            base_url=base_url,
            api_key=api_key,
        )

        return llm

# 全局 LLM 工厂实例
llm_factory = LLMFactory()
