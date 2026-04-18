#!/usr/bin/env python3
"""
拼音/英文自动识别引擎
基于规则 + 词典匹配的智能识别
"""

import re
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

    def __init__(self):
        self.english_words = self._load_english_words()
        self.pinyin_dict = self._build_pinyin_dict()

    def _load_english_words(self) -> set:
        """加载常用英文单词词典"""
        # 核心高频词（约500个）
        common_words = {
            # 代词 & be动词
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
            'my', 'your', 'his', 'her', 'its', 'our', 'their', 'mine', 'yours', 'ours', 'theirs',
            'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'this', 'that', 'these', 'those',

            # 冠词 & 介词
            'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'over', 'after', 'under', 'again', 'further',
            'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'each',

            # 高频动词
            'have', 'has', 'had', 'do', 'does', 'did', 'done', 'doing',
            'get', 'gets', 'got', 'gotten', 'make', 'makes', 'made', 'making',
            'know', 'knows', 'knew', 'known', 'knowing',
            'take', 'takes', 'took', 'taken', 'taking',
            'see', 'sees', 'saw', 'seen', 'seeing',
            'come', 'comes', 'came', 'coming',
            'look', 'looks', 'looked', 'looking',
            'use', 'uses', 'used', 'using',
            'find', 'finds', 'found', 'finding',
            'give', 'gives', 'gave', 'given', 'giving',
            'tell', 'tells', 'told', 'telling',
            'ask', 'asks', 'asked', 'asking',
            'work', 'works', 'worked', 'working',
            'try', 'tries', 'tried', 'trying',
            'feel', 'feels', 'felt', 'feeling',
            'become', 'becomes', 'became', 'becoming',
            'leave', 'leaves', 'left', 'leaving',
            'put', 'puts', 'call', 'calls', 'called', 'calling',
            'keep', 'keeps', 'kept', 'keeping',
            'bring', 'brings', 'brought', 'bringing',
            'begin', 'begins', 'began', 'begun', 'beginning',
            'help', 'helps', 'helped', 'helping',
            'show', 'shows', 'showed', 'shown', 'showing',
            'hear', 'hears', 'heard', 'hearing',
            'play', 'plays', 'played', 'playing',
            'run', 'runs', 'ran', 'running',
            'move', 'moves', 'moved', 'moving',
            'live', 'lives', 'lived', 'living',
            'believe', 'believes', 'believed', 'believing',
            'bring', 'brings', 'brought', 'bringing',
            'happen', 'happens', 'happened', 'happening',
            'write', 'writes', 'wrote', 'written', 'writing',
            'sit', 'sits', 'sat', 'sitting',
            'stand', 'stands', 'stood', 'standing',
            'lose', 'loses', 'lost', 'losing',
            'pay', 'pays', 'paid', 'paying',
            'meet', 'meets', 'met', 'meeting',
            'include', 'includes', 'included', 'including',
            'continue', 'continues', 'continued', 'continuing',
            'set', 'sets', 'learn', 'learns', 'learned', 'learning',
            'change', 'changes', 'changed', 'changing',
            'lead', 'leads', 'led', 'leading',
            'understand', 'understands', 'understood', 'understanding',
            'watch', 'watches', 'watched', 'watching',
            'follow', 'follows', 'followed', 'following',
            'stop', 'stops', 'stopped', 'stopping',
            'create', 'creates', 'created', 'creating',
            'speak', 'speaks', 'spoke', 'spoken', 'speaking',
            'read', 'reads', 'reading', 'allow', 'allows', 'allowed', 'allowing',
            'add', 'adds', 'added', 'adding', 'spend', 'spends', 'spent', 'spending',
            'grow', 'grows', 'grew', 'grown', 'growing',
            'open', 'opens', 'opened', 'opening',
            'walk', 'walks', 'walked', 'walking',
            'win', 'wins', 'won', 'winning',
            'offer', 'offers', 'offered', 'offering',
            'remember', 'remembers', 'remembered', 'remembering',
            'love', 'loves', 'loved', 'loving',
            'consider', 'considers', 'considered', 'considering',
            'appear', 'appears', 'appeared', 'appearing',
            'buy', 'buys', 'bought', 'buying',
            'wait', 'waits', 'waited', 'waiting',
            'serve', 'serves', 'served', 'serving',
            'die', 'dies', 'died', 'dying',
            'send', 'sends', 'sent', 'sending',
            'expect', 'expects', 'expected', 'expecting',
            'build', 'builds', 'built', 'building',
            'stay', 'stays', 'stayed', 'staying',
            'fall', 'falls', 'fell', 'fallen', 'falling',
            'cut', 'cuts', 'cutting', 'reach', 'reaches', 'reached', 'reaching',
            'kill', 'kills', 'killed', 'killing',
            'remain', 'remains', 'remained', 'remaining',
            'suggest', 'suggests', 'suggested', 'suggesting',
            'raise', 'raises', 'raised', 'raising',
            'pass', 'passes', 'passed', 'passing',
            'sell', 'sells', 'sold', 'selling',
            'require', 'requires', 'required', 'requiring',
            'report', 'reports', 'reported', 'reporting',
            'decide', 'decides', 'decided', 'deciding',
            'pull', 'pulls', 'pulled', 'pulling',

            # 高频名词
            'time', 'person', 'year', 'way', 'day', 'thing', 'man', 'world', 'life', 'hand',
            'part', 'child', 'eye', 'woman', 'place', 'work', 'week', 'case', 'point',
            'government', 'company', 'number', 'group', 'problem', 'fact', 'water', 'room',
            'mother', 'area', 'money', 'story', 'month', 'lot', 'right', 'study', 'book',
            'word', 'business', 'issue', 'side', 'kind', 'head', 'house', 'service', 'friend',
            'father', 'power', 'hour', 'game', 'line', 'end', 'member', 'law', 'car', 'city',
            'community', 'name', 'president', 'team', 'minute', 'idea', 'kid', 'body',
            'information', 'back', 'parent', 'face', 'others', 'level', 'office', 'door',
            'health', 'person', 'art', 'war', 'history', 'party', 'result', 'change',
            'morning', 'reason', 'research', 'girl', 'guy', 'moment', 'air', 'teacher',
            'force', 'education', 'age', 'policy', 'everything', 'love', 'process',
            'music', 'market', 'sense', 'nation', 'plan', 'college', 'interest', 'death',
            'experience', 'effect', 'class', 'control', 'care', 'field', 'development',
            'role', 'effort', 'rate', 'heart', 'drug', 'show', 'leader', 'light', 'voice',
            'wife', 'police', 'mind', 'price', 'report', 'decision', 'son', 'view',
            'town', 'building', 'action', 'model', 'season', 'society', 'tax', 'player',
            'record', 'office', 'support', 'minute', 'vote', 'value', 'center', 'figure',
            'industry', 'table', 'death', 'course', 'food', 'project', 'activity',
            'practice', 'relationship', 'thought', 'economy', 'theory', 'management',
            'system', 'computer', 'media', 'fire', 'chance', 'ability', 'event', 'army',
            'camera', 'fish', 'garden', 'red', 'oil', 'direction', 'choice', 'freedom',
            'truth', 'phone', 'paper', 'university', 'employee', 'chief', 'congress',
            'newspaper', 'danger', 'culture', 'presence', 'region', 'resource', 'activity',
            'analysis', 'income', 'association', 'article', 'equipment', 'technology',
            'opportunity', 'performance', 'security', 'committee', 'language', 'reality',
            'version', 'majority', 'opinion', 'population', 'environment', 'variety',
            'organization', 'hospital', 'success', 'agreement', 'disaster', 'foundation',
            'statement', 'protection', 'attitude', 'context', 'commission', 'discussion',
            'implication', 'administration', 'possibility', 'reaction', 'solution',
            'resolution', 'tradition', 'application', 'conference', 'attention',
            'attitude', 'conversation', 'expression', 'improvement', 'measurement',
            'professional', 'satisfaction', 'significance', 'strategy', 'technology',

            # 高频形容词
            'good', 'new', 'first', 'last', 'long', 'great', 'little', 'own', 'other', 'old',
            'right', 'big', 'high', 'different', 'small', 'large', 'next', 'early', 'young',
            'important', 'few', 'public', 'bad', 'same', 'able', 'sure', 'free', 'real',
            'full', 'special', 'easy', 'clear', 'recent', 'certain', 'personal', 'open',
            'red', 'difficult', 'available', 'likely', 'short', 'single', 'medical', 'current',
            'wrong', 'private', 'past', 'foreign', 'simple', 'concerned', 'central',
            'difficult', 'various', 'individual', 'following', 'present', 'financial',
            'beautiful', 'happy', 'difficult', 'significant', 'medical', 'interesting',
            'successful', 'electrical', 'impossible', 'technical', 'normal', 'competitive',
            'critical', 'aware', 'afraid', 'willing', 'positive', 'human', 'serious',
            'fundamental', 'necessary', 'civil', 'additional', 'professional', 'ready',
            'financial', 'similar', 'international', 'complete', 'recent', 'correct',
            'healthy', 'future', 'positive', 'beautiful', 'responsible', 'separate',
            'primary', 'global', 'useful', 'alive', 'involved', 'actual', 'advanced',
            'capable', 'strange', 'rare', 'entire', 'excellent', 'surprised', 'conservative',
            'pleasant', 'reasonable', 'strict', 'familiar', 'confident', 'increasing',
            'quiet', 'slow', 'responsible', 'active', 'constant', 'independent', 'expensive',
            'dangerous', 'guilty', 'aggressive', 'obvious', 'nervous', 'popular',
            'wonderful', 'comfortable', 'emotional', 'suitable', 'academic', 'effective',
            'historical', 'aware', 'helpful', 'leading', 'limited', 'natural', 'physical',
            'scientific', 'basic', 'direct', 'existing', 'male', 'unable', 'female',
            'massive', 'unhappy', 'unlikely', 'usual', 'visual', 'vital', 'wide',
            'apparent', 'appropriate', 'automatic', 'collective', 'distinct', 'domestic',
            'efficient', 'enormous', 'entirely', 'essential', 'everyday', 'evil',
            'favorable', 'flat', 'flexible', 'formal', 'grand', 'ideal', 'illegal',
            'intelligent', 'internal', 'legal', 'mere', 'military', 'moral', 'naked',
            'nasty', 'naughty', 'neat', 'negative', 'nuclear', 'objective', 'odd',
            'ordinary', 'outdoor', 'outstanding', 'overall', 'pale', 'permanent',
            'political', 'pregnant', 'previous', 'prime', 'prior', 'professional',
            'profound', 'prominent', 'proud', 'pure', 'rapid', 'rational', 'regional',
            'relative', 'relevant', 'remarkable', 'respective', 'reverse', 'rough',
            'rural', 'sacred', 'scared', 'secret', 'secure', 'select', 'sensitive',
            'severe', 'sharp', 'short-term', 'significant', 'skilled', 'slight',
            'social', 'solid', 'southern', 'specific', 'spiritual', 'stable', 'steady',
            'still', 'strong', 'substantial', 'sudden', 'sufficient', 'suitable',
            'superior', 'surprising', 'suspicious', 'sweet', 'talented', 'tall',
            'terrible', 'thick', 'thin', 'tight', 'tiny', 'total', 'tough', 'toxic',
            'tremendous', 'typical', 'ugly', 'ultimate', 'unexpected', 'unfair',
            'unfortunate', 'unique', 'united', 'universal', 'unknown', 'upper',
            'urban', 'urgent', 'used', 'useful', 'useless', 'usual', 'valuable',
            'variable', 'various', 'vast', 'verbal', 'vertical', 'visible', 'visual',
            'vital', 'volatile', 'vulnerable', 'weak', 'wealthy', 'weird', 'western',
            'wet', 'whole', 'wicked', 'wide', 'widespread', 'wild', 'wise', 'wonderful',
            'wooden', 'working', 'worldwide', 'worried', 'worse', 'worst', 'worth',
            'worthwhile', 'worthy', 'written', 'wrong', 'yellow', 'young',

            # 高频副词
            'so', 'up', 'out', 'if', 'about', 'into', 'just', 'also', 'how', 'all', 'no',
            'most', 'other', 'some', 'time', 'very', 'when', 'much', 'only', 'over',
            'even', 'more', 'here', 'there', 'back', 'still', 'as', 'well', 'too',
            'any', 'may', 'say', 'where', 'between', 'both', 'again', 'never', 'really',
            'always', 'however', 'often', 'once', 'around', 'every', 'away', 'down',
            'off', 'pretty', 'through', 'far', 'actually', 'probably', 'perhaps',
            'especially', 'finally', 'quite', 'rather', 'almost', 'certainly',
            'clearly', 'early', 'easily', 'especially', 'finally', 'generally',
            'hardly', 'immediately', 'likely', 'mainly', 'merely', 'mostly',
            'necessarily', 'normally', 'obviously', 'occasionally', 'particularly',
            'possibly', 'quickly', 'rarely', 'readily', 'really', 'recently',
            'relatively', 'seriously', 'significantly', 'simply', 'slightly',
            'slowly', 'somehow', 'sometimes', 'somewhere', 'soon', 'specifically',
            'strongly', 'successfully', 'suddenly', 'surely', 'totally', 'truly',
            'twice', 'ultimately', 'undoubtedly', 'usually', 'widely',

            # 高频连词
            'and', 'but', 'or', 'yet', 'so', 'for', 'nor',
            'although', 'because', 'before', 'unless', 'while', 'whereas',
            'whether', 'either', 'neither', 'both', 'since', 'until', 'after',
            'though', 'even', 'once', 'whenever', 'wherever', 'however',
            'moreover', 'furthermore', 'therefore', 'otherwise', 'instead',
            'meanwhile', 'nevertheless', 'nonetheless', 'notwithstanding',
            'consequently', 'accordingly', 'thus', 'hence', 'still', 'yet',

            # 计算机/技术领域
            'app', 'api', 'web', 'net', 'data', 'code', 'file', 'user', 'server',
            'client', 'database', 'software', 'hardware', 'network', 'system',
            'program', 'function', 'class', 'object', 'method', 'variable',
            'interface', 'module', 'package', 'library', 'framework', 'platform',
            'application', 'development', 'programming', 'coding', 'debugging',
            'testing', 'deployment', 'production', 'environment', 'version',
            'update', 'upgrade', 'install', 'configuration', 'setting',
            'algorithm', 'structure', 'array', 'list', 'tree', 'graph', 'stack',
            'queue', 'heap', 'hash', 'string', 'number', 'integer', 'float',
            'boolean', 'character', 'byte', 'bit', 'token', 'syntax', 'parser',
            'compiler', 'interpreter', 'runtime', 'exception', 'error', 'bug',
            'issue', 'problem', 'solution', 'feature', 'requirement', 'design',
            'pattern', 'architecture', 'protocol', 'format', 'schema', 'model',
            'entity', 'attribute', 'relation', 'query', 'command', 'request',
            'response', 'event', 'callback', 'promise', 'async', 'sync',
            'thread', 'process', 'lock', 'mutex', 'semaphore', 'signal',
            'input', 'output', 'stream', 'buffer', 'cache', 'memory', 'disk',
            'storage', 'device', 'driver', 'port', 'socket', 'address',
            'protocol', 'layer', 'packet', 'frame', 'header', 'body', 'payload',
            'encryption', 'security', 'auth', 'login', 'logout', 'session',
            'cookie', 'token', 'key', 'certificate', 'password', 'credential',
            'permission', 'role', 'admin', 'root', 'user', 'guest', 'owner',
            'group', 'team', 'member', 'account', 'profile', 'settings',
            'config', 'yaml', 'json', 'xml', 'html', 'css', 'sql', 'bash',
            'shell', 'terminal', 'console', 'editor', 'ide', 'tool', 'git',
            'github', 'gitlab', 'docker', 'kubernetes', 'k8s', 'cloud',
            'aws', 'azure', 'gcp', 'lambda', 'ec2', 's3', 'bucket', 'queue',
            'topic', 'stream', 'pipeline', 'workflow', 'job', 'task', 'cron',
            'schedule', 'trigger', 'hook', 'event', 'log', 'metric', 'monitor',
            'alert', 'dashboard', 'report', 'analytics', 'statistics',
        }
        return common_words

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

        # 规则2: 音节数量合理性
        num_syllables = len(syllables)
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

        # 拼音元音密度通常在30%-60%
        if 0.25 <= vowel_ratio <= 0.65:
            vowel_score = 1.0
        else:
            vowel_score = 0.7

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

        # 拼音中很少有连续3个以上辅音
        if max_consonant_run <= 2:
            consonant_score = 1.0
        elif max_consonant_run == 3:
            consonant_score = 0.8
        else:
            consonant_score = 0.5

        # 综合评分
        final_score = syllable_score * vowel_score * consonant_score
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

        # 纯数字判断
        if text.isdigit():
            return DetectionResult(text, 'numeric', 1.0, [])

        # 包含非字母字符，可能是mixed
        if not text.isalpha():
            return DetectionResult(text, 'mixed', 0.5, [])

        # 计算两种语言的评分
        pinyin_score = self._calculate_pinyin_score(text)
        english_score = self._calculate_english_score(text)

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
            # 模糊地带，选分数高的
            if pinyin_score >= english_score:
                script_type = 'pinyin'
                confidence = pinyin_conf * 0.8  # 降低置信度
            else:
                script_type = 'english'
                confidence = english_conf * 0.8

        candidates = [
            {'type': 'pinyin', 'score': round(pinyin_score, 3), 'confidence': round(pinyin_conf, 3)},
            {'type': 'english', 'score': round(english_score, 3), 'confidence': round(english_conf, 3)}
        ]

        return DetectionResult(text, script_type, round(confidence, 3), candidates)


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
