"""LLM 客户端 - 统一接口，支持任意 OpenAI 兼容 API，设置热更新"""
from openai import AsyncOpenAI, OpenAI
from .config import get_settings
from typing import Optional, AsyncGenerator


class LLMClient:
    """异步 LLM 客户端 — 每次调用时读取最新配置，支持热更新"""

    def __init__(self, use_fast: bool = False):
        self.use_fast = use_fast
        self._client: Optional[AsyncOpenAI] = None
        self._sync_client: Optional[OpenAI] = None
        self._last_api_key = ""
        self._last_api_base = ""

    def _ensure_client(self):
        settings = get_settings()
        key = settings.llm_api_key
        base = settings.llm_api_base
        if self._client is None or key != self._last_api_key or base != self._last_api_base:
            self._client = AsyncOpenAI(api_key=key, base_url=base)
            self._sync_client = OpenAI(api_key=key, base_url=base)
            self._last_api_key = key
            self._last_api_base = base

    @property
    def model(self) -> str:
        settings = get_settings()
        return settings.llm_fast_model if self.use_fast else settings.llm_model

    @property
    def client(self):
        self._ensure_client()
        return self._client

    @property
    def sync_client(self):
        self._ensure_client()
        return self._sync_client

    async def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stop: Optional[list[str]] = None,
    ) -> str:
        settings = get_settings()
        resp = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature or settings.llm_temperature,
            top_p=settings.llm_top_p,
            max_tokens=max_tokens or settings.llm_max_tokens,
            stop=stop,
        )
        return resp.choices[0].message.content or ""

    async def chat_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        settings = get_settings()
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature or settings.llm_temperature,
            top_p=settings.llm_top_p,
            max_tokens=max_tokens or settings.llm_max_tokens,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def chat_sync(self, system_prompt: str, user_prompt: str, temperature: Optional[float] = None) -> str:
        """同步客户端，供非异步场景使用"""
        settings = get_settings()
        resp = self.sync_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature or settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
        )
        return resp.choices[0].message.content or ""


# 全局实例
main_llm = LLMClient(use_fast=False)
fast_llm = LLMClient(use_fast=True)
