#!/usr/bin/env python3
"""
上下文感知模块
利用前文信息辅助判断当前输入
"""

from collections import deque
from typing import Optional, List, Dict


class ContextAwareDetector:
    """
    上下文感知检测器
    维护输入历史，利用上下文辅助判断
    """

    def __init__(self, base_detector, history_size: int = 5):
        """
        初始化上下文感知检测器

        Args:
            base_detector: 基础检测器实例
            history_size: 历史记录大小
        """
        self.detector = base_detector
        self.history_size = history_size
        self.history: deque = deque(maxlen=history_size)
        self.context_language: Optional[str] = None  # 当前上下文语言偏好

    def add_to_history(self, text: str, script_type: str, confidence: float):
        """
        添加识别结果到历史

        Args:
            text: 输入文本
            script_type: 识别类型
            confidence: 置信度
        """
        self.history.append({
            'text': text,
            'type': script_type,
            'confidence': confidence,
            'timestamp': __import__('time').time()
        })

        # 更新上下文语言
        self._update_context_language()

    def _update_context_language(self):
        """根据历史更新上下文语言偏好"""
        if len(self.history) < 2:
            self.context_language = None
            return

        # 统计最近输入的语言分布
        pinyin_count = sum(1 for h in self.history if h['type'] == 'pinyin')
        english_count = sum(1 for h in self.history if h['type'] == 'english')

        total = pinyin_count + english_count
        if total == 0:
            self.context_language = None
            return

        # 如果某种语言占主导，更新上下文
        pinyin_ratio = pinyin_count / total
        english_ratio = english_count / total

        if pinyin_ratio > 0.7:
            self.context_language = 'pinyin'
        elif english_ratio > 0.7:
            self.context_language = 'english'
        else:
            self.context_language = 'mixed'

    def get_context_boost(self, script_type: str) -> float:
        """
        获取上下文对某语言类型的加分

        Args:
            script_type: 语言类型

        Returns:
            加分值 (0-0.2)
        """
        if self.context_language is None:
            return 0.0

        if self.context_language == script_type:
            return 0.15  # 上下文匹配，加15%
        elif self.context_language == 'mixed':
            return 0.05  # 混合上下文，轻微加分
        else:
            return -0.05  # 不匹配，轻微减分

    def detect_with_context(self, text: str) -> dict:
        """
        使用上下文感知的检测

        Args:
            text: 输入文本

        Returns:
            包含上下文信息的检测结果
        """
        # 基础检测
        result = self.detector.detect(text)

        # 应用上下文调整
        pinyin_score = result.candidates[0]['score']
        english_score = result.candidates[1]['score']

        # 添加上下文加分
        pinyin_boost = self.get_context_boost('pinyin')
        english_boost = self.get_context_boost('english')

        adjusted_pinyin = pinyin_score * (1 + pinyin_boost)
        adjusted_english = english_score * (1 + english_boost)

        # 重新判断
        if adjusted_pinyin > adjusted_english * 1.1:
            final_type = 'pinyin'
            final_confidence = result.candidates[0]['confidence'] * (1 + pinyin_boost)
        elif adjusted_english > adjusted_pinyin * 1.1:
            final_type = 'english'
            final_confidence = result.candidates[1]['confidence'] * (1 + english_boost)
        else:
            # 仍然模糊，保持原判断但降低置信度
            final_type = result.script_type
            final_confidence = result.confidence * 0.9

        return {
            'input': text,
            'base_type': result.script_type,
            'base_confidence': result.confidence,
            'final_type': final_type,
            'final_confidence': min(final_confidence, 1.0),
            'context_language': self.context_language,
            'context_boost': {
                'pinyin': pinyin_boost,
                'english': english_boost
            },
            'history_size': len(self.history)
        }

    def get_suggestions(self, partial_input: str) -> List[str]:
        """
        根据上下文和当前输入提供建议

        Args:
            partial_input: 部分输入

        Returns:
            建议列表
        """
        suggestions = []

        # 根据上下文语言推荐
        if self.context_language == 'english' or partial_input.isalpha():
            # 从英文词典中找前缀匹配
            for word in self.detector.english_words:
                if word.startswith(partial_input.lower()) and len(word) > len(partial_input):
                    suggestions.append(word)

        # 限制建议数量
        suggestions = suggestions[:10]

        return suggestions


class SentenceContextDetector:
    """
    句子级上下文检测器
    处理整句输入，智能切分中英文
    """

    def __init__(self, base_detector):
        """
        初始化句子级检测器

        Args:
            base_detector: 基础检测器实例
        """
        self.detector = base_detector

    def detect_sentence(self, text: str) -> List[Dict]:
        """
        对整句进行分段检测

        Args:
            text: 输入句子

        Returns:
            分段结果列表
        """
        segments = []
        current_segment = {'text': '', 'type': None}

        # 简单的贪心切分
        words = self._split_into_words(text)

        for word in words:
            if not word.isalpha():
                # 非字母字符，作为独立段
                if current_segment['text']:
                    segments.append(current_segment)
                    current_segment = {'text': '', 'type': None}
                segments.append({'text': word, 'type': 'symbol'})
                continue

            result = self.detector.detect(word)

            if current_segment['type'] is None:
                # 第一个词
                current_segment['text'] = word
                current_segment['type'] = result.script_type
            elif current_segment['type'] == result.script_type:
                # 同类型，合并
                current_segment['text'] += word
            else:
                # 类型切换，保存当前段，开始新段
                segments.append(current_segment)
                current_segment = {'text': word, 'type': result.script_type}

        # 添加最后一个段
        if current_segment['text']:
            segments.append(current_segment)

        return segments

    def _split_into_words(self, text: str) -> List[str]:
        """
        将文本切分为单词

        Args:
            text: 输入文本

        Returns:
            单词列表
        """
        words = []
        current_word = ''

        for char in text:
            if char.isalpha():
                current_word += char
            else:
                if current_word:
                    words.append(current_word)
                    current_word = ''
                if not char.isspace():
                    words.append(char)

        if current_word:
            words.append(current_word)

        return words


if __name__ == '__main__':
    from pinyin_english_detector import PinyinEnglishDetector

    detector = PinyinEnglishDetector()
    context_detector = ContextAwareDetector(detector)

    # 模拟上下文
    test_inputs = [
        ('hello', 'english'),
        ('world', 'english'),
        ('nihao', None),  # 应该被上下文影响
        ('women', None),  # 应该被上下文影响
        ('python', None),
    ]

    print("上下文感知测试:")
    print("-" * 60)

    for text, expected in test_inputs:
        result = context_detector.detect_with_context(text)
        print(f"输入: {text:15} -> 基础: {result['base_type']:8} "
              f"最终: {result['final_type']:8} "
              f"上下文: {result['context_language'] or 'None':8}")
        context_detector.add_to_history(text, result['final_type'], result['final_confidence'])
