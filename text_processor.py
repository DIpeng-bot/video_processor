import os
import openai
import logging
from typing import Dict, Optional

class TextProcessor:
    """文本处理类，用于优化和总结转录文本"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        
    def process_transcript(self, transcript: str) -> Dict[str, str]:
        """
        处理转录文本，生成优化后的文本和总结
        
        Args:
            transcript: 原始转录文本
            
        Returns:
            Dict包含以下字段：
            - optimized: 优化后的文本
            - summary: 文本总结
        """
        try:
            # 优化转录文本
            optimized = self._optimize_text(transcript)
            
            # 生成总结
            summary = self._generate_summary(optimized)
            
            return {
                "optimized": optimized,
                "summary": summary
            }
        except Exception as e:
            logging.error(f"处理文本时出错: {str(e)}")
            return {
                "optimized": transcript,
                "summary": "生成总结时出错"
            }
    
    def _optimize_text(self, text: str) -> str:
        """优化转录文本，修正标点符号和语法"""
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个文本优化助手，负责优化语音转录文本。请修正文本中的标点符号、语法错误，并保持文本的原意。"},
                    {"role": "user", "content": f"请优化以下转录文本，修正标点符号和语法，使其更加通顺易读：\n\n{text}"}
                ],
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logging.error(f"优化文本时出错: {str(e)}")
            return text
    
    def _generate_summary(self, text: str) -> str:
        """生成文本总结"""
        try:
            system_prompt = """你是一个专业的文本优化专家，专注于提升转录文字质量。你的主要职责是：
1. 高效文本清理：删除冗余内容，避免信息堆砌和语句重复
2. 逻辑结构优化：调整段落与信息顺序，确保逻辑清晰、表达连贯
3. 内容补充：通过分析上下文识别遗漏，补充关键信息
4. 小标题设计：添加准确、概括性强的小标题

工作流程：
1. 全面扫描：检查内容，标记冗余和不通顺的语句
2. 逻辑优化：重组段落顺序，调整句式逻辑
3. 补充完善：基于上下文分析补充必要信息
4. 设计小标题：添加简洁、有引导性的小标题
5. 最终检查：确保语言简练，逻辑完整

规则：
1. 保持原意：不改变原文核心信息
2. 语言自然：表达简洁流畅
3. 标题引导：小标题需高度概括主旨
4. 受众适配：符合目标读者的阅读习惯"""

            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"请对以下文本进行优化和总结，添加合适的小标题，使其更易阅读和理解：\n\n{text}"}
                ],
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logging.error(f"生成总结时出错: {str(e)}")
            return "生成总结时出错" 