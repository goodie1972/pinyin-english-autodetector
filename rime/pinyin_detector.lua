-- 拼音/英文智能识别处理器 for Rime
-- 作者: Claude Code
-- 版本: 1.1.0
-- 功能: 自动判断输入是拼音还是英文，智能切换输入模式

-- 拼音音节表（完整）
local initials = {
    'b', 'p', 'm', 'f', 'd', 't', 'n', 'l',
    'g', 'k', 'h', 'j', 'q', 'x',
    'zh', 'ch', 'sh', 'r', 'z', 'c', 's', 'y', 'w'
}

local finals = {
    'a', 'o', 'e', 'i', 'u', 'v',
    'ai', 'ei', 'ui', 'ao', 'ou', 'iu', 'ie', 've', 'er',
    'an', 'en', 'in', 'un', 'vn',
    'ang', 'eng', 'ing', 'ong',
    'ia', 'iao', 'ian', 'iang', 'iong',
    'ua', 'uo', 'uai', 'uan', 'uang', 'ong',
    'ue', 'uan', 'un'
}

local whole_syllables = {
    'zhi', 'chi', 'shi', 'ri', 'zi', 'ci', 'si',
    'yi', 'wu', 'yu', 'ye', 'yue', 'yuan', 'yin', 'yun', 'ying'
}

-- 英文词典（常用技术词汇）
local english_words = {
    -- 基础词汇
    ['hello'] = true, ['world'] = true, ['python'] = true, ['java'] = true,
    ['javascript'] = true, ['code'] = true, ['program'] = true, ['software'] = true,
    ['hardware'] = true, ['computer'] = true, ['server'] = true, ['client'] = true,
    ['database'] = true, ['data'] = true, ['file'] = true, ['user'] = true,
    ['system'] = true, ['network'] = true, ['web'] = true, ['app'] = true,
    ['api'] = true, ['interface'] = true, ['function'] = true, ['method'] = true,
    ['class'] = true, ['object'] = true, ['variable'] = true, ['string'] = true,
    ['array'] = true, ['list'] = true, ['map'] = true, ['set'] = true,
    ['development'] = true, ['programming'] = true, ['coding'] = true, ['debug'] = true,
    ['test'] = true, ['testing'] = true, ['deploy'] = true, ['deployment'] = true,
    ['production'] = true, ['environment'] = true, ['version'] = true, ['git'] = true,
    ['github'] = true, ['docker'] = true, ['kubernetes'] = true, ['cloud'] = true,
    ['aws'] = true, ['azure'] = true, ['gcp'] = true, ['linux'] = true,
    ['windows'] = true, ['macos'] = true, ['ios'] = true, ['android'] = true,
    ['html'] = true, ['css'] = true, ['json'] = true, ['xml'] = true,
    ['yaml'] = true, ['sql'] = true, ['bash'] = true, ['shell'] = true,
    ['terminal'] = true, ['console'] = true, ['editor'] = true, ['ide'] = true,
    ['vscode'] = true, ['vim'] = true, ['emacs'] = true, ['sublime'] = true,
    ['config'] = true, ['setting'] = true, ['option'] = true, ['feature'] = true,
    ['bug'] = true, ['issue'] = true, ['error'] = true, ['warning'] = true,
    ['fix'] = true, ['update'] = true, ['upgrade'] = true, ['install'] = true,
    ['download'] = true, ['upload'] = true, ['import'] = true, ['export'] = true,
    ['input'] = true, ['output'] = true, ['process'] = true, ['thread'] = true,
    ['lock'] = true, ['sync'] = true, ['async'] = true, ['cache'] = true,
    ['memory'] = true, ['disk'] = true, ['storage'] = true, ['driver'] = true,
    ['device'] = true, ['port'] = true, ['socket'] = true, ['protocol'] = true,
    ['format'] = true, ['schema'] = true, ['model'] = true, ['entity'] = true,
    ['attribute'] = true, ['query'] = true, ['command'] = true, ['request'] = true,
    ['response'] = true, ['event'] = true, ['callback'] = true, ['promise'] = true,
    ['manager'] = true, ['service'] = true, ['controller'] = true, ['handler'] = true,
    ['provider'] = true, ['factory'] = true, ['builder'] = true, ['adapter'] = true,
    ['proxy'] = true, ['wrapper'] = true, ['helper'] = true, ['util'] = true,
    ['common'] = true, ['core'] = true, ['base'] = true, ['main'] = true,
    ['index'] = true, ['home'] = true, ['start'] = true, ['end'] = true,
    ['begin'] = true, ['finish'] = true, ['stop'] = true, ['pause'] = true,
    ['resume'] = true, ['restart'] = true, ['reload'] = true, ['refresh'] = true,
    ['reset'] = true, ['restore'] = true, ['backup'] = true, ['recover'] = true,
    ['save'] = true, ['load'] = true, ['read'] = true, ['write'] = true,
    ['open'] = true, ['close'] = true, ['create'] = true, ['delete'] = true,
    ['remove'] = true, ['add'] = true, ['insert'] = true, ['append'] = true,
    ['prepend'] = true, ['push'] = true, ['pop'] = true, ['shift'] = true,
    ['unshift'] = true, ['slice'] = true, ['splice'] = true, ['split'] = true,
    ['join'] = true, ['concat'] = true, ['merge'] = true, ['extend'] = true,
    ['implement'] = true, ['extend'] = true, ['inherit'] = true, ['override'] = true,
    ['overload'] = true, ['abstract'] = true, ['virtual'] = true, ['static'] = true,
    ['public'] = true, ['private'] = true, ['protected'] = true, ['internal'] = true,
    ['external'] = true, ['global'] = true, ['local'] = true, ['const'] = true,
    ['let'] = true, ['var'] = true, ['function'] = true, ['def'] = true,
    ['void'] = true, ['null'] = true, ['nil'] = true, ['none'] = true,
    ['true'] = true, ['false'] = true, ['boolean'] = true, ['number'] = true,
    ['integer'] = true, ['float'] = true, ['double'] = true, ['decimal'] = true,
    ['char'] = true, ['byte'] = true, ['bit'] = true, ['word'] = true,
    ['long'] = true, ['short'] = true, ['signed'] = true, ['unsigned'] = true,
    ['auto'] = true, ['register'] = true, ['volatile'] = true, ['mutable'] = true,
    ['immutable'] = true, ['final'] = true, ['sealed'] = true, ['partial'] = true,
    ['dynamic'] = true, ['weak'] = true, ['strong'] = true, ['unowned'] = true,
    ['optional'] = true, ['required'] = true, ['lazy'] = true, ['eager'] = true,
}

-- 构建拼音词典
local pinyin_dict = {}
for _, initial in ipairs(initials) do
    for _, final in ipairs(finals) do
        pinyin_dict[initial .. final] = true
    end
end
for _, syllable in ipairs(whole_syllables) do
    pinyin_dict[syllable] = true
end

-- 检查是否是有效拼音音节
local function is_valid_pinyin(s)
    return pinyin_dict[s] ~= nil
end

-- 拼音切分算法
local function segment_pinyin(text)
    local n = #text
    local dp = {}
    dp[0] = {0, {}}

    for i = 1, n do
        dp[i] = {999, {}}
        for j = math.max(0, i - 6), i - 1 do
            local substr = string.sub(text, j + 1, i)
            if is_valid_pinyin(substr) and dp[j][1] < 999 then
                local new_count = dp[j][1] + 1
                if new_count < dp[i][1] then
                    local new_seg = {}
                    for _, v in ipairs(dp[j][2]) do table.insert(new_seg, v) end
                    table.insert(new_seg, substr)
                    dp[i] = {new_count, new_seg}
                end
            end
        end
    end

    if dp[n][1] < 999 then
        return dp[n][2], 1.0
    else
        -- 找到最长匹配前缀
        for i = n, 0, -1 do
            if dp[i][1] < 999 then
                return dp[i][2], i / n
            end
        end
    end
    return {}, 0.0
end

-- 计算拼音评分
local function calc_pinyin_score(text)
    local syllables, coverage = segment_pinyin(text)
    if coverage < 1.0 then
        return coverage * 0.5
    end

    -- 元音密度检查
    local vowels = 'aeiouv'
    local vowel_count = 0
    for i = 1, #text do
        local c = string.sub(text, i, i)
        if string.find(vowels, c, 1, true) then
            vowel_count = vowel_count + 1
        end
    end
    local vowel_ratio = vowel_count / #text

    local vowel_score = 1.0
    if vowel_ratio < 0.25 or vowel_ratio > 0.65 then
        vowel_score = 0.7
    end

    return vowel_score
end

-- 计算英文评分
local function calc_english_score(text)
    -- 词典匹配
    if english_words[text] then
        return 1.0
    end

    -- 前缀匹配
    local prefix_matches = 0
    for word, _ in pairs(english_words) do
        if string.sub(word, 1, #text) == text then
            prefix_matches = prefix_matches + 1
        end
    end

    local prefix_score = 0.2
    if prefix_matches >= 5 then
        prefix_score = 0.7
    elseif prefix_matches >= 1 then
        prefix_score = 0.5
    end

    -- 常见双字母组合
    local common_bigrams = {
        th=true, he=true, in=true, er=true, an=true, re=true,
        on=true, at=true, en=true, nd=true, ti=true, es=true,
        or=true, te=true, of=true, ed=true, is=true, it=true,
        al=true, ar=true, st=true, to=true, nt=true, ng=true,
        se=true, ha=true, as=true, ou=true, io=true, le=true
    }

    local bigram_count = 0
    for i = 1, #text - 1 do
        local bigram = string.sub(text, i, i + 1)
        if common_bigrams[bigram] then
            bigram_count = bigram_count + 1
        end
    end

    local bigram_ratio = bigram_count / math.max(#text - 1, 1)
    local bigram_score = 0.6
    if bigram_ratio >= 0.3 then
        bigram_score = 0.6 + (bigram_ratio - 0.3) * 0.5
    else
        bigram_score = bigram_ratio * 2
    end

    return math.min(math.max(prefix_score, bigram_score * 0.7), 0.9)
end

-- 主检测函数
local function detect(text)
    text = string.lower(text)

    -- 纯数字
    if string.match(text, '^%d+$') then
        return 'numeric', 1.0
    end

    -- 非纯字母
    if not string.match(text, '^[a-z]+$') then
        return 'mixed', 0.5
    end

    local pinyin_score = calc_pinyin_score(text)
    local english_score = calc_english_score(text)

    local total = pinyin_score + english_score
    local pinyin_conf = pinyin_score / total
    local english_conf = english_score / total

    if pinyin_score > english_score * 1.2 then
        return 'pinyin', pinyin_conf
    elseif english_score > pinyin_score * 1.2 then
        return 'english', english_conf
    else
        if pinyin_score >= english_score then
            return 'pinyin', pinyin_conf * 0.8
        else
            return 'english', english_conf * 0.8
        end
    end
end

-- Rime处理器主函数
local function detect_and_switch(key, env)
    local ctx = env.context
    local input = ctx.input

    -- 输入太短时不判断（减少误触发）
    if #input < 3 then
        return 2  -- kNoop
    end

    -- 调用识别引擎
    local script_type, confidence = detect(input)

    -- 记录日志（调试用）
    -- log.info("PinyinDetector: input=" .. input .. " type=" .. script_type .. " confidence=" .. confidence)

    -- 高置信度英文判断时，自动切换ASCII模式
    if script_type == "english" and confidence > 0.7 then
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
    detect = detect,
    detect_and_switch = detect_and_switch,
}