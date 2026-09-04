"""
飞书消息格式化器模块
"""
import re
from typing import Optional, Dict, Any


class FeishuMessageFormatter:
    """飞书消息格式化器"""

    @staticmethod
    def _escape_markdown(text: str) -> str:
        """转义 Markdown 特殊字符

        Args:
            text: 原始文本

        Returns:
            str: 转义后的文本
        """
        # 转义 Markdown 特殊字符
        special_chars = r'[_*~`>|]'
        return re.sub(special_chars, r'\\\g<0>', text)

    @staticmethod
    def format_confirmation_card(task_id: str, content: str, context: Optional[Dict[str, Any]] = None) -> dict:
        """格式化确认卡片

        Args:
            task_id: 任务ID
            content: 任务内容
            context: 上下文信息

        Returns:
            dict: 卡片内容

        Raises:
            ValueError: 参数无效
        """
        if not content:
            raise ValueError('content cannot be empty')

        if not task_id:
            raise ValueError('task_id cannot be empty')

        # 构建消息内容
        escaped_content = FeishuMessageFormatter._escape_markdown(content)
        message_content = f'**任务内容**\n{escaped_content}'

        if context:
            context_text = '\n\n**上下文信息**\n'
            for key, value in context.items():
                escaped_key = FeishuMessageFormatter._escape_markdown(str(key))
                escaped_value = FeishuMessageFormatter._escape_markdown(str(value))
                context_text += f'- {escaped_key}: {escaped_value}\n'
            message_content += context_text

        card = {
            'config': {'wide_screen_mode': True},
            'header': {
                'title': {'tag': 'plain_text', 'content': '确认请求'},
                'template': 'blue'
            },
            'elements': [
                {
                    'tag': 'div',
                    'text': {
                        'tag': 'lark_md',
                        'content': message_content
                    }
                },
                {
                    'tag': 'hr'
                },
                {
                    'tag': 'note',
                    'elements': [
                        {
                            'tag': 'plain_text',
                            'content': f'任务ID: {task_id}'
                        }
                    ]
                },
                {
                    'tag': 'action',
                    'actions': [
                        {
                            'tag': 'button',
                            'text': {
                                'tag': 'plain_text',
                                'content': '确认'
                            },
                            'type': 'primary',
                            'value': {
                                'action': 'confirm',
                                'task_id': task_id
                            }
                        },
                        {
                            'tag': 'button',
                            'text': {
                                'tag': 'plain_text',
                                'content': '取消'
                            },
                            'type': 'danger',
                            'value': {
                                'action': 'cancel',
                                'task_id': task_id
                            }
                        }
                    ]
                }
            ]
        }

        return card

    @staticmethod
    def format_text_message(content: str, context: Optional[Dict[str, Any]] = None) -> str:
        """格式化文本消息

        Args:
            content: 消息内容
            context: 上下文信息

        Returns:
            str: 格式化后的文本

        Raises:
            ValueError: 参数无效
        """
        if not content:
            raise ValueError('content cannot be empty')

        if not context:
            return content

        context_text = '\n\n上下文信息：'
        for key, value in context.items():
            context_text += f'\n- {key}: {value}'

        return f'{content}{context_text}'
