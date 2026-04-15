import os
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, models
from PIL import Image
from sklearn.model_selection import train_test_split

# 1. 定义增强型数据集类，支持两种格式：
#    格式 A: [image_name, label] + 外部图片文件夹
#    格式 B: [pixels, emotion] 纯 CSV 像素字符串 (类似 FER2013)
class MicroExpressionDataset(Dataset):
    def __init__(self, csv_file, img_dir=None, transform=None):
        self.data = pd.read_csv(csv_file)
        self.img_dir = img_dir
        self.transform = transform
        
        # 标签映射：统一将文字或数字转为 0-6
        # 如果你的 CSV 标签是数字 (0-6)，它会自动处理；如果是中文，则按此映射
        self.label_map = {"开心": 0, "悲伤": 1, "愤怒": 2, "惊讶": 3, "恐惧": 4, "厌恶": 5, "平静": 6}
        
        # 自动检测格式
        self.is_pixel_format = 'pixels' in self.data.columns
        print(f"检测到数据集格式: {'纯 CSV 像素字符串' if self.is_pixel_format else '图片路径+文件夹'}")

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        if self.is_pixel_format:
            # 格式 B: 从 CSV 字符串解析像素 (假设是 48x48 或 224x224 的空格分隔数字)
            pixels = self.data.iloc[idx]['pixels']
            if isinstance(pixels, str):
                pixels = np.array(pixels.split(), dtype='uint8')
            else:
                pixels = np.array(pixels, dtype='uint8')
            
            # 自动推断正方形尺寸 (通常 FER2013 是 48x48)
            size = int(np.sqrt(len(pixels)))
            image = pixels.reshape(size, size)
            image = Image.fromarray(image).convert('RGB')
            
            label_raw = self.data.iloc[idx]['emotion']
        else:
            # 格式 A: 从文件夹读取图片
            img_name = os.path.join(self.img_dir, str(self.data.iloc[idx, 0]))
            image = Image.open(img_name).convert('RGB')
            label_raw = self.data.iloc[idx, 1]

        # 处理标签
        if isinstance(label_raw, str):
            label = self.label_map.get(label_raw, 6)
        else:
            label = int(label_raw)

        if self.transform:
            image = self.transform(image)

        return image, label

# 2. 定义模型 (ResNet18)
class ExpressionModel(nn.Module):
    def __init__(self, num_classes=7):
        super(ExpressionModel, self).__init__()
        self.backbone = models.resnet18(pretrained=True)
        num_ftrs = self.backbone.fc.in_features
        self.backbone.fc = nn.Sequential(
            nn.Linear(num_ftrs, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, num_classes)
        )

    def forward(self, x):
        return self.backbone(x)

def train():
    # 配置路径 (你可以根据实际情况修改这里)
    CSV_PATH = "datasets/data.csv" # 你的 20000 行 CSV 文件
    IMG_DIR = "datasets/images/"   # 如果是格式 A，图片放这里
    MODEL_SAVE_PATH = "models/micro_expression.pth"
    ONNX_SAVE_PATH = "models/micro_expression.onnx"

    if not os.path.exists("models"):
        os.makedirs("models")

    # 数据预处理 (与后端推理逻辑对齐)
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    # 检查数据集是否存在
    if not os.path.exists(CSV_PATH):
        print(f"\n[提示] 找不到数据集文件: {CSV_PATH}")
        print(f"请将你的 CSV 文件重命名为 'data.csv' 并放入 'datasets/' 文件夹中。")
        return

    # 加载数据
    try:
        dataset = MicroExpressionDataset(CSV_PATH, IMG_DIR, transform=transform)
        if len(dataset) < 10:
            print("数据集样本太少，请检查 CSV 内容。")
            return
            
        train_idx, val_idx = train_test_split(list(range(len(dataset))), test_size=0.2)
        
        train_loader = DataLoader(torch.utils.data.Subset(dataset, train_idx), batch_size=32, shuffle=True)
        val_loader = DataLoader(torch.utils.data.Subset(dataset, val_idx), batch_size=32)

        # 初始化模型
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = ExpressionModel().to(device)
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(model.parameters(), lr=0.0001)

        # 训练循环
        epochs = 10;
        print(f"\n成功加载 {len(dataset)} 条数据。开始训练...")
        print(f"使用设备: {device}")
        
        for epoch in range(epochs):
            model.train()
            running_loss = 0.0
            for images, labels in train_loader:
                images, labels = images.to(device), labels.to(device)
                optimizer.zero_grad()
                outputs = model(images)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()
                running_loss += loss.item()
            
            print(f"Epoch {epoch+1}/{epochs}, 平均损失 Loss: {running_loss/len(train_loader):.4f}")

        # 保存训练好的模型 (.pth)
        torch.save(model.state_dict(), MODEL_SAVE_PATH)
        print(f"\n[1/2] PyTorch 权重已保存至: {MODEL_SAVE_PATH}")
        
        # 尝试导出为 ONNX (后端推理引擎使用)
        try:
            import onnx
            model.eval()
            dummy_input = torch.randn(1, 3, 224, 224).to(device)
            torch.onnx.export(model, dummy_input, ONNX_SAVE_PATH, 
                             input_names=['input'], output_names=['output'], 
                             dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}})
            print(f"[2/2] ONNX 模型已成功导出至: {ONNX_SAVE_PATH}")
            print("\n恭喜！模型已练成。现在重新启动后端服务，系统将自动使用该模型进行识别。")
        except (ImportError, ModuleNotFoundError):
            print("\n[注意] 导出 ONNX 失败：未检测到 'onnx' 库。")
            print("请运行: pip install onnx")
            print("由于 ONNX 模型缺失，后端目前仍会运行在 Demo 模式。")
        except Exception as export_error:
            print(f"\n[注意] 导出 ONNX 时发生错误: {export_error}")

    except Exception as e:
        if "onnx" in str(e).lower():
            # 如果是因为 onnx 导致的异常（虽然前面已经 try 了，但以防万一）
            print(f"\n训练已完成但导出失败: {e}")
            print("请运行: pip install onnx")
        else:
            print(f"\n训练过程中出错: {e}")
            print("请检查 CSV 列名是否正确 (例如格式 A 需要文件名列，格式 B 需要 'pixels' 和 'emotion' 列)")

if __name__ == "__main__":
    train()
