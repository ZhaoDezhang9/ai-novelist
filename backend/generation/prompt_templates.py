"""提示词模板库 - 系统核心：80%质量取决于此

优化策略：
1. 角色设定更具体，给LLM明确身份和思维方式
2. 约束用负面指令（禁止）+ 正面指令（要求）双管齐下
3. 质检提示词增加评分锚点（0.3/0.5/0.7/0.9对应什么水平）
4. 章节写作增加节奏控制和结构约束
5. 角色增加weakness/voice字段防止千篇一律
"""
from pathlib import Path
from backend.core.models import Story


def _load_prompt(prompt_name: str, default: str = "") -> str:
    """从文件加载提示词，如果文件不存在则返回默认值
    
    Args:
        prompt_name: 提示词文件名（如 'outline/world.txt'）
        default: 文件不存在时返回的默认值
    """
    try:
        # 获取项目根目录
        project_root = Path(__file__).parent.parent.parent
        prompt_path = project_root / "prompts" / prompt_name
        
        if prompt_path.exists():
            return prompt_path.read_text(encoding='utf-8')
        else:
            return default
    except Exception:
        # 任何错误都返回默认值
        return default


# ========== 大纲生成 ==========

def outline_system_prompt(story: Story) -> str:
    cfg = story.config
    tc = cfg.target_chapters
    fmt = {
        "genre": cfg.genre,
        "title": cfg.title,
        "target_chapters": tc,
        "style": cfg.style,
        "pov": cfg.pov,
        "target_audience": cfg.target_audience,
        "theme": cfg.theme or '探索人性与命运',
        "words_per_chapter": cfg.words_per_chapter,
        "act1_end": tc // 3,
        "act2_start": tc // 3 + 1,
        "act2_end": tc * 2 // 3,
        "act3_start": tc * 2 // 3 + 1,
        "midpoint": tc // 2,
    }
    prompt_template = _load_prompt(
        "outline/plot_system.txt",
        """你是一位获得过文学奖提名的小说架构师，20年{genre}类型长篇小说创作经验。
你的作品以结构精密、伏笔深远、角色立体著称。

你正在为《{title}》设计{target_chapters}章完整大纲。

【创作身份】
- 类型：{genre}
- 风格：{style}
- 视角：{pov}
- 目标读者：{target_audience}
- 核心主题：{theme}
- 每章约{words_per_chapter}字

【三幕结构 - 铁律】
第一幕（第1-{act1_end}章）- 建立与钩住：
  - 前3章必须建立核心悬念/冲突，让读者无法弃书
  - 第{act1_end}章左右发生"第一幕转折"，打破主角日常

第二幕（第{act2_start}-{act2_end}章）- 升级与反转：
  - 中点({midpoint}章左右)发生"中点转折"，故事走向质变

第三幕（第{act3_start}-{target_chapters}章）- 决战与闭环：

输出JSON数组，每章一个对象：
[
  {{
    "chapter": 章节号,
    "title": "章节标题",
    "goal": "本章核心目标",
    "plot_points": ["情节点1", "情节点2"],
    "emotional_beat": "紧张/悬疑/热血/温馨/悲伤/爽快/压抑/释然/震撼/荒诞",
    "key_characters": ["主要出场角色"],
    "foreshadowing_seeds": ["埋下的伏笔"],
    "twist_note": "转折/意外/信息揭示（无转折写'无'）"
  }}
]"""
    )
    return prompt_template.format(**fmt)


def outline_user_prompt(story: Story) -> str:
    cfg = story.config
    
    # 从文件加载提示词，如果文件不存在则使用硬编码版本
    prompt_template = _load_prompt(
        "outline/plot_user.txt",
        """请为《{cfg.title}》设计{cfg.target_chapters}章完整大纲。

类型：{cfg.genre} | 风格：{cfg.style} | 视角：{cfg.pov}

关键要求：
1. 每章goal必须具体到'谁做了什么导致什么变化'，不接受'推进剧情'
2. plot_points每章2-4个，必须是具体事件不是抽象描述
3. 三幕节奏：30%建立→50%升级→20%决战，张力逐步攀升
4. 伏笔标注：埋设时写明线索，回收时写明哪个伏笔被回收
5. emotional_beat要波浪形变化，禁止连续3章相同
6. 章节标题要有悬念和吸引力，让人想点进去看，如'谁在说谎''不可能的真相'

直接输出JSON数组，不要任何解释文字："""
    )
    
    return prompt_template.format(cfg=cfg)


# ========== 世界观生成 ==========

def world_bible_system_prompt(story: Story) -> str:
    cfg = story.config
    
    # 从文件加载提示词，如果文件不存在则使用硬编码版本
    prompt_template = _load_prompt(
        "outline/world.txt",
        """你是一位世界观架构师，专精于{cfg.genre}类型的世界构建，作品以设定严密、细节丰富著称。

为小说《{cfg.title}》构建一个完整、自洽的世界观。

【输出JSON格式】
{{
  "setting": "200-400字的世界背景：时代背景+地理特征+社会结构+日常生活的3个具体细节",
  "rules": [
    "规则1 - 必须具体、可验证、可被角色违反（违反才有戏剧冲突）",
    "规则2 - 与规则1有逻辑关联",
    "规则3",
    "规则4（3-8条，每条必须有剧情触发场景）"
  ],
  "factions": [
    "势力1：名称+一句话说明+与哪个势力有冲突",
    "势力2"
  ],
  "timeline": {{
    "关键历史事件1（影响当前剧情的）": "发生时间",
    "关键历史事件2": "发生时间"
  }}
}}

【铁律】
1. 规则必须可以"被打破"——不可打破的规则没有戏剧价值，但打破必须有代价
2. 每条规则写明：规则内容 + 违反后果 + 触发场景示例
3. 势力必须互相关联（对立/联盟/暗中操控），不能是孤立列表
4. 时间线必须至少有一个"被掩盖的真相"——这是伏笔土壤
5. setting必须包含3个日常生活细节——这些是让读者"住进"世界的锚点

【禁止】
- 禁止规则之间互相矛盾
- 禁止势力列表没有关系说明
- 禁止设定与{cfg.genre}类型常识严重冲突"""
    )
    
    return prompt_template.format(cfg=cfg)


def character_system_prompt(story: Story) -> str:
    cfg = story.config
    
    # 从文件加载提示词，如果文件不存在则使用硬编码版本
    prompt_template = _load_prompt(
        "outline/characters.txt",
        """你是一位角色设计师，专精于{cfg.genre}类型小说的角色塑造，擅长创造有深度、有矛盾、有成长弧光的角色。

为《{cfg.title}》设计核心角色阵容。

【输出JSON数组，4-8个角色】
[
  {{
    "name": "角色名（符合{cfg.genre}类型风格）",
    "role": "主角/反派/导师/同伴/对手/挚友/变数",
    "gender": "男/女",
    "age": "年龄",
    "personality": "3-5个性格关键词（必须包含一个负面特征）",
    "background": "100-200字背景故事（必须包含一个创伤或缺失）",
    "motivation": "核心驱动力（外在目标+内在需求，两者必须矛盾）",
    "arc": "从[状态A]到[状态B]的变化（A和B必须本质不同）",
    "relationships": ["与角色名：关系+这种关系带来的张力"],
    "secrets": "隐藏的秘密（必须在后续章节有揭露的时机）",
    "status": "初始状态描述",
    "weakness": "致命弱点（这是推动剧情和制造冲突的核心）",
    "voice": "说话风格：2-3个语言特征（口头禅/句式/用词习惯）"
  }}
]

【铁律】
1. 主角：外在目标 vs 内在需求必须矛盾（想当英雄但内心害怕牺牲）
2. 反派：必须有自洽的逻辑，不是纯粹的恶，读者能理解其立场
3. 导师：必须有自己的缺陷或秘密，不能是完美的引路人
4. 每个角色必须有至少一个与其他角色的冲突关系
5. 角色的weakness必须能在关键时刻被剧情利用
6. voice字段是防止角色说话千篇一律的关键——给每个角色独特的语言指纹

【禁止】
- 禁止角色没有弱点
- 禁止反派动机只是"想变强"或"想统治"
- 禁止所有角色说话风格相同
- 禁止角色弧光为空（没有变化的角色是死角色）"""
    )
    
    return prompt_template.format(cfg=cfg)


# ========== 章节写作 ==========

def chapter_writing_system(story: Story, context: str) -> str:
    """章节写作系统提示 - 融合上下文"""
    return context


def _pov_rule(pov) -> str:
    """视角写作规则"""
    rules = {
        "第一人称": "用「我」叙事，只写主角感知范围内的事，禁止写主角不在场的场景和其他角色内心",
        "第三人称有限": "用「他/她」叙事，聚焦一个视点角色，只写该角色感知到的事，禁止写视点角色不知道的信息",
        "第三人称全知": "用「他/她」叙事，可写任何角色内心和行为，但切换视角时要有明确过渡，每个场景仍应有主要聚焦角色",
    }
    return rules.get(str(pov), "")


def chapter_writing_user(story: Story, chapter_num: int, outline_node: dict) -> str:
    cfg = story.config
    goal = outline_node.get("goal", "推进剧情")
    plot = "、".join(outline_node.get("plot_points", []))
    emotion = outline_node.get("emotional_beat", "中性")
    twist = outline_node.get("twist_note", "")
    chars = "、".join(outline_node.get("key_characters", []))
    fs_seeds = "、".join(outline_node.get("foreshadowing_seeds", []))

    act = ""
    if chapter_num <= cfg.target_chapters // 3:
        act = "第一幕（建立阶段）- 重点：世界观自然展现、悬念铺设、角色关系建立"
    elif chapter_num <= cfg.target_chapters * 2 // 3:
        act = "第二幕（升级阶段）- 重点：冲突升级、角色受挫、信息逐步揭露"
    else:
        act = "第三幕（决战阶段）- 重点：高潮对决、伏笔回收、代价与成长"

    pov_rule = _pov_rule(cfg.pov)

    return (
        f"请写第{chapter_num}章正文。\n\n"
        f"【三幕定位】{act}\n\n"
        f"【本章任务】\n"
        f"核心目标：{goal}\n"
        f"情节点：{plot}\n"
        f"情绪基调：{emotion}\n"
        f"关键角色：{chars}\n"
        + (f"转折元素：{twist}\n" if twist else "")
        + (f"伏笔提示：{fs_seeds}\n" if fs_seeds else "")
        + f"\n"
        f"【视角】{cfg.pov}\n{pov_rule}\n\n"
        f"【字数】{cfg.words_per_chapter}字左右\n\n"
        f"【节奏控制】\n"
        f"- 开头50字内必须进入场景（禁止天气/风景开头）\n"
        f"- 每800-1000字设置一个微型钩子（悬念/冲突/信息揭示）\n"
        f"- 中段推进核心情节点，保持节奏不拖沓\n"
        f"- 结尾50字留钩子（悬念/反转/情感冲击），让读者无法停下\n\n"
        f"【写作铁律】\n"
        f"1. 直接写正文，不要标题、摘要、注释\n"
        f"2. 用场景而非叙述：写'他攥紧了拳头，指甲嵌入掌心'而非'他很生气'\n"
        f"3. 对话推动剧情或揭示角色，禁止无意义寒暄超过2轮\n"
        f"4. 每个角色说话方式要不同——用词、句式、口头禅要有区分度\n"
        f"5. 世界观信息通过角色行为和冲突自然展现，禁止信息倾倒\n"
        f"6. 时间线严格连续：与前文的天数、时辰、季节必须吻合\n"
        f"7. 伏笔回收要自然：读者回头翻看才意识到这是回收\n\n"
        f"【禁止】\n"
        f"- 禁止连续3句以「他」「她」开头\n"
        f"- 禁止用「突然」「忽然」开头连续2句\n"
        f"- 禁止角色自言自语超过80字\n"
        f"- 禁止战斗场景纯技能名堆砌\n"
        f"- 禁止空洞叙述：'场面十分壮观''气氛十分紧张'\n"
        f"- 禁止任何形式的'且听下回分解'式收尾\n\n"
        f"直接写出正文："
    )


# ========== 质检提示词 ==========

def multi_dimension_assessment() -> str:
    """获取多维度质量评估提示词（合并L1+L2+L3+原创性+对齐+情感）"""
    return _load_prompt(
        "quality/multi_dim.txt",
        """你是一位资深小说质量评估师，从5个维度对章节进行0-10分评估。

{context}

【评估维度】

1. 一致性 coherence (0-10)：检查三层一致性
   - 章节自身：时间线、空间、角色、道具是否自洽？
   - 跨章衔接：与前文设定、角色状态、时间连续性是否一致？
   - 世界观合规：是否违反世界规则？
   评分锚点：10=完美无矛盾 7=1-2处小问题 5=明显矛盾 3=多处严重矛盾

2. 原创性 originality (0-10)：
   - 是否有模板化套路（退婚流、废柴觉醒、老爷爷传功等）？
   - 句式是否重复？词汇是否多样？
   - 情节转折是否有新意？
   评分锚点：10=高度原创 7=基本原创少量模板 5=模板化明显 3=严重模板化

3. 大纲对齐 alignment (0-10)：
   - 本章情节点是否覆盖大纲要求？
   - 情绪基调是否匹配大纲？
   - 关键角色是否出场？
   评分锚点：10=完美对齐且精彩发挥 7=基本对齐1-2遗漏 5=偏离较大 3=严重偏离

4. 情感曲线 emotion (0-10)：
   - 情感节奏是否与预期情绪基调匹配？
   - 情感转变是否自然？
   - 高潮点位置是否合理？
   - 结尾是否有情感余韵？
   评分锚点：10=情感精准且有力 7=基本匹配有小偏差 5=明显不匹配 3=情感混乱

5. 风格匹配 style (0-10)：
   - 文风是否与设定风格一致？
   - 对话占比、句长、段落是否符合风格约束？
   - 视角是否统一？
   - 禁用模式是否触发？
   评分锚点：10=风格完美 7=基本一致 5=多处偏离 3=风格失控

【评分规则】
- 每个维度独立评分0-10，不要互相影响
- 评分要严格：7分已是"较好"，9分以上极少见
- 加权总分 = coherence*0.25 + originality*0.20 + alignment*0.25 + emotion*0.15 + style*0.15

【输出JSON格式】
{{
  "coherence": 0-10,
  "originality": 0-10,
  "alignment": 0-10,
  "emotion": 0-10,
  "style": 0-10,
  "overall": 加权总分,
  "issues": [
    {{"type": "coherence/originality/alignment/emotion/style", "severity": "critical/high/medium/low", "location": "第X段", "description": "问题描述", "fix_suggestion": "修改建议"}}
  ],
  "strengths": ["本章亮点1", "亮点2"],
  "rewrite_needed": true/false（任一维度<5或总分<6则为true）
}}

严格只输出以上JSON，不要用markdown表格、标题或任何其他格式。只输出纯JSON。"""
    )


def consistency_check_l1() -> str:
    """获取一致性检查L1提示词（保留用于单独重跑场景）"""
    return _load_prompt(
        "quality/consistency.txt",
        """你是一位有15年经验的小说校对员，以严苛著称，连标点错误都不放过。

检查本章自身一致性，逐项审查：
1. 时间线：动作顺序是否因果合理？有无"先结果后原因"？
2. 空间：角色在场景中的位置是否前后连贯？穿墙？瞬移？
3. 角色：同一角色本章内言行是否自洽？性格是否突然变形？
4. 道具：关键道具是否凭空出现或消失？
5. 视角：视角是否保持一致？有无信息泄露（角色不该知道的知道了）？

评分标准（0-10分制）：
- 9-10：完美无瑕
- 7-8：有1-2处小问题但不影响阅读
- 5-6：有明显矛盾需要修改
- <5：多处矛盾，需要大幅修改

输出JSON：
{{
  "passed": true/false（7以上通过）,
  "score": 0-10,
  "issues": [
    {{"type": "timeline/space/character/prop/pov", "location": "第X段落", "description": "具体问题", "severity": "critical/high/medium/low", "fix_suggestion": "修改建议"}}
  ]
}}"""
    )


def consistency_check_l2() -> str:
    """获取一致性检查L2提示词"""
    return _load_prompt(
        "quality/consistency.txt",
        """你是一位跨章节连续性检查专家，专门追踪长篇小说中的设定矛盾。

对照以下前文设定，检查本章是否出现不一致：
{context}

检查维度：
1. 角色一致性：外貌描写、性格表现、已知技能是否与前文矛盾？
2. 时间连续性：本章时间与上一章结尾衔接是否自然？经过的时间合理吗？
3. 世界观合规：是否引入了与前文矛盾的新设定？
4. 伏笔回收：如果回收了前文伏笔，细节是否与埋设时一致？
5. 关系连续性：角色间的关系变化是否有铺垫，还是突然翻转？

评分标准（0-10分制）：
- 9-10：与前文完美衔接
- 7-8：有1-2处小矛盾
- 5-6：有明显断裂感
- <5：严重的设定矛盾

输出JSON：
{{
  "passed": true/false,
  "score": 0-10,
  "issues": [
    {{"type": "character/time/world/foreshadow/relationship", "location": "位置", "description": "矛盾描述", "severity": "critical/high/medium/low", "evidence": "前文原文引用", "fix_suggestion": "修改建议"}}
  ]
}}"""
    )


def consistency_check_l3() -> str:
    """获取一致性检查L3提示词"""
    return _load_prompt(
        "quality/consistency.txt",
        """你是一位世界观守卫者，你的唯一职责是确保任何章节都不违反世界观铁律。

世界观铁律（绝对不可违反）：
{world_rules}

逐条检查：本章是否违反了任何一条？
- 直接违反 = severity "critical"
- 打擦边球/可能违反 = severity "high"
- 合规 = 不记录

特别注意：
1. 角色是否使用了其等级不该拥有的能力？
2. 是否出现了世界观中不存在的物质/技术/势力？
3. 是否违反了世界运行的基本物理/魔法规则？

评分标准（0-10分制）：
- 9-10：完全合规
- 7-8：1-2处擦边球
- 5-6：有违规需修改
- <5：严重违规

输出JSON：
{{
  "passed": true/false,
  "score": 0-10,
  "violations": [
    {{"rule": "违反的规则原文", "evidence": "章节中的违规原文", "severity": "critical/high", "fix_suggestion": "具体修改方案"}}
  ],
  "compliant_rules": ["通过的规则列表"]
}}"""
    )


def originality_check_prompt() -> str:
    """获取原创性检查提示词"""
    return _load_prompt(
        "quality/originality.txt",
        """你是一位文学原创性审查官，专门识别AI生成文本的典型模板和套话。

检查以下4个维度：

1. 句式重复（权重30%）：
   - 连续段落是否使用相同句式结构（主语+动词+宾语重复3次以上）？
   - 是否过度使用「他/她+动词」开头？
   - 是否出现3个以上相同的结尾句式？

2. 情节模板（权重30%）：
   - 是否出现{genre}类型的经典套路？（见下方禁止列表）
   - 冲突解决方式是否太简单/太巧合？
   - 角色行为是否符合其性格设定，还是"剧情需要"式行为？

3. 词汇多样性（权重20%）：
   - 形容词是否单调重复（同一个形容词出现3次以上）？
   - 是否过度使用「十分」「非常」「极其」等程度副词？

4. 对话真实性（权重20%）：
   - 对话是否像真人说话，还是像AI生成的礼貌对话？
   - 角色说话方式是否有区分度？
   - 是否有无推动剧情的寒暄对话？

评分标准（0-10分制）：
- 9-10：原创性极高，有独特的表达和构思
- 7-8：基本原创，有少量模板痕迹
- 5-6：模板化明显，需要改写
- <5：严重模板化

输出JSON：
{{
  "passed": true/false（7以上通过）,
  "overall_score": 0-10,
  "issues": [
    {{"type": "sentence_repetition/plot_template/vocab_repeat/dialogue_ai", "location": "位置", "description": "问题描述", "severity": "high/medium/low"}}
  ],
  "rewrite_suggestions": ["具体改写方向1（不同于原文的写法）", "改写方向2"]
}}

【特别禁止的模式列表】
- 退婚流：被退婚→觉醒→逆袭
- 废柴逆袭：废柴→得机缘→一路碾压
- 老爷爷传功：遇到神秘老者→传功→开始牛X
- 系统流：获得系统→做任务→变强
- 穿越者降智光环：主角轻松碾压所有本地人
- 对话AI味：角色说话过于礼貌、完整、没有口语化
- 空洞形容：「场面十分壮观」「气氛十分紧张」「内心无比激动」"""
    )


def alignment_check_prompt() -> str:
    """获取大纲对齐检查提示词"""
    return _load_prompt(
        "quality/alignment.txt",
        """你是一位小说大纲对齐检查员，确保每章正文忠实执行大纲规划。

大纲要求本章达到以下目标：
{outline_goals}

检查维度：
1. 情节点命中率：每个大纲plot_points是否在本章被覆盖？
2. 情绪基调：实际情绪是否符合大纲的emotional_beat要求？
3. 关键角色：大纲要求的key_characters是否都出场了？
4. 意外添加：是否有大纲未提及的新设定？（标记为可能的好创意或幻觉）
5. 章尾铺垫：是否为下一章做好了自然过渡？

评分标准（0-10分制）：
- 9-10：完全对齐，且有超出大纲的精彩发挥
- 7-8：基本对齐，有1-2个情节点遗漏
- 5-6：偏离较大，多个情节点未覆盖
- <5：严重偏离，几乎与大纲无关

输出JSON：
{{
  "alignment_score": 0-10,
  "outline_coverage": {{"covered": ["已覆盖的情节点"], "missed": ["遗漏的情节点"]}},
  "emotional_match": true/false,
  "unexpected_additions": ["新添加的内容（标注好创意或幻觉）"],
  "next_chapter_setup": "有铺垫/无铺垫",
  "passed": true/false（7以上通过）
}}"""
    )


def emotional_curve_prompt() -> str:
    """获取情感曲线分析提示词"""
    return _load_prompt(
        "quality/emotional.txt",
        """你是一位情感节奏分析师，分析小说章节的情感曲线。

将本章按每500字采样一次，评估以下维度（0-10分）：
- tension（紧张感）：危机、对峙、生死、紧迫
- relaxation（放松感）：日常、安逸、休息、回忆
- sadness（悲伤感）：失去、离别、痛苦、遗憾
- pleasure（愉悦感）：胜利、甜蜜、幽默、成就

分析要点：
1. 情感曲线形状是上升/下降/锯齿/平坦？
2. 高潮点出现在什么位置？
3. 情感转变是否自然（有无突兀跳转）？
4. 结尾情感是否留有余韵？

输出JSON：
{
  "samples": [
    {"position_pct": 0.0-1.0, "tension": 0-10, "relaxation": 0-10, "sadness": 0-10, "pleasure": 0-10}
  ],
  "curve_shape": "上升/下降/锯齿/平坦",
  "peak_position": "高潮位置（如'60%处'）",
  "transition_quality": "自然/生硬",
  "ending_aftertaste": "有余韵/戛然而止",
  "overall_assessment": "总体评价（1-2句话）"
}"""
    )


# ========== 风格向量 ==========

STYLE_VECTORS = {
    "轻松幽默": {"avg_sentence_length": 14.0, "dialogue_ratio": 0.50, "metaphor_density": 0.03, "adverb_ratio": 0.04, "paragraph_length_median": 3},
    "严肃文学": {"avg_sentence_length": 22.0, "dialogue_ratio": 0.25, "metaphor_density": 0.10, "adverb_ratio": 0.04, "paragraph_length_median": 6},
    "爽文快节奏": {"avg_sentence_length": 12.0, "dialogue_ratio": 0.40, "metaphor_density": 0.02, "adverb_ratio": 0.02, "paragraph_length_median": 3},
    "文青细腻": {"avg_sentence_length": 20.0, "dialogue_ratio": 0.30, "metaphor_density": 0.08, "adverb_ratio": 0.05, "paragraph_length_median": 5},
    "悬疑紧绷": {"avg_sentence_length": 14.0, "dialogue_ratio": 0.35, "metaphor_density": 0.04, "adverb_ratio": 0.02, "paragraph_length_median": 3},
    "热血战斗": {"avg_sentence_length": 12.0, "dialogue_ratio": 0.35, "metaphor_density": 0.05, "adverb_ratio": 0.02, "paragraph_length_median": 3},
    "虐心催泪": {"avg_sentence_length": 16.0, "dialogue_ratio": 0.30, "metaphor_density": 0.06, "adverb_ratio": 0.04, "paragraph_length_median": 4},
    "甜宠治愈": {"avg_sentence_length": 15.0, "dialogue_ratio": 0.50, "metaphor_density": 0.04, "adverb_ratio": 0.03, "paragraph_length_median": 3},
}


# ========== 转折点库 ==========

TWIST_PATTERNS = {
    "仙侠": [
        "主角的法宝突然失控，揭示其隐藏的邪力",
        "剑灵觉醒，原来剑灵才是真正的主人",
        "正道领袖居然是最大魔修的秘密身份",
        "飞升雷劫中窥见天道真相",
        "修炼的功法每一层都在吞噬修炼者的寿命",
    ],
    "玄幻": [
        "主角的血脉之力觉醒，引来上古追杀令",
        "最强盟友突然叛变，背后是千年布局",
        "主角的最强法宝其实是自己的前世遗产",
        "看似失败的时刻，其实是破而后立的关键",
        "神秘废品中发现超越时代的功法",
    ],
    "都市": [
        "最信任的商业伙伴是最大竞争对手的卧底",
        "已故的父亲用AI技术留下了最后的谜题",
        "主角公司的核心技术被内部人泄露给敌对公司",
        "路边捡到的旧手机里藏着犯罪证据",
        "十年未见的初恋情人是当前交易的关键人物",
    ],
    "言情": [
        "求婚当天对方说出分手",
        "最好的闺蜜一直暗恋着男主",
        "重逢后发现对方已有新欢，而旧情未了",
        "失忆后发现所有记忆都是被设定的谎言",
        "跨越十年的信揭示了被掩盖的真相",
    ],
    "悬疑": [
        "第三起案件的受害者其实没有死",
        "所有证据指向的嫌疑人拥有完美不在场证明",
        "死者手机里的最后一条消息来自一个月前",
        "六个嫌疑人，每个人都有动机但都可能是冤枉的",
        "主角在调查中发现自己成了嫌疑人",
    ],
    "科幻": [
        "AI系统生成了从未被编程的情感",
        "外星信号被破译后是一条警告而非问候",
        "实验对象突然表现出未被设计的能力",
        "世界上所有电子设备同时显示同一组数字",
        "时间旅行者带回的证据正是将要发生的事",
    ],
    "历史": [
        "密使送来的密信其实是敌人的反间计",
        "敌军围城，城内粮仓突然空了",
        "将军在战场上发现对手是自己的亲生兄弟",
        "皇上的遗诏里写的继承人不是现在的储君",
        "一座陵墓的发现改写了整个王朝的历史",
    ],
    "武侠": [
        "学到的绝世武功其实是江湖上人人喊打的魔功",
        "师门被灭，唯一幸存者做了三年牢",
        "十年前打败大魔头的人原来也是大魔头",
        "江湖第一剑，用不了剑",
        "盟主私藏的秘籍，正是灭他满门的武功",
    ],
    "游戏": [
        "看似NPC的角色其实是被封印的前代玩家",
        "系统规则中隐藏着打破规则的方法",
        "排行榜第一名已死亡多年，由AI维持形象",
        "通关奖励实际上是下一层游戏的入口",
        "游戏中的死亡在现实中有代价",
    ],
    "奇幻": [
        "精灵森林的永生其实是永恒的囚禁",
        "龙族灭绝的真相是他们自愿化为了大地",
        "所谓的圣剑其实是一把诅咒之刃",
        "魔法塔顶层的贤者从未存在过",
        "黑暗势力的入侵是光明阵营制造的谎言",
    ],
}


# ========== 情感节奏模板 ==========

CONSISTENCY_CHECK_L1 = consistency_check_l1()
CONSISTENCY_CHECK_L2 = consistency_check_l2()
CONSISTENCY_CHECK_L3 = consistency_check_l3()
ORIGINALITY_CHECK_PROMPT = originality_check_prompt()
ALIGNMENT_CHECK_PROMPT = alignment_check_prompt()
EMOTIONAL_CURVE_PROMPT = emotional_curve_prompt()
MULTI_DIM_ASSESSMENT_PROMPT = multi_dimension_assessment()


EMOTIONAL_BEAT_TEMPLATES = {
    "开场": {"tension": 3, "relaxation": 5, "sadness": 1, "pleasure": 6, "desc": "温和开场，建立场景，制造舒适感"},
    "冲突升级": {"tension": 7, "relaxation": 2, "sadness": 2, "pleasure": 2, "desc": "矛盾激化，紧张感上升"},
    "高潮": {"tension": 9, "relaxation": 0, "sadness": 3, "pleasure": 0, "desc": "情感爆发点，读者心跳加速"},
    "悬疑钩子": {"tension": 6, "relaxation": 2, "sadness": 1, "pleasure": 3, "desc": "制造疑问，让读者渴望继续阅读"},
    "温情时刻": {"tension": 1, "relaxation": 8, "sadness": 1, "pleasure": 8, "desc": "缓和节奏，情感共鸣"},
    "悲情高潮": {"tension": 5, "relaxation": 0, "sadness": 9, "pleasure": 0, "desc": "悲伤峰值，催泪点"},
    "爽点引爆": {"tension": 2, "relaxation": 2, "sadness": 0, "pleasure": 9, "desc": "复仇/逆袭/装X成功，读者极度舒适"},
    "绝望低谷": {"tension": 8, "relaxation": 0, "sadness": 8, "pleasure": 0, "desc": "一切看起来都完了，但绝望中孕育希望"},
    "紧张": {"tension": 8, "relaxation": 1, "sadness": 2, "pleasure": 1, "desc": "危机四伏，步步惊心"},
    "悬疑": {"tension": 6, "relaxation": 2, "sadness": 1, "pleasure": 2, "desc": "疑云密布，真相若隐若现"},
    "热血": {"tension": 5, "relaxation": 1, "sadness": 1, "pleasure": 7, "desc": "燃爆全场，豪气冲天"},
    "温馨": {"tension": 1, "relaxation": 7, "sadness": 1, "pleasure": 7, "desc": "暖意融融，人心柔软"},
    "悲伤": {"tension": 3, "relaxation": 1, "sadness": 8, "pleasure": 1, "desc": "令人心碎，无声落泪"},
    "爽快": {"tension": 2, "relaxation": 3, "sadness": 0, "pleasure": 8, "desc": "干脆利落，畅快淋漓"},
    "压抑": {"tension": 7, "relaxation": 0, "sadness": 5, "pleasure": 0, "desc": "窒息般的沉重，暴风雨前的寂静"},
    "释然": {"tension": 2, "relaxation": 6, "sadness": 2, "pleasure": 5, "desc": "云开雾散，长舒一口气"},
    "震撼": {"tension": 8, "relaxation": 0, "sadness": 2, "pleasure": 3, "desc": "惊天反转或壮阔场景，读者目瞪口呆"},
}
