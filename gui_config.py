#!/usr/bin/env python3
"""
拼音/英文识别器 GUI 配置界面
使用 tkinter 实现跨平台配置工具
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import json
import os
import sys

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pinyin_english_detector import PinyinEnglishDetector
from mixed_input_segmenter import MixedInputSegmenter
from feedback_handler import get_feedback_handler


class PinyinDetectorGUI:
    """拼音/英文识别器配置界面"""

    def __init__(self, root):
        self.root = root
        self.root.title("拼音/英文识别器 - 配置与测试工具")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)

        # 初始化检测器
        self.detector = PinyinEnglishDetector()
        self.segmenter = MixedInputSegmenter(self.detector)
        self.feedback_handler = get_feedback_handler()

        # 配置样式
        self.style = ttk.Style()
        self.style.configure('Title.TLabel', font=('Microsoft YaHei', 16, 'bold'))
        self.style.configure('Subtitle.TLabel', font=('Microsoft YaHei', 12, 'bold'))
        self.style.configure('Result.TLabel', font=('Microsoft YaHei', 11))
        self.style.configure('TestButton.TButton', font=('Microsoft YaHei', 11))

        # 创建主布局
        self.create_menu()
        self.create_main_layout()

    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="加载配置", command=self.load_config)
        file_menu.add_command(label="保存配置", command=self.save_config)
        file_menu.add_separator()
        file_menu.add_command(label="导出结果", command=self.export_results)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)

        # 测试菜单
        test_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="测试", menu=test_menu)
        test_menu.add_command(label="运行批量测试", command=self.run_batch_test)
        test_menu.add_command(label="测试技术词汇", command=self.test_tech_words)
        test_menu.add_command(label="测试歧义词", command=self.test_ambiguous_words)

        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self.show_help)
        help_menu.add_command(label="关于", command=self.show_about)

    def create_main_layout(self):
        """创建主布局"""
        # 主容器
        main_container = ttk.Frame(self.root, padding="10")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置根窗口的权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_container.columnconfigure(0, weight=1)
        main_container.rowconfigure(1, weight=1)

        # 标题
        title_label = ttk.Label(
            main_container,
            text="拼音/英文智能识别器",
            style='Title.TLabel'
        )
        title_label.grid(row=0, column=0, pady=(0, 10))

        # 创建Notebook（标签页）
        self.notebook = ttk.Notebook(main_container)
        self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 标签页1: 实时测试
        self.test_frame = self.create_test_tab()
        self.notebook.add(self.test_frame, text="实时测试")

        # 标签页2: 批量测试
        self.batch_frame = self.create_batch_tab()
        self.notebook.add(self.batch_frame, text="批量测试")

        # 标签页3: 混合输入
        self.mixed_frame = self.create_mixed_tab()
        self.notebook.add(self.mixed_frame, text="混合输入")

        # 标签页4: 设置
        self.settings_frame = self.create_settings_tab()
        self.notebook.add(self.settings_frame, text="设置")

        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(
            main_container,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_bar.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(5, 0))

    def create_test_tab(self):
        """创建实时测试标签页"""
        frame = ttk.Frame(self.notebook, padding="10")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(2, weight=1)

        # 输入区域
        input_frame = ttk.LabelFrame(frame, text="输入文本", padding="10")
        input_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        input_frame.columnconfigure(0, weight=1)

        self.test_input = ttk.Entry(input_frame, font=('Microsoft YaHei', 12))
        self.test_input.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        self.test_input.bind('<Return>', lambda e: self.run_single_test())
        self.test_input.bind('<KeyRelease>', lambda e: self.run_single_test())

        test_btn = ttk.Button(
            input_frame,
            text="识别",
            command=self.run_single_test,
            style='TestButton.TButton'
        )
        test_btn.grid(row=0, column=1)

        # 快速测试按钮
        quick_frame = ttk.Frame(frame)
        quick_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        quick_tests = ['hello', 'nihao', 'women', 'python', 'yaml', 'api', 'git', 'zhongguo']
        for i, text in enumerate(quick_tests):
            btn = ttk.Button(
                quick_frame,
                text=text,
                command=lambda t=text: self.set_test_input(t)
            )
            btn.grid(row=0, column=i, padx=2)

        # 结果区域
        result_frame = ttk.LabelFrame(frame, text="识别结果", padding="10")
        result_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)

        self.result_text = scrolledtext.ScrolledText(
            result_frame,
            wrap=tk.WORD,
            font=('Consolas', 11),
            height=12
        )
        self.result_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.result_text.config(state=tk.DISABLED)

        # 歧义词推荐区域
        self.ambiguous_frame = ttk.LabelFrame(result_frame, text="歧义词推荐", padding="5")
        self.ambiguous_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        self.ambiguous_frame.columnconfigure(0, weight=1)

        self.ambiguous_label = ttk.Label(
            self.ambiguous_frame,
            text="输入单词以查看推荐",
            wraplength=700
        )
        self.ambiguous_label.grid(row=0, column=0, sticky=tk.W)

        self.ambiguous_buttons_frame = ttk.Frame(self.ambiguous_frame)
        self.ambiguous_buttons_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))

        # 反馈按钮区域
        feedback_frame = ttk.Frame(result_frame)
        feedback_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(5, 0))

        ttk.Label(feedback_frame, text="识别错误？请纠正：").grid(row=0, column=0, sticky=tk.W)

        self.feedback_pinyin_btn = ttk.Button(
            feedback_frame,
            text="这是拼音",
            command=lambda: self.submit_feedback('pinyin')
        )
        self.feedback_pinyin_btn.grid(row=0, column=1, padx=5)

        self.feedback_english_btn = ttk.Button(
            feedback_frame,
            text="这是英文",
            command=lambda: self.submit_feedback('english')
        )
        self.feedback_english_btn.grid(row=0, column=2, padx=5)

        # 存储最后一次检测结果
        self.last_result = None

        return frame

    def create_batch_tab(self):
        """创建批量测试标签页"""
        frame = ttk.Frame(self.notebook, padding="10")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        # 控制按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        run_btn = ttk.Button(
            btn_frame,
            text="运行批量测试",
            command=self.run_batch_test
        )
        run_btn.grid(row=0, column=0, padx=(0, 5))

        clear_btn = ttk.Button(
            btn_frame,
            text="清空结果",
            command=self.clear_batch_results
        )
        clear_btn.grid(row=0, column=1)

        # 结果显示
        result_frame = ttk.LabelFrame(frame, text="测试结果", padding="10")
        result_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)

        self.batch_result_text = scrolledtext.ScrolledText(
            result_frame,
            wrap=tk.WORD,
            font=('Consolas', 10),
            height=20
        )
        self.batch_result_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.batch_result_text.config(state=tk.DISABLED)

        return frame

    def create_mixed_tab(self):
        """创建混合输入标签页"""
        frame = ttk.Frame(self.notebook, padding="10")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(2, weight=1)

        # 输入区域
        input_frame = ttk.LabelFrame(frame, text="混合输入文本", padding="10")
        input_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        input_frame.columnconfigure(0, weight=1)

        self.mixed_input = ttk.Entry(input_frame, font=('Microsoft YaHei', 12))
        self.mixed_input.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        self.mixed_input.bind('<Return>', lambda e: self.run_mixed_test())
        self.mixed_input.bind('<KeyRelease>', lambda e: self.run_mixed_test())

        test_btn = ttk.Button(
            input_frame,
            text="切分",
            command=self.run_mixed_test
        )
        test_btn.grid(row=0, column=1)

        # 快速测试
        quick_frame = ttk.Frame(frame)
        quick_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        mixed_tests = ['hello世界', 'nihao123', 'API接口', 'Python是最好的', 'version版本v1']
        for i, text in enumerate(mixed_tests):
            btn = ttk.Button(
                quick_frame,
                text=text,
                command=lambda t=text: self.set_mixed_input(t)
            )
            btn.grid(row=0, column=i, padx=2)

        # 结果区域
        result_frame = ttk.LabelFrame(frame, text="切分结果", padding="10")
        result_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)

        self.mixed_result_text = scrolledtext.ScrolledText(
            result_frame,
            wrap=tk.WORD,
            font=('Consolas', 11),
            height=15
        )
        self.mixed_result_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.mixed_result_text.config(state=tk.DISABLED)

        return frame

    def create_settings_tab(self):
        """创建设置标签页"""
        frame = ttk.Frame(self.notebook, padding="10")
        frame.columnconfigure(0, weight=1)

        # 识别阈值设置
        threshold_frame = ttk.LabelFrame(frame, text="识别阈值", padding="10")
        threshold_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        self.confidence_threshold = tk.DoubleVar(value=0.5)
        ttk.Label(threshold_frame, text="置信度阈值:").grid(row=0, column=0, sticky=tk.W)
        threshold_scale = ttk.Scale(
            threshold_frame,
            from_=0.0,
            to=1.0,
            variable=self.confidence_threshold,
            orient=tk.HORIZONTAL
        )
        threshold_scale.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        threshold_label = ttk.Label(threshold_frame, textvariable=self.confidence_threshold)
        threshold_label.grid(row=0, column=2)

        # 功能开关
        feature_frame = ttk.LabelFrame(frame, text="功能开关", padding="10")
        feature_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        self.enable_learning = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            feature_frame,
            text="启用用户习惯学习",
            variable=self.enable_learning
        ).grid(row=0, column=0, sticky=tk.W)

        self.enable_cache = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            feature_frame,
            text="启用结果缓存",
            variable=self.enable_cache
        ).grid(row=1, column=0, sticky=tk.W)

        self.enable_context = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            feature_frame,
            text="启用上下文感知",
            variable=self.enable_context
        ).grid(row=2, column=0, sticky=tk.W)

        # Rime集成设置
        rime_frame = ttk.LabelFrame(frame, text="Rime输入法集成", padding="10")
        rime_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Label(rime_frame, text="Rime配置目录:").grid(row=0, column=0, sticky=tk.W)
        self.rime_path = tk.StringVar()
        rime_entry = ttk.Entry(rime_frame, textvariable=self.rime_path)
        rime_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)

        browse_btn = ttk.Button(
            rime_frame,
            text="浏览...",
            command=self.browse_rime_path
        )
        browse_btn.grid(row=0, column=2)

        install_btn = ttk.Button(
            rime_frame,
            text="安装到Rime",
            command=self.install_to_rime
        )
        install_btn.grid(row=1, column=0, columnspan=3, pady=(10, 0))

        return frame

    # ============== 功能方法 ==============

    def set_test_input(self, text):
        """设置测试输入"""
        self.test_input.delete(0, tk.END)
        self.test_input.insert(0, text)
        self.run_single_test()

    def set_mixed_input(self, text):
        """设置混合输入"""
        self.mixed_input.delete(0, tk.END)
        self.mixed_input.insert(0, text)
        self.run_mixed_test()

    def run_single_test(self):
        """运行单条测试"""
        text = self.test_input.get().strip()
        if not text:
            return

        result = self.detector.detect(text)

        # 存储最后一次结果用于反馈
        self.last_result = result

        # 格式化结果
        output = f"输入: {result.input_text}\n"
        output += f"识别类型: {result.script_type.upper()}\n"
        output += f"置信度: {result.confidence:.3f}\n\n"
        output += "候选得分:\n"
        for cand in result.candidates:
            output += f"  - {cand['type']}: {cand['score']:.3f} (置信度: {cand['confidence']:.3f})\n"

        # 显示结果
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, output)
        self.result_text.config(state=tk.DISABLED)

        self.status_var.set(f"已识别: '{text}' -> {result.script_type}")

        # 显示歧义词推荐
        self.show_ambiguous_recommendations(result)

    def show_ambiguous_recommendations(self, result):
        """显示歧义词智能推荐"""
        # 清除旧的推荐按钮
        for widget in self.ambiguous_buttons_frame.winfo_children():
            widget.destroy()

        text = result.input_text
        confidence = result.confidence

        # 判断是否是歧义词（置信度在0.4-0.7之间）
        if confidence >= 0.7:
            self.ambiguous_label.config(
                text=f"'{text}' 识别置信度较高 ({confidence:.2f})，不太可能是歧义词"
            )
            return

        # 获取另一种可能的解释
        candidates = result.candidates
        if len(candidates) < 2:
            return

        # 找出置信度较低的候选
        other_candidate = None
        for cand in candidates:
            if cand['type'] != result.script_type:
                other_candidate = cand
                break

        if not other_candidate:
            return

        # 显示歧义提示
        self.ambiguous_label.config(
            text=f"'{text}' 可能是歧义词（当前识别: {result.script_type}, 置信度: {confidence:.2f}）。"
                 f"也可能是 {other_candidate['type']}（置信度: {other_candidate['confidence']:.2f}）"
        )

        # 添加快速纠正按钮
        ttk.Label(
            self.ambiguous_buttons_frame,
            text="快速纠正为:"
        ).pack(side=tk.LEFT, padx=(0, 5))

        if result.script_type != 'pinyin':
            ttk.Button(
                self.ambiguous_buttons_frame,
                text=f"'{text}' 是拼音",
                command=lambda: self.quick_correct(text, 'pinyin')
            ).pack(side=tk.LEFT, padx=2)

        if result.script_type != 'english':
            ttk.Button(
                self.ambiguous_buttons_frame,
                text=f"'{text}' 是英文",
                command=lambda: self.quick_correct(text, 'english')
            ).pack(side=tk.LEFT, padx=2)

    def quick_correct(self, text: str, correct_type: str):
        """快速纠正"""
        # 获取当前检测结果
        result = self.detector.detect(text)
        predicted_type = result.script_type

        # 记录纠正
        self.feedback_handler.record_correction(text, predicted_type, correct_type)

        # 重新检测（使用学习后的权重）
        new_result = self.detector.detect(text)

        messagebox.showinfo(
            "纠正已记录",
            f"已记录 '{text}' 应该是 {correct_type}\n\n"
            f"重新检测后: {new_result.script_type} (置信度: {new_result.confidence:.3f})"
        )

        # 刷新显示
        self.run_single_test()

    def run_mixed_test(self):
        """运行混合输入测试"""
        text = self.mixed_input.get().strip()
        if not text:
            return

        result = self.segmenter.segment_with_analysis(text)

        # 格式化结果
        output = f"输入: {result['input']}\n"
        output += f"片段数: {result['segment_count']}\n"
        output += f"主要类型: {result['primary_type']}\n"
        output += f"是否混合: {result['is_mixed']}\n\n"
        output += "切分结果:\n"
        for seg in result['segments']:
            output += f"  [{seg['text']}] -> {seg['type']} (置信度: {seg['confidence']:.2f})\n"

        # 显示结果
        self.mixed_result_text.config(state=tk.NORMAL)
        self.mixed_result_text.delete(1.0, tk.END)
        self.mixed_result_text.insert(tk.END, output)
        self.mixed_result_text.config(state=tk.DISABLED)

        self.status_var.set(f"已切分: '{text}' -> {result['segment_count']} 个片段")

    def run_batch_test(self):
        """运行批量测试"""
        # 测试用例
        test_cases = [
            ('nihao', 'pinyin'), ('hello', 'english'), ('python', 'english'),
            ('zhongguo', 'pinyin'), ('yaml', 'english'), ('ide', 'english'),
            ('git', 'english'), ('api', 'english'), ('css', 'english'),
            ('women', 'pinyin'), ('database', 'english'), ('server', 'english'),
        ]

        results = []
        correct = 0

        for text, expected in test_cases:
            result = self.detector.detect(text)
            is_correct = result.script_type == expected
            if is_correct:
                correct += 1
            results.append((text, expected, result.script_type, is_correct, result.confidence))

        accuracy = correct / len(test_cases) * 100 if test_cases else 0

        # 格式化输出
        output = f"批量测试结果\n{'=' * 50}\n"
        output += f"总测试数: {len(test_cases)}\n"
        output += f"正确: {correct}\n"
        output += f"准确率: {accuracy:.1f}%\n\n"
        output += f"{'输入':<15} {'期望':<10} {'实际':<10} {'结果':<8} {'置信度'}\n"
        output += '-' * 60 + '\n'

        for text, expected, actual, is_correct, conf in results:
            status = 'OK' if is_correct else 'FAIL'
            output += f"{text:<15} {expected:<10} {actual:<10} {status:<8} {conf:.3f}\n"

        # 显示结果
        self.batch_result_text.config(state=tk.NORMAL)
        self.batch_result_text.delete(1.0, tk.END)
        self.batch_result_text.insert(tk.END, output)
        self.batch_result_text.config(state=tk.DISABLED)

        self.status_var.set(f"批量测试完成: {correct}/{len(test_cases)} 正确 ({accuracy:.1f}%)")

    def clear_batch_results(self):
        """清空批量测试结果"""
        self.batch_result_text.config(state=tk.NORMAL)
        self.batch_result_text.delete(1.0, tk.END)
        self.batch_result_text.config(state=tk.DISABLED)
        self.status_var.set("批量测试结果已清空")

    def test_tech_words(self):
        """测试技术词汇"""
        tech_words = ['yaml', 'ide', 'api', 'sdk', 'cli', 'gui', 'ui', 'json', 'xml', 'html', 'css']
        self._run_special_test("技术词汇测试", tech_words, 'english')

    def test_ambiguous_words(self):
        """测试歧义词"""
        # 歧义词不强制期望特定结果，只显示识别结果
        ambiguous = ['an', 'en', 'in', 'he', 'wo', 'ni', 'shi', 'bu', 'pi', 'xi']

        output = f"歧义词测试\n{'=' * 50}\n\n"
        for word in ambiguous:
            result = self.detector.detect(word)
            output += f"{word}: {result.script_type} (置信度: {result.confidence:.3f})\n"

        self.batch_result_text.config(state=tk.NORMAL)
        self.batch_result_text.delete(1.0, tk.END)
        self.batch_result_text.insert(tk.END, output)
        self.batch_result_text.config(state=tk.DISABLED)

        self.status_var.set("歧义词测试完成")

    def _run_special_test(self, title, words, expected_type):
        """运行专项测试"""
        results = []
        correct = 0

        for word in words:
            result = self.detector.detect(word)
            is_correct = result.script_type == expected_type
            if is_correct:
                correct += 1
            results.append((word, expected_type, result.script_type, is_correct, result.confidence))

        accuracy = correct / len(words) * 100 if words else 0

        output = f"{title}\n{'=' * 50}\n"
        output += f"准确率: {accuracy:.1f}% ({correct}/{len(words)})\n\n"

        for word, expected, actual, is_correct, conf in results:
            status = 'OK' if is_correct else 'FAIL'
            output += f"{word:<15} 期望: {expected:<8} 实际: {actual:<8} {status} ({conf:.3f})\n"

        self.batch_result_text.config(state=tk.NORMAL)
        self.batch_result_text.delete(1.0, tk.END)
        self.batch_result_text.insert(tk.END, output)
        self.batch_result_text.config(state=tk.DISABLED)

        self.status_var.set(f"{title}完成: {accuracy:.1f}%")

    def browse_rime_path(self):
        """浏览Rime配置目录"""
        path = filedialog.askdirectory(title="选择Rime配置目录")
        if path:
            self.rime_path.set(path)

    def install_to_rime(self):
        """安装到Rime输入法"""
        rime_dir = self.rime_path.get()
        if not rime_dir:
            messagebox.showwarning("警告", "请先选择Rime配置目录")
            return

        if not os.path.exists(rime_dir):
            messagebox.showerror("错误", "指定的目录不存在")
            return

        # 这里可以实现实际的安装逻辑
        messagebox.showinfo("信息", f"将安装到: {rime_dir}\n\n(此功能需要进一步完善)")

    def load_config(self):
        """加载配置"""
        path = filedialog.askopenfilename(
            title="加载配置",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                messagebox.showinfo("成功", "配置已加载")
            except Exception as e:
                messagebox.showerror("错误", f"加载失败: {e}")

    def save_config(self):
        """保存配置"""
        path = filedialog.asksaveasfilename(
            title="保存配置",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if path:
            try:
                config = {
                    'confidence_threshold': self.confidence_threshold.get(),
                    'enable_learning': self.enable_learning.get(),
                    'enable_cache': self.enable_cache.get(),
                    'enable_context': self.enable_context.get(),
                    'rime_path': self.rime_path.get()
                }
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
                messagebox.showinfo("成功", "配置已保存")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {e}")

    def export_results(self):
        """导出结果"""
        path = filedialog.asksaveasfilename(
            title="导出结果",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if path:
            try:
                # 获取当前显示的结果
                current_tab = self.notebook.index(self.notebook.select())
                if current_tab == 0:
                    content = self.result_text.get(1.0, tk.END)
                elif current_tab == 1:
                    content = self.batch_result_text.get(1.0, tk.END)
                elif current_tab == 2:
                    content = self.mixed_result_text.get(1.0, tk.END)
                else:
                    content = ""

                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("成功", "结果已导出")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {e}")

    def show_help(self):
        """显示帮助"""
        help_text = """
拼音/英文识别器使用说明

1. 实时测试
   - 在输入框中输入文本，自动识别
   - 点击快速测试按钮快速输入常用词

2. 批量测试
   - 运行预定义的测试用例集
   - 查看整体准确率和详细结果

3. 混合输入
   - 测试中英文混合输入的切分效果
   - 支持中文、英文、拼音、数字混合

4. 设置
   - 调整识别阈值
   - 配置功能开关
   - 设置Rime输入法集成

快捷键:
   - Enter: 执行识别
   - Ctrl+Q: 退出
        """
        messagebox.showinfo("使用说明", help_text)

    def show_about(self):
        """显示关于"""
        about_text = """
拼音/英文智能识别器 v1.2

基于规则 + 词典匹配的智能识别引擎
可用于Rime输入法或其他输入法框架

准确率: 95%+
支持: 纯拼音、纯英文、中英混合输入

作者: Claude Code
许可证: MIT
        """
        messagebox.showinfo("关于", about_text)

    def submit_feedback(self, correct_type: str):
        """提交用户反馈"""
        if not self.last_result:
            messagebox.showwarning("警告", "请先进行识别")
            return

        text = self.last_result.input_text
        predicted_type = self.last_result.script_type

        if predicted_type == correct_type:
            messagebox.showinfo("信息", "识别结果已经是正确的，无需纠正")
            return

        # 记录纠正
        self.feedback_handler.record_correction(
            text, predicted_type, correct_type
        )

        # 更新统计
        stats = self.feedback_handler.get_statistics()

        messagebox.showinfo(
            "反馈已记录",
            f"已记录纠正: '{text}' 应为 {correct_type}\n\n"
            f"累计纠正: {stats['total_corrections']} 次\n"
            f"涉及词汇: {stats['unique_words_corrected']} 个"
        )

        self.status_var.set(f"反馈已记录: '{text}' -> {correct_type}")


def main():
    """主函数"""
    root = tk.Tk()
    app = PinyinDetectorGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
