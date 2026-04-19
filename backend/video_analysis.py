from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import logging
import os
import threading
import time
from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from backend.inference import get_cached_inference_engine

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class VideoAnalyzer:
    """
    视频流实时情绪分析模块
    支持实时帧分析和情绪趋势追踪
    增强特性：
    - 会话超时管理
    - 帧处理错误重试机制
    - 情绪平滑滤波（避免抖动）
    - 会话状态持久化
    """

    # 情绪平滑配置
    SMOOTHING_WINDOW_SIZE = 5  # 滑动窗口大小
    MIN_CONFIDENCE_FOR_UPDATE = 0.4  # 更新情绪所需的最小置信度

    def __init__(self, session_timeout_minutes: int = 30):
        self.engine = get_cached_inference_engine()
        self.active_sessions: Dict[str, SessionState] = {}
        self._lock = threading.Lock()
        self._session_timeout = timedelta(minutes=session_timeout_minutes)
        self._cleanup_interval = 30  # 清理间隔（秒）- 缩短以更快释放资源
        self._max_concurrent_sessions = 100  # 最大并发会话数
        self._start_cleanup_thread()
        
        logger.info("视频分析器已初始化")

    def _start_cleanup_thread(self):
        """启动会话清理线程"""
        def cleanup_loop():
            while True:
                try:
                    self._cleanup_expired_sessions()
                except Exception as e:
                    logger.error(f"会话清理失败: {e}")
                time.sleep(self._cleanup_interval)
        
        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        cleanup_thread.start()
        logger.debug("会话清理线程已启动")

    def _cleanup_expired_sessions(self):
        """清理过期会话"""
        with self._lock:
            now = datetime.now()
            expired_sessions = []
            
            for session_id, session in self.active_sessions.items():
                if now - session.last_activity_time > self._session_timeout:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                logger.info(f"会话超时自动关闭: {session_id}")
                del self.active_sessions[session_id]

    def create_session(self, user_id: int) -> str:
        """创建视频分析会话"""
        # 检查并发会话数限制
        with self._lock:
            if len(self.active_sessions) >= self._max_concurrent_sessions:
                raise ValueError("当前系统会话数已达上限，请稍后重试")
            
            session_id = hashlib.sha256(f"{user_id}_{datetime.now().timestamp()}_{os.urandom(8)}".encode()).hexdigest()[:16]
            self.active_sessions[session_id] = SessionState(user_id=user_id)
        
        logger.info(f"创建新会话: {session_id}, 用户: {user_id}")
        return session_id

    def get_session_count(self) -> int:
        """获取当前活跃会话数"""
        with self._lock:
            return len(self.active_sessions)

    def process_frame(self, session_id: str, frame_base64: str, timestamp: float) -> Dict[str, Any]:
        """处理单帧图像（带错误重试机制和情绪平滑）"""
        if session_id not in self.active_sessions:
            raise ValueError("会话不存在")
        
        session = self.active_sessions[session_id]
        session.update_activity()
        
        # 执行情绪识别（带重试）
        max_retries = 3
        retry_delay = 0.1
        result = None
        
        for attempt in range(max_retries):
            try:
                result = self.engine.predict(frame_base64)
                break
            except Exception as e:
                logger.warning(f"帧处理失败 (尝试 {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
        
        if result is None:
            # 所有重试都失败
            session.record_error(f"帧处理失败: 所有重试均失败")
            return {
                "label": "平静",
                "confidence": 0.0,
                "intensity": 0.0,
                "duration_ms": 0,
                "secondary_label": "平静",
                "engine": self.engine.name,
                "engine_version": self.engine.version,
                "error": "帧处理失败"
            }
        
        # 应用情绪平滑滤波
        smoothed_result = self._apply_smoothing(session, result)
        session.add_frame(smoothed_result, timestamp)
        
        return smoothed_result

    def _apply_smoothing(self, session: 'SessionState', current_result: Dict[str, Any]) -> Dict[str, Any]:
        """应用情绪平滑滤波，避免情绪快速抖动"""
        if len(session.frames) < self.SMOOTHING_WINDOW_SIZE:
            # 帧数不足，直接返回当前结果
            return current_result
        
        confidence = current_result.get("confidence", 0.0)
        
        # 低置信度结果不参与平滑
        if confidence < self.MIN_CONFIDENCE_FOR_UPDATE:
            # 使用历史最可能的情绪
            recent_emotions = [f.label for f in session.frames[-self.SMOOTHING_WINDOW_SIZE:]]
            emotion_counts = Counter(recent_emotions)
            most_common = emotion_counts.most_common(1)
            if most_common:
                smoothed_label = most_common[0][0]
                return {
                    **current_result,
                    "label": smoothed_label,
                    "smoothed": True,
                    "original_label": current_result["label"]
                }
        
        # 检查情绪是否与最近历史一致
        recent_labels = [f.label for f in session.frames[-self.SMOOTHING_WINDOW_SIZE//2:]]
        if recent_labels and current_result["label"] != recent_labels[-1]:
            # 情绪发生变化，检查是否是有效变化
            same_count = sum(1 for l in recent_labels if l == current_result["label"])
            if same_count < 2:  # 至少需要2个相同情绪才确认变化
                # 使用历史情绪
                return {
                    **current_result,
                    "label": recent_labels[-1],
                    "smoothed": True,
                    "original_label": current_result["label"]
                }
        
        return {**current_result, "smoothed": False}

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """获取会话分析摘要"""
        if session_id not in self.active_sessions:
            raise ValueError("会话不存在")
        
        session = self.active_sessions[session_id]
        session.update_activity()
        
        return session.get_summary()

    def close_session(self, session_id: str) -> Dict[str, Any]:
        """关闭会话并返回最终分析报告"""
        if session_id not in self.active_sessions:
            raise ValueError("会话不存在")
        
        summary = self.get_session_summary(session_id)
        
        with self._lock:
            del self.active_sessions[session_id]
        
        logger.info(f"会话已关闭: {session_id}")
        return summary

    def get_live_emotion(self, session_id: str) -> Dict[str, Any]:
        """获取实时情绪状态"""
        if session_id not in self.active_sessions:
            raise ValueError("会话不存在")
        
        session = self.active_sessions[session_id]
        session.update_activity()
        
        return session.get_live_state()

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话基本信息"""
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        return {
            "session_id": session_id,
            "user_id": session.user_id,
            "frame_count": len(session.frames),
            "session_duration": round((datetime.now() - session.start_time).total_seconds(), 2),
            "last_activity": session.last_activity_time.isoformat(),
            "current_emotion": session.current_emotion
        }

    def list_active_sessions(self) -> List[Dict[str, Any]]:
        """列出所有活跃会话"""
        with self._lock:
            sessions = []
            for session_id, session in self.active_sessions.items():
                sessions.append({
                    "session_id": session_id,
                    "user_id": session.user_id,
                    "frame_count": len(session.frames),
                    "session_duration": round((datetime.now() - session.start_time).total_seconds(), 2),
                    "last_activity": session.last_activity_time.isoformat()
                })
            return sessions


class SessionState:
    """视频分析会话状态"""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.start_time = datetime.now()
        self.last_activity_time = datetime.now()
        self.frames: List[FrameData] = []
        self.emotion_history: List[str] = []
        self.current_emotion = "平静"
        self.confidence_sum = 0.0
        self.errors: List[str] = []
    
    def update_activity(self):
        """更新最后活动时间"""
        self.last_activity_time = datetime.now()
    
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
    
    def record_error(self, error_message: str):
        """记录错误"""
        self.errors.append(f"{datetime.now().isoformat()}: {error_message}")
    
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
                "end_time": datetime.now().isoformat(),
                "error_count": len(self.errors),
                "status": "no_data"
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
            window_confidence_avg = sum(
                f.confidence for f in self.frames[i:i+window_size]
            ) / len(window) if window else 0
            trend.append({
                "frame_range": f"{i+1}-{min(i+window_size, len(self.emotion_history))}",
                "emotion": window_dominant,
                "count": len(window),
                "avg_confidence": round(window_confidence_avg, 3)
            })
        
        # 计算情绪稳定性
        stability_score = self._calculate_stability()
        
        return {
            "session_duration": round(duration, 2),
            "frame_count": len(self.frames),
            "dominant_emotion": dominant_emotion,
            "emotion_distribution": dict(counter),
            "average_confidence": round(avg_confidence, 3),
            "average_intensity": round(avg_intensity, 3),
            "emotion_trend": trend,
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "error_count": len(self.errors),
            "stability_score": stability_score,
            "status": "completed"
        }
        
    def _calculate_stability(self) -> float:
        """计算情绪稳定性分数（0-100，越高越稳定）"""
        if len(self.emotion_history) < 2:
            return 100.0
        
        # 计算情绪变化频率
        changes = 0
        for i in range(1, len(self.emotion_history)):
            if self.emotion_history[i] != self.emotion_history[i-1]:
                changes += 1
        
        change_rate = changes / (len(self.emotion_history) - 1)
        stability = max(0, 100 - (change_rate * 100))
        
        return round(stability, 2)
        
    def get_live_state(self) -> Dict[str, Any]:
        """获取实时状态"""
        if not self.frames:
            return {
                "current_emotion": "平静",
                "confidence": 0.0,
                "intensity": 0.0,
                "frame_count": 0,
                "session_duration": round((datetime.now() - self.start_time).total_seconds(), 2),
                "status": "waiting"
            }
        
        latest = self.frames[-1]
        return {
            "current_emotion": latest.label,
            "confidence": latest.confidence,
            "intensity": latest.intensity,
            "frame_count": len(self.frames),
            "session_duration": round((datetime.now() - self.start_time).total_seconds(), 2),
            "status": "active"
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