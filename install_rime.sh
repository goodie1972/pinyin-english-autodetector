#!/bin/bash
#
# Rime 拼音/英文自动识别输入法安装脚本
# 支持: Linux, macOS, Windows (Git Bash)
#

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印信息
info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检测操作系统
detect_os() {
    case "$(uname -s)" in
        Linux*)     OS=Linux;;
        Darwin*)    OS=Mac;;
        CYGWIN*)    OS=Windows;;
        MINGW*)     OS=Windows;;
        MSYS*)      OS=Windows;;
        *)          OS="UNKNOWN";;
    esac
    info "检测到操作系统: $OS"
}

# 获取Rime配置目录
get_rime_dir() {
    if [ "$OS" = "Mac" ]; then
        RIME_DIR="$HOME/Library/Rime"
    elif [ "$OS" = "Linux" ]; then
        if [ -d "$HOME/.config/ibus/rime" ]; then
            RIME_DIR="$HOME/.config/ibus/rime"
        elif [ -d "$HOME/.config/fcitx/rime" ]; then
            RIME_DIR="$HOME/.config/fcitx/rime"
        elif [ -d "$HOME/.local/share/fcitx5/rime" ]; then
            RIME_DIR="$HOME/.local/share/fcitx5/rime"
        else
            RIME_DIR="$HOME/.config/ibus/rime"
        fi
    elif [ "$OS" = "Windows" ]; then
        RIME_DIR="$APPDATA/Rime"
    else
        error "不支持的操作系统"
        exit 1
    fi

    info "Rime配置目录: $RIME_DIR"
}

# 创建Rime目录
create_rime_dir() {
    if [ ! -d "$RIME_DIR" ]; then
        info "创建Rime配置目录..."
        mkdir -p "$RIME_DIR"
    fi

    # 创建lua目录
    if [ ! -d "$RIME_DIR/lua" ]; then
        mkdir -p "$RIME_DIR/lua"
    fi
}

# 复制文件
copy_files() {
    info "复制配置文件..."

    # 获取脚本所在目录
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    RIME_SRC="$SCRIPT_DIR/rime"

    # 检查源文件是否存在
    if [ ! -d "$RIME_SRC" ]; then
        error "找不到Rime配置文件目录: $RIME_SRC"
        exit 1
    fi

    # 复制schema文件
    if [ -f "$RIME_SRC/pinyin_detector.schema.yaml" ]; then
        cp "$RIME_SRC/pinyin_detector.schema.yaml" "$RIME_DIR/"
        info "已复制: pinyin_detector.schema.yaml"
    fi

    # 复制lua文件
    if [ -f "$RIME_SRC/pinyin_detector.lua" ]; then
        cp "$RIME_SRC/pinyin_detector.lua" "$RIME_DIR/lua/"
        info "已复制: pinyin_detector.lua"
    fi

    if [ -f "$RIME_SRC/pinyin_detector_processor.lua" ]; then
        cp "$RIME_SRC/pinyin_detector_processor.lua" "$RIME_DIR/lua/"
        info "已复制: pinyin_detector_processor.lua"
    fi
}

# 更新default.yaml配置
update_default_config() {
    local DEFAULT_FILE="$RIME_DIR/default.custom.yaml"

    info "更新Rime默认配置..."

    # 检查是否已配置
    if [ -f "$DEFAULT_FILE" ] && grep -q "pinyin_detector" "$DEFAULT_FILE" 2>/dev/null; then
        warn "配置已存在，跳过更新"
        return 0
    fi

    # 创建或追加配置
    cat >> "$DEFAULT_FILE" << 'EOF'

# 拼音/英文自动识别输入法配置
patch:
  schema_list:
    - schema: pinyin_detector
    - schema: luna_pinyin
    - schema: luna_pinyin_simp
EOF

    info "已更新: default.custom.yaml"
}

# 部署Rime
deploy_rime() {
    info "重新部署Rime..."

    case "$OS" in
        Mac)
            if command -v squirrel >/dev/null 2>&1; then
                squirrel --reload
            else
                warn "请手动重新部署Rime（点击输入法菜单->重新部署）"
            fi
            ;;
        Linux)
            if command -v ibus-daemon >/dev/null 2>&1; then
                ibus restart 2>/dev/null || true
            elif command -v fcitx5 >/dev/null 2>&1; then
                fcitx5-remote -r 2>/dev/null || true
            elif command -v fcitx >/dev/null 2>&1; then
                fcitx-remote -r 2>/dev/null || true
            fi
            warn "请手动重新部署Rime输入法"
            ;;
        Windows)
            warn "Windows用户请手动重新部署Rime（右键点击任务栏图标->重新部署）"
            ;;
    esac
}

# 打印使用说明
print_usage() {
    echo ""
    echo "========================================"
    echo "  拼音/英文自动识别输入法 安装完成"
    echo "========================================"
    echo ""
    echo "使用说明:"
    echo "  1. 切换到'拼音英文自动识别'输入法方案"
    echo "  2. 输入英文单词（如'hello'）将自动识别并上屏"
    echo "  3. 输入拼音（如'nihao'）将显示中文候选"
    echo ""
    echo "快捷键:"
    echo "  Ctrl+`    - 切换输入法方案"
    echo "  Shift     - 临时切换中英文"
    echo ""
    echo "配置文件位置:"
    echo "  $RIME_DIR"
    echo ""
    echo "如需卸载，请删除以下文件:"
    echo "  - $RIME_DIR/pinyin_detector.schema.yaml"
    echo "  - $RIME_DIR/lua/pinyin_detector*.lua"
    echo "  - $RIME_DIR/default.custom.yaml (移除相关配置)"
    echo ""
}

# 主函数
main() {
    echo "========================================"
    echo "  Rime 拼音/英文自动识别输入法 安装器"
    echo "========================================"
    echo ""

    detect_os
    get_rime_dir
    create_rime_dir
    copy_files
    update_default_config
    deploy_rime
    print_usage

    info "安装完成!"
}

# 运行主函数
main
