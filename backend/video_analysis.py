from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import os
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.inference import get_inference_engine


class VideoAnalyzer:
    """
    视频流实时情绪分析模块
    支持实时帧分析和情绪趋势追踪
    """

    def __init__(self):
        self.engine = get_inference_engine()
        self.active_sessions: Dict[str, SessionState] = {}

    def create_session(self, user_id: int) -> str:
        """创建视频分析会话"""
        session_id = hashlib.sha256(f"{user_id}_{datetime.now().timestamp()}".encode()).hexdigest()[:16]
        self.active_sessions[session_id] = SessionState(user_id=user_id)
        return session_id

    def process_frame(self, session_id: str, frame_base64: str, timestamp: float) -> Dict[str, Any]:
        """处理单帧图像"""
        if session_id not in self.active_sessions:
            raise ValueError("会话不存在")
        
        session = self.active_sessions[session_id]
        
        # 执行情绪识别
        result = self.engine.predict(frame_base64)
        
        # 更新会话状态
        session.add_frame(result, timestamp)
        
        return result

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """获取会话分析摘要"""
        if session_id not in self.active_sessions:
            raise ValueError("会话不存在")
        
        session = self.active_sessions[session_id]
        return session.get_summary()

    def close_session(self, session_id: str) -> Dict[str, Any]:
        """关闭会话并返回最终分析报告"""
        if session_id not in self.active_sessions:
            raise ValueError("会话不存在")
        
        summary = self.get_session_summary(session_id)
        del self.active_sessions[session_id]
        
        return summary

    def get_live_emotion(self, session_id: str) -> Dict[str, Any]:
        """获取实时情绪状态"""
        if session_id not in self.active_sessions:
            raise ValueError("会话不存在")
        
        session = self.active_sessions[session_id]
        return session.get_live_state()


class SessionState:
    """视频分析会话状态"""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.start_time = datetime.now()
        self.frames: List[FrameData] = []
        self.emotion_history: List[str] = []
        self.current_emotion = "平静"
        self.confidence_sum = 0.0
        
    def add_frame(self, result: Dict[str, Any], timestamp: float):
        """添加帧数据"""
        frame_data = FrameData(
            timestamp=timestamp,
            label=result["label"],
            confidence=result["confidence"],
            intensity=result["intensity"],
            duration_ms=result["duration_ms"]
        )
        self.frames.append(frame_data)
        self.emotion_history.append(result["label"])
        self.current_emotion = result["label"]
        self.confidence_sum += result["confidence"]
        
    def get_summary(self) -> Dict[str, Any]:
        """获取会话摘要"""
        if not self.frames:
            return {
                "session_duration": 0,
                "frame_count": 0,
                "dominant_emotion": "平静",
                "emotion_distribution": {},
                "average_confidence": 0.0,
                "average_intensity": 0.0,
                "emotion_trend": [],
                "start_time": self.start_time.isoformat(),
                "end_time": datetime.now().isoformat()
            }
        
        duration = (datetime.now() - self.start_time).total_seconds()
        
        counter = Counter(self.emotion_history)
        dominant_emotion = counter.most_common(1)[0][0]
        
        avg_confidence = self.confidence_sum / len(self.frames)
        avg_intensity = sum(f.intensity for f in self.frames) / len(self.frames)
        
        # 生成情绪趋势（每5帧取一个点）
        trend = []
        window_size = 5
        for i in range(0, len(self.emotion_history), window_size):
            window = self.emotion_history[i:i+window_size]
            window_counter = Counter(window)
            window_dominant = window_counter.most_common(1)[0][0]
            trend.append({
                "frame_range": f"{i+1}-{min(i+window_size, len(self.emotion_history))}",
                "emotion": window_dominant,
                "count": len(window)
            })
        
        return {
            "session_duration": round(duration, 2),
            "frame_count": len(self.frames),
            "dominant_emotion": dominant_emotion,
            "emotion_distribution": dict(counter),
            "average_confidence": round(avg_confidence, 3),
            "average_intensity": round(avg_intensity, 3),
            "emotion_trend": trend,
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now().isoformat()
        }
        
    def get_live_state(self) -> Dict[str, Any]:
        """获取实时状态"""
        if not self.frames:
            return {
                "current_emotion": "平静",
                "confidence": 0.0,
                "intensity": 0.0,
                "frame_count": 0,
                "session_duration": round((datetime.now() - self.start_time).total_seconds(), 2)
            }
        
        latest = self.frames[-1]
        return {
            "current_emotion": latest.label,
            "confidence": latest.confidence,
            "intensity": latest.intensity,
            "frame_count": len(self.frames),
            "session_duration": round((datetime.now() - self.start_time).total_seconds(), 2)
        }


class FrameData:
    """帧数据"""
    
    def __init__(self, timestamp: float, label: str, confidence: float, intensity: float, duration_ms: int):
        self.timestamp = timestamp
        self.label = label
        self.confidence = confidence
        self.intensity = intensity
        self.duration_ms = duration_ms


# 全局视频分析器实例
video_analyzer = VideoAnalyzer()
