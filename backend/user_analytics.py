from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

from backend.db import get_connection, get_recent_recognitions, DB_TYPE


class UserAnalytics:
    """用户分析类"""
    
    @staticmethod
    def get_user_behavior_analysis(user_id: int, days: int = 30) -> Dict[str, Any]:
        """获取用户行为分析"""
        # 计算时间范围
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        start_date_str = start_date.isoformat(timespec="seconds")
        
        # 获取用户活动数据
        activity_data = UserAnalytics._get_user_activity(user_id, start_date_str)
        
        # 分析功能使用分布
        feature_usage = UserAnalytics._analyze_feature_usage(user_id, start_date_str)
        
        # 计算活跃度指标
        activity_metrics = UserAnalytics._calculate_activity_metrics(activity_data)
        
        return {
            "time_range": {
                "start": start_date_str,
                "end": end_date.isoformat(timespec="seconds"),
                "days": days
            },
            "activity_metrics": activity_metrics,
            "feature_usage": feature_usage,
            "trends": UserAnalytics._analyze_trends(activity_data)
        }
    
    @staticmethod
    def _get_user_activity(user_id: int, start_date: str) -> List[Dict[str, Any]]:
        """获取用户活动数据"""
        sql = """
        SELECT * FROM recognitions 
        WHERE user_id = ? AND created_at >= ? 
        ORDER BY created_at
        """
        if DB_TYPE == "mysql":
            sql = sql.replace("?", "%s")
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (user_id, start_date))
            rows = cursor.fetchall()
            
            result = []
            for row in rows:
                if isinstance(row, dict):
                    result.append(row)
                else:
                    result.append({
                        "id": row[0],
                        "user_id": row[1],
                        "created_at": row[2],
                        "source_type": row[3],
                        "label": row[4],
                        "confidence": row[5],
                        "intensity": row[6],
                        "duration_ms": row[7],
                        "payload_json": row[8]
                    })
            return result
    
    @staticmethod
    def _analyze_feature_usage(user_id: int, start_date: str) -> Dict[str, int]:
        """分析功能使用分布"""
        sql = """
        SELECT source_type, COUNT(*) as count 
        FROM recognitions 
        WHERE user_id = ? AND created_at >= ? 
        GROUP BY source_type
        """
        if DB_TYPE == "mysql":
            sql = sql.replace("?", "%s")
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (user_id, start_date))
            rows = cursor.fetchall()
            
            usage = {}
            for row in rows:
                if isinstance(row, dict):
                    usage[row["source_type"]] = row["count"]
                else:
                    usage[row[0]] = row[1]
            return usage
    
    @staticmethod
    def _calculate_activity_metrics(activity_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算活跃度指标"""
        if not activity_data:
            return {
                "total_activities": 0,
                "active_days": 0,
                "average_daily_activities": 0,
                "activity_frequency": "低"
            }
        
        # 计算总活动数
        total_activities = len(activity_data)
        
        # 计算活跃天数
        active_days = len(set(item["created_at"].split("T")[0] for item in activity_data))
        
        # 计算日均活动数
        average_daily_activities = total_activities / active_days if active_days > 0 else 0
        
        # 计算活动频率
        if average_daily_activities >= 5:
            frequency = "高"
        elif average_daily_activities >= 2:
            frequency = "中"
        else:
            frequency = "低"
        
        return {
            "total_activities": total_activities,
            "active_days": active_days,
            "average_daily_activities": round(average_daily_activities, 2),
            "activity_frequency": frequency
        }
    
    @staticmethod
    def _analyze_trends(activity_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """分析活动趋势"""
        if not activity_data:
            return []
        
        # 按日期分组
        daily_activities = {}
        for item in activity_data:
            date = item["created_at"].split("T")[0]
            if date not in daily_activities:
                daily_activities[date] = 0
            daily_activities[date] += 1
        
        # 转换为趋势数据
        trends = []
        for date, count in sorted(daily_activities.items()):
            trends.append({
                "date": date,
                "count": count
            })
        
        return trends
    
    @staticmethod
    def get_emotion_analysis(user_id: int, days: int = 30) -> Dict[str, Any]:
        """获取情绪分析"""
        # 获取最近的识别记录
        recognitions = get_recent_recognitions(user_id, limit=100)
        
        # 过滤时间范围
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        filtered_recognitions = [
            r for r in recognitions 
            if datetime.fromisoformat(r["created_at"]) >= start_date
        ]
        
        if not filtered_recognitions:
            return {
                "emotion_distribution": {},
                "dominant_emotion": None,
                "emotion_trends": [],
                "average_intensity": 0
            }
        
        # 分析情绪分布
        emotion_distribution = {}
        total_intensity = 0
        for item in filtered_recognitions:
            emotion = item["label"]
            emotion_distribution[emotion] = emotion_distribution.get(emotion, 0) + 1
            total_intensity += item["intensity"]
        
        # 计算主导情绪
        dominant_emotion = max(emotion_distribution, key=emotion_distribution.get)
        
        # 计算平均强度
        average_intensity = total_intensity / len(filtered_recognitions)
        
        # 分析情绪趋势
        emotion_trends = UserAnalytics._analyze_emotion_trends(filtered_recognitions)
        
        return {
            "emotion_distribution": emotion_distribution,
            "dominant_emotion": dominant_emotion,
            "average_intensity": round(average_intensity, 2),
            "emotion_trends": emotion_trends
        }
    
    @staticmethod
    def _analyze_emotion_trends(recognitions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """分析情绪趋势"""
        if not recognitions:
            return []
        
        # 按日期分组，计算每天的情绪分布
        daily_emotions = {}
        for item in recognitions:
            date = item["created_at"].split("T")[0]
            if date not in daily_emotions:
                daily_emotions[date] = {}
            emotion = item["label"]
            daily_emotions[date][emotion] = daily_emotions[date].get(emotion, 0) + 1
        
        # 转换为趋势数据
        trends = []
        for date, emotions in sorted(daily_emotions.items()):
            # 找出当天的主导情绪
            if emotions:
                dominant = max(emotions, key=emotions.get)
            else:
                dominant = "平静"
            
            trends.append({
                "date": date,
                "emotions": emotions,
                "dominant_emotion": dominant
            })
        
        return trends
    
    @staticmethod
    def get_user_segmentation(user_id: int) -> Dict[str, Any]:
        """获取用户分群"""
        # 获取用户行为数据
        behavior_analysis = UserAnalytics.get_user_behavior_analysis(user_id, days=90)
        
        # 获取情绪数据
        emotion_analysis = UserAnalytics.get_emotion_analysis(user_id, days=90)
        
        # 综合分析用户特征
        segment = UserAnalytics._determine_user_segment(behavior_analysis, emotion_analysis)
        
        return {
            "segment": segment,
            "behavior_profile": behavior_analysis["activity_metrics"],
            "emotion_profile": {
                "dominant_emotion": emotion_analysis["dominant_emotion"],
                "average_intensity": emotion_analysis["average_intensity"]
            },
            "recommendations": UserAnalytics._generate_recommendations(segment)
        }
    
    @staticmethod
    def _determine_user_segment(behavior: Dict[str, Any], emotion: Dict[str, Any]) -> str:
        """确定用户分群"""
        activity_frequency = behavior["activity_metrics"]["activity_frequency"]
        dominant_emotion = emotion["dominant_emotion"]
        
        # 基于活跃度和情绪的分群逻辑
        if activity_frequency == "高":
            if dominant_emotion in ["开心", "平静"]:
                return "积极活跃用户"
            elif dominant_emotion in ["悲伤", "恐惧"]:
                return "需要支持用户"
            else:
                return "高频使用用户"
        elif activity_frequency == "中":
            if dominant_emotion in ["开心", "惊讶"]:
                return "兴趣用户"
            else:
                return "普通用户"
        else:
            return "低活跃用户"
    
    @staticmethod
    def _generate_recommendations(segment: str) -> List[str]:
        """生成个性化推荐"""
        recommendations_map = {
            "积极活跃用户": [
                "尝试高级会员服务，享受无限报告功能",
                "参与我们的社区活动，分享您的使用经验",
                "考虑企业版API，将微表情识别集成到您的业务中"
            ],
            "需要支持用户": [
                "我们的情绪陪伴功能可以帮助您管理情绪",
                "考虑参加我们的情绪管理课程",
                "尝试使用我们的健康评估功能"
            ],
            "高频使用用户": [
                "高级会员可以为您提供更多高级功能",
                "企业版API适合您的高频使用需求",
                "我们可以为您提供定制化的分析方案"
            ],
            "兴趣用户": [
                "普通会员可以满足您的基本需求",
                "尝试我们的职场评估功能",
                "参与我们的情绪识别挑战活动"
            ],
            "普通用户": [
                "普通会员服务可以提升您的使用体验",
                "尝试我们的情绪报告功能",
                "关注我们的公众号获取更多情绪管理技巧"
            ],
            "低活跃用户": [
                "我们的快速识别功能非常适合您的使用场景",
                "尝试使用我们的情绪陪伴功能",
                "关注我们的优惠活动，享受会员折扣"
            ]
        }
        
        return recommendations_map.get(segment, [])
    
    @staticmethod
    def predict_churn_risk(user_id: int) -> Dict[str, Any]:
        """预测用户流失风险"""
        # 获取用户行为数据
        behavior_analysis = UserAnalytics.get_user_behavior_analysis(user_id, days=30)
        
        # 计算流失风险
        risk_score = UserAnalytics._calculate_churn_risk(behavior_analysis)
        
        # 确定风险等级
        if risk_score >= 70:
            risk_level = "高"
        elif risk_score >= 40:
            risk_level = "中"
        else:
            risk_level = "低"
        
        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "factors": UserAnalytics._identify_risk_factors(behavior_analysis),
            "interventions": UserAnalytics._generate_interventions(risk_level)
        }
    
    @staticmethod
    def _calculate_churn_risk(behavior: Dict[str, Any]) -> int:
        """计算流失风险分数"""
        metrics = behavior["activity_metrics"]
        
        # 基于活跃度计算风险
        if metrics["activity_frequency"] == "低":
            base_score = 70
        elif metrics["activity_frequency"] == "中":
            base_score = 40
        else:
            base_score = 10
        
        # 基于活跃天数调整
        if metrics["active_days"] < 5:
            base_score += 20
        elif metrics["active_days"] < 10:
            base_score += 10
        
        # 基于日均活动数调整
        if metrics["average_daily_activities"] < 1:
            base_score += 10
        
        return min(100, base_score)
    
    @staticmethod
    def _identify_risk_factors(behavior: Dict[str, Any]) -> List[str]:
        """识别风险因素"""
        factors = []
        metrics = behavior["activity_metrics"]
        
        if metrics["activity_frequency"] == "低":
            factors.append("使用频率低")
        if metrics["active_days"] < 5:
            factors.append("活跃天数少")
        if metrics["average_daily_activities"] < 1:
            factors.append("日均使用次数少")
        
        return factors
    
    @staticmethod
    def _generate_interventions(risk_level: str) -> List[str]:
        """生成干预措施"""
        interventions_map = {
            "高": [
                "发送个性化邮件，提醒用户使用我们的功能",
                "提供限时会员折扣",
                "推荐用户尝试我们的核心功能"
            ],
            "中": [
                "发送功能更新通知",
                "推荐用户尝试新功能",
                "提供使用技巧指南"
            ],
            "低": [
                "定期发送使用报告",
                "邀请用户参与反馈",
                "推荐高级功能"
            ]
        }
        
        return interventions_map.get(risk_level, [])
