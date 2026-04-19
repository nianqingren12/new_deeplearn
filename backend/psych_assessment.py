from __future__ import annotations

import time
from typing import Any, Dict, List, Tuple


class PsychologicalAssessment:
    """
    标准化心理评估量表模块
    包含：焦虑自评量表(SAS)、抑郁自评量表(SDS)、压力知觉量表(PSS)
    
    增强特性：
    - 量表答案验证
    - 更详细的结果解释和建议
    - 临床参考信息
    - 评估结果追踪
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
    def validate_answers(scale_type: str, answers: Dict[str, int]) -> Tuple[bool, str]:
        """验证量表答案的有效性"""
        questions = PsychologicalAssessment.get_scale_questions(scale_type)
        
        # 检查是否有缺失的答案
        missing_keys = []
        for q in questions:
            key = q["key"]
            if key not in answers:
                missing_keys.append(key)
        
        if missing_keys:
            return False, f"缺少以下问题的答案: {', '.join(missing_keys)}"
        
        # 检查答案范围是否有效（1-4分）
        for key, value in answers.items():
            if not isinstance(value, int) or value < 1 or value > 4:
                return False, f"问题 {key} 的答案 {value} 无效，必须是1-4之间的整数"
        
        return True, "答案验证通过"

    @staticmethod
    def get_scale_info(scale_type: str) -> Dict[str, Any]:
        """获取量表的基本信息"""
        scale_info = {
            "sas": {
                "name": "焦虑自评量表",
                "abbreviation": "SAS",
                "question_count": 20,
                "time_required": "约5分钟",
                "purpose": "评估近期焦虑情绪水平",
                "validity": "信度系数0.92，效度良好",
                "reference": "Zung, W.W.K. (1971)"
            },
            "sds": {
                "name": "抑郁自评量表",
                "abbreviation": "SDS",
                "question_count": 20,
                "time_required": "约5分钟",
                "purpose": "评估近期抑郁情绪水平",
                "validity": "信度系数0.93，效度良好",
                "reference": "Zung, W.W.K. (1965)"
            },
            "pss": {
                "name": "压力知觉量表",
                "abbreviation": "PSS",
                "question_count": 10,
                "time_required": "约3分钟",
                "purpose": "评估近期压力感知水平",
                "validity": "信度系数0.85，效度良好",
                "reference": "Cohen, S. et al. (1983)"
            }
        }
        return scale_info.get(scale_type, {})

    @staticmethod
    def calculate_sas_score(answers: Dict[str, int]) -> Dict[str, Any]:
        """计算SAS焦虑自评量表得分"""
        # 验证答案
        is_valid, msg = PsychologicalAssessment.validate_answers("sas", answers)
        if not is_valid:
            return {
                "error": msg,
                "valid": False,
                "scale_type": "SAS",
                "scale_name": "焦虑自评量表"
            }
        
        raw_score = 0
        for q in PsychologicalAssessment.SAS_QUESTIONS:
            key = q["key"]
            answer = answers.get(key, 1)
            if q.get("reverse", False):
                answer = 5 - answer
            raw_score += answer
        
        standard_score = int(raw_score * 1.25)
        
        # 评估等级和详细解释
        levels = [
            {"range": (0, 49), "level": "正常", "color": "green"},
            {"range": (50, 59), "level": "轻度焦虑", "color": "yellow"},
            {"range": (60, 69), "level": "中度焦虑", "color": "orange"},
            {"range": (70, 100), "level": "重度焦虑", "color": "red"}
        ]
        
        current_level = next((l for l in levels if l["range"][0] <= standard_score <= l["range"][1]), levels[0])
        
        interpretations = {
            "正常": {
                "interpretation": "您的焦虑水平在正常范围内，情绪状态良好。",
                "suggestions": [
                    "继续保持当前的生活节奏和应对方式",
                    "建议定期进行自我情绪检查",
                    "保持健康的生活习惯，如规律运动和充足睡眠"
                ],
                "clinical_note": "无临床干预需求，建议维持现有状态"
            },
            "轻度焦虑": {
                "interpretation": "您可能存在轻度焦虑情绪，这在日常生活中较为常见。",
                "suggestions": [
                    "学习放松技巧，如深呼吸、冥想或渐进式肌肉放松",
                    "保持规律的运动习惯",
                    "与亲友沟通，分享感受",
                    "尝试时间管理，减轻压力源"
                ],
                "clinical_note": "建议自我调节，如持续2周以上未改善可考虑专业咨询"
            },
            "中度焦虑": {
                "interpretation": "您存在中度焦虑情绪，可能对日常生活产生一定影响。",
                "suggestions": [
                    "寻求专业心理咨询师的帮助",
                    "学习认知行为疗法(CBT)技巧",
                    "考虑正念训练或接纳与承诺疗法",
                    "与医生讨论是否需要进一步评估"
                ],
                "clinical_note": "建议寻求专业帮助，可考虑心理治疗"
            },
            "重度焦虑": {
                "interpretation": "您存在重度焦虑情绪，可能显著影响日常生活和工作。",
                "suggestions": [
                    "立即寻求专业心理健康服务",
                    "联系精神科医生进行全面评估",
                    "告知亲友您的状况，寻求支持",
                    "考虑短期的专业治疗干预"
                ],
                "clinical_note": "强烈建议立即寻求专业医疗帮助"
            }
        }
        
        result = interpretations[current_level["level"]]
        
        return {
            "raw_score": raw_score,
            "standard_score": standard_score,
            "level": current_level["level"],
            "level_color": current_level["color"],
            "interpretation": result["interpretation"],
            "suggestions": result["suggestions"],
            "clinical_note": result["clinical_note"],
            "scale_type": "SAS",
            "scale_name": "焦虑自评量表",
            "valid": True,
            "score_range": {"min": 20, "max": 80, "your_score": standard_score},
            "norm_reference": "中国常模：均值41.88±10.57"
        }

    @staticmethod
    def calculate_sds_score(answers: Dict[str, int]) -> Dict[str, Any]:
        """计算SDS抑郁自评量表得分"""
        is_valid, msg = PsychologicalAssessment.validate_answers("sds", answers)
        if not is_valid:
            return {
                "error": msg,
                "valid": False,
                "scale_type": "SDS",
                "scale_name": "抑郁自评量表"
            }
        
        raw_score = 0
        for q in PsychologicalAssessment.SDS_QUESTIONS:
            key = q["key"]
            answer = answers.get(key, 1)
            if q.get("reverse", False):
                answer = 5 - answer
            raw_score += answer
        
        standard_score = int(raw_score * 1.25)
        
        levels = [
            {"range": (0, 52), "level": "正常", "color": "green"},
            {"range": (53, 62), "level": "轻度抑郁", "color": "yellow"},
            {"range": (63, 72), "level": "中度抑郁", "color": "orange"},
            {"range": (73, 100), "level": "重度抑郁", "color": "red"}
        ]
        
        current_level = next((l for l in levels if l["range"][0] <= standard_score <= l["range"][1]), levels[0])
        
        interpretations = {
            "正常": {
                "interpretation": "您的抑郁水平在正常范围内，情绪状态良好。",
                "suggestions": [
                    "继续保持积极的生活态度",
                    "维持社交活动和兴趣爱好",
                    "保持规律作息和健康饮食"
                ],
                "clinical_note": "无临床干预需求"
            },
            "轻度抑郁": {
                "interpretation": "您可能存在轻度抑郁情绪，这是常见的情绪反应。",
                "suggestions": [
                    "增加户外活动和阳光接触",
                    "保持规律运动",
                    "与信任的人分享感受",
                    "培养新的兴趣爱好"
                ],
                "clinical_note": "建议自我调节，如持续2周以上未改善可考虑专业咨询"
            },
            "中度抑郁": {
                "interpretation": "您存在中度抑郁情绪，可能影响日常生活功能。",
                "suggestions": [
                    "寻求专业心理咨询",
                    "考虑认知行为疗法",
                    "保持规律的生活节奏",
                    "告知亲友获得支持"
                ],
                "clinical_note": "建议寻求专业帮助"
            },
            "重度抑郁": {
                "interpretation": "您存在重度抑郁情绪，可能严重影响日常生活。",
                "suggestions": [
                    "立即联系心理健康专业人士",
                    "考虑精神科评估",
                    "确保身边有亲友陪伴",
                    "避免独处，寻求紧急支持"
                ],
                "clinical_note": "强烈建议立即寻求专业医疗帮助"
            }
        }
        
        result = interpretations[current_level["level"]]
        
        return {
            "raw_score": raw_score,
            "standard_score": standard_score,
            "level": current_level["level"],
            "level_color": current_level["color"],
            "interpretation": result["interpretation"],
            "suggestions": result["suggestions"],
            "clinical_note": result["clinical_note"],
            "scale_type": "SDS",
            "scale_name": "抑郁自评量表",
            "valid": True,
            "score_range": {"min": 20, "max": 80, "your_score": standard_score},
            "norm_reference": "中国常模：均值41.38±10.57"
        }

    @staticmethod
    def calculate_pss_score(answers: Dict[str, int]) -> Dict[str, Any]:
        """计算PSS压力知觉量表得分"""
        is_valid, msg = PsychologicalAssessment.validate_answers("pss", answers)
        if not is_valid:
            return {
                "error": msg,
                "valid": False,
                "scale_type": "PSS",
                "scale_name": "压力知觉量表"
            }
        
        raw_score = 0
        for q in PsychologicalAssessment.PSS_QUESTIONS:
            key = q["key"]
            answer = answers.get(key, 1)
            if q.get("reverse", False):
                answer = 5 - answer
            raw_score += answer
        
        levels = [
            {"range": (10, 13), "level": "低压力", "color": "green"},
            {"range": (14, 26), "level": "中等压力", "color": "yellow"},
            {"range": (27, 40), "level": "高压力", "color": "red"}
        ]
        
        current_level = next((l for l in levels if l["range"][0] <= raw_score <= l["range"][1]), levels[0])
        
        interpretations = {
            "低压力": {
                "interpretation": "您的压力水平较低，能够较好地应对生活中的挑战。",
                "suggestions": [
                    "继续保持当前的应对策略",
                    "维持健康的生活方式",
                    "定期进行自我反思"
                ],
                "clinical_note": "压力水平正常，建议维持现有状态"
            },
            "中等压力": {
                "interpretation": "您正经历中等程度的压力，这是大多数人都会经历的正常状态。",
                "suggestions": [
                    "学习时间管理技巧",
                    "练习放松技巧如冥想或瑜伽",
                    "保持充足的睡眠",
                    "定期进行体育锻炼"
                ],
                "clinical_note": "建议采取压力管理策略，预防压力升高"
            },
            "高压力": {
                "interpretation": "您的压力水平较高，长期处于高压状态可能影响身心健康。",
                "suggestions": [
                    "寻求专业心理咨询",
                    "学习压力管理技巧",
                    "设定合理的工作生活界限",
                    "考虑正念减压(MBSR)训练"
                ],
                "clinical_note": "建议寻求专业帮助进行压力管理"
            }
        }
        
        result = interpretations[current_level["level"]]
        
        return {
            "raw_score": raw_score,
            "level": current_level["level"],
            "level_color": current_level["color"],
            "interpretation": result["interpretation"],
            "suggestions": result["suggestions"],
            "clinical_note": result["clinical_note"],
            "scale_type": "PSS",
            "scale_name": "压力知觉量表",
            "valid": True,
            "score_range": {"min": 10, "max": 40, "your_score": raw_score},
            "norm_reference": "常模范围：10-40分，得分越高压力越大"
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
            },
            "valid": True,
            "scale_type": "COMPREHENSIVE",
            "scale_name": "综合心理健康评估",
            "assessment_timestamp": time.time()
        }

    @staticmethod
    def generate_progress_report(history: List[Dict]) -> Dict[str, Any]:
        """生成历史评估进度报告"""
        if not history:
            return {
                "error": "无历史评估记录",
                "valid": False
            }
        
        history_sorted = sorted(history, key=lambda x: x.get("assessment_timestamp", 0))
        
        trends = {
            "sas": [],
            "sds": [],
            "pss": [],
            "health_index": []
        }
        
        for record in history_sorted:
            if record.get("components"):
                trends["sas"].append(record["components"]["anxiety"].get("standard_score", 0))
                trends["sds"].append(record["components"]["depression"].get("standard_score", 0))
                trends["pss"].append(record["components"]["stress"].get("raw_score", 0))
            if record.get("health_index"):
                trends["health_index"].append(record["health_index"])
        
        trend_analysis = {}
        for key, scores in trends.items():
            if len(scores) >= 2:
                change = scores[-1] - scores[0]
                if abs(change) < 5:
                    trend_analysis[key] = {"direction": "稳定", "change": round(change, 2)}
                elif change > 0:
                    trend_analysis[key] = {"direction": "上升" if key == "health_index" else "恶化", "change": round(change, 2)}
                else:
                    trend_analysis[key] = {"direction": "下降" if key == "health_index" else "改善", "change": round(change, 2)}
            else:
                trend_analysis[key] = {"direction": "数据不足", "change": 0}
        
        return {
            "total_assessments": len(history),
            "first_assessment": history_sorted[0].get("assessment_timestamp"),
            "latest_assessment": history_sorted[-1].get("assessment_timestamp"),
            "trends": trend_analysis,
            "trend_details": trends,
            "valid": True,
            "scale_name": "心理健康进度报告"
        }
