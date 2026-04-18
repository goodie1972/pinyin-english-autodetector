#!/usr/bin/env python3
"""
拼音/英文识别器测试套件
"""

import sys
sys.path.insert(0, '.')

from pinyin_english_detector import PinyinEnglishDetector


def run_tests():
    """运行测试用例"""
    detector = PinyinEnglishDetector()

    # 测试用例: (输入, 期望类型)
    test_cases = [
        # 纯拼音测试
        ('nihao', 'pinyin'),
        ('wo', 'pinyin'),
        ('women', 'pinyin'),
        ('zhongguo', 'pinyin'),
        ('beijing', 'pinyin'),
        ('shanghai', 'pinyin'),
        ('xuexi', 'pinyin'),
        ('gongzuo', 'pinyin'),
        ('shenghuo', 'pinyin'),
        ('aiqing', 'pinyin'),
        ('pengyou', 'pinyin'),
        ('jia', 'pinyin'),
        ('jiaoshi', 'pinyin'),
        ('xuesheng', 'pinyin'),
        ('laoshi', 'pinyin'),
        ('daxue', 'pinyin'),
        ('zhongxue', 'pinyin'),
        ('xiaoxue', 'pinyin'),
        ('yiyuan', 'pinyin'),
        ('yisheng', 'pinyin'),
        ('bingren', 'pinyin'),
        ('yaoshi', 'pinyin'),
        ('chi', 'pinyin'),
        ('he', 'pinyin'),
        ('shuijiao', 'pinyin'),
        ('shangban', 'pinyin'),
        ('xiaban', 'pinyin'),
        ('huijia', 'pinyin'),
        ('zuofan', 'pinyin'),
        ('chifan', 'pinyin'),
        ('shuijiao', 'pinyin'),
        ('qichuang', 'pinyin'),
        ('shangxue', 'pinyin'),
        ('fangxue', 'pinyin'),
        ('zuoye', 'pinyin'),
        ('kaoshi', 'pinyin'),
        ('chengji', 'pinyin'),
        ('fenshu', 'pinyin'),
        ('gaoxing', 'pinyin'),
        ('nanguo', 'pinyin'),
        ('shangxin', 'pinyin'),
        ('kaixin', 'pinyin'),
        ('shengqi', 'pinyin'),
        ('haipa', 'pinyin'),
        ('jingzhang', 'pinyin'),
        ('fangxin', 'pinyin'),
        ('dandan', 'pinyin'),
        ('zhongyao', 'pinyin'),
        ('bixu', 'pinyin'),
        ('yiding', 'pinyin'),
        ('keneng', 'pinyin'),

        # 纯英文测试
        ('hello', 'english'),
        ('world', 'english'),
        ('python', 'english'),
        ('computer', 'english'),
        ('internet', 'english'),
        ('software', 'english'),
        ('development', 'english'),
        ('programming', 'english'),
        ('algorithm', 'english'),
        ('database', 'english'),
        ('network', 'english'),
        ('system', 'english'),
        ('application', 'english'),
        ('interface', 'english'),
        ('function', 'english'),
        ('variable', 'english'),
        ('framework', 'english'),
        ('library', 'english'),
        ('module', 'english'),
        ('package', 'english'),
        ('server', 'english'),
        ('client', 'english'),
        ('browser', 'english'),
        ('website', 'english'),
        ('webpage', 'english'),
        ('download', 'english'),
        ('upload', 'english'),
        ('install', 'english'),
        ('update', 'english'),
        ('upgrade', 'english'),
        ('version', 'english'),
        ('config', 'english'),
        ('setting', 'english'),
        ('option', 'english'),
        ('feature', 'english'),
        ('support', 'english'),
        ('service', 'english'),
        ('product', 'english'),
        ('project', 'english'),
        ('manager', 'english'),
        ('designer', 'english'),
        ('developer', 'english'),
        ('engineer', 'english'),
        ('architect', 'english'),
        ('analyst', 'english'),
        ('consultant', 'english'),
        ('director', 'english'),
        ('president', 'english'),
        ('customer', 'english'),
        ('company', 'english'),
        ('business', 'english'),

        # 歧义/模糊测试（这些可能误判）
        ('an', 'ambiguous'),  # 既可以是拼音"安"，也可以是英文"an"
        ('en', 'ambiguous'),  # 拼音"恩"或英文缩写
        ('in', 'ambiguous'),  # 拼音"因"或英文介词
        ('on', 'ambiguous'),  # 拼音"ong"的缩写或英文介词
        ('wu', 'ambiguous'),  # 拼音"无"或英文姓氏
        ('he', 'ambiguous'),  # 拼音"和/喝"或英文"他"
        ('shi', 'ambiguous'),  # 拼音"是/十"或英文"shi"
        ('bu', 'ambiguous'),  # 拼音"不"或英文"bu"
        ('pi', 'ambiguous'),  # 拼音"皮"或圆周率
        ('xi', 'ambiguous'),  # 拼音"西/喜"或希腊字母
    ]

    results = {
        'correct': 0,
        'incorrect': 0,
        'pinyin_correct': 0,
        'pinyin_total': 0,
        'english_correct': 0,
        'english_total': 0,
        'ambiguous_correct': 0,
        'ambiguous_total': 0,
        'errors': []
    }

    print("=" * 70)
    print("拼音/英文识别器测试报告")
    print("=" * 70)
    print()

    for text, expected in test_cases:
        result = detector.detect(text)
        actual = result.script_type
        status = "?"  # 默认状态

        # 对于ambiguous类型，只要判断为拼音或英文都算对
        if expected == 'ambiguous':
            results['ambiguous_total'] += 1
            # ambiguous允许有一定偏差，主要看置信度
            if result.confidence >= 0.5:
                status = "OK"
                results['ambiguous_correct'] += 1
        else:
            if expected == 'pinyin':
                results['pinyin_total'] += 1
                if actual == 'pinyin':
                    results['pinyin_correct'] += 1
                    results['correct'] += 1
                    status = "OK"
                else:
                    results['incorrect'] += 1
                    status = "FAIL"
                    results['errors'].append((text, expected, actual, result.confidence))
            elif expected == 'english':
                results['english_total'] += 1
                if actual == 'english':
                    results['english_correct'] += 1
                    results['correct'] += 1
                    status = "OK"
                else:
                    results['incorrect'] += 1
                    status = "FAIL"
                    results['errors'].append((text, expected, actual, result.confidence))

        # 打印详细结果
        if expected != 'ambiguous':
            print(f"{status} '{text}' -> {actual} (期望: {expected}, 置信度: {result.confidence:.3f})")

    # 打印统计
    print()
    print("-" * 70)
    print("统计结果")
    print("-" * 70)

    total_definite = results['pinyin_total'] + results['english_total']
    correct_definite = results['pinyin_correct'] + results['english_correct']

    print(f"总测试数: {len(test_cases)}")
    print(f"明确分类测试数: {total_definite}")
    print(f"正确识别: {correct_definite}")
    print(f"错误识别: {results['incorrect']}")
    print(f"整体准确率: {correct_definite / total_definite * 100:.1f}%")
    print()
    print(f"拼音识别: {results['pinyin_correct']}/{results['pinyin_total']} "
          f"({results['pinyin_correct'] / results['pinyin_total'] * 100:.1f}%)")
    print(f"英文识别: {results['english_correct']}/{results['english_total']} "
          f"({results['english_correct'] / results['english_total'] * 100:.1f}%)")

    if results['errors']:
        print()
        print("-" * 70)
        print("错误详情")
        print("-" * 70)
        for text, expected, actual, conf in results['errors']:
            print(f"  '{text}': 期望 {expected}, 实际 {actual} (置信度: {conf:.3f})")

    print()
    print("=" * 70)

    return results


def test_edge_cases():
    """测试边界情况"""
    detector = PinyinEnglishDetector()

    print()
    print("边界情况测试")
    print("-" * 70)

    edge_cases = [
        ('', '空字符串'),
        ('123', '纯数字'),
        ('abc123', '字母数字混合'),
        ('hello_world', '带下划线'),
        ('hello-world', '带连字符'),
        ('Hello', '首字母大写'),
        ('HELLO', '全大写'),
        ('a', '单字母'),
        ('ab', '双字母'),
        ('z', '单字母z'),
    ]

    for text, desc in edge_cases:
        result = detector.detect(text)
        print(f"  '{text}' ({desc}): {result.script_type} (置信度: {result.confidence:.3f})")


if __name__ == '__main__':
    results = run_tests()
    test_edge_cases()

    # 返回退出码
    total_definite = results['pinyin_total'] + results['english_total']
    correct_definite = results['pinyin_correct'] + results['english_correct']
    accuracy = correct_definite / total_definite if total_definite > 0 else 0

    print()
    if accuracy >= 0.90:
        print("[PASS] 测试通过 (准确率 >= 90%)")
        sys.exit(0)
    else:
        print("[FAIL] 测试未通过 (准确率 < 90%)")
        sys.exit(1)
