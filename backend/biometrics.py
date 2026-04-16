from __future__ import annotations

import hashlib
import math
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.inference import EMOTIONS


class BiometricIntegrator:
    """
    生理指标集成模块
    支持模拟生理数据和真实数据的整合分析
    """

    @staticmethod
    def simulate_biometrics(emotion: str, intensity: float, base_hr: int = 72) -> Dict[str, Any]:
        """
        基于情绪模拟生理指标
        :param emotion: 当前情绪
        :param intensity: 情绪强度 (0-1)
        :param base_hr: 基础心率
        :return: 模拟的生理指标
        """
        # 情绪对心率的影响系数
        hr_effect = {
            "开心": 0.15,
            "悲伤": 0.05,
            "愤怒": 0.35,
            "惊讶": 0.25,
            "恐惧": 0.40,
            "厌恶": 0.10,
            "平静": -0.05
        }
        
        # 情绪对HRV的影响系数
        hrv_effect = {
            "开心": 0.10,
            "悲伤": -0.15,
            "愤怒": -0.30,
            "惊讶": -0.10,
            "恐惧": -0.35,
            "厌恶": -0.20,
            "平静": 0.20
        }
        
        # 计算心率
        hr_delta = hr_effect.get(emotion, 0) * intensity * 20
        heart_rate = base_hr + int(hr_delta)
        
        # 计算HRV（心率变异性）
        base_hrv = 70 + int(hashlib.sha256(str(intensity).encode()).digest()[0] % 30)
        hrv_delta = hrv_effect.get(emotion, 0) * intensity * 20
        hrv_value = max(20, min(150, base_hrv + int(hrv_delta)))
        
        # 计算呼吸率
        base_breath = 15
        breath_delta = hr_delta * 0.3
        breath_rate = max(8, min(30, int(base_breath + breath_delta)))
        
        # 计算皮肤电反应（GSR）
        gsr_base = 2.0
        gsr_delta = (0.3 + hr_effect.get(emotion, 0) * intensity) * 2
        gsr_value = max(0.5, min(5.0, round(gsr_base + gsr_delta, 2)))
        
        # 计算血压
        base_systolic = 115
        base_diastolic = 75
        bp_delta = hr_effect.get(emotion, 0) * intensity * 10
        systolic = max(90, min(160, int(base_systolic + bp_delta)))
        diastolic = max(60, min(100, int(base_diastolic + bp_delta * 0.6)))
        
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
                "status": BiometricIntegrator._get_bp_status(systolic, diastolic)
            },
            "stress_level": BiometricIntegrator._calculate_stress_level(heart_rate, hrv_value, gsr_value),
            "emotion": emotion,
            "intensity": intensity
        }

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
        
        # 综合评分
        stress_score = int((hr_score * 0.3 + hrv_score * 0.4 + gsr_score * 0.3))
        
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
                "overall_health": "未评估"
            }
        
        avg_hr = sum(d["heart_rate"] for d in biometric_data) / len(biometric_data)
        avg_hrv = sum(d["hrv"] for d in biometric_data) / len(biometric_data)
        avg_stress = sum(d["stress_level"] for d in biometric_data) / len(biometric_data)
        max_stress = max(d["stress_level"] for d in biometric_data)
        min_stress = min(d["stress_level"] for d in biometric_data)
        
        # 判断压力趋势
        if len(biometric_data) >= 3:
            recent_stress = [d["stress_level"] for d in biometric_data[-3:]]
            earlier_stress = [d["stress_level"] for d in biometric_data[:3]]
            if sum(recent_stress) > sum(earlier_stress) * 1.2:
                trend = "上升"
            elif sum(recent_stress) < sum(earlier_stress) * 0.8:
                trend = "下降"
            else:
                trend = "稳定"
        else:
            trend = "稳定"
        
        # 综合健康评估
        if avg_stress < 30:
            health = "优秀"
        elif avg_stress < 50:
            health = "良好"
        elif avg_stress < 70:
            health = "一般"
        else:
            health = "较差"
        
        return {
            "average_hr": round(avg_hr, 1),
            "average_hrv": round(avg_hrv, 1),
            "average_stress": round(avg_stress, 1),
            "max_stress": max_stress,
            "min_stress": min_stress,
            "stress_trend": trend,
            "overall_health": health,
            "data_points": len(biometric_data)
        }

    @staticmethod
    def _get_health_advice(biometrics: Dict[str, Any]) -> str:
        """根据生理指标生成健康建议"""
        stress = biometrics["stress_level"]
        hr_status = biometrics["heart_rate_status"]
        hrv_status = biometrics["hrv_status"]
        
        advice_parts = []
        
        if stress >= 70:
            advice_parts.append("您的压力水平较高，建议立即进行放松训练。")
        elif stress >= 50:
            advice_parts.append("您当前有一定的压力，建议适当休息。")
        
        if hr_status in ["偏快", "过快"]:
            advice_parts.append("心率偏快，建议进行深呼吸练习。")
        
        if hrv_status in ["一般", "较差"]:
            advice_parts.append("心率变异性较低，建议进行正念冥想。")
        
        if not advice_parts:
            return "您的生理指标正常，继续保持良好的生活习惯。"
        
        return " ".join(advice_parts)
