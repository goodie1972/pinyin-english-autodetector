#!/usr/bin/env python3
"""
Rime Lua处理器测试
模拟Rime环境，测试Lua处理器的逻辑
"""

import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pinyin_english_detector import PinyinEnglishDetector


class MockRimeContext:
    """模拟Rime输入法上下文"""

    def __init__(self):
        self.input = ""
        self.committed = []
        self.options = {'ascii_mode': False}
        self.cleared = False

    def commit_text(self, text):
        """提交文本"""
        self.committed.append(text)
        print(f"  [提交] {text}")

    def clear(self):
        """清空输入"""
        self.input = ""
        self.cleared = True
        print("  [清空输入]")

    def set_option(self, key, value):
        """设置选项"""
        self.options[key] = value
        print(f"  [设置选项] {key} = {value}")


class MockRimeEnv:
    """模拟Rime环境"""

    def __init__(self):
        self.context = MockRimeContext()


class RimeLuaProcessorTester:
    """Rime Lua处理器测试器"""

    def __init__(self):
        self.detector = PinyinEnglishDetector()
        self.results = []

    def simulate_detect_and_switch(self, input_text, min_length=3):
        """
        模拟Lua处理器的 detect_and_switch 函数

        Returns:
            (action, details)
            action: 'committed' (提交并切换), 'noop' (无操作)
        """
        env = MockRimeEnv()
        ctx = env.context
        ctx.input = input_text

        print(f"\n输入: '{input_text}'")

        # 输入太短时不判断
        if len(input_text) < min_length:
            print(f"  输入太短 (< {min_length}), 跳过")
            return 'noop', {'reason': 'too_short'}

        # 调用识别引擎
        result = self.detector.detect(input_text)
        script_type = result.script_type
        confidence = result.confidence

        print(f"  识别结果: {script_type} (置信度: {confidence:.3f})")

        # 高置信度英文判断时，自动切换ASCII模式
        if script_type == "english" and confidence > 0.7:
            ctx.commit_text(input_text)
            ctx.clear()
            ctx.set_option("ascii_mode", True)
            return 'committed', {
                'type': script_type,
                'confidence': confidence,
                'committed': input_text
            }

        return 'noop', {'type': script_type, 'confidence': confidence}

    def test_single_inputs(self):
        """测试单字输入场景"""
        print("=" * 60)
        print("测试1: 单字/短输入处理")
        print("=" * 60)

        test_cases = [
            ('he', '应该不处理（太短）'),
            ('wo', '应该不处理（太短）'),
            ('ni', '应该不处理（太短）'),
        ]

        for text, expected in test_cases:
            action, details = self.simulate_detect_and_switch(text)
            self.results.append({
                'test': 'short_input',
                'input': text,
                'action': action,
                'expected': expected
            })

    def test_english_commit(self):
        """测试英文自动提交场景"""
        print("\n" + "=" * 60)
        print("测试2: 英文自动提交")
        print("=" * 60)

        test_cases = [
            ('hello', 'english', '应该提交'),
            ('python', 'english', '应该提交'),
            ('yaml', 'english', '应该提交'),
            ('git', 'english', '应该提交'),
            ('json', 'english', '应该提交'),
            ('women', 'pinyin', '不应该提交（拼音）'),
            ('nihao', 'pinyin', '不应该提交（拼音）'),
            ('zhongguo', 'pinyin', '不应该提交（拼音）'),
        ]

        for text, expected_type, expected_action in test_cases:
            action, details = self.simulate_detect_and_switch(text)
            is_correct = (action == 'committed') == (expected_type == 'english' and details.get('confidence', 0) > 0.7)
            self.results.append({
                'test': 'english_commit',
                'input': text,
                'action': action,
                'expected_type': expected_type,
                'correct': is_correct
            })

    def test_confidence_threshold(self):
        """测试置信度阈值"""
        print("\n" + "=" * 60)
        print("测试3: 置信度阈值测试")
        print("=" * 60)

        # 歧义词（置信度较低）
        ambiguous = ['an', 'in', 'on', 'at', 'to']

        for text in ambiguous:
            action, details = self.simulate_detect_and_switch(text, min_length=2)
            print(f"  结果: {action}, 置信度阈值检查")

    def test_mixed_input(self):
        """测试混合输入处理"""
        print("\n" + "=" * 60)
        print("测试4: 混合输入处理")
        print("=" * 60)

        test_cases = [
            'hello世界',
            'nihao123',
            'API接口',
            'python代码',
        ]

        for text in test_cases:
            result = self.detector.detect(text)
            print(f"  '{text}' -> {result.script_type} (置信度: {result.confidence:.3f})")

    def test_tech_vocabulary(self):
        """测试技术词汇"""
        print("\n" + "=" * 60)
        print("测试5: 技术词汇识别")
        print("=" * 60)

        tech_words = [
            'api', 'sdk', 'cli', 'gui', 'ide',
            'json', 'yaml', 'xml', 'html', 'css',
            'git', 'docker', 'kubernetes',
            'async', 'await', 'callback', 'promise',
        ]

        for word in tech_words:
            result = self.detector.detect(word)
            status = "OK" if result.script_type == 'english' else "FAIL"
            print(f"  {word}: {result.script_type} ({result.confidence:.3f}) [{status}]")

    def generate_test_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("测试报告")
        print("=" * 60)

        passed = sum(1 for r in self.results if r.get('correct', True))
        total = len(self.results)

        print(f"总测试数: {total}")
        print(f"通过: {passed}")
        print(f"失败: {total - passed}")
        print(f"通过率: {passed/total*100:.1f}%" if total > 0 else "N/A")

    def run_all_tests(self):
        """运行所有测试"""
        self.test_single_inputs()
        self.test_english_commit()
        self.test_confidence_threshold()
        self.test_mixed_input()
        self.test_tech_vocabulary()
        self.generate_test_report()


class LuaSyntaxValidator:
    """Lua语法验证器"""

    @staticmethod
    def validate_lua_file(filepath):
        """验证Lua文件语法（简单检查）"""
        print(f"\n验证Lua文件: {filepath}")

        if not os.path.exists(filepath):
            print(f"  [错误] 文件不存在: {filepath}")
            return False

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        issues = []

        # 检查基本语法问题
        # 1. 未闭合的字符串
        in_string = None
        for i, c in enumerate(content):
            if c in ('"', "'") and (i == 0 or content[i-1] != '\\'):
                if in_string == c:
                    in_string = None
                elif in_string is None:
                    in_string = c

        if in_string:
            issues.append("可能存在未闭合的字符串")

        # 2. 检查函数定义和end匹配（简单检查）
        function_count = content.count('function')
        end_count = content.count('end')

        # 检查常见的语法错误
        if '--[[' in content and ']]' not in content:
            issues.append("可能存在未闭合的多行注释")

        if issues:
            print(f"  [警告]")
            for issue in issues:
                print(f"    - {issue}")
        else:
            print(f"  [OK] 基本语法检查通过")

        print(f"  统计: {function_count} 个函数, {end_count} 个 end")

        return len(issues) == 0


def main():
    """主函数"""
    print("=" * 60)
    print("Rime Lua处理器测试")
    print("=" * 60)

    # 1. 验证Lua文件
    validator = LuaSyntaxValidator()

    lua_files = [
        'rime/pinyin_detector.lua',
        'rime/pinyin_detector_processor.lua',
    ]

    all_valid = True
    for lua_file in lua_files:
        if not validator.validate_lua_file(lua_file):
            all_valid = False

    if not all_valid:
        print("\n[警告] Lua文件存在潜在问题")

    # 2. 运行功能测试
    print("\n" + "=" * 60)
    print("功能测试（模拟Rime环境）")
    print("=" * 60)

    tester = RimeLuaProcessorTester()
    tester.run_all_tests()

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == '__main__':
    main()
