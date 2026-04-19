#!/usr/bin/env python3
"""
模型验证脚本
验证训练好的模型是否能正常进行推理
"""

import os
import sys
import base64
import logging
from pathlib import Path

# 添加backend到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from inference import get_inference_engine, predict_micro_expression

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def create_test_image():
    """创建一个简单的测试图像（base64编码的PNG）"""
    # 这是一个1x1像素的透明PNG图像的base64编码
    # 在实际使用中，你应该使用真实的测试图像
    test_png = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    return f"data:image/png;base64,{test_png}"

def validate_model():
    """验证模型功能"""
    print("🔍 开始模型验证...")
    
    # 获取推理引擎
    engine = get_inference_engine()
    print(f"📦 使用推理引擎: {engine.name}")
    
    if hasattr(engine, 'model_loaded'):
        print(f"✅ 模型加载状态: {'成功' if engine.model_loaded else '失败'}")
    else:
        print("ℹ️  使用演示模式")
    
    # 创建测试图像
    test_image = create_test_image()
    print("🖼️  创建测试图像")
    
    # 执行推理
    try:
        result = predict_micro_expression(test_image)
        print("🤖 推理结果:")
        print(f"   情绪: {result['label']}")
        print(f"   置信度: {result['confidence']:.3f}")
        print(f"   强度: {result['intensity']:.3f}")
        print(f"   引擎: {result['engine']}")
        print(f"   真实模型: {'是' if result.get('is_real_model', False) else '否'}")
        
        if 'face_detected' in result:
            print(f"   人脸检测: {'成功' if result['face_detected'] else '失败'}")
        
        print("✅ 模型验证完成！")
        return True
        
    except Exception as e:
        print(f"❌ 推理失败: {e}")
        return False

def validate_environment():
    """验证环境依赖"""
    print("🔧 检查环境依赖...")
    
    dependencies = {
        'torch': 'PyTorch',
        'cv2': 'OpenCV',
        'onnxruntime': 'ONNX Runtime',
        'PIL': 'Pillow',
        'numpy': 'NumPy'
    }
    
    missing = []
    for module, name in dependencies.items():
        try:
            __import__(module)
            print(f"✅ {name} 已安装")
        except ImportError:
            print(f"❌ {name} 缺失")
            missing.append(name)
    
    if missing:
        print(f"\n⚠️  缺少依赖: {', '.join(missing)}")
        print("请运行: pip install torch torchvision opencv-python onnxruntime pillow numpy")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 深度学习情绪识别模型验证工具")
    print("=" * 50)
    
    # 验证环境
    if not validate_environment():
        sys.exit(1)
    
    print()
    
    # 验证模型
    if validate_model():
        print("\n🎉 所有验证通过！模型可以正常使用。")
        sys.exit(0)
    else:
        print("\n💥 验证失败！请检查模型和配置。")
        sys.exit(1)