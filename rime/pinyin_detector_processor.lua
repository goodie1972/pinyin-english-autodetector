-- 拼音/英文智能识别处理器 for Rime
-- 作者: Claude Code
-- 功能: 自动判断输入是拼音还是英文，智能切换输入模式

local pinyin_detector = require("pinyin_detector_core")

-- 处理器主函数
local function detect_and_switch(key, env)
    local ctx = env.context
    local input = ctx.input

    -- 输入太短时不判断（减少误触发）
    if #input < 2 then
        return 2  -- kNoop
    end

    -- 调用识别引擎
    local result = pinyin_detector.detect(input)

    -- 记录日志（调试用）
    -- log.info("PinyinDetector: input=" .. input .. " type=" .. result.type .. " confidence=" .. result.confidence)

    -- 高置信度英文判断时，自动切换ASCII模式
    if result.type == "english" and result.confidence > 0.7 then
        -- 提交当前输入并切换到ASCII模式
        ctx:commit_text(input)
        ctx:clear()
        ctx:set_option("ascii_mode", true)
        return 1  -- kAccepted
    end

    return 2  -- kNoop
end

-- 导出函数
return {
    detect_and_switch = detect_and_switch,
}
