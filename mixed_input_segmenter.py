#!/usr/bin/env python3
"""
中英混合输入切分器
智能切分包含中英文混合的输入字符串
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from pinyin_english_detector import PinyinEnglishDetector


@dataclass
class Segment:
    """切分片段"""
    text: str
    segment_type: str  # 'chinese', 'english', 'pinyin', 'numeric', 'symbol', 'mixed'
    confidence: float
    start_pos: int
    end_pos: int


class MixedInputSegmenter:
    """
    中英混合输入切分器
    支持: 纯英文、纯拼音、中文、数字、符号以及它们的混合
    """

    def __init__(self, detector: Optional[PinyinEnglishDetector] = None):
        self.detector = detector or PinyinEnglishDetector()

        # 加载词典
        self.english_words = self.detector.english_words
        self.pinyin_dict = self.detector.pinyin_dict

        # 中文字符范围
        self.chinese_pattern = re.compile(r'[\u4e00-\u9fff]+')
        self.english_pattern = re.compile(r'[a-zA-Z]+')
        self.numeric_pattern = re.compile(r'\d+')
        self.symbol_pattern = re.compile(r'[^\u4e00-\u9fffa-zA-Z0-9]+')

    def segment(self, text: str) -> List[Segment]:
        """
        对输入文本进行智能切分

        Args:
            text: 输入文本（可能包含中英混合）

        Returns:
            切分后的片段列表
        """
        if not text:
            return []

        segments = []
        pos = 0

        while pos < len(text):
            char = text[pos]

            # 1. 检查中文
            if self._is_chinese(char):
                chinese_seg, end_pos = self._extract_chinese(text, pos)
                segments.append(Segment(
                    text=chinese_seg,
                    segment_type='chinese',
                    confidence=1.0,
                    start_pos=pos,
                    end_pos=end_pos
                ))
                pos = end_pos
                continue

            # 2. 检查数字
            if char.isdigit():
                num_seg, end_pos = self._extract_numeric(text, pos)
                segments.append(Segment(
                    text=num_seg,
                    segment_type='numeric',
                    confidence=1.0,
                    start_pos=pos,
                    end_pos=end_pos
                ))
                pos = end_pos
                continue

            # 3. 检查英文字母
            if char.isalpha():
                # 提取整个英文字符串
                eng_end = pos
                while eng_end < len(text) and text[eng_end].isalpha() and text[eng_end].isascii():
                    eng_end += 1
                full_eng = text[pos:eng_end]

                # 如果字符串较长(>6字符)，尝试智能切分
                if len(full_eng) > 6:
                    smart_segments = self._smart_segment_english(full_eng, pos)
                    segments.extend(smart_segments)
                    pos = eng_end
                else:
                    # 短字符串直接识别
                    segment_type, confidence = self._classify_english(full_eng)
                    segments.append(Segment(
                        text=full_eng,
                        segment_type=segment_type,
                        confidence=confidence,
                        start_pos=pos,
                        end_pos=eng_end
                    ))
                    pos = eng_end
                continue

            # 4. 其他符号
            symbol_seg, end_pos = self._extract_symbol(text, pos)
            segments.append(Segment(
                text=symbol_seg,
                segment_type='symbol',
                confidence=1.0,
                start_pos=pos,
                end_pos=end_pos
            ))
            pos = end_pos

        # 后处理：合并相邻的同类型片段
        segments = self._merge_adjacent(segments)

        return segments

    def _is_chinese(self, char: str) -> bool:
        """检查字符是否为中文字符"""
        return '\u4e00' <= char <= '\u9fff'

    def _extract_chinese(self, text: str, start: int) -> Tuple[str, int]:
        """提取连续的中文字符"""
        end = start
        while end < len(text) and self._is_chinese(text[end]):
            end += 1
        return text[start:end], end

    def _extract_numeric(self, text: str, start: int) -> Tuple[str, int]:
        """提取连续的数字"""
        end = start
        while end < len(text) and text[end].isdigit():
            end += 1
        return text[start:end], end

    def _extract_english(self, text: str, start: int) -> Tuple[str, int]:
        """提取连续的英文字母（仅ASCII），并进行智能切分"""
        # 先提取整个英文字符串
        end = start
        while end < len(text) and text[end].isalpha() and text[end].isascii():
            end += 1
        full_text = text[start:end]

        # 如果字符串较长，尝试智能切分
        if len(full_text) > 6:
            segments = self._smart_segment_english(full_text)
            if len(segments) > 1:
                # 返回智能切分后的结果，但这里只能返回一个片段
                # 所以我们将切分结果存储，供后续处理
                self._pending_segments = segments
                # 返回第一个片段
                first_seg = segments[0]
                return first_seg.text, start + len(first_seg.text)

        return full_text, end

    def _smart_segment_english(self, text: str, offset: int = 0) -> List[Segment]:
        """
        智能切分英文字符串（拼音和英文混合）
        基于词典匹配和动态规划 - 优化版本

        Args:
            text: 要切分的英文字符串
            offset: 在原始文本中的起始位置
        """
        if not text:
            return []

        n = len(text)
        text_lower = text.lower()

        # 使用直接字典查找替代函数调用
        english_words = self.english_words
        pinyin_dict = self.pinyin_dict
        detector = self.detector

        # 检查是否在英文词典中（内联）
        def is_english_word(s: str) -> bool:
            return s in english_words

        # 检查是否能完全切分为拼音音节 - 使用缓存
        def can_be_pinyin(s: str) -> bool:
            syllables, coverage = detector._segment_pinyin(s)
            return coverage == 1.0 and len(syllables) >= 1

        # 检查是否是多音节拼音
        def is_multi_syllable_pinyin(s: str) -> bool:
            syllables, coverage = detector._segment_pinyin(s)
            return coverage == 1.0 and len(syllables) >= 2

        # 检查是否是单音节拼音
        def is_pinyin_syllable(s: str) -> bool:
            return s in pinyin_dict

        def can_segment_remaining(s: str) -> bool:
            """检查剩余部分是否能有效切分（至少有一个有效词开头）"""
            if not s:
                return True
            sn = len(s)
            s_lower = s.lower()
            for length in range(1, min(11, sn + 1)):
                substr = s_lower[:length]
                if substr in english_words:
                    return True
                # 快速检查是否是拼音前缀
                syllables, coverage = detector._segment_pinyin(substr)
                if coverage == 1.0:
                    return True
            return False

        force_segment = len(text) > 6

        # 动态规划切分
        # dp[i] = (最大得分, 切分方案)
        dp = [(float('-inf'), []) for _ in range(n + 1)]
        dp[0] = (0, [])

        for i in range(n):
            if dp[i][0] == float('-inf'):
                continue

            # 尝试不同长度（从长到短，优先长词）
            for length in range(min(10, n - i), 0, -1):
                j = i + length
                substr = text_lower[i:j]
                remaining = text_lower[j:]  # 剩余部分

                seg_type = None
                confidence = 0.5
                score = 0
                is_good_match = False

                # 检查英文词典
                if is_english_word(substr):
                    seg_type = 'english'
                    confidence = 1.0
                    score = 100 + length * 10
                    is_good_match = True
                # 检查多音节拼音（如 women = wo + men）
                # 需要确保剩余部分也能有效切分
                elif is_multi_syllable_pinyin(substr):
                    if can_segment_remaining(remaining):
                        seg_type = 'pinyin'
                        confidence = 0.85
                        score = 90 + length * 9
                        is_good_match = True
                    else:
                        # 后续无法切分，跳过这个词
                        continue
                # 检查是否是有效拼音（完整拼音词）
                elif can_be_pinyin(substr):
                    seg_type = 'pinyin'
                    confidence = 0.8
                    score = 80 + length * 8
                    is_good_match = True
                # 检查是否是单音节拼音（短）
                elif length <= 6 and is_pinyin_syllable(substr):
                    seg_type = 'pinyin'
                    confidence = 0.6
                    score = 30 + length * 3

                if seg_type:
                    new_score = dp[i][0] + score
                    new_segments = dp[i][1] + [Segment(
                        text=text[i:j],
                        segment_type=seg_type,
                        confidence=confidence,
                        start_pos=offset + i,
                        end_pos=offset + j
                    )]

                    if new_score > dp[j][0]:
                        dp[j] = (new_score, new_segments)

                    # 如果找到好的长词匹配，提前结束（贪心）
                    if is_good_match and length >= 3:
                        break

        if dp[n][0] != float('-inf'):
            # 如果强制切分且找到了多片段方案，使用它
            if force_segment and len(dp[n][1]) > 1:
                return dp[n][1]
            # 否则如果找到了任何切分方案，且得分合理，使用它
            elif len(dp[n][1]) > 1:
                return dp[n][1]

        # 保底：返回整体识别
        result = self.detector.detect(text)
        return [Segment(
            text=text,
            segment_type=result.script_type,
            confidence=result.confidence,
            start_pos=offset,
            end_pos=offset + n
        )]

    def _extract_symbol(self, text: str, start: int) -> Tuple[str, int]:
        """提取连续的符号"""
        end = start
        while end < len(text) and not (text[end].isalnum() or self._is_chinese(text[end])):
            end += 1
        return text[start:end], end

    def _classify_english(self, text: str) -> Tuple[str, float]:
        """
        对英文字符串进行分类（拼音 vs 英文）

        Returns:
            (类型, 置信度)
        """
        result = self.detector.detect(text)
        return result.script_type, result.confidence

    def _merge_adjacent(self, segments: List[Segment]) -> List[Segment]:
        """合并相邻的同类型片段"""
        if not segments:
            return segments

        merged = [segments[0]]

        for seg in segments[1:]:
            last = merged[-1]

            # 检查是否可以合并
            if last.segment_type == seg.segment_type and last.end_pos == seg.start_pos:
                # 合并
                merged[-1] = Segment(
                    text=last.text + seg.text,
                    segment_type=last.segment_type,
                    confidence=(last.confidence + seg.confidence) / 2,
                    start_pos=last.start_pos,
                    end_pos=seg.end_pos
                )
            else:
                merged.append(seg)

        return merged

    def segment_with_analysis(self, text: str) -> Dict:
        """
        切分并返回详细分析结果

        Args:
            text: 输入文本

        Returns:
            包含切分结果和分析信息的字典
        """
        segments = self.segment(text)

        # 统计信息
        type_counts = {}
        for seg in segments:
            type_counts[seg.segment_type] = type_counts.get(seg.segment_type, 0) + 1

        return {
            'input': text,
            'segments': [
                {
                    'text': seg.text,
                    'type': seg.segment_type,
                    'confidence': seg.confidence,
                    'position': (seg.start_pos, seg.end_pos)
                }
                for seg in segments
            ],
            'segment_count': len(segments),
            'type_distribution': type_counts,
            'has_chinese': 'chinese' in type_counts,
            'has_english': 'english' in type_counts,
            'has_pinyin': 'pinyin' in type_counts,
            'is_mixed': len(type_counts) > 1,
            'primary_type': self._determine_primary_type_from_counts(type_counts)
        }

    def _determine_primary_type_from_counts(self, type_counts: Dict) -> str:
        """根据类型计数确定主要类型"""
        if not type_counts:
            return 'unknown'

        # 按优先级排序
        priority = ['chinese', 'pinyin', 'english', 'numeric', 'symbol']

        for t in priority:
            if t in type_counts:
                return t

        return list(type_counts.keys())[0]


class SmartInputProcessor:
    """
    智能输入处理器
    针对输入法场景优化，提供实时处理建议
    """

    def __init__(self):
        self.segmenter = MixedInputSegmenter()
        self.buffer = ""  # 输入缓冲区

    def process(self, input_text: str) -> Dict:
        """
        处理输入文本

        Args:
            input_text: 当前输入

        Returns:
            处理结果和建议
        """
        # 切分输入
        analysis = self.segmenter.segment_with_analysis(input_text)

        # 生成建议
        suggestions = self._generate_suggestions(analysis)

        return {
            'input': input_text,
            'analysis': analysis,
            'suggestions': suggestions,
            'primary_type': self._determine_primary_type(analysis),
            'should_convert': self._should_convert_to_chinese(analysis)
        }

    def _generate_suggestions(self, analysis: Dict) -> List[str]:
        """基于分析生成输入建议"""
        suggestions = []

        for seg in analysis['segments']:
            seg_type = seg['type']
            text = seg['text']

            if seg_type == 'pinyin':
                suggestions.append(f"拼音 '{text}' -> 可转换为中文")
            elif seg_type == 'english':
                suggestions.append(f"英文 '{text}' -> 保持原样")
            elif seg_type == 'chinese':
                suggestions.append(f"中文 '{text}' -> 已确定")

        return suggestions

    def _determine_primary_type(self, analysis: Dict) -> str:
        """确定输入的主要类型"""
        type_dist = analysis['type_distribution']

        if not type_dist:
            return 'unknown'

        # 按优先级排序
        priority = ['chinese', 'pinyin', 'english', 'numeric', 'symbol']

        for t in priority:
            if t in type_dist:
                return t

        return list(type_dist.keys())[0]

    def _should_convert_to_chinese(self, analysis: Dict) -> bool:
        """判断是否应该转换为中文"""
        # 如果主要是拼音，建议转换
        if analysis.get('has_pinyin') and not analysis.get('has_english'):
            return True

        # 如果有中文，不转换
        if analysis.get('has_chinese'):
            return False

        return False


# CLI 测试接口
if __name__ == '__main__':
    import sys
    import json

    segmenter = MixedInputSegmenter()

    # 测试用例
    test_cases = [
        "hello世界",  # 英文 + 中文
        "nihao123",   # 拼音 + 数字
        "test测试abc", # 英文 + 中文 + 英文
        "API接口文档", # 英文缩写 + 中文
        "Python是最好的语言",  # 英文 + 中文
        "zhongguo中国",  # 拼音 + 中文
        "version版本号v1.0",  # 英文 + 中文 + 版本号
        "JSON格式数据",  # 英文缩写 + 中文
    ]

    if len(sys.argv) > 1:
        # 命令行参数模式
        text = ' '.join(sys.argv[1:])
        result = segmenter.segment_with_analysis(text)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # 演示模式
        print("中英混合输入切分器")
        print("=" * 70)

        for text in test_cases:
            result = segmenter.segment_with_analysis(text)
            print(f"\n输入: {text}")
            print(f"切分: ", end="")
            for seg in result['segments']:
                print(f"[{seg['text']}]({seg['type']})", end=" ")
            print()
            print(f"主要类型: {result['primary_type']}")
            print(f"是否混合: {result['is_mixed']}")
            print("-" * 70)

        # 交互模式
        print("\n交互模式 (输入 'quit' 退出):")
        while True:
            try:
                text = input("> ").strip()
                if text.lower() in ('quit', 'exit', 'q'):
                    break
                if not text:
                    continue

                result = segmenter.segment_with_analysis(text)
                print(f"切分结果: ")
                for seg in result['segments']:
                    print(f"  '{seg['text']}' -> {seg['type']} (置信度: {seg['confidence']:.2f})")
                print()
            except KeyboardInterrupt:
                print("\n再见!")
                break
            except EOFError:
                break
