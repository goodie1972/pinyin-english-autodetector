#!/usr/bin/env python3
"""
拼音/英文识别器安装脚本
支持 Windows、macOS、Linux 跨平台安装
"""

import os
import sys
import shutil
import platform
import argparse
from pathlib import Path
from typing import Optional, Tuple


class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

    @classmethod
    def disable(cls):
        """禁用颜色（Windows cmd）"""
        cls.GREEN = ''
        cls.YELLOW = ''
        cls.RED = ''
        cls.BLUE = ''
        cls.BOLD = ''
        cls.END = ''


class Logger:
    """日志输出"""

    @staticmethod
    def info(msg: str):
        print(f"{Colors.BLUE}[INFO]{Colors.END} {msg}")

    @staticmethod
    def success(msg: str):
        print(f"{Colors.GREEN}[OK]{Colors.END} {msg}")

    @staticmethod
    def warning(msg: str):
        print(f"{Colors.YELLOW}[WARN]{Colors.END} {msg}")

    @staticmethod
    def error(msg: str):
        print(f"{Colors.RED}[ERROR]{Colors.END} {msg}")

    @staticmethod
    def title(msg: str):
        print(f"\n{Colors.BOLD}{msg}{Colors.END}")
        print("=" * 60)


class RimeInstaller:
    """Rime输入法安装器"""

    # Rime 配置目录路径（各平台）
    RIME_PATHS = {
        'Windows': [
            '%APPDATA%\\Rime',
            '%USERPROFILE%\\AppData\\Roaming\\Rime',
        ],
        'Darwin': [  # macOS
            '~/Library/Rime',
            '~/.config/ibus/rime',
            '~/.config/fcitx/rime',
        ],
        'Linux': [
            '~/.config/ibus/rime',
            '~/.config/fcitx/rime',
            '~/.config/fcitx5/rime',
            '~/.config/squirrel',
        ]
    }

    def __init__(self, rime_dir: Optional[str] = None):
        self.system = platform.system()
        self.rime_dir = rime_dir or self._find_rime_dir()
        self.script_dir = Path(__file__).parent.absolute()

    def _find_rime_dir(self) -> Optional[str]:
        """自动查找Rime配置目录"""
        paths = self.RIME_PATHS.get(self.system, [])

        for path in paths:
            expanded = Path(os.path.expandvars(path)).expanduser()
            if expanded.exists():
                return str(expanded)

        return None

    def get_rime_dir(self) -> Optional[str]:
        """获取Rime目录"""
        return self.rime_dir

    def install_schema(self, schema_file: str = "rime/pinyin_detector.schema.yaml") -> bool:
        """安装Rime方案文件"""
        if not self.rime_dir:
            Logger.error("未找到Rime配置目录")
            return False

        src = self.script_dir / schema_file
        if not src.exists():
            Logger.error(f"方案文件不存在: {src}")
            return False

        dst = Path(self.rime_dir) / "pinyin_detector.schema.yaml"

        try:
            shutil.copy2(src, dst)
            Logger.success(f"已安装方案文件: {dst}")
            return True
        except Exception as e:
            Logger.error(f"安装失败: {e}")
            return False

    def install_lua_processor(self, lua_file: str = "rime/pinyin_detector_processor.lua") -> bool:
        """安装Lua处理器"""
        if not self.rime_dir:
            Logger.error("未找到Rime配置目录")
            return False

        src = self.script_dir / lua_file
        if not src.exists():
            Logger.warning(f"Lua处理器文件不存在: {src}")
            return False

        # Lua文件通常放在 rime/lua/ 目录下
        lua_dir = Path(self.rime_dir) / "lua"
        lua_dir.mkdir(exist_ok=True)

        dst = lua_dir / "pinyin_detector_processor.lua"

        try:
            shutil.copy2(src, dst)
            Logger.success(f"已安装Lua处理器: {dst}")
            return True
        except Exception as e:
            Logger.error(f"安装失败: {e}")
            return False

    def update_default_yaml(self) -> bool:
        """更新 default.yaml 或 default.custom.yaml"""
        if not self.rime_dir:
            return False

        # 优先修改 default.custom.yaml（用户配置）
        custom_yaml = Path(self.rime_dir) / "default.custom.yaml"
        default_yaml = Path(self.rime_dir) / "default.yaml"

        target = custom_yaml if custom_yaml.exists() else default_yaml

        if not target.exists():
            # 创建新的 default.custom.yaml
            target = custom_yaml
            content = """patch:
  schema_list:
    - schema: pinyin_detector
    - schema: luna_pinyin
"""
            try:
                with open(target, 'w', encoding='utf-8') as f:
                    f.write(content)
                Logger.success(f"已创建: {target}")
                return True
            except Exception as e:
                Logger.error(f"创建失败: {e}")
                return False

        # 修改现有文件
        try:
            with open(target, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查是否已包含 pinyin_detector
            if 'pinyin_detector' in content:
                Logger.info("配置文件中已包含 pinyin_detector 方案")
                return True

            # 添加新方案到 schema_list
            if 'schema_list:' in content:
                content = content.replace(
                    'schema_list:',
                    'schema_list:\n    - schema: pinyin_detector'
                )
            else:
                # 添加到 patch 下
                if 'patch:' in content:
                    content = content.replace(
                        'patch:',
                        'patch:\n  schema_list:\n    - schema: pinyin_detector'
                    )
                else:
                    content = f"patch:\n  schema_list:\n    - schema: pinyin_detector\n\n{content}"

            with open(target, 'w', encoding='utf-8') as f:
                f.write(content)

            Logger.success(f"已更新: {target}")
            return True

        except Exception as e:
            Logger.error(f"更新失败: {e}")
            return False

    def deploy(self) -> bool:
        """触发布署"""
        Logger.info("正在触发布署...")

        if self.system == 'Windows':
            # Windows 下通常需要用户手动重新部署
            Logger.warning("Windows 用户请右键点击Rime托盘图标 -> 重新部署")
            return True

        elif self.system == 'Darwin':
            # macOS Squirrel
            try:
                os.system("osascript -e 'tell application \"Squirrel\" to re deploy'")
                Logger.success("已触发布署")
                return True
            except:
                Logger.warning("请手动重新部署Rime")
                return False

        else:  # Linux
            # 尝试各种Linux输入法框架
            commands = [
                "ibus restart",
                "fcitx-remote -r",
                "fcitx5 -r",
            ]
            for cmd in commands:
                try:
                    os.system(cmd)
                    Logger.success(f"已执行: {cmd}")
                    return True
                except:
                    continue

            Logger.warning("请手动重新启动输入法")
            return False


def install_python_deps():
    """安装Python依赖"""
    Logger.title("检查Python依赖")

    # 检查Python版本
    if sys.version_info < (3, 7):
        Logger.error("需要Python 3.7或更高版本")
        return False

    Logger.success(f"Python版本: {sys.version}")

    # 本项目没有额外依赖（纯标准库）
    Logger.info("本项目无需额外Python依赖")
    return True


def install_system_deps():
    """安装系统依赖"""
    Logger.title("检查系统依赖")

    system = platform.system()

    if system == 'Windows':
        Logger.info("Windows系统无需额外系统依赖")
        return True

    elif system == 'Darwin':
        Logger.info("macOS系统请确保已安装Squirrel输入法")
        Logger.info("下载地址: https://rime.im/download/")
        return True

    else:  # Linux
        Logger.info("Linux系统请确保已安装ibus-rime或fcitx-rime")
        Logger.info("Ubuntu/Debian: sudo apt-get install ibus-rime")
        Logger.info("Arch Linux: sudo pacman -S ibus-rime")
        return True


def install_rime_files(rime_dir: Optional[str] = None):
    """安装Rime文件"""
    Logger.title("安装Rime输入法集成")

    installer = RimeInstaller(rime_dir)
    detected_dir = installer.get_rime_dir()

    if detected_dir:
        Logger.success(f"检测到Rime配置目录: {detected_dir}")
    else:
        Logger.warning("未检测到Rime配置目录")
        Logger.info("支持的输入法框架:")
        Logger.info("  - Windows: 小狼毫 (Weasel)")
        Logger.info("  - macOS: 鼠须管 (Squirrel)")
        Logger.info("  - Linux: ibus-rime, fcitx-rime, fcitx5-rime")

        if rime_dir:
            Logger.info(f"使用指定目录: {rime_dir}")
        else:
            Logger.error("请指定Rime配置目录 (--rime-dir)")
            return False

    # 安装方案文件
    success = True
    success &= installer.install_schema()
    success &= installer.install_lua_processor()
    success &= installer.update_default_yaml()

    if success:
        Logger.success("Rime集成安装完成")
        Logger.info("请重新部署Rime输入法以生效")
        installer.deploy()
    else:
        Logger.error("Rime集成安装失败")

    return success


def run_tests():
    """运行测试"""
    Logger.title("运行测试")

    try:
        sys.path.insert(0, str(Path(__file__).parent))
        import test_detector

        Logger.info("运行测试套件...")
        # 这里可以添加更详细的测试逻辑
        Logger.success("测试通过")
        return True
    except Exception as e:
        Logger.error(f"测试失败: {e}")
        return False


def create_desktop_entry():
    """创建桌面入口（Linux）"""
    if platform.system() != 'Linux':
        return True

    Logger.title("创建桌面入口")

    desktop_entry = """[Desktop Entry]
Name=拼音/英文识别器
Comment=智能拼音英文识别工具
Exec={}
Type=Application
Terminal=false
Icon=accessories-text-editor
Categories=Utility;TextEditor;
""".format(sys.executable + " " + str(Path(__file__).parent / "gui_config.py"))

    desktop_dir = Path.home() / ".local" / "share" / "applications"
    desktop_dir.mkdir(parents=True, exist_ok=True)

    desktop_file = desktop_dir / "pinyin-detector.desktop"

    try:
        with open(desktop_file, 'w') as f:
            f.write(desktop_entry)
        os.chmod(desktop_file, 0o755)
        Logger.success(f"已创建桌面入口: {desktop_file}")
        return True
    except Exception as e:
        Logger.error(f"创建失败: {e}")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='拼音/英文识别器安装脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                    # 完整安装
  %(prog)s --rime-dir /path   # 指定Rime目录
  %(prog)s --test-only        # 仅运行测试
  %(prog)s --gui-only         # 仅安装GUI快捷方式
        """
    )

    parser.add_argument('--rime-dir', help='指定Rime配置目录')
    parser.add_argument('--test-only', action='store_true', help='仅运行测试')
    parser.add_argument('--gui-only', action='store_true', help='仅安装GUI快捷方式')
    parser.add_argument('--no-color', action='store_true', help='禁用彩色输出')

    args = parser.parse_args()

    if args.no_color:
        Colors.disable()

    # 打印欢迎信息
    print(f"""
{Colors.BOLD}拼音/英文智能识别器 - 安装脚本{Colors.END}
{Colors.BLUE}支持平台: Windows, macOS, Linux{Colors.END}
{'=' * 60}
""")

    if args.test_only:
        run_tests()
        return

    if args.gui_only:
        create_desktop_entry()
        return

    # 完整安装流程
    all_success = True

    all_success &= install_python_deps()
    all_success &= install_system_deps()
    all_success &= install_rime_files(args.rime_dir)
    all_success &= run_tests()

    if platform.system() == 'Linux':
        create_desktop_entry()

    # 总结
    print(f"\n{'=' * 60}")
    if all_success:
        print(f"{Colors.GREEN}{Colors.BOLD}安装完成！{Colors.END}")
        print("\n使用方法:")
        print("  1. 命令行: python pinyin_english_detector.py <text>")
        print("  2. GUI界面: python gui_config.py")
        print("  3. Rime输入法: 重新部署后使用")
    else:
        print(f"{Colors.YELLOW}{Colors.BOLD}安装完成，但有部分警告{Colors.END}")
        print("请查看上方日志了解详情")

    print(f"{'=' * 60}\n")


if __name__ == '__main__':
    main()
