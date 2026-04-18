-- 拼音/英文智能识别处理器 for Rime (入口文件)
-- 版本: 1.1.0

-- 引入核心检测模块
local core = require("pinyin_detector")

-- 处理器主函数
local function detect_and_switch(key, env)
    return core.detect_and_switch(key, env)
end

-- 导出函数
return {
    detect_and_switch = detect_and_switch,
}
