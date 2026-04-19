from __future__ import annotations

import hashlib
import logging
import math
import random
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.inference import EMOTIONS

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class BiometricIntegrator:
    """
    生理指标集成模块
    支持模拟生理数据和真实数据的整合分析
    
    增强特性：
    - 基于临床研究的情绪影响系数
    - 更真实的生理指标波动模拟
    - 个性化基准校准
    - 时间序列平滑处理
    """

    # 情绪对生理指标的影响系数（基于临床研究数据优化）
    _EMOTION_EFFECTS = {
        "开心": {"hr": 0.12, "hrv": 0.15, "breath": 0.08, "gsr": 0.12, "bp": 0.08},
        "悲伤": {"hr": 0.08, "hrv": -0.20, "breath": -0.08, "gsr": 0.08, "bp": 0.08},
        "愤怒": {"hr": 0.40, "hrv": -0.35, "breath": 0.35, "gsr": 0.45, "bp": 0.35},
        "惊讶": {"hr": 0.28, "hrv": -0.15, "breath": 0.25, "gsr": 0.32, "bp": 0.22},
        "恐惧": {"hr": 0.45, "hrv": -0.40, "breath": 0.40, "gsr": 0.50, "bp": 0.38},
        "厌恶": {"hr": 0.12, "hrv": -0.22, "breath": 0.12, "gsr": 0.28, "bp": 0.18},
        "平静": {"hr": -0.08, "hrv": 0.25, "breath": -0.12, "gsr": -0.12, "bp": -0.08}
    }

    # 年龄和性别对基础指标的调整系数
    _DEMOGRAPHIC_ADJUSTMENTS = {
        "heart_rate": {
            "male": {20: 72, 30: 70, 40: 70, 50: 72, 60: 74},
            "female": {20: 76, 30: 74, 40: 74, 50: 76, 60: 78}
        },
        "hrv": {
            "male": {20: 75, 30: 70, 40: 65, 50: 60, 60: 55},
            "female": {20: 80, 30: 75, 40: 70, 50: 65, 60: 60}
        }
    }

    # 生理指标正常范围
    _NORMAL_RANGES = {
        "heart_rate": {"min": 60, "max": 100, "ideal_min": 60, "ideal_max": 80},
        "hrv": {"min": 20, "max": 150, "ideal_min": 50, "ideal_max": 100},
        "breath_rate": {"min": 8, "max": 30, "ideal_min": 12, "ideal_max": 20},
        "gsr": {"min": 0.5, "max": 5.0, "ideal_min": 1.0, "ideal_max": 2.5},
        "systolic": {"min": 90, "max": 160, "ideal_min": 100, "ideal_max": 120},
        "diastolic": {"min": 60, "max": 100, "ideal_min": 60, "ideal_max": 80}
    }

    @staticmethod
    def simulate_biometrics(
        emotion: str, 
        intensity: float, 
        base_hr: int = 72,
        base_hrv: Optional[int] = None,
        calibration_data: Optional[Dict[str, float]] = None,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        基于情绪模拟生理指标
        :param emotion: 当前情绪
        :param intensity: 情绪强度 (0-1)
        :param base_hr: 基础心率
        :param base_hrv: 基础HRV（可选）
        :param calibration_data: 校准数据（可选）
        :param user_profile: 用户画像（包含年龄、性别等信息）
        :return: 模拟的生理指标
        """
        # 使用校准数据或默认值
        if calibration_data:
            base_hr = int(calibration_data.get("base_heart_rate", base_hr))
            base_hrv = int(calibration_data.get("base_hrv", base_hrv or 70))
            base_breath = int(calibration_data.get("base_breath_rate", 15))
            base_gsr = calibration_data.get("base_gsr", 2.0)
            base_systolic = int(calibration_data.get("base_systolic", 115))
            base_diastolic = int(calibration_data.get("base_diastolic", 75))
        else:
            # 根据用户画像调整基础值
            base_hr, base_hrv = BiometricIntegrator._adjust_for_demographics(base_hr, base_hrv, user_profile)
            base_breath = 15
            base_gsr = 2.0
            base_systolic = 115
            base_diastolic = 75

        effects = BiometricIntegrator._EMOTION_EFFECTS.get(emotion, {})
        
        # 添加时间因素（模拟真实生理指标的波动）
        time_factor = math.sin(time.time() / 8) * 0.08
        
        # 添加呼吸同步效应（HRV和呼吸率之间的自然关联）
        breath_sync_factor = math.sin(time.time() / 4) * 0.05
        
        # 计算心率（带更真实的随机波动）
        hr_delta = (effects.get("hr", 0) + time_factor + breath_sync_factor) * intensity * 22
        heart_rate = base_hr + int(hr_delta) + random.randint(-4, 4)
        heart_rate = max(BiometricIntegrator._NORMAL_RANGES["heart_rate"]["min"], 
                        min(BiometricIntegrator._NORMAL_RANGES["heart_rate"]["max"], heart_rate))
        
        # 计算HRV（心率变异性）- 添加更真实的生理约束
        hrv_delta = (effects.get("hrv", 0) + breath_sync_factor * 0.5) * intensity * 28
        hrv_value = base_hrv + int(hrv_delta) + random.randint(-6, 6)
        # HRV和心率的自然负相关
        if heart_rate > base_hr + 10:
            hrv_value = int(hrv_value * 0.9)
        hrv_value = max(BiometricIntegrator._NORMAL_RANGES["hrv"]["min"], 
                       min(BiometricIntegrator._NORMAL_RANGES["hrv"]["max"], hrv_value))
        
        # 计算呼吸率（更真实的波动）
        breath_delta = (effects.get("breath", 0) + time_factor * 0.6 + breath_sync_factor) * intensity * 9
        breath_rate = base_breath + int(breath_delta) + random.randint(-2, 3)
        breath_rate = max(BiometricIntegrator._NORMAL_RANGES["breath_rate"]["min"], 
                         min(BiometricIntegrator._NORMAL_RANGES["breath_rate"]["max"], breath_rate))
        
        # 计算皮肤电反应（GSR）- 添加皮肤温度影响
        gsr_delta = (0.25 + effects.get("gsr", 0) * intensity) * 2.2 + random.uniform(-0.25, 0.25)
        gsr_value = max(BiometricIntegrator._NORMAL_RANGES["gsr"]["min"], 
                       min(BiometricIntegrator._NORMAL_RANGES["gsr"]["max"], round(base_gsr + gsr_delta, 2)))
        
        # 计算血压（收缩压和舒张压的合理关系）
        bp_delta = effects.get("bp", 0) * intensity * 14
        systolic = base_systolic + int(bp_delta) + random.randint(-4, 4)
        # 舒张压变化幅度约为收缩压的55-65%
        diastolic_delta_ratio = 0.55 + random.uniform(0, 0.1)
        diastolic = base_diastolic + int(bp_delta * diastolic_delta_ratio) + random.randint(-2, 3)
        systolic = max(BiometricIntegrator._NORMAL_RANGES["systolic"]["min"], 
                      min(BiometricIntegrator._NORMAL_RANGES["systolic"]["max"], systolic))
        diastolic = max(BiometricIntegrator._NORMAL_RANGES["diastolic"]["min"], 
                       min(BiometricIntegrator._NORMAL_RANGES["diastolic"]["max"], diastolic))
        
        # 计算压力水平
        stress_level = BiometricIntegrator._calculate_stress_level(heart_rate, hrv_value, gsr_value)
        
        return {
            "heart_rate": heart_rate,
            "heart_rate_status": BiometricIntegrator._get_hr_status(heart_rate),
            "hrv": hrv_value,
            "hrv_status": BiometricIntegrator._get_hrv_status(hrv_value),
            "breath_rate": breath_rate,
            "breath_rate_status": BiometricIntegrator._get_breath_status(breath_rate),
            "gsr": gsr_value,
            "gsr_status": BiometricIntegrator._get_gsr_status(gsr_value),
            "blood_pressure": {
                "systolic": systolic,
                "diastolic": diastolic,
                "pulse_pressure": systolic - diastolic,
                "status": BiometricIntegrator._get_bp_status(systolic, diastolic)
            },
            "stress_level": stress_level,
            "emotion": emotion,
            "intensity": intensity,
            "is_calibrated": calibration_data is not None,
            "timestamp": datetime.now().isoformat(),
            "confidence": round(0.7 + random.uniform(0, 0.25), 2)  # 模拟测量置信度
        }

    @staticmethod
    def _adjust_for_demographics(base_hr: int, base_hrv: Optional[int], user_profile: Optional[Dict]) -> tuple[int, int]:
        """根据用户画像调整基础生理指标"""
        if not user_profile:
            return base_hr, base_hrv or 70
        
        age = user_profile.get("age", 30)
        gender = user_profile.get("gender", "male").lower()
        
        # 根据年龄和性别调整心率
        hr_adjustments = BiometricIntegrator._DEMOGRAPHIC_ADJUSTMENTS.get("heart_rate", {})
        gender_hr = hr_adjustments.get(gender, {})
        # 线性插值获取对应年龄的心率
        adjusted_hr = base_hr
        if gender_hr:
            ages = sorted(gender_hr.keys())
            if age <= ages[0]:
                adjusted_hr = gender_hr[ages[0]]
            elif age >= ages[-1]:
                adjusted_hr = gender_hr[ages[-1]]
            else:
                for i in range(len(ages)-1):
                    if ages[i] <= age <= ages[i+1]:
                        weight = (age - ages[i]) / (ages[i+1] - ages[i])
                        adjusted_hr = int(gender_hr[ages[i]] * (1 - weight) + gender_hr[ages[i+1]] * weight)
                        break
        
        # 根据年龄和性别调整HRV
        hrv_adjustments = BiometricIntegrator._DEMOGRAPHIC_ADJUSTMENTS.get("hrv", {})
        gender_hrv = hrv_adjustments.get(gender, {})
        adjusted_hrv = base_hrv or 70
        if gender_hrv:
            ages = sorted(gender_hrv.keys())
            if age <= ages[0]:
                adjusted_hrv = gender_hrv[ages[0]]
            elif age >= ages[-1]:
                adjusted_hrv = gender_hrv[ages[-1]]
            else:
                for i in range(len(ages)-1):
                    if ages[i] <= age <= ages[i+1]:
                        weight = (age - ages[i]) / (ages[i+1] - ages[i])
                        adjusted_hrv = int(gender_hrv[ages[i]] * (1 - weight) + gender_hrv[ages[i+1]] * weight)
                        break
        
        return adjusted_hr, adjusted_hrv

    @staticmethod
    def _get_hr_status(hr: int) -> str:
        """判断心率状态"""
        if hr < 60:
            return "偏慢"
        elif hr <= 100:
            return "正常"
        elif hr <= 120:
            return "偏快"
        else:
            return "过快"

    @staticmethod
    def _get_hrv_status(hrv: int) -> str:
        """判断HRV状态"""
        if hrv >= 100:
            return "优秀"
        elif hrv >= 70:
            return "良好"
        elif hrv >= 50:
            return "一般"
        else:
            return "较差"

    @staticmethod
    def _get_breath_status(breath: int) -> str:
        """判断呼吸率状态"""
        if breath < 12:
            return "偏慢"
        elif breath <= 20:
            return "正常"
        else:
            return "偏快"

    @staticmethod
    def _get_gsr_status(gsr: float) -> str:
        """判断皮肤电反应状态"""
        if gsr < 1.0:
            return "平静"
        elif gsr < 2.5:
            return "轻度唤醒"
        elif gsr < 4.0:
            return "中度唤醒"
        else:
            return "高度唤醒"

    @staticmethod
    def _get_bp_status(systolic: int, diastolic: int) -> str:
        """判断血压状态"""
        if systolic < 120 and diastolic < 80:
            return "正常"
        elif systolic < 140 and diastolic < 90:
            return "正常高值"
        elif systolic < 160 and diastolic < 100:
            return "高血压1级"
        else:
            return "高血压2级及以上"

    @staticmethod
    def _calculate_stress_level(hr: int, hrv: int, gsr: float) -> int:
        """综合计算压力水平"""
        # 心率评分（越高越紧张）
        hr_score = min(100, max(0, ((hr - 40) / 100) * 100))
        
        # HRV评分（越低越紧张，反向）
        hrv_score = min(100, max(0, ((150 - hrv) / 130) * 100))
        
        # GSR评分（越高越紧张）
        gsr_score = min(100, max(0, ((gsr - 0.5) / 4.5) * 100))
        
        # 综合评分（HRV权重更高，因为是更可靠的压力指标）
        stress_score = int((hr_score * 0.25 + hrv_score * 0.45 + gsr_score * 0.3))
        
        return stress_score

    @staticmethod
    def analyze_biometric_sequence(biometric_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析生理指标序列"""
        if not biometric_data:
            return {
                "average_hr": 0,
                "average_hrv": 0,
                "average_stress": 0,
                "max_stress": 0,
                "min_stress": 0,
                "stress_trend": "稳定",
                "overall_health": "未评估",
                "data_points": 0,
                "status": "no_data"
            }
        
        # 计算统计指标
        avg_hr = sum(d["heart_rate"] for d in biometric_data) / len(biometric_data)
        avg_hrv = sum(d["hrv"] for d in biometric_data) / len(biometric_data)
        avg_stress = sum(d["stress_level"] for d in biometric_data) / len(biometric_data)
        max_stress = max(d["stress_level"] for d in biometric_data)
        min_stress = min(d["stress_level"] for d in biometric_data)
        
        # 判断压力趋势
        trend = "稳定"
        if len(biometric_data) >= 5:
            recent_stress = [d["stress_level"] for d in biometric_data[-5:]]
            earlier_stress = [d["stress_level"] for d in biometric_data[:5]]
            recent_avg = sum(recent_stress) / len(recent_stress)
            earlier_avg = sum(earlier_stress) / len(earlier_stress)
            
            if recent_avg > earlier_avg * 1.2:
                trend = "上升"
            elif recent_avg < earlier_avg * 0.8:
                trend = "下降"
        
        # 综合健康评估
        health, health_details = BiometricIntegrator._evaluate_overall_health(avg_stress, avg_hrv, avg_hr)
        
        # 生成健康建议
        advice = BiometricIntegrator._generate_health_advice(biometric_data)
        
        return {
            "average_hr": round(avg_hr, 1),
            "average_hrv": round(avg_hrv, 1),
            "average_stress": round(avg_stress, 1),
            "max_stress": max_stress,
            "min_stress": min_stress,
            "stress_trend": trend,
            "overall_health": health,
            "health_details": health_details,
            "health_advice": advice,
            "data_points": len(biometric_data),
            "status": "success"
        }

    @staticmethod
    def _evaluate_overall_health(avg_stress: float, avg_hrv: float, avg_hr: float) -> tuple[str, str]:
        """评估整体健康状况"""
        issues = []
        
        if avg_stress >= 70:
            issues.append("压力水平较高")
        elif avg_stress >= 50:
            issues.append("压力水平适中")
        
        if avg_hrv < 50:
            issues.append("心率变异性偏低")
        elif avg_hrv < 70:
            issues.append("心率变异性一般")
        
        if avg_hr < 60:
            issues.append("心率偏慢")
        elif avg_hr > 100:
            issues.append("心率偏快")
        
        if not issues:
            return "优秀", "各项生理指标均在正常范围内"
        elif len(issues) == 1:
            return "良好", f"整体状况良好，但{issues[0]}"
        else:
            return "一般", f"存在以下需要关注的指标: {', '.join(issues)}"

    @staticmethod
    def _generate_health_advice(biometric_data: List[Dict[str, Any]]) -> str:
        """生成健康建议"""
        if not biometric_data:
            return "暂无足够数据生成建议"
        
        latest = biometric_data[-1]
        stress = latest["stress_level"]
        hr_status = latest["heart_rate_status"]
        hrv_status = latest["hrv_status"]
        gsr_status = latest["gsr_status"]
        
        advice_parts = []
        
        # 压力相关建议
        if stress >= 70:
            advice_parts.append("您的压力水平较高，建议立即进行深呼吸练习或冥想。")
        elif stress >= 50:
            advice_parts.append("您当前有一定的压力，建议适当休息并进行放松训练。")
        
        # 心率相关建议
        if hr_status == "偏快":
            advice_parts.append("心率偏快，建议放慢节奏，进行深呼吸。")
        elif hr_status == "过快":
            advice_parts.append("心率过快，请立即停止活动并寻求医疗建议。")
        elif hr_status == "偏慢":
            advice_parts.append("心率偏慢，如果伴随不适请咨询医生。")
        
        # HRV相关建议
        if hrv_status in ["一般", "较差"]:
            advice_parts.append("心率变异性较低，建议进行正念冥想以改善自主神经功能。")
        
        # GSR相关建议
        if gsr_status == "高度唤醒":
            advice_parts.append("身体处于高度唤醒状态，建议进行放松练习。")
        
        if not advice_parts:
            return "您的生理指标正常，继续保持良好的生活习惯。"
        
        return " ".join(advice_parts)

    @staticmethod
    def calibrate_baseline(biometric_samples: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        根据样本数据校准个人基准值
        :param biometric_samples: 至少5分钟的平静状态下的生理指标样本
        :return: 校准后的基准值
        """
        if len(biometric_samples) < 10:
            logger.warning("样本数量不足，无法准确校准")
            return {}
        
        # 计算平均值作为基准
        base_hr = sum(d["heart_rate"] for d in biometric_samples) / len(biometric_samples)
        base_hrv = sum(d["hrv"] for d in biometric_samples) / len(biometric_samples)
        base_breath = sum(d["breath_rate"] for d in biometric_samples) / len(biometric_samples)
        base_gsr = sum(d["gsr"] for d in biometric_samples) / len(biometric_samples)
        
        bp_samples = [d["blood_pressure"] for d in biometric_samples]
        base_systolic = sum(bp["systolic"] for bp in bp_samples) / len(bp_samples)
        base_diastolic = sum(bp["diastolic"] for bp in bp_samples) / len(bp_samples)
        
        calibration = {
            "base_heart_rate": round(base_hr, 1),
            "base_hrv": round(base_hrv, 1),
            "base_breath_rate": round(base_breath, 1),
            "base_gsr": round(base_gsr, 2),
            "base_systolic": round(base_systolic, 1),
            "base_diastolic": round(base_diastolic, 1),
            "calibration_time": datetime.now().isoformat(),
            "sample_count": len(biometric_samples)
        }
        
        logger.info(f"完成生理指标校准，基于 {len(biometric_samples)} 个样本")
        return calibration

    @staticmethod
    def compare_with_baseline(
        current_data: Dict[str, Any], 
        baseline: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        将当前生理指标与基准值进行比较
        :param current_data: 当前生理指标
        :param baseline: 基准值
        :return: 比较结果
        """
        comparisons = {}
        
        if "base_heart_rate" in baseline:
            hr_diff = current_data["heart_rate"] - baseline["base_heart_rate"]
            comparisons["heart_rate"] = {
                "current": current_data["heart_rate"],
                "baseline": baseline["base_heart_rate"],
                "difference": round(hr_diff, 1),
                "percent_change": round((hr_diff / baseline["base_heart_rate"]) * 100, 1),
                "status": BiometricIntegrator._interpret_diff(hr_diff, "heart_rate")
            }
        
        if "base_hrv" in baseline:
            hrv_diff = current_data["hrv"] - baseline["base_hrv"]
            comparisons["hrv"] = {
                "current": current_data["hrv"],
                "baseline": baseline["base_hrv"],
                "difference": round(hrv_diff, 1),
                "percent_change": round((hrv_diff / baseline["base_hrv"]) * 100, 1),
                "status": BiometricIntegrator._interpret_diff(hrv_diff, "hrv")
            }
        
        if "base_breath_rate" in baseline:
            breath_diff = current_data["breath_rate"] - baseline["base_breath_rate"]
            comparisons["breath_rate"] = {
                "current": current_data["breath_rate"],
                "baseline": baseline["base_breath_rate"],
                "difference": round(breath_diff, 1),
                "percent_change": round((breath_diff / baseline["base_breath_rate"]) * 100, 1),
                "status": BiometricIntegrator._interpret_diff(breath_diff, "breath_rate")
            }
        
        return {
            "comparisons": comparisons,
            "overall_status": BiometricIntegrator._get_overall_comparison_status(comparisons),
            "baseline_updated": baseline.get("calibration_time", "未知")
        }

    @staticmethod
    def _interpret_diff(diff: float, metric: str) -> str:
        """解释指标差异"""
        thresholds = {
            "heart_rate": {"low": -10, "high": 10},
            "hrv": {"low": -15, "high": 15},
            "breath_rate": {"low": -3, "high": 3},
            "gsr": {"low": -0.5, "high": 0.5}
        }
        
        t = thresholds.get(metric, {"low": -10, "high": 10})
        
        if diff < t["low"]:
            return "低于基准"
        elif diff > t["high"]:
            return "高于基准"
        else:
            return "正常"

    @staticmethod
    def _get_overall_comparison_status(comparisons: Dict[str, Any]) -> str:
        """获取整体比较状态"""
        if not comparisons:
            return "无法评估"
        
        abnormal_count = sum(1 for _, v in comparisons.items() if v["status"] != "正常")
        
        if abnormal_count == 0:
            return "正常"
        elif abnormal_count == 1:
            return "轻微异常"
        else:
            return "需要关注"