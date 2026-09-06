import re

DIMS = [
    {"key":"accuracy","name":"事实与政策一致性","max":15,"group":"可信基础"},
    {"key":"reliability","name":"可靠性与证据可核验性","max":15,"group":"可信基础"},
    {"key":"targeting","name":"问题针对性","max":12,"group":"决策价值"},
    {"key":"feasibility","name":"政策可行性","max":15,"group":"决策价值"},
    {"key":"innovation","name":"政策创新性","max":10,"group":"决策价值"},
    {"key":"effect","name":"预期效果与可评估性","max":10,"group":"决策价值"},
    {"key":"logic","name":"分析逻辑与约束识别","max":13,"group":"决策价值"},
    {"key":"format","name":"咨政规范与表达效率","max":10,"group":"报送质量"},
]

AREAS = {
    "economy":{"name":"产业经济","keywords":["产业","经济","市场","企业","投资","消费","财政","税收","就业","营商环境","供应链","产业链","价格"]},
    "governance":{"name":"社会治理","keywords":["治理","基层","社区","社会组织","公共管理","协同治理","网格","社会稳定","矛盾化解","行政效能"]},
    "public_service":{"name":"民生与公共服务","keywords":["民生","教育","医疗","养老","住房","社会保障","公共服务","困难群体","就业服务","托育"]},
    "ecology":{"name":"资源环境","keywords":["生态","环境","资源","绿色","低碳","碳排放","污染","保护","可持续","水资源","土地","能源"]},
    "technology":{"name":"科技与数字治理","keywords":["科技","创新","数字化","数据","人工智能","平台","算法","信息化","智能化","研发","技术转化"]},
    "regional":{"name":"区域与城乡发展","keywords":["区域","城乡","乡村","城市","县域","都市圈","区域协调","乡村振兴","基础设施","公共资源"]},
    "safety":{"name":"公共安全与应急","keywords":["安全","应急","风险","灾害","预警","韧性","事故","公共卫生","处置","防控"]},
    "general":{"name":"综合政策","keywords":["政策","机制","制度","改革","治理","责任","考核","激励","监管","实施","规划","方案"]},
}

def clamp(x,a,b): return max(a,min(b,x))
def uniq_hits(text, words): return list(dict.fromkeys([w for w in words if w in text]))
def add(rs,label,value,pos=True):
    if value>0: rs.append({"label":label,"value":round(float(value),2),"positive":pos})

def score_text(text, selected_areas=None):
    text=text or ""
    selected_areas=selected_areas or ["general"]
    L=len(re.sub(r"\s+","",text))
    out={"reasons":{},"flags":[],"defects":[],"area_scores":{},"length":L}

    # 1 事实与政策一致性：自动系统主要评估“可核查程度”和内部政策表达规范，不声称完成外部事实核验
    s=0; rs=[]
    policy_names=re.findall(r"《[^》]{3,45}》",text)
    v=min(3.5,len(set(policy_names))*.9); s+=v; add(rs,"具体政策/法规名称锚点",v)
    agencies=uniq_hits(text,["党中央","国务院","全国人大","全国政协","国家发展改革委","财政部","教育部","科技部","工业和信息化部","民政部","人力资源社会保障部","自然资源部","生态环境部","住房城乡建设部","交通运输部","农业农村部","商务部","国家卫生健康委","国家统计局","市场监管总局","地方政府","省级政府","市级政府"])
    v=min(3.5,len(agencies)*.55); s+=v; add(rs,"政策主体/发布机关明确",v)
    dates=re.findall(r"(?:20\d{2}年(?:\d{1,2}月(?:\d{1,2}日)?)?)",text)
    v=min(2.5,len(set(dates))*.5); s+=v; add(rs,"政策时点较明确",v)
    concepts=uniq_hits(text,["适用范围","实施主体","责任主体","政策对象","目标群体","试点范围","约束条件","风险防范"])
    v=min(2.5,len(concepts)*.55); s+=v; add(rs,"政策对象与边界表达",v)
    if re.search(r"截至|根据|依据|按照|以.*为基准",text): s+=1.5; add(rs,"关键判断具有时间/口径限定",1.5)
    absolutes=re.findall(r"必然|完全解决|彻底解决|唯一(?:途径|办法|选择)|绝对|毫无疑问|全面消除",text)
    if absolutes:
        v=min(2,len(absolutes)*.7); s-=v; add(rs,"结论强度过高，需人工核验",v,False)
        out["flags"].append("发现绝对化或过强结论，建议核对证据范围并降低表述强度。")
    vague_time=re.findall(r"当前|目前|近期|近年来|现阶段",text)
    if len(vague_time)>=5 and not dates:
        s-=1; add(rs,"时点表述较多但缺少明确日期",1,False)
    out["accuracy"]=round(clamp(s,0,15),1); out["reasons"]["accuracy"]=rs

    # 2 可靠性
    s=0; rs=[]
    nums=re.findall(r"\d+(?:\.\d+)?%?|\d+(?:\.\d+)?(?:亿元|万元|万人|万户|万家|公里|平方公里|个百分点|倍)",text)
    v=min(3,len(nums)/8); s+=v; add(rs,"存在可核查量化信息",v)
    src=uniq_hits(text,["国家统计局","统计年鉴","政府公报","白皮书","年度报告","监测报告","审计报告","研究报告","学报","数据库","数据来源","资料来源","政策依据","文号","公开数据","官网"])
    v=min(5,len(src)*.7); s+=v; add(rs,"来源/依据标识",v)
    refs=len(re.findall(r"[（(][^）)]{2,50}(?:20\d{2}|来源|文号|报告|年鉴|数据库|官网)[^）)]*[）)]",text))
    v=min(3,refs*.6); s+=v; add(rs,"括注式证据线索",v)
    if re.search(r"数据来源|资料来源|政策依据|参考文献|参考依据",text): s+=2; add(rs,"设置独立证据说明",2)
    if re.search(r"有研究表明|有数据显示|据统计|有关数据显示|相关研究认为",text) and len(src)<2:
        s-=1.5; add(rs,"存在泛化来源表述",1.5,False)
        out["defects"].append({"severity":"中","dimension":"可靠性","issue":"证据出处不够具体","evidence":"出现“有研究表明/据统计”等泛化来源","action":"补充发布机关、文件或数据名称、年份、统计口径和可访问出处。"})
    if len(nums)>=8 and len(src)<2:
        s-=2; add(rs,"精确数字较多但来源不足",2,False)
        out["defects"].append({"severity":"高","dimension":"可靠性","issue":"量化结论缺少可追溯来源","evidence":"文本中精确数字较多，但权威来源标识不足","action":"逐一绑定数据来源、统计年度、单位和统计口径；无法核验的精确数字不宜保留。"})
    out["reliability"]=round(clamp(s,0,15),1); out["reasons"]["reliability"]=rs

    # 领域覆盖
    area_hits=[]
    for key in selected_areas:
        if key in AREAS:
            hh=uniq_hits(text,AREAS[key]["keywords"])
            sc=min(100,round(len(hh)/max(4,min(8,len(AREAS[key]["keywords"])))*100))
            out["area_scores"][key]={"name":AREAS[key]["name"],"score":sc,"hits":hh}
            area_hits += hh

    # 3 针对性
    s=0; rs=[]
    v=min(4.5,len(set(area_hits))*.55); s+=v; add(rs,"所选政策领域关键要素覆盖",v)
    objects=uniq_hits(text,["企业","中小企业","居民","老年人","儿童","青年","农民","低收入群体","困难群体","基层政府","社区","学校","医院","科研机构","行业协会","平台企业","地方政府","县域","农村地区","城市社区"])
    v=min(2.5,len(objects)*.45); s+=v; add(rs,"政策对象较具体",v)
    problems=uniq_hits(text,["问题","矛盾","短板","难点","堵点","痛点","约束","原因","风险","需求","缺口"])
    v=min(2,len(problems)*.35); s+=v; add(rs,"问题诊断较明确",v)
    if re.search(r"适用范围|重点对象|针对|重点地区|试点地区|目标群体",text): s+=1.5; add(rs,"适用范围/对象有明确限定",1.5)
    if re.search(r"一是|二是|三是|首先|其次|重点",text): s+=1.5; add(rs,"重点任务有所排序",1.5)
    out["targeting"]=round(clamp(s,0,12),1); out["reasons"]["targeting"]=rs

    # 4 可行性
    s=0; rs=[]
    actions=uniq_hits(text,["建立","制定","修订","改革","明确","设立","调整","纳入","统筹","委托","拨付","监管","试点","出台","建设","实施","考核","评估","公开","共享","采购","补贴","减免","培训","联动","协同"])
    v=min(4.5,len(actions)*.35); s+=v; add(rs,"政策动作具体",v)
    actors=uniq_hits(text,["国务院","国家发展改革委","财政部","教育部","科技部","工业和信息化部","民政部","人力资源社会保障部","自然资源部","生态环境部","住房城乡建设部","交通运输部","农业农村部","商务部","国家卫生健康委","国家统计局","省级政府","市级政府","县级政府","牵头部门","责任部门","第三方机构"])
    v=min(3,len(actors)*.45); s+=v; add(rs,"责任主体较明确",v)
    implementation=uniq_hits(text,["第一阶段","第二阶段","分阶段","试点","推广","时间表","年度","预算","资金","财政","人员","数据","平台","部门协同","监督","审计","绩效考核","动态调整"])
    v=min(4.5,len(implementation)*.5); s+=v; add(rs,"实施条件与阶段安排",v)
    if re.search(r"适用范围|限制条件|风险防范|退出机制|负面清单",text): s+=2; add(rs,"实施边界和风险安排较清楚",2)
    vague=len(re.findall(r"建议(?:进一步)?(?:加强|完善|推进|强化|加大|提升)",text))
    if vague>=5:
        s-=1.5; add(rs,"泛化建议较多",1.5,False)
        out["defects"].append({"severity":"中","dimension":"可行性","issue":"部分建议仍停留在原则性表述","evidence":"“加强、完善、推进、强化”等表述较集中","action":"逐条补充牵头部门、具体政策工具、实施对象、时间节点、资源来源和验收指标。"})
    out["feasibility"]=round(clamp(s,0,15),1); out["reasons"]["feasibility"]=rs

    # 5 创新性
    s=0; rs=[]
    innovative=uniq_hits(text,["机制创新","制度创新","政策组合","差异化","分类分级","动态调整","协同机制","联动机制","跨部门","跨区域","数字化","数据共享","试点","负面清单","第三方评估","场景应用","揭榜挂帅","沙盒监管"])
    v=min(4.5,len(innovative)*.6); s+=v; add(rs,"机制/工具创新线索",v)
    if re.search(r"相较|相比|区别于|不同于|现有.*不足|在现有.*基础上|由.*转向|从.*转向",text): s+=2.5; add(rs,"说明与现有机制的增量关系",2.5)
    if re.search(r"试点|先行先试|分阶段|评估后推广|动态调整",text): s+=1.5; add(rs,"创新方案具有验证路径",1.5)
    if re.search(r"数据|数字化|平台|算法|模型|监测|指数|系数",text): s+=1.5; add(rs,"包含数据或技术支撑型创新",1.5)
    if text.count("创新")>=4 and not re.search(r"相较|相比|区别于|现有.*不足",text):
        s-=1; add(rs,"创新表述较多但基准比较不足",1,False)
    out["innovation"]=round(clamp(s,0,10),1); out["reasons"]["innovation"]=rs

    # 6 效果
    s=0; rs=[]
    effects=uniq_hits(text,["提高","降低","提升","改善","增强","减少","稳定","促进","缓解","缩短","节约","覆盖率","满意度","效率","效果","绩效","成效"])
    v=min(3,len(effects)*.3); s+=v; add(rs,"预期效果有所表达",v)
    metrics=uniq_hits(text,["指标","比例","增长率","下降率","覆盖率","满意度","目标值","基准值","年度","季度","每年","考核","监测","评估","阈值","百分点","时限"])
    v=min(3.5,len(metrics)*.45); s+=v; add(rs,"效果具备量化/监测线索",v)
    if re.search(r"短期|中期|长期|近期目标|阶段目标|年度目标",text): s+=1.5; add(rs,"区分效果时间尺度",1.5)
    if re.search(r"副作用|风险|挤出|扭曲|防止|避免|成本上升|公平性",text): s+=1; add(rs,"考虑副作用或政策成本",1)
    if re.search(r"反馈|动态调整|闭环|绩效考核|第三方评估",text): s+=1; add(rs,"形成效果反馈机制",1)
    out["effect"]=round(clamp(s,0,10),1); out["reasons"]["effect"]=rs

    # 7 逻辑
    s=0; rs=[]
    constraints=uniq_hits(text,["约束","限制条件","风险","财政承受","协商成本","统计口径","监管","成本","公平","利益平衡","边界","不确定性","数据质量","执行偏差","政策冲突"])
    v=min(6.5,len(constraints)*.55); s+=v; add(rs,"约束、风险与边界识别",v)
    connect=uniq_hits(text,["因此","从而","如果","若","导致","由于","同时","但是","但","而非","需要","避免","防止","一方面","另一方面","鉴于","基于"])
    v=min(3,len(connect)*.3); s+=v; add(rs,"因果/条件逻辑表达",v)
    if re.search(r"问题背景|主要问题|问题诊断|现实困境|主要矛盾",text): s+=1.5; add(rs,"问题诊断结构清楚",1.5)
    if re.search(r"约束条件|限制条件|风险防范|实施边界",text): s+=2; add(rs,"显式呈现边界条件",2)
    out["logic"]=round(clamp(s,0,13),1); out["reasons"]["logic"]=rs

    # 8 格式
    s=0; rs=[]
    if re.search(r"核心结论|摘要|要点|主要判断|【要报】",text): s+=2.5; add(rs,"核心判断前置",2.5)
    if re.search(r"政策依据|数据来源|事实依据|参考依据",text): s+=1.2; add(rs,"证据模块较清晰",1.2)
    if re.search(r"问题背景|主要问题|问题诊断|现实困境",text): s+=1.3; add(rs,"问题模块较清晰",1.3)
    if re.search(r"政策建议|对策建议|工作建议|建议措施",text): s+=1.5; add(rs,"建议模块较清晰",1.5)
    if re.search(r"约束条件|风险防范|实施保障",text): s+=1; add(rs,"约束/保障模块较清晰",1)
    heads=len(re.findall(r"(?:^|\n)(?:[一二三四五六七八九十]+[、.．]|\[[^\]]+\]|【[^】]+】|（[^）]{2,15}）|#{1,3}\s*)",text))
    v=min(1.5,heads*.16); s+=v; add(rs,"层级标题较规范",v)
    if 800<=L<=5000: s+=1; add(rs,"篇幅适合政策文本初稿",1)
    if L>7500: s-=1.5; add(rs,"篇幅偏长，信息密度下降",1.5,False)
    out["format"]=round(clamp(s,0,10),1); out["reasons"]["format"]=rs

    # 系统性缺陷（确保良策不是只报高分）
    if out["effect"]<6.5: out["defects"].append({"severity":"中","dimension":"预期效果","issue":"效果评价闭环不足","evidence":"目标值、监测指标、时间尺度或反馈安排不足","action":"对核心措施增加基准值、目标值、监测频率、责任单位和调整触发条件。"})
    if out["innovation"]<6: out["defects"].append({"severity":"中","dimension":"创新性","issue":"创新增量尚未充分证明","evidence":"与现行政策或既有机制的对照不足","action":"增加“现有做法—现存不足—拟议增量—试点验证”的四段式论证。"})
    if out["feasibility"]<8: out["defects"].append({"severity":"高","dimension":"可行性","issue":"实施条件不够完整","evidence":"责任主体、资源、时间表或监管条件不足","action":"补充部门责任矩阵、资源来源、实施阶段、风险处置和验收标准。"})
    if out["targeting"]<7: out["defects"].append({"severity":"中","dimension":"针对性","issue":"问题—对象—措施匹配度不足","evidence":"适用对象、地区或政策工具不够具体","action":"将每项建议绑定具体对象、应用场景、问题症结和政策工具。"})
    if out["reliability"]<8: out["defects"].append({"severity":"高","dimension":"可靠性","issue":"证据链需要加强","evidence":"来源层级、数据口径或引用信息不足","action":"优先使用政府正式文件、统计公报和权威数据库，并保留具体出处。"})
    if not out["defects"]:
        weakest=sorted(DIMS,key=lambda d:out[d["key"]]/d["max"])[:2]
        for d in weakest: out["defects"].append({"severity":"低","dimension":d["name"],"issue":"仍有精细化改进空间","evidence":f'该维度得分为 {out[d["key"]]}/{d["max"]}',"action":"结合人工复核进一步补充证据、边界条件和可量化指标。"})

    out["total"]=round(sum(out[d["key"]] for d in DIMS),1)
    return out


def _split_sentences(text):
    # 保留换行和句末标点，便于按原文顺序展示
    parts=re.findall(r"[^。！？!?；\n]+[。！？!?；]?|\n+",text or "")
    return [p for p in parts if p]


def proofread_text(text):
    """生成接近Word批注的句段级修改建议，不自动改写事实内容。"""
    segments=_split_sentences(text)
    issues=[]
    issue_id=0
    annotated=[]

    source_words=["国家统计局","统计年鉴","政府公报","年度报告","监测报告","审计报告","文号","数据来源","资料来源","官网","数据库","《"]
    actor_words=["国务院","国家发展改革委","财政部","教育部","科技部","工业和信息化部","民政部","人力资源社会保障部","自然资源部","生态环境部","住房城乡建设部","交通运输部","农业农村部","商务部","国家卫生健康委","省级政府","市级政府","县级政府","牵头部门","责任部门"]
    metric_words=["指标","目标值","基准值","覆盖率","满意度","增长率","下降率","年度","季度","时限","监测","考核","评估"]

    def add_issue(seg_index, category, severity, original, problem, suggestion, rewrite):
        nonlocal issue_id
        if len(issues)>=45: return
        issue_id+=1
        issues.append({"id":issue_id,"segment_index":seg_index,"category":category,"severity":severity,"original":original.strip(),"problem":problem,"suggestion":suggestion,"rewrite":rewrite})

    for i,seg in enumerate(segments):
        st=seg.strip()
        if not st or st.startswith("#"): continue

        # 泛化来源
        if re.search(r"有研究表明|研究显示|数据显示|据统计|有关数据显示|相关研究认为|有关部门认为",st) and not any(w in st for w in source_words):
            add_issue(i,"证据","中",st,"引用了研究或数据，但没有给出可追溯的具体来源。","补充发布机关/作者、文件或数据名称、年份、统计口径；如无法核验，降低结论精度。","据【发布机关/研究机构】【文件或数据名称】（【年份/文号】），……")

        # 精确数字无来源
        if re.search(r"\d+(?:\.\d+)?%?|\d+(?:\.\d+)?(?:亿元|万元|万人|万户|万家|公里|个百分点|倍)",st) and not any(w in st for w in source_words) and not re.search(r"（[^）]*(?:来源|报告|年鉴|20\d{2})[^）]*）",st):
            add_issue(i,"数据核验","高",st,"包含精确数字，但本句未显示来源、统计年度或口径。","在数字后补充来源、年度、单位和统计口径；不能核验时避免保留过度精确的数值。","……【数字】（来源：【机构/数据库】；统计期：【时间】；口径：【说明】）。")

        # 绝对化
        abs_words=re.findall(r"必然|完全解决|彻底解决|唯一(?:途径|办法|选择)|绝对|毫无疑问|全面消除|根本杜绝",st)
        if abs_words:
            repl=st
            for w in abs_words:
                repl=repl.replace(w,"有望在一定条件下改善" if w in ["必然","毫无疑问"] else "在一定程度上缓解")
            add_issue(i,"表述强度","中",st,"结论强度超过当前句子展示的证据范围，容易形成过度承诺。","明确成立条件、适用范围和不确定性，使用“有望、可在一定程度上、在……条件下”等限定语。",repl)

        # 模糊时点
        if re.search(r"当前|目前|近期|近年来|现阶段",st) and not re.search(r"20\d{2}年|截至|近\d+年",st):
            add_issue(i,"时点","低",st,"使用相对时间表述，材料归档后可能失去明确含义。","尽可能改为具体时间点或统计区间。","截至【YYYY年MM月】/根据【YYYY—YYYY年】数据，……")

        # 泛化措施
        if re.search(r"建议(?:进一步)?(?:加强|完善|推进|强化|加大|提升)",st):
            has_actor=any(w in st for w in actor_words)
            has_tool=bool(re.search(r"建立|制定|修订|设立|试点|清单|标准|补贴|减免|采购|考核|平台|机制|预算|资金",st))
            if not (has_actor and has_tool):
                add_issue(i,"措施设计","高",st,"建议以原则性动词为主，责任主体和政策工具不够具体。","按“谁来做—对谁做—用什么工具—何时完成—如何验收”重写。","建议由【牵头部门】会同【协同部门】，针对【对象/地区】，通过【具体政策工具】，在【时间节点】完成【事项】，并以【指标】进行验收。")

        # 建议句无主体
        if re.search(r"建议|应当|应|需要",st) and not any(w in st for w in actor_words) and len(st)>35:
            add_issue(i,"责任主体","中",st,"措施提出了行动要求，但没有明确牵头实施主体。","补充牵头部门、协同部门及职责分工。","由【牵头部门】负责【核心事项】，会同【协同部门】完成【配套事项】，并由【监督主体】开展评估。")

        # 效果不可量化
        if re.search(r"提高|提升|改善|增强|降低|减少|促进|缓解|优化",st) and not any(w in st for w in metric_words) and re.search(r"建议|通过|实施|建立|完善",st):
            add_issue(i,"效果评估","中",st,"提出了预期效果，但缺少可观测指标和时间尺度。","为核心目标配置基准值、目标值、时间节点、监测频率和责任部门。","实施后，力争在【时间】内使【核心指标】由【基准值】达到【目标值】，由【责任部门】按【频率】监测并公开评估结果。")

        # 创新缺基准
        if re.search(r"创新|新机制|新模式|新路径|首创",st) and not re.search(r"相较|相比|区别于|不同于|现有.*不足|在现有.*基础上",st):
            add_issue(i,"创新论证","中",st,"提出了创新判断，但没有说明相对现有政策的具体增量。","增加既有机制比较，并说明新增制度安排解决了什么旧问题、如何试点验证。","与现行【机制/政策】相比，本方案新增【制度安排】，主要解决【既有不足】，先在【范围】试点，并以【指标】评估后再推广。")

        # 句长
        if len(st)>125:
            add_issue(i,"文字表达","低",st,"单句信息负荷较高，判断、原因、措施或条件混在同一句中。","按“一句一个核心判断”拆分，优先保留主干信息。","建议拆为2—3句：①核心判断；②主要依据或原因；③措施/适用条件。")

    issue_map={}
    for it in issues: issue_map.setdefault(it["segment_index"],[]).append(it["id"])
    for i,seg in enumerate(segments): annotated.append({"text":seg,"issue_ids":issue_map.get(i,[])})
    return {"issues":issues,"segments":annotated,"count":len(issues)}
