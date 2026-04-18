#!/usr/bin/env python3
"""
用户习惯学习模块
记录用户输入选择，自适应调整识别偏好
"""

import json
import os
from typing import Dict, List, Tuple
from datetime import datetime, timedelta


class UserPreferenceLearner:
    """
    用户习惯学习器
    记录用户实际选择，动态调整识别权重
    """

    def __init__(self, data_file: str = None):
        """
        初始化学习器

        Args:
            data_file: 用户数据存储文件路径
        """
        if data_file is None:
            # 默认存储在用户主目录
            home = os.path.expanduser("~")
            data_file = os.path.join(home, ".pinyin_detector_prefs.json")

        self.data_file = data_file
        self.preferences: Dict[str, Dict] = {}
        self.word_history: Dict[str, int] = {}
        self.load_data()

    def load_data(self):
        """从文件加载用户数据"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.preferences = data.get('preferences', {})
                    self.word_history = data.get('word_history', {})
            except Exception as e:
                print(f"加载用户数据失败: {e}")
                self.preferences = {}
                self.word_history = {}

    def save_data(self):
        """保存用户数据到文件"""
        try:
            data = {
                'preferences': self.preferences,
                'word_history': self.word_history,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存用户数据失败: {e}")

    def record_choice(self, input_text: str, chosen_type: str, confidence: float = 1.0):
        """
        记录用户的选择

        Args:
            input_text: 输入的文本
            chosen_type: 用户选择的类型 ('pinyin' 或 'english')
            confidence: 用户对此选择的置信度 (1.0 = 确定)
        """
        text = input_text.lower().strip()
        if not text:
            return

        # 更新偏好
        if text not in self.preferences:
            self.preferences[text] = {
                'pinyin_count': 0,
                'english_count': 0,
                'total_count': 0,
                'last_choice': None,
                'last_time': None
            }

        pref = self.preferences[text]
        pref['total_count'] += 1

        if chosen_type == 'pinyin':
            pref['pinyin_count'] += confidence
        else:
            pref['english_count'] += confidence

        pref['last_choice'] = chosen_type
        pref['last_time'] = datetime.now().isoformat()

        # 更新词频历史
        self.word_history[text] = self.word_history.get(text, 0) + 1

        # 保存数据
        self.save_data()

    def get_user_preference(self, input_text: str) -> Tuple[str, float]:
        """
        获取用户对特定输入的偏好

        Args:
            input_text: 输入的文本

        Returns:
            (偏好类型, 置信度)
        """
        text = input_text.lower().strip()
        if text not in self.preferences:
            return None, 0.0

        pref = self.preferences[text]
        total = pref['pinyin_count'] + pref['english_count']

        if total == 0:
            return None, 0.0

        pinyin_ratio = pref['pinyin_count'] / total
        english_ratio = pref['english_count'] / total

        # 需要足够样本才使用用户偏好
        if pref['total_count'] < 2:
            return None, 0.0

        if pinyin_ratio > 0.7:
            return 'pinyin', pinyin_ratio
        elif english_ratio > 0.7:
            return 'english', english_ratio
        else:
            return None, 0.0

    def adjust_score(self, input_text: str, pinyin_score: float, english_score: float) -> Tuple[float, float]:
        """
        根据用户偏好调整评分

        Args:
            input_text: 输入的文本
            pinyin_score: 原始拼音评分
            english_score: 原始英文评分

        Returns:
            (调整后拼音评分, 调整后英文评分)
        """
        pref_type, pref_conf = self.get_user_preference(input_text)

        if pref_type is None:
            return pinyin_score, english_score

        # 根据用户偏好调整
        boost_factor = 0.3 * pref_conf  # 最大提升30%

        if pref_type == 'pinyin':
            pinyin_score = pinyin_score * (1 + boost_factor)
        else:
            english_score = english_score * (1 + boost_factor)

        return pinyin_score, english_score

    def get_statistics(self) -> Dict:
        """获取学习统计信息"""
        total_words = len(self.preferences)
        total_choices = sum(p['total_count'] for p in self.preferences.values())

        # 最常用的英文词
        english_favorites = [
            (word, pref['english_count'])
            for word, pref in self.preferences.items()
            if pref['english_count'] > pref['pinyin_count']
        ]
        english_favorites.sort(key=lambda x: x[1], reverse=True)

        # 最常用的拼音
        pinyin_favorites = [
            (word, pref['pinyin_count'])
            for word, pref in self.preferences.items()
            if pref['pinyin_count'] > pref['english_count']
        ]
        pinyin_favorites.sort(key=lambda x: x[1], reverse=True)

        return {
            'total_tracked_words': total_words,
            'total_recorded_choices': total_choices,
            'top_english_words': english_favorites[:10],
            'top_pinyin_words': pinyin_favorites[:10],
            'data_file': self.data_file
        }

    def clear_history(self):
        """清除所有学习历史"""
        self.preferences = {}
        self.word_history = {}
        if os.path.exists(self.data_file):
            os.remove(self.data_file)


# 单例模式，全局共享
_learner_instance = None


def get_learner() -> UserPreferenceLearner:
    """获取全局学习器实例"""
    global _learner_instance
    if _learner_instance is None:
        _learner_instance = UserPreferenceLearner()
    return _learner_instance


if __name__ == '__main__':
    # 测试
    learner = UserPreferenceLearner()

    # 模拟用户选择
    learner.record_choice('database', 'english')
    learner.record_choice('database', 'english')
    learner.record_choice('database', 'english')

    learner.record_choice('nihao', 'pinyin')
    learner.record_choice('nihao', 'pinyin')

    # 测试偏好查询
    print("database偏好:", learner.get_user_preference('database'))
    print("nihao偏好:", learner.get_user_preference('nihao'))

    # 测试分数调整
    p_score, e_score = learner.adjust_score('database', 0.5, 0.5)
    print(f"database调整后: pinyin={p_score:.3f}, english={e_score:.3f}")

    # 显示统计
    stats = learner.get_statistics()
    print("\n统计信息:")
    print(f"  跟踪词汇数: {stats['total_tracked_words']}")
    print(f"  记录选择数: {stats['total_recorded_choices']}")
