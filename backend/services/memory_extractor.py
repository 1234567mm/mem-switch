from typing import Dict, List
from services.ollama_service import OllamaService
from config import AppConfig


EXTRACT_DIMENSIONS = {
    'preference': {
        'label': '偏好习惯',
        'prompt': '''从以下对话中提取用户的偏好习惯，包括：
- 语言风格和常用术语
- 交互偏好（如喜欢简洁/详细解释）
- 工作习惯
- 其他偏好特征

对话内容：
{content}

请以JSON格式输出提取结果：''',
        'fields': ['language_style', 'terminology', 'interaction_pattern', 'work_habits', 'other'],
    },
    'expertise': {
        'label': '专业知识',
        'prompt': '''从以下对话中提取用户的专业知识领域，包括：
- 领域方向
- 技能水平
- 使用的工具和技术
- 学习轨迹

对话内容：
{content}

请以JSON格式输出提取结果：''',
        'fields': ['domain', 'skill_level', 'tools', 'learning_path'],
    },
    'project_context': {
        'label': '项目上下文',
        'prompt': '''从以下对话中提取用户的项目上下文，包括：
- 当前进行的工作
- 关注的问题和挑战
- 尝试过的解决方案
- 项目目标和进展

对话内容：
{content}

请以JSON格式输出提取结果：''',
        'fields': ['current_work', 'focus_issues', 'solutions', 'goals', 'progress'],
    },
}


class MemoryExtractor:
    """记忆提取器 - 使用 Ollama 从对话中提取关键信息"""

    def __init__(self, ollama_service: OllamaService, config: AppConfig):
        self.ollama = ollama_service
        self.config = config

    def extract_memories(
        self,
        conversation_text: str,
        dimensions: list[str] = None,
    ) -> dict[str, dict]:
        """
        从对话中提取记忆

        Args:
            conversation_text: 对话文本内容
            dimensions: 要提取的维度列表，默认使用配置的维度

        Returns:
            dict[str, dict]: 以维度为键的提取结果
        """
        if dimensions is None:
            dimensions = self.config.get(
                "extract_dimensions",
                ["preference", "expertise", "project_context"]
            )

        results = {}

        for dim in dimensions:
            if dim not in EXTRACT_DIMENSIONS:
                continue

            dim_config = EXTRACT_DIMENSIONS[dim]
            prompt = dim_config['prompt'].format(content=conversation_text)

            try:
                response = self.ollama.generate(
                    prompt=prompt,
                    model=self.config.get("llm_model", "qwen2.5:7b"),
                )

                # 解析JSON响应
                import json
                import re

                json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
                if json_match:
                    extracted = json.loads(json_match.group())
                else:
                    extracted = {"raw_response": response}

                results[dim] = {
                    "label": dim_config['label'],
                    "data": extracted,
                    "confidence": 0.8,
                }

            except Exception as e:
                results[dim] = {
                    "label": dim_config['label'],
                    "data": {"error": str(e)},
                    "confidence": 0.0,
                }

        return results

    def summarize_conversation(self, conversation_text: str) -> str:
        """生成对话摘要"""
        prompt = f'''请简要总结以下对话的核心内容和目的（不超过100字）：

{conversation_text}

摘要：'''

        return self.ollama.generate(
            prompt=prompt,
            model=self.config.get("llm_model", "qwen2.5:7b"),
        )