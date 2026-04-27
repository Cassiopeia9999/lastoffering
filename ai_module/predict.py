"""
校园失物招领系统 - AI 推理模块（带 GUI 界面）
功能：
  1. predict()       - 分类预测（返回类别 + 置信度）
  2. extract_features() - 提取 L2 归一化特征向量（用于以图搜图）
  3. GUI 界面        - 可视化预测、切换模型版本
框架：PyTorch + EfficientNet-B0
"""

import os
import json
import glob
import numpy as np
import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ==================== 模型结构（与 train.py 保持一致）====================

class LostItemModel(nn.Module):
    def __init__(self, num_classes: int, feature_dim: int = 512):
        super().__init__()
        backbone = models.efficientnet_b0(weights=None)
        in_features = backbone.classifier[1].in_features

        self.backbone = backbone.features
        self.pool = backbone.avgpool

        self.feature_head = nn.Sequential(
            nn.Linear(in_features, feature_dim),
            nn.BatchNorm1d(feature_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
        )
        self.classifier = nn.Linear(feature_dim, num_classes)

    def forward_features(self, x):
        x = self.backbone(x)
        x = self.pool(x)
        x = x.flatten(1)
        feat = self.feature_head(x)
        return nn.functional.normalize(feat, p=2, dim=1)

    def forward(self, x):
        feat = self.forward_features(x)
        return self.classifier(feat)


# ==================== 推理类 ====================

class LostItemAI:
    """
    失物识别 AI：分类 + 特征提取 + 以图搜图
    支持加载不同版本的模型
    """

    def __init__(self, version: str = None):
        """
        初始化模型
        Args:
            version: 模型版本，如 "V1", "V2"，None 表示使用 latest
        """
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_dir = os.path.join(self.base_dir, "models")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.prototype_mode = False
        self.prototypes = None
        self.prototype_temperature = 12.0
        self.backbone = None
        self.pool = None
        self.idx_to_class = None
        self.img_size = 224
        self.version = version
        self.meta = None

        self._load_model(version)

    def _build_pretrained_feature_extractor(self):
        """加载 ImageNet 预训练 EfficientNet-B0 特征提取器（V0 基线使用）"""
        backbone = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.DEFAULT)
        self.backbone = backbone.features.to(self.device)
        self.pool = backbone.avgpool.to(self.device)
        self.backbone.eval()
        self.pool.eval()

    def _extract_backbone_feature(self, img_path: str):
        """使用预训练骨干提取 L2 归一化特征"""
        tensor = self._load_image(img_path)
        with torch.no_grad():
            feat = self.backbone(tensor)
            feat = self.pool(feat)
            feat = feat.flatten(1)
            feat = nn.functional.normalize(feat, p=2, dim=1)
        return feat.squeeze(0).cpu().numpy()

    def _load_model(self, version: str = None):
        """加载指定版本的模型，如果没有指定版本且latest不存在，自动寻找可用版本"""
        if version:
            model_path = os.path.join(self.model_dir, f"lost_item_model_{version}.pth")
            meta_path = os.path.join(self.model_dir, f"model_meta_{version}.json")
        else:
            # 先尝试加载 latest 版本（不带版本号）
            model_path = os.path.join(self.model_dir, "lost_item_model.pth")
            meta_path = os.path.join(self.model_dir, "model_meta.json")
            
            # 如果 latest 不存在，自动寻找最高版本
            if not os.path.exists(model_path) or not os.path.exists(meta_path):
                available_versions = self.get_available_versions()
                # 过滤掉 latest，只保留 V1, V2 等版本
                versioned = [v for v in available_versions if v != "latest"]
                if versioned:
                    # 使用版本号最高的
                    version = versioned[0]
                    model_path = os.path.join(self.model_dir, f"lost_item_model_{version}.pth")
                    meta_path = os.path.join(self.model_dir, f"model_meta_{version}.json")
                    print(f"[INFO] latest版本不存在，自动加载 {version} 版本")

        if not os.path.exists(meta_path):
            print(f"[ERROR] 找不到模型元数据文件: {meta_path}")
            print(f"[ERROR] 请确保模型已训练并保存在 {self.model_dir}")
            return False

        with open(meta_path, "r", encoding="utf-8") as f:
            self.meta = json.load(f)

        self.img_size = self.meta["img_size"]
        self.idx_to_class = {int(k): v for k, v in self.meta["idx_to_class"].items()}

        if self.meta.get("model_type") == "prototype":
            prototype_path = os.path.join(
                self.model_dir,
                self.meta.get("prototype_file", f"class_prototypes_{self.meta.get('version', 'V0')}.npz")
            )
            if not os.path.exists(prototype_path):
                print(f"[ERROR] 找不到 V0 原型文件: {prototype_path}")
                return False

            data = np.load(prototype_path)
            self.prototypes = data["prototypes"].astype(np.float32)
            self.prototype_temperature = float(self.meta.get("temperature", 12.0))
            self.prototype_mode = True
            self._build_pretrained_feature_extractor()

            self.transform = transforms.Compose([
                transforms.Resize((self.img_size, self.img_size)),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
            ])

            self.version = self.meta.get("version", version or "V0")
            print(f"[INFO] 已加载 V0 预训练基线模型：{self.version}")
            return True

        if not os.path.exists(model_path):
            print(f"[ERROR] 找不到模型文件: {model_path}")
            print(f"[ERROR] 请确保模型已训练并保存在 {self.model_dir}")
            return False

        num_classes = self.meta["num_classes"]
        feature_dim = self.meta["feature_dim"]

        self.model = LostItemModel(num_classes, feature_dim).to(self.device)
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.eval()

        self.transform = transforms.Compose([
            transforms.Resize((self.img_size, self.img_size)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])
        
        self.version = version or self.meta.get("version", "latest")
        return True

    def get_available_versions(self):
        """获取所有可用的模型版本，按版本号降序排列（V2在V1前面）"""
        versions = []
        
        # 检查 latest 版本
        if os.path.exists(os.path.join(self.model_dir, "lost_item_model.pth")):
            versions.append("latest")
        
        # 检查版本化模型
        model_files = glob.glob(os.path.join(self.model_dir, "lost_item_model_V*.pth"))
        for f in model_files:
            filename = os.path.basename(f)
            version = filename.replace("lost_item_model_", "").replace(".pth", "")
            versions.append(version)
        
        # 排序：latest 在最前，其他按版本号数字降序（V2在V1前面）
        def version_key(x):
            if x == "latest":
                return (0, 0)  # latest 排第一
            # 提取版本号数字
            try:
                num = int(x.replace("V", ""))
                return (1, -num)  # 数字大的排前面
            except:
                return (1, 0)
        
        return sorted(versions, key=version_key)

    def _load_image(self, img_path: str) -> torch.Tensor:
        """加载并预处理图片 → (1, C, H, W) tensor"""
        img = Image.open(img_path).convert("RGB")
        return self.transform(img).unsqueeze(0).to(self.device)

    def predict(self, img_path: str):
        """
        预测物品类别
        返回：(class_id: str, confidence: float)
        如模型未加载则返回 (None, 0.0)
        """
        if self.prototype_mode:
            topk = self.predict_topk(img_path, k=1)
            return topk[0] if topk else (None, 0.0)

        if self.model is None:
            return None, 0.0

        tensor = self._load_image(img_path)
        with torch.no_grad():
            logits = self.model(tensor)
            probs = torch.softmax(logits, dim=1)
            confidence, idx = probs.max(dim=1)

        class_id = self.idx_to_class.get(idx.item(), "unknown")
        return class_id, round(confidence.item(), 4)

    def predict_topk(self, img_path: str, k: int = 5):
        """
        预测 Top-K 类别
        返回：[(class_id, confidence), ...]
        """
        if self.prototype_mode:
            feat = self._extract_backbone_feature(img_path)
            sims = self.prototypes @ feat
            logits = torch.tensor(sims * self.prototype_temperature, dtype=torch.float32)
            probs = torch.softmax(logits, dim=0).cpu().numpy()
            top_idx = np.argsort(probs)[::-1][:min(k, len(probs))]

            results = []
            for idx in top_idx:
                class_id = self.idx_to_class.get(int(idx), "unknown")
                results.append((class_id, round(float(probs[idx]), 4)))
            return results

        if self.model is None:
            return []

        tensor = self._load_image(img_path)
        with torch.no_grad():
            logits = self.model(tensor)
            probs = torch.softmax(logits, dim=1)
            topk = probs.topk(k=min(k, len(self.idx_to_class)))

        results = []
        for conf, idx in zip(topk.values[0], topk.indices[0]):
            class_id = self.idx_to_class.get(idx.item(), "unknown")
            results.append((class_id, round(conf.item(), 4)))
        return results

    def extract_features(self, img_path: str):
        """提取 L2 归一化特征向量"""
        if self.prototype_mode:
            return self._extract_backbone_feature(img_path)

        if self.model is None:
            return None

        tensor = self._load_image(img_path)
        with torch.no_grad():
            feat = self.model.forward_features(tensor)

        return feat.squeeze(0).cpu().numpy()


# ==================== GUI 界面 ====================

class PredictGUI:
    """预测工具图形界面"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("校园失物招领 - AI 分类预测")
        self.root.geometry("800x600")
        self.root.configure(bg="#f0f0f0")
        
        self.ai = None
        self.current_image_path = None
        self.current_image_pil = None
        
        self._setup_ui()
        self._init_model()

    def _setup_ui(self):
        """设置界面布局"""
        # 顶部控制栏
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(fill="x")
        
        # 模型选择
        ttk.Label(control_frame, text="模型版本:").pack(side="left", padx=5)
        self.model_var = ttk.Combobox(control_frame, width=15, state="readonly")
        self.model_var.pack(side="left", padx=5)
        self.model_var.bind("<<ComboboxSelected>>", self._on_model_change)
        
        # 刷新模型列表
        self.refresh_btn = ttk.Button(control_frame, text="🔄 刷新", command=self._refresh_models)
        self.refresh_btn.pack(side="left", padx=5)
        
        # 选择图片按钮
        self.select_btn = ttk.Button(control_frame, text="📁 选择图片", command=self._select_image)
        self.select_btn.pack(side="right", padx=5)
        
        # 主内容区
        content_frame = ttk.Frame(self.root, padding="10")
        content_frame.pack(fill="both", expand=True)
        
        # 左侧：图片预览
        left_frame = ttk.LabelFrame(content_frame, text="图片预览", padding="10")
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        self.image_label = ttk.Label(left_frame, text="请选择图片", anchor="center")
        self.image_label.pack(fill="both", expand=True)
        
        # 右侧：预测结果
        right_frame = ttk.LabelFrame(content_frame, text="预测结果", padding="10")
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        # 最佳预测
        self.result_label = ttk.Label(right_frame, text="", font=("Arial", 14), anchor="center")
        self.result_label.pack(fill="x", pady=10)
        
        # 置信度进度条
        self.confidence_frame = ttk.Frame(right_frame)
        self.confidence_frame.pack(fill="x", pady=5)
        ttk.Label(self.confidence_frame, text="置信度:").pack(side="left")
        self.confidence_bar = ttk.Progressbar(self.confidence_frame, length=200, mode="determinate")
        self.confidence_bar.pack(side="left", padx=10)
        self.confidence_label = ttk.Label(self.confidence_frame, text="0%")
        self.confidence_label.pack(side="left")
        
        # Top-K 结果
        ttk.Label(right_frame, text="Top-5 预测:", font=("Arial", 10, "bold")).pack(anchor="w", pady=(20, 5))
        
        self.topk_frame = ttk.Frame(right_frame)
        self.topk_frame.pack(fill="both", expand=True)
        
        # 模型信息
        self.info_label = ttk.Label(right_frame, text="", font=("Arial", 9), foreground="gray")
        self.info_label.pack(side="bottom", fill="x", pady=10)

    def _init_model(self):
        """初始化模型"""
        self._refresh_models()

    def _model_ready(self):
        """判断当前是否存在可用模型（微调模型或 V0 原型基线）"""
        return self.ai is not None and (self.ai.model is not None or self.ai.prototype_mode)
        
    def _refresh_models(self):
        """刷新模型列表"""
        # 临时创建 AI 实例获取版本列表
        temp_ai = LostItemAI()
        versions = temp_ai.get_available_versions()
        
        self.model_var['values'] = versions
        if versions:
            self.model_var.set(versions[0])
            self._load_selected_model()

    def _load_selected_model(self):
        """加载选中的模型"""
        version = self.model_var.get()
        if not version:
            return
        
        # 显示加载中
        self.result_label.config(text="⏳ 加载模型中...")
        self.root.update()
        
        # 加载模型
        if version == "latest":
            self.ai = LostItemAI()
        else:
            self.ai = LostItemAI(version)
        
        if self._model_ready():
            self.result_label.config(text=f"✅ 模型 {self.ai.version} 已就绪")
            # 更新模型信息
            if self.ai.meta:
                info = f"类别数: {self.ai.meta.get('num_classes', '?')} | "
                info += f"验证准确率: {self.ai.meta.get('best_val_acc', '?'):.2%}" if 'best_val_acc' in (self.ai.meta or {}) else ""
                self.info_label.config(text=info)
        else:
            self.result_label.config(text="❌ 模型加载失败")
            self.info_label.config(text="")

    def _on_model_change(self, event=None):
        """模型切换事件"""
        self._load_selected_model()
        # 如果有图片，重新预测
        if self.current_image_path:
            self._predict()

    def _select_image(self):
        """选择图片"""
        filetypes = [
            ("图片文件", "*.jpg *.jpeg *.png *.gif *.bmp *.webp"),
            ("所有文件", "*.*")
        ]
        filepath = filedialog.askopenfilename(filetypes=filetypes)
        
        if filepath:
            self.current_image_path = filepath
            self._display_image(filepath)
            self._predict()

    def _display_image(self, filepath):
        """显示图片"""
        try:
            self.current_image_pil = Image.open(filepath).convert("RGB")
            
            # 缩放到合适大小
            max_size = (400, 400)
            img = self.current_image_pil.copy()
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # 转换为 Tkinter 格式
            photo = ImageTk.PhotoImage(img)
            self.image_label.config(image=photo, text="")
            self.image_label.image = photo  # 保持引用
            
        except Exception as e:
            self.image_label.config(text=f"❌ 无法加载图片\n{str(e)}", image="")

    def _predict(self):
        """执行预测"""
        if not self._model_ready():
            self.result_label.config(text="❌ 请先加载模型")
            return
        
        if not self.current_image_path:
            return
        
        try:
            # 获取 Top-K 预测
            topk = self.ai.predict_topk(self.current_image_path, k=5)
            
            if not topk:
                self.result_label.config(text="❌ 预测失败")
                return
            
            # 显示最佳结果
            best_class, best_conf = topk[0]
            self.result_label.config(text=f"🏷️ {best_class}")
            
            # 更新置信度条
            self.confidence_bar['value'] = best_conf * 100
            self.confidence_label.config(text=f"{best_conf:.1%}")
            
            # 清空并重新填充 Top-K 列表
            for widget in self.topk_frame.winfo_children():
                widget.destroy()
            
            for i, (cls, conf) in enumerate(topk):
                frame = ttk.Frame(self.topk_frame)
                frame.pack(fill="x", pady=2)
                
                # 排名
                rank_label = ttk.Label(frame, text=f"{i+1}.", width=3)
                rank_label.pack(side="left")
                
                # 类别
                class_label = ttk.Label(frame, text=cls, width=15)
                class_label.pack(side="left", padx=5)
                
                # 置信度条
                bar = ttk.Progressbar(frame, length=100, mode="determinate", value=conf*100)
                bar.pack(side="left", padx=5)
                
                # 百分比
                conf_label = ttk.Label(frame, text=f"{conf:.1%}", width=6)
                conf_label.pack(side="left")
                
                # 高亮最佳结果
                if i == 0:
                    class_label.config(font=("Arial", 10, "bold"))
            
        except Exception as e:
            self.result_label.config(text=f"❌ 预测出错: {str(e)}")

    def run(self):
        """运行界面"""
        self.root.mainloop()


# ==================== 命令行入口 ====================

def main_cli():
    """命令行模式"""
    import sys

    ai = LostItemAI()
    if ai.model is None and not ai.prototype_mode:
        sys.exit(0)

    test_img = sys.argv[1] if len(sys.argv) > 1 else None
    if not test_img or not os.path.exists(test_img):
        print("用法：python predict.py <图片路径>")
        print("      python predict.py --gui  # 启动图形界面")
        sys.exit(0)

    print(f"\n模型版本: {ai.version}")
    print(f"设备: {ai.device}")
    
    cls, conf = ai.predict(test_img)
    print(f"\n分类结果：{cls}（置信度 {conf:.2%}）")

    print("\nTop-5 预测:")
    for i, (c, p) in enumerate(ai.predict_topk(test_img, 5), 1):
        print(f"  {i}. {c}: {p:.2%}")

    feat = ai.extract_features(test_img)
    if feat is not None:
        print(f"\n特征维度：{feat.shape}，L2 范数：{np.linalg.norm(feat):.4f}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        # 命令行模式（显式指定）
        main_cli()
    else:
        # 默认启动 GUI 模式
        gui = PredictGUI()
        gui.run()
