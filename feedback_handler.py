#!/usr/bin/env python3
"""
用户反馈处理器
处理用户纠正，动态调整识别权重
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict


class FeedbackHandler:
    """
    用户反馈处理器
    记录用户纠正历史，动态调整识别偏好
    """

    def __init__(self, data_file: str = None):
        """
        初始化反馈处理器

        Args:
            data_file: 反馈数据存储文件路径
        """
        if data_file is None:
            home = os.path.expanduser("~")
            data_file = os.path.join(home, ".pinyin_detector_feedback.json")

        self.data_file = data_file
        self.feedback_data = {
            'corrections': {},  # {input_text: {'correct_type': str, 'count': int, 'last_time': str}}
            'frequent_words': defaultdict(int),  # 用户常用词频率
            'type_preferences': {'pinyin': 0, 'english': 0},  # 整体类型偏好
            'context_patterns': [],  # 上下文模式学习
        }
        self.load_data()

    def load_data(self):
        """加载反馈数据"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.feedback_data['corrections'] = data.get('corrections', {})
                    self.feedback_data['frequent_words'] = defaultdict(
                        int, data.get('frequent_words', {})
                    )
                    self.feedback_data['type_preferences'] = data.get(
                        'type_preferences', {'pinyin': 0, 'english': 0}
                    )
                    self.feedback_data['context_patterns'] = data.get(
                        'context_patterns', []
                    )
            except Exception as e:
                print(f"加载反馈数据失败: {e}")

    def save_data(self):
        """保存反馈数据"""
        try:
            data = {
                'corrections': self.feedback_data['corrections'],
                'frequent_words': dict(self.feedback_data['frequent_words']),
                'type_preferences': self.feedback_data['type_preferences'],
                'context_patterns': self.feedback_data['context_patterns'],
                'last_updated': datetime.now().isoformat()
            }
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存反馈数据失败: {e}")

    def record_correction(self, input_text: str, predicted_type: str,
                         correct_type: str, context: Optional[List[str]] = None):
        """
        记录用户纠正

        Args:
            input_text: 输入文本
            predicted_type: 预测类型
            correct_type: 用户纠正的正确类型
            context: 上下文（前后词）
        """
        text = input_text.lower().strip()
        if not text:
            return

        # 记录纠正
        if text not in self.feedback_data['corrections']:
            self.feedback_data['corrections'][text] = {
                'predicted': predicted_type,
                'corrections': defaultdict(int),
                'first_time': datetime.now().isoformat(),
            }

        self.feedback_data['corrections'][text]['corrections'][correct_type] += 1
        self.feedback_data['corrections'][text]['last_time'] = datetime.now().isoformat()

        # 更新词频
        self.feedback_data['frequent_words'][text] += 1

        # 更新类型偏好
        self.feedback_data['type_preferences'][correct_type] += 1

        # 记录上下文模式
        if context:
            self.feedback_data['context_patterns'].append({
                'context': context,
                'input': text,
                'type': correct_type,
                'time': datetime.now().isoformat()
            })
            # 只保留最近100条
            if len(self.feedback_data['context_patterns']) > 100:
                self.feedback_data['context_patterns'] = \
                    self.feedback_data['context_patterns'][-100:]

        self.save_data()

    def get_correction_stats(self, input_text: str) -> Optional[Dict]:
        """
        获取某词的纠正统计

        Returns:
            统计信息，如果没有纠正记录返回None
        """
        text = input_text.lower().strip()
        if text not in self.feedback_data['corrections']:
            return None

        data = self.feedback_data['corrections'][text]
        total_corrections = sum(data['corrections'].values())

        # 计算最可能的类型
        most_likely = max(data['corrections'].items(), key=lambda x: x[1])

        return {
            'total_corrections': total_corrections,
            'most_likely_type': most_likely[0],
            'confidence': most_likely[1] / total_corrections,
            'correction_history': dict(data['corrections']),
        }

    def adjust_score(self, input_text: str, pinyin_score: float,
                    english_score: float, context: Optional[List[str]] = None) -> Tuple[float, float]:
        """
        根据用户反馈调整分数

        Returns:
            (调整后拼音分数, 调整后英文分数)
        """
        text = input_text.lower().strip()

        # 1. 检查直接纠正记录
        stats = self.get_correction_stats(text)
        if stats and stats['total_corrections'] >= 2:
            # 有足够样本，使用用户偏好
            preferred_type = stats['most_likely_type']
            confidence = stats['confidence']

            boost = 0.3 * confidence  # 最大30%提升

            if preferred_type == 'pinyin':
                pinyin_score *= (1 + boost)
            else:
                english_score *= (1 + boost)

        # 2. 常用词加成
        word_freq = self.feedback_data['frequent_words'].get(text, 0)
        if word_freq > 5:
            # 常用词额外加成
            freq_boost = min(0.1, word_freq * 0.01)  # 最多10%
            if stats:
                if stats['most_likely_type'] == 'pinyin':
                    pinyin_score *= (1 + freq_boost)
                else:
                    english_score *= (1 + freq_boost)

        # 3. 上下文模式匹配
        if context:
            context_boost = self._get_context_boost(text, context)
            if context_boost > 0:
                pinyin_score *= (1 + context_boost)
            elif context_boost < 0:
                english_score *= (1 - context_boost)

        return pinyin_score, english_score

    def _get_context_boost(self, input_text: str, context: List[str]) -> float:
        """
        根据上下文模式计算加成

        Returns:
            >0: 倾向拼音, <0: 倾向英文, 0: 无影响
        """
        if not self.feedback_data['context_patterns']:
            return 0.0

        # 查找相似上下文
        matches = []
        for pattern in self.feedback_data['context_patterns']:
            if self._context_similarity(context, pattern['context']) > 0.7:
                if pattern['input'] == input_text.lower():
                    matches.append(pattern)

        if len(matches) < 2:
            return 0.0

        # 统计匹配的模式
        pinyin_count = sum(1 for m in matches if m['type'] == 'pinyin')
        english_count = sum(1 for m in matches if m['type'] == 'english')

        total = pinyin_count + english_count
        if total == 0:
            return 0.0

        # 返回倾向性
        if pinyin_count > english_count:
            return 0.2 * (pinyin_count / total)
        elif english_count > pinyin_count:
            return -0.2 * (english_count / total)
        return 0.0

    def _context_similarity(self, ctx1: List[str], ctx2: List[str]) -> float:
        """计算上下文相似度"""
        if not ctx1 or not ctx2:
            return 0.0

        # 简单的Jaccard相似度
        set1 = set(ctx1)
        set2 = set(ctx2)

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

    def get_frequent_misclassifications(self, limit: int = 10) -> List[Dict]:
        """
        获取经常识别错误的词

        Returns:
            列表，每项包含词和纠正次数
        """
        items = []
        for text, data in self.feedback_data['corrections'].items():
            total = sum(data['corrections'].values())
            if total >= 2:  # 至少纠正过2次
                most_likely = max(data['corrections'].items(), key=lambda x: x[1])
                items.append({
                    'text': text,
                    'predicted': data['predicted'],
                    'correct': most_likely[0],
                    'count': total,
                    'confidence': most_likely[1] / total
                })

        # 按纠正次数排序
        items.sort(key=lambda x: x['count'], reverse=True)
        return items[:limit]

    def export_personal_dict(self, output_file: str):
        """导出个人词库"""
        data = {
            'frequent_words': dict(self.feedback_data['frequent_words']),
            'correction_rules': {
                text: {
                    'preferred_type': max(data['corrections'].items(), key=lambda x: x[1])[0],
                    'confidence': max(data['corrections'].values()) / sum(data['corrections'].values())
                }
                for text, data in self.feedback_data['corrections'].items()
                if sum(data['corrections'].values()) >= 2
            },
            'type_preferences': self.feedback_data['type_preferences'],
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def import_personal_dict(self, input_file: str):
        """导入个人词库"""
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 合并数据
        for word, freq in data.get('frequent_words', {}).items():
            self.feedback_data['frequent_words'][word] += freq

        for text, rule in data.get('correction_rules', {}).items():
            if text not in self.feedback_data['corrections']:
                self.feedback_data['corrections'][text] = {
                    'predicted': 'unknown',
                    'corrections': defaultdict(int),
                }
            self.feedback_data['corrections'][text]['corrections'][rule['preferred_type']] += 10

        self.save_data()

    def get_statistics(self) -> Dict:
        """获取反馈统计信息"""
        total_corrections = sum(
            sum(data['corrections'].values())
            for data in self.feedback_data['corrections'].values()
        )

        return {
            'total_corrections': total_corrections,
            'unique_words_corrected': len(self.feedback_data['corrections']),
            'frequent_words': len(self.feedback_data['frequent_words']),
            'type_preferences': self.feedback_data['type_preferences'],
            'frequent_misclassifications': self.get_frequent_misclassifications(5),
        }

    def reset(self):
        """重置所有反馈数据"""
        self.feedback_data = {
            'corrections': {},
            'frequent_words': defaultdict(int),
            'type_preferences': {'pinyin': 0, 'english': 0},
            'context_patterns': [],
        }
        self.save_data()


# 单例模式
_feedback_handler = None


def get_feedback_handler() -> FeedbackHandler:
    """获取全局反馈处理器实例"""
    global _feedback_handler
    if _feedback_handler is None:
        _feedback_handler = FeedbackHandler()
    return _feedback_handler


if __name__ == '__main__':
    # 测试
    handler = FeedbackHandler()

    # 模拟用户纠正
    handler.record_correction('women', 'english', 'pinyin')
    handler.record_correction('women', 'english', 'pinyin')
    handler.record_correction('hello', 'pinyin', 'english')

    print("统计信息:", handler.get_statistics())

    # 测试分数调整
    p_score, e_score = handler.adjust_score('women', 0.5, 0.5)
    print(f"women 调整后: pinyin={p_score:.3f}, english={e_score:.3f}")

    p_score, e_score = handler.adjust_score('hello', 0.5, 0.5)
    print(f"hello 调整后: pinyin={p_score:.3f}, english={e_score:.3f}")
