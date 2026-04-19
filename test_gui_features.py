#!/usr/bin/env python3
"""
GUI新功能测试脚本
验证歧义词推荐和反馈闭环功能
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pinyin_english_detector import PinyinEnglishDetector
from feedback_handler import get_feedback_handler


class GUITestSimulator:
    """模拟GUI测试"""

    def __init__(self):
        self.detector = PinyinEnglishDetector()
        self.feedback_handler = get_feedback_handler()

    def test_ambiguous_detection(self):
        """测试歧义词检测"""
        print("=" * 60)
        print("测试1: 歧义词检测与推荐")
        print("=" * 60)

        # 歧义词（置信度0.4-0.7之间）
        ambiguous_cases = [
            'an',   # 可能拼音也可能英文
            'he',   # 可能拼音也可能英文
            'in',   # 可能拼音也可能英文
            'wo',   # 可能是拼音"我"
            'ni',   # 可能是拼音"你"
        ]

        for text in ambiguous_cases:
            result = self.detector.detect(text)
            confidence = result.confidence

            # 判断是否是歧义词
            is_ambiguous = 0.4 <= confidence < 0.7

            print(f"\n输入: '{text}'")
            print(f"  识别结果: {result.script_type}")
            print(f"  置信度: {confidence:.3f}")
            print(f"  是否歧义: {'是' if is_ambiguous else '否'}")

            if is_ambiguous and len(result.candidates) >= 2:
                other = [c for c in result.candidates if c['type'] != result.script_type][0]
                print(f"  推荐: 也可能是 {other['type']} (置信度: {other['confidence']:.3f})")
                print(f"  [GUI显示] 歧义词推荐区域: 显示纠正按钮")

    def test_feedback_loop(self):
        """测试反馈闭环"""
        print("\n" + "=" * 60)
        print("测试2: 反馈闭环")
        print("=" * 60)

        # 模拟用户纠正
        test_cases = [
            ('women', 'english', 'pinyin'),  # 被误判为英文，纠正为拼音
            ('hello', 'pinyin', 'english'),  # 被误判为拼音，纠正为英文
        ]

        for text, predicted, correct in test_cases:
            print(f"\n输入: '{text}'")

            # 检测
            result = self.detector.detect(text)
            print(f"  检测前: {result.script_type} (置信度: {result.confidence:.3f})")

            # 记录纠正
            self.feedback_handler.record_correction(text, predicted, correct)
            print(f"  [用户反馈] 纠正为: {correct}")

            # 重新检测（使用学习后的权重）
            new_result = self.detector.detect(text)
            print(f"  检测后: {new_result.script_type} (置信度: {new_result.confidence:.3f})")

        # 显示统计
        stats = self.feedback_handler.get_statistics()
        print(f"\n[反馈统计]")
        print(f"  总纠正次数: {stats['total_corrections']}")
        print(f"  涉及词汇数: {stats['unique_words_corrected']}")
        print(f"  常用词数: {stats['frequent_words']}")

    def test_high_confidence_skip(self):
        """测试高置信度跳过推荐"""
        print("\n" + "=" * 60)
        print("测试3: 高置信度跳过歧义推荐")
        print("=" * 60)

        high_confidence_cases = [
            'hello',    # 英文，置信度高
            'python',   # 英文，置信度高
            'nihao',    # 拼音，置信度较高
            'zhongguo', # 拼音，置信度较高
        ]

        for text in high_confidence_cases:
            result = self.detector.detect(text)
            confidence = result.confidence
            is_ambiguous = 0.4 <= confidence < 0.7

            print(f"\n'{text}': {result.script_type} (置信度: {confidence:.3f})")
            if not is_ambiguous:
                print(f"  [GUI显示] 歧义词推荐区域: 显示'置信度较高，不太可能是歧义词'")

    def test_quick_correct(self):
        """测试快速纠正功能"""
        print("\n" + "=" * 60)
        print("测试4: 快速纠正按钮功能")
        print("=" * 60)

        # 模拟GUI中的快速纠正
        text = 'women'
        result = self.detector.detect(text)

        print(f"\n输入: '{text}'")
        print(f"  当前识别: {result.script_type}")
        print(f"  [GUI按钮] '这是拼音' | '这是英文'")

        # 用户点击"这是拼音"
        correct_type = 'pinyin'
        self.feedback_handler.record_correction(text, result.script_type, correct_type)
        print(f"  [用户点击] '{text} 是拼音'")
        print(f"  [反馈已记录] 纠正: {result.script_type} -> {correct_type}")

        # 重新检测
        new_result = self.detector.detect(text)
        print(f"  重新检测: {new_result.script_type} (置信度: {new_result.confidence:.3f})")

    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("GUI新功能测试")
        print("=" * 60)

        self.test_ambiguous_detection()
        self.test_feedback_loop()
        self.test_high_confidence_skip()
        self.test_quick_correct()

        print("\n" + "=" * 60)
        print("测试完成")
        print("=" * 60)


if __name__ == '__main__':
    tester = GUITestSimulator()
    tester.run_all_tests()
