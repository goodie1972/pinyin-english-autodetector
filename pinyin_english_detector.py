#!/usr/bin/env python3
"""
拼音/英文自动识别引擎
基于规则 + 词典匹配的智能识别
"""

from english_dictionary import get_extended_english_words
from user_preference import get_learner
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class DetectionResult:
    """识别结果"""
    input_text: str
    script_type: str  # 'pinyin', 'english', 'unknown', 'mixed'
    confidence: float
    candidates: list  # 候选解析结果


class PinyinEnglishDetector:
    """
    拼音/英文识别器
    核心算法：音节切分 + 词典匹配 + 规则评分
    """

    # 拼音声母表
    INITIALS = {
        'b', 'p', 'm', 'f', 'd', 't', 'n', 'l',
        'g', 'k', 'h', 'j', 'q', 'x',
        'zh', 'ch', 'sh', 'r', 'z', 'c', 's', 'y', 'w'
    }

    # 拼音韵母表（完整）
    FINALS = {
        'a', 'o', 'e', 'i', 'u', 'v', 'ü',
        'ai', 'ei', 'ui', 'ao', 'ou', 'iu', 'ie', 've', 'er',
        'an', 'en', 'in', 'un', 'vn',
        'ang', 'eng', 'ing', 'ong',
        'ia', 'iao', 'ian', 'iang', 'iong',
        'ua', 'uo', 'uai', 'uan', 'uang', 'ong',
        'ue', 'uan', 'un'
    }

    # 整体认读音节（无需拼读）
    WHOLE_SYLLABLES = {
        'zhi', 'chi', 'shi', 'ri', 'zi', 'ci', 'si',
        'yi', 'wu', 'yu', 'ye', 'yue', 'yuan', 'yin', 'yun', 'ying'
    }

    def __init__(self, enable_learning=True):
        self.english_words = self._load_english_words()
        self.pinyin_dict = self._build_pinyin_dict()
        self.learner = get_learner() if enable_learning else None
        # 缓存
        self._cache = {}
        self._cache_max_size = 1000

    def _get_from_cache(self, text: str):
        """从缓存获取结果"""
        return self._cache.get(text)

    def _add_to_cache(self, text: str, result):
        """添加结果到缓存"""
        if len(self._cache) >= self._cache_max_size:
            # 简单LRU：清空一半缓存
            self._cache = dict(list(self._cache.items())[self._cache_max_size//2:])
        self._cache[text] = result

    def _load_english_words(self) -> set:
        """加载常用英文单词词典"""
        # 使用扩展词典（5000+词汇）
        return get_extended_english_words()

    def _build_pinyin_dict(self) -> dict:
        """构建拼音音节词典"""
        pinyin_dict = {}

        # 生成所有有效拼音组合
        for initial in self.INITIALS | {''}:
            for final in self.FINALS:
                if initial:
                    syllable = initial + final
                else:
                    syllable = final
                pinyin_dict[syllable] = True

        # 添加整体认读音节
        for s in self.WHOLE_SYLLABLES:
            pinyin_dict[s] = True

        return pinyin_dict

    def _is_valid_pinyin_syllable(self, s: str) -> bool:
        """判断是否是有效拼音音节"""
        return s in self.pinyin_dict

    def _segment_pinyin(self, text: str) -> Tuple[list, float]:
        """
        将字符串切分为拼音音节序列
        返回: (音节列表, 覆盖率)
        """
        text = text.lower()
        n = len(text)

        # 动态规划求解最优切分
        # dp[i] = (最少音节数, 切分方案)
        dp = [(float('inf'), []) for _ in range(n + 1)]
        dp[0] = (0, [])

        for i in range(n):
            if dp[i][0] == float('inf'):
                continue

            # 尝试1-6个字符的切分（拼音最长约6字符）
            for j in range(i + 1, min(i + 7, n + 1)):
                substr = text[i:j]
                if self._is_valid_pinyin_syllable(substr):
                    new_count = dp[i][0] + 1
                    if new_count < dp[j][0]:
                        dp[j] = (new_count, dp[i][1] + [substr])

        if dp[n][0] != float('inf'):
            coverage = 1.0
        else:
            # 部分匹配，计算覆盖率
            # 找到最长匹配前缀
            coverage = 0.0
            matched_prefix_len = 0
            for i in range(n, -1, -1):
                if dp[i][0] != float('inf'):
                    coverage = i / n
                    matched_prefix_len = i
                    break
            return dp[matched_prefix_len][1] if matched_prefix_len > 0 else [], coverage

        return dp[n][1], coverage

    def _calculate_pinyin_score(self, text: str) -> float:
        """计算文本是拼音的评分 (0-1)"""
        text = text.lower()

        # 规则1: 能否完整切分为拼音音节
        syllables, coverage = self._segment_pinyin(text)

        if coverage < 1.0:
            # 不能完全切分，降低分数
            return coverage * 0.5

        # 如果能完整切分为2+个音节，给予基础高分
        # 这可以修复 "jingzhang" -> jing+zhang 被低估的问题
        num_syllables = len(syllables)
        if num_syllables >= 2:
            base_score = 0.9  # 多音节拼音基础分0.9
        else:
            base_score = 1.0  # 单音节保持1.0

        # 规则2: 音节数量合理性
        avg_len = len(text) / num_syllables if num_syllables > 0 else 0

        # 平均每个音节2-4个字母比较合理
        if 1.5 <= avg_len <= 4.5:
            syllable_score = 1.0
        else:
            syllable_score = 0.8

        # 规则3: 元音密度检查（拼音必须有元音）
        vowels = set('aeiouv')
        vowel_count = sum(1 for c in text if c in vowels)
        vowel_ratio = vowel_count / len(text) if text else 0

        # 拼音元音密度通常在20%-70%（放宽范围，修复 jingzhang 问题）
        if 0.20 <= vowel_ratio <= 0.70:
            vowel_score = 1.0
        else:
            vowel_score = 0.8

        # 规则4: 连续辅音检查（拼音中不常见）
        consonants = set('bcdfghjklmnpqrstwxyz')
        max_consonant_run = 0
        current_run = 0

        for c in text:
            if c in consonants:
                current_run += 1
                max_consonant_run = max(max_consonant_run, current_run)
            else:
                current_run = 0

        # 放宽连续辅音限制（修复 jingzhang 中的 ng+zh 情况）
        if max_consonant_run <= 3:
            consonant_score = 1.0
        elif max_consonant_run == 4:
            consonant_score = 0.8
        else:
            consonant_score = 0.5

        # 综合评分（使用base_score作为基础）
        final_score = base_score * syllable_score * vowel_score * consonant_score
        return final_score

    def _calculate_english_score(self, text: str) -> float:
        """计算文本是英文的评分 (0-1)"""
        text_lower = text.lower()

        # 规则1: 是否在英文词典中
        if text_lower in self.english_words:
            return 1.0

        # 规则2: 前缀匹配（词典中以该字符串开头的词数量）
        prefix_matches = sum(1 for word in self.english_words if word.startswith(text_lower))

        # 如果有多个词以此开头，增加可能性
        if prefix_matches >= 5:
            prefix_score = 0.7
        elif prefix_matches >= 1:
            prefix_score = 0.5
        else:
            prefix_score = 0.2

        # 规则3: 英文常见n-gram模式
        common_bigrams = {'th', 'he', 'in', 'er', 'an', 're', 'on', 'at', 'en', 'nd',
                         'ti', 'es', 'or', 'te', 'of', 'ed', 'is', 'it', 'al', 'ar',
                         'st', 'to', 'nt', 'ng', 'se', 'ha', 'as', 'ou', 'io', 'le',
                         've', 'co', 'me', 'de', 'hi', 'ri', 'ro', 'ic', 'ne', 'ea',
                         'ra', 'ce', 'li', 'ch', 'll', 'be', 'ma', 'si', 'om', 'ur'}

        bigram_count = 0
        for i in range(len(text) - 1):
            if text_lower[i:i+2] in common_bigrams:
                bigram_count += 1

        bigram_ratio = bigram_count / max(len(text) - 1, 1)

        # 英文常用双字母组合占比通常在40-70%
        if bigram_ratio >= 0.3:
            bigram_score = 0.6 + (bigram_ratio - 0.3) * 0.5
        else:
            bigram_score = bigram_ratio * 2

        # 规则4: 元音密度（英文通常30-45%）
        vowels = set('aeiou')
        vowel_count = sum(1 for c in text_lower if c in vowels)
        vowel_ratio = vowel_count / len(text) if text else 0

        if 0.2 <= vowel_ratio <= 0.5:
            vowel_score = 1.0
        else:
            vowel_score = 0.7

        # 综合评分
        final_score = max(prefix_score, bigram_score * 0.7) * vowel_score
        return min(final_score, 0.9)  # 不在词典中的最高0.9

    def detect(self, text: str) -> DetectionResult:
        """
        检测输入文本是拼音还是英文

        Args:
            text: 输入字符串（小写）

        Returns:
            DetectionResult: 包含检测结果和置信度
        """
        if not text or not isinstance(text, str):
            return DetectionResult(text, 'unknown', 0.0, [])

        # 清理输入
        text = text.strip().lower()
        if not text:
            return DetectionResult(text, 'unknown', 0.0, [])

        # 检查缓存
        cached = self._get_from_cache(text)
        if cached:
            return cached

        # 纯数字判断
        if text.isdigit():
            return DetectionResult(text, 'numeric', 1.0, [])

        # 包含非字母字符，可能是mixed
        if not text.isalpha():
            return DetectionResult(text, 'mixed', 0.5, [])

        # 计算两种语言的评分
        pinyin_score = self._calculate_pinyin_score(text)
        english_score = self._calculate_english_score(text)

        # 应用用户偏好学习
        if self.learner:
            pinyin_score, english_score = self.learner.adjust_score(text, pinyin_score, english_score)

        # 归一化置信度
        total = pinyin_score + english_score
        if total > 0:
            pinyin_conf = pinyin_score / total
            english_conf = english_score / total
        else:
            pinyin_conf = english_conf = 0.5

        # 判断结果
        if pinyin_score > english_score * 1.2:  # 拼音优势明显
            script_type = 'pinyin'
            confidence = pinyin_conf
        elif english_score > pinyin_score * 1.2:  # 英文优势明显
            script_type = 'english'
            confidence = english_conf
        else:
            # 模糊地带，优先检查词典
            # 如果在英文词典中，优先选英文
            if text in self.english_words:
                script_type = 'english'
                confidence = english_conf
            elif pinyin_score >= english_score:
                script_type = 'pinyin'
                confidence = pinyin_conf * 0.8  # 降低置信度
            else:
                script_type = 'english'
                confidence = english_conf * 0.8

        # 特殊处理：2字母歧义词，优先拼音（修复 he/an/in 等问题）
        # 因为在中文输入法场景下，用户更可能输入拼音
        if len(text) == 2 and script_type == 'english' and confidence < 0.6:
            # 检查是否也是有效拼音
            if text in self.pinyin_dict:
                script_type = 'pinyin'
                confidence = 0.55  # 稍微偏向拼音

        candidates = [
            {'type': 'pinyin', 'score': round(pinyin_score, 3), 'confidence': round(pinyin_conf, 3)},
            {'type': 'english', 'score': round(english_score, 3), 'confidence': round(english_conf, 3)}
        ]

        result = DetectionResult(text, script_type, round(confidence, 3), candidates)

        # 添加到缓存
        self._add_to_cache(text, result)

        return result


# CLI接口
if __name__ == '__main__':
    import sys
    import json

    detector = PinyinEnglishDetector()

    if len(sys.argv) > 1:
        # 命令行参数模式
        text = ' '.join(sys.argv[1:])
        result = detector.detect(text)
        print(json.dumps({
            'input': result.input_text,
            'type': result.script_type,
            'confidence': result.confidence,
            'candidates': result.candidates
        }, ensure_ascii=False, indent=2))
    else:
        # 交互模式
        print("拼音/英文识别器 (输入 'quit' 退出)")
        print("-" * 40)
        while True:
            try:
                text = input("> ").strip()
                if text.lower() in ('quit', 'exit', 'q'):
                    break
                if not text:
                    continue

                result = detector.detect(text)
                print(f"  输入: {result.input_text}")
                print(f"  识别: {result.script_type} (置信度: {result.confidence})")
                print(f"  候选: 拼音={result.candidates[0]['score']}, 英文={result.candidates[1]['score']}")
                print()
            except KeyboardInterrupt:
                print("\n再见!")
                break
            except EOFError:
                break
