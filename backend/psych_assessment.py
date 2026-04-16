from __future__ import annotations

from typing import Any, Dict, List, Tuple


class PsychologicalAssessment:
    """
    标准化心理评估量表模块
    包含：焦虑自评量表(SAS)、抑郁自评量表(SDS)、压力知觉量表(PSS)
    """

    # 焦虑自评量表(SAS) - 20题
    SAS_QUESTIONS = [
        {"question": "我觉得比平常容易紧张和着急", "key": "q1"},
        {"question": "我无缘无故地感到害怕", "key": "q2"},
        {"question": "我容易心里烦乱或觉得惊恐", "key": "q3"},
        {"question": "我觉得我可能将要发疯", "key": "q4"},
        {"question": "我觉得一切都很好，也不会发生什么不幸", "key": "q5", "reverse": True},
        {"question": "我手脚发抖打颤", "key": "q6"},
        {"question": "我因为头痛、颈痛和背痛而苦恼", "key": "q7"},
        {"question": "我感觉容易衰弱和疲乏", "key": "q8"},
        {"question": "我觉得心平气和，并且容易安静坐着", "key": "q9", "reverse": True},
        {"question": "我觉得心跳得很快", "key": "q10"},
        {"question": "我因为一阵阵头晕而苦恼", "key": "q11"},
        {"question": "我有晕倒发作或觉得要晕倒似的", "key": "q12"},
        {"question": "我吸气呼气都感到很容易", "key": "q13", "reverse": True},
        {"question": "我的手脚麻木和刺痛", "key": "q14"},
        {"question": "我因为胃痛和消化不良而苦恼", "key": "q15"},
        {"question": "我常常要小便", "key": "q16"},
        {"question": "我的手脚常常是干燥温暖的", "key": "q17", "reverse": True},
        {"question": "我脸红发热", "key": "q18"},
        {"question": "我容易入睡并且一夜睡得很好", "key": "q19", "reverse": True},
        {"question": "我做噩梦", "key": "q20"},
    ]

    # 抑郁自评量表(SDS) - 20题
    SDS_QUESTIONS = [
        {"question": "我感到情绪沮丧，郁闷", "key": "q1"},
        {"question": "我感到早晨心情最好", "key": "q2", "reverse": True},
        {"question": "我要哭或想哭", "key": "q3"},
        {"question": "我夜间睡眠不好", "key": "q4"},
        {"question": "我吃饭像平时一样多", "key": "q5", "reverse": True},
        {"question": "我的性功能正常", "key": "q6", "reverse": True},
        {"question": "我感到体重减轻", "key": "q7"},
        {"question": "我为便秘烦恼", "key": "q8"},
        {"question": "我的心跳比平时快", "key": "q9"},
        {"question": "我无故感到疲劳", "key": "q10"},
        {"question": "我的头脑像往常一样清楚", "key": "q11", "reverse": True},
        {"question": "我做事情像平时一样不感到困难", "key": "q12", "reverse": True},
        {"question": "我坐卧不安，难以保持平静", "key": "q13"},
        {"question": "我对未来感到有希望", "key": "q14", "reverse": True},
        {"question": "我比平时更容易生气激动", "key": "q15"},
        {"question": "我觉得决定什么事很容易", "key": "q16", "reverse": True},
        {"question": "我感到自己是有用的和不可缺少的人", "key": "q17", "reverse": True},
        {"question": "我的生活很有意义", "key": "q18", "reverse": True},
        {"question": "我认为如果我死了别人会过得更好", "key": "q19"},
        {"question": "我仍旧喜爱自己平时喜爱的东西", "key": "q20", "reverse": True},
    ]

    # 压力知觉量表(PSS) - 10题
    PSS_QUESTIONS = [
        {"question": "在过去的一个月里，你经常感到无法控制生活中重要的事情吗？", "key": "q1"},
        {"question": "在过去的一个月里，你经常感到紧张不安或心烦意乱吗？", "key": "q2"},
        {"question": "在过去的一个月里，你经常感到因为事情太多而无法应付吗？", "key": "q3"},
        {"question": "在过去的一个月里，你经常感到有信心处理自己的问题吗？", "key": "q4", "reverse": True},
        {"question": "在过去的一个月里，你经常感到事情都在按你的意愿发展吗？", "key": "q5", "reverse": True},
        {"question": "在过去的一个月里，你经常感到无法解决生活中面临的难题吗？", "key": "q6"},
        {"question": "在过去的一个月里，你经常感到能把握自己生活的方向吗？", "key": "q7", "reverse": True},
        {"question": "在过去的一个月里，你经常感到事情顺利吗？", "key": "q8", "reverse": True},
        {"question": "在过去的一个月里，你经常感到无法克服面临的困难吗？", "key": "q9"},
        {"question": "在过去的一个月里，你经常感到自己是有效率的吗？", "key": "q10", "reverse": True},
    ]

    @staticmethod
    def get_scale_questions(scale_type: str) -> List[Dict[str, Any]]:
        """获取指定量表的问题列表"""
        if scale_type == "sas":
            return PsychologicalAssessment.SAS_QUESTIONS
        elif scale_type == "sds":
            return PsychologicalAssessment.SDS_QUESTIONS
        elif scale_type == "pss":
            return PsychologicalAssessment.PSS_QUESTIONS
        else:
            raise ValueError(f"未知的量表类型: {scale_type}")

    @staticmethod
    def calculate_sas_score(answers: Dict[str, int]) -> Dict[str, Any]:
        """计算SAS焦虑自评量表得分"""
        raw_score = 0
        for q in PsychologicalAssessment.SAS_QUESTIONS:
            key = q["key"]
            answer = answers.get(key, 1)
            if q.get("reverse", False):
                # 反向计分：1→4, 2→3, 3→2, 4→1
                answer = 5 - answer
            raw_score += answer
        
        # 标准分 = 粗分 × 1.25
        standard_score = int(raw_score * 1.25)
        
        # 评估等级
        if standard_score < 50:
            level = "正常"
            interpretation = "您的焦虑水平在正常范围内，情绪状态良好。"
        elif standard_score < 60:
            level = "轻度焦虑"
            interpretation = "您可能存在轻度焦虑情绪，建议关注情绪变化，适当放松。"
        elif standard_score < 70:
            level = "中度焦虑"
            interpretation = "您存在中度焦虑情绪，建议寻求专业心理支持。"
        else:
            level = "重度焦虑"
            interpretation = "您存在重度焦虑情绪，强烈建议立即寻求专业心理咨询或医疗帮助。"
        
        return {
            "raw_score": raw_score,
            "standard_score": standard_score,
            "level": level,
            "interpretation": interpretation,
            "scale_type": "SAS",
            "scale_name": "焦虑自评量表"
        }

    @staticmethod
    def calculate_sds_score(answers: Dict[str, int]) -> Dict[str, Any]:
        """计算SDS抑郁自评量表得分"""
        raw_score = 0
        for q in PsychologicalAssessment.SDS_QUESTIONS:
            key = q["key"]
            answer = answers.get(key, 1)
            if q.get("reverse", False):
                answer = 5 - answer
            raw_score += answer
        
        standard_score = int(raw_score * 1.25)
        
        if standard_score < 53:
            level = "正常"
            interpretation = "您的抑郁水平在正常范围内，情绪状态良好。"
        elif standard_score < 63:
            level = "轻度抑郁"
            interpretation = "您可能存在轻度抑郁情绪，建议保持积极心态，多与他人交流。"
        elif standard_score < 73:
            level = "中度抑郁"
            interpretation = "您存在中度抑郁情绪，建议寻求专业心理支持和帮助。"
        else:
            level = "重度抑郁"
            interpretation = "您存在重度抑郁情绪，强烈建议立即寻求专业心理咨询或医疗帮助。"
        
        return {
            "raw_score": raw_score,
            "standard_score": standard_score,
            "level": level,
            "interpretation": interpretation,
            "scale_type": "SDS",
            "scale_name": "抑郁自评量表"
        }

    @staticmethod
    def calculate_pss_score(answers: Dict[str, int]) -> Dict[str, Any]:
        """计算PSS压力知觉量表得分"""
        raw_score = 0
        for q in PsychologicalAssessment.PSS_QUESTIONS:
            key = q["key"]
            answer = answers.get(key, 1)
            if q.get("reverse", False):
                answer = 5 - answer
            raw_score += answer
        
        # PSS评分范围10-40，得分越高压力越大
        if raw_score <= 13:
            level = "低压力"
            interpretation = "您的压力水平较低，能够较好地应对生活中的挑战。"
        elif raw_score <= 26:
            level = "中等压力"
            interpretation = "您正经历中等程度的压力，建议采取适当的压力管理策略。"
        else:
            level = "高压力"
            interpretation = "您的压力水平较高，长期处于高压状态可能影响身心健康，建议寻求支持和帮助。"
        
        return {
            "raw_score": raw_score,
            "level": level,
            "interpretation": interpretation,
            "scale_type": "PSS",
            "scale_name": "压力知觉量表"
        }

    @staticmethod
    def calculate_comprehensive_score(sas_result: Dict, sds_result: Dict, pss_result: Dict) -> Dict[str, Any]:
        """计算综合心理健康评分"""
        # 权重：SAS 30%, SDS 35%, PSS 35%
        sas_weight = 0.3
        sds_weight = 0.35
        pss_weight = 0.35
        
        # 将各量表得分归一化到0-100
        sas_norm = (sas_result["standard_score"] / 80) * 100  # SAS最高约80
        sds_norm = (sds_result["standard_score"] / 80) * 100  # SDS最高约80
        pss_norm = ((pss_result["raw_score"] - 10) / 30) * 100  # PSS范围10-40
        
        # 综合得分（反向，越低越好）
        raw_composite = (sas_norm * sas_weight) + (sds_norm * sds_weight) + (pss_norm * pss_weight)
        
        # 转换为健康指数（越高越好）
        health_index = 100 - raw_composite
        
        if health_index >= 80:
            overall_level = "优秀"
            advice = "您的心理健康状况优秀！请继续保持健康的生活方式和积极的心态。"
        elif health_index >= 60:
            overall_level = "良好"
            advice = "您的心理健康状况良好，但仍有提升空间。建议定期进行自我检查和情绪管理。"
        elif health_index >= 40:
            overall_level = "一般"
            advice = "您的心理健康状况需要关注。建议采取积极的应对策略，必要时寻求专业帮助。"
        else:
            overall_level = "较差"
            advice = "您的心理健康状况较差，强烈建议立即寻求专业心理咨询师的帮助。"
        
        return {
            "health_index": round(health_index, 2),
            "overall_level": overall_level,
            "advice": advice,
            "components": {
                "anxiety": sas_result,
                "depression": sds_result,
                "stress": pss_result
            }
        }
