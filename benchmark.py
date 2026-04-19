#!/usr/bin/env python3
"""
性能基准测试
测试识别器的处理速度和内存占用
"""

import time
import sys
import os
import tracemalloc

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pinyin_english_detector import PinyinEnglishDetector
from mixed_input_segmenter import MixedInputSegmenter


def benchmark_detector(iterations=1000):
    """基准测试：单条检测性能"""
    detector = PinyinEnglishDetector()

    test_cases = [
        'hello',      # 短英文
        'nihao',      # 短拼音
        'python',     # 中等英文
        'zhongguo',   # 中等拼音
        'javascript', # 较长英文
        'womenyiqichiqu', # 较长拼音
    ]

    print("=" * 60)
    print("拼音/英文识别器性能基准测试")
    print("=" * 60)

    # 预热
    for text in test_cases:
        detector.detect(text)

    # 测试单条性能
    print("\n【单条检测性能】")
    print(f"{'输入':<20} {'类型':<10} {'时间(ms)':<12} {'速度(次/秒)':<10}")
    print("-" * 60)

    for text in test_cases:
        start = time.perf_counter()
        for _ in range(iterations):
            detector.detect(text)
        elapsed = time.perf_counter() - start

        result = detector.detect(text)
        avg_time = (elapsed / iterations) * 1000  # ms
        speed = iterations / elapsed

        print(f"{text:<20} {result.script_type:<10} {avg_time:<12.3f} {speed:<10.1f}")

    # 测试批量性能
    print("\n【批量检测性能】")
    total_iterations = iterations * len(test_cases)
    start = time.perf_counter()
    for _ in range(iterations):
        for text in test_cases:
            detector.detect(text)
    elapsed = time.perf_counter() - start

    avg_time = (elapsed / total_iterations) * 1000
    speed = total_iterations / elapsed

    print(f"总测试次数: {total_iterations}")
    print(f"总耗时: {elapsed:.3f} 秒")
    print(f"平均每次: {avg_time:.3f} ms")
    print(f"处理速度: {speed:.1f} 次/秒")

    return detector


def benchmark_mixed_segmentation(iterations=500):
    """基准测试：混合输入切分性能"""
    detector = PinyinEnglishDetector()
    segmenter = MixedInputSegmenter(detector)

    test_cases = [
        "hello世界",
        "nihao123",
        "test测试abc",
        "API接口文档",
        "Python是最好的语言",
        "zhongguo中国",
        "version版本号v1.0",
        "JSON格式数据",
        "womendoushuohellonihaoa",  # 长混合输入
    ]

    print("\n" + "=" * 60)
    print("混合输入切分性能测试")
    print("=" * 60)

    # 预热
    for text in test_cases:
        segmenter.segment(text)

    print("\n【切分性能】")
    print(f"{'输入':<30} {'片段数':<8} {'时间(ms)':<12} {'速度(次/秒)':<10}")
    print("-" * 70)

    for text in test_cases:
        start = time.perf_counter()
        for _ in range(iterations):
            segmenter.segment(text)
        elapsed = time.perf_counter() - start

        segments = segmenter.segment(text)
        avg_time = (elapsed / iterations) * 1000
        speed = iterations / elapsed

        display_text = text[:25] + "..." if len(text) > 25 else text
        print(f"{display_text:<30} {len(segments):<8} {avg_time:<12.3f} {speed:<10.1f}")

    # 批量性能
    print("\n【批量切分性能】")
    total_iterations = iterations * len(test_cases)
    start = time.perf_counter()
    for _ in range(iterations):
        for text in test_cases:
            segmenter.segment(text)
    elapsed = time.perf_counter() - start

    avg_time = (elapsed / total_iterations) * 1000
    speed = total_iterations / elapsed

    print(f"总测试次数: {total_iterations}")
    print(f"总耗时: {elapsed:.3f} 秒")
    print(f"平均每次: {avg_time:.3f} ms")
    print(f"处理速度: {speed:.1f} 次/秒")


def benchmark_memory():
    """内存占用测试"""
    print("\n" + "=" * 60)
    print("内存占用测试")
    print("=" * 60)

    tracemalloc.start()

    # 测试检测器内存
    snapshot1 = tracemalloc.take_snapshot()
    detector = PinyinEnglishDetector()
    snapshot2 = tracemalloc.take_snapshot()

    diff = snapshot2.compare_to(snapshot1, 'lineno')
    detector_memory = sum(stat.size for stat in diff if stat.size > 0)

    print(f"\n检测器初始化内存: {detector_memory / 1024:.1f} KB")

    # 测试切分器内存
    snapshot3 = tracemalloc.take_snapshot()
    segmenter = MixedInputSegmenter(detector)
    snapshot4 = tracemalloc.take_snapshot()

    diff2 = snapshot4.compare_to(snapshot3, 'lineno')
    segmenter_memory = sum(stat.size for stat in diff2 if stat.size > 0)

    print(f"切分器初始化内存: {segmenter_memory / 1024:.1f} KB")

    # 测试缓存内存
    test_words = ['hello', 'nihao', 'python', 'zhongguo'] * 100
    for word in test_words:
        detector.detect(word)

    snapshot5 = tracemalloc.take_snapshot()
    cache_memory = sum(stat.size for stat in snapshot5.compare_to(snapshot4, 'lineno') if stat.size > 0)

    print(f"缓存 400 条结果内存: {cache_memory / 1024:.1f} KB")
    print(f"每条缓存平均: {cache_memory / 400:.1f} bytes")

    tracemalloc.stop()


def benchmark_optimization_comparison():
    """优化前后对比测试"""
    print("\n" + "=" * 60)
    print("缓存优化效果对比")
    print("=" * 60)

    # 无缓存测试
    detector_no_cache = PinyinEnglishDetector()
    detector_no_cache._cache_max_size = 0  # 禁用缓存

    # 有缓存测试
    detector_with_cache = PinyinEnglishDetector()

    test_words = ['hello', 'nihao', 'python', 'women', 'yaml', 'git'] * 50

    # 无缓存
    start = time.perf_counter()
    for word in test_words:
        detector_no_cache.detect(word)
    no_cache_time = time.perf_counter() - start

    # 有缓存（第一轮 - 填充缓存）
    start = time.perf_counter()
    for word in test_words:
        detector_with_cache.detect(word)
    cache_fill_time = time.perf_counter() - start

    # 有缓存（第二轮 - 使用缓存）
    start = time.perf_counter()
    for word in test_words:
        detector_with_cache.detect(word)
    cache_use_time = time.perf_counter() - start

    print(f"\n测试词数: {len(test_words)}")
    print(f"无缓存总耗时: {no_cache_time*1000:.1f} ms")
    print(f"缓存填充耗时: {cache_fill_time*1000:.1f} ms")
    print(f"缓存命中耗时: {cache_use_time*1000:.1f} ms")
    print(f"缓存加速比: {no_cache_time/cache_use_time:.1f}x")


if __name__ == '__main__':
    benchmark_detector(1000)
    benchmark_mixed_segmentation(500)
    benchmark_memory()
    benchmark_optimization_comparison()

    print("\n" + "=" * 60)
    print("性能测试完成")
    print("=" * 60)
