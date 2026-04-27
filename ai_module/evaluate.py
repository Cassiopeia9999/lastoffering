"""
模型评估工具 - 带GUI界面
功能：
  1. 批量评估验证集准确率
  2. 切换不同模型版本
  3. 保存评估结果到文件
运行方式：
  conda activate efftrain
  python evaluate.py
"""
import os
import sys
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from collections import defaultdict
from tqdm import tqdm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from predict import LostItemAI


def calc_class_metrics(confusion_matrix, categories):
    """根据混淆矩阵计算每类 precision / recall / f1"""
    metrics = {}
    for class_name in categories:
        tp = confusion_matrix.get(class_name, {}).get(class_name, 0)
        fp = sum(
            confusion_matrix.get(other_class, {}).get(class_name, 0)
            for other_class in categories
            if other_class != class_name
        )
        fn = sum(
            count
            for predicted_class, count in confusion_matrix.get(class_name, {}).items()
            if predicted_class != class_name
        )

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        metrics[class_name] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "tp": tp,
            "fp": fp,
            "fn": fn,
        }

    if not metrics:
        return metrics, {"precision": 0.0, "recall": 0.0, "f1": 0.0}

    macro = {
        "precision": sum(item["precision"] for item in metrics.values()) / len(metrics),
        "recall": sum(item["recall"] for item in metrics.values()) / len(metrics),
        "f1": sum(item["f1"] for item in metrics.values()) / len(metrics),
    }
    return metrics, macro


class EvaluateGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("模型评估工具")
        self.root.geometry("700x540")
        
        self.ai = None
        self.results = None
        
        self._build_ui()
        self._load_versions()

    def _model_ready(self):
        """判断当前是否已有可用模型（微调模型或 V0 原型基线）"""
        return self.ai is not None and (self.ai.model is not None or self.ai.prototype_mode)
    
    def _build_ui(self):
        # 标题
        tk.Label(self.root, text="模型评估工具", font=("Microsoft YaHei", 16, "bold")).pack(pady=10)
        
        # 模型选择区域
        frame_model = tk.LabelFrame(self.root, text="模型选择", padx=10, pady=10)
        frame_model.pack(fill="x", padx=20, pady=5)
        
        tk.Label(frame_model, text="模型版本:").grid(row=0, column=0, sticky="w")
        self.version_var = tk.StringVar(value="自动选择")
        self.combo_version = ttk.Combobox(frame_model, textvariable=self.version_var, 
                                          values=["自动选择"], width=20, state="readonly")
        self.combo_version.grid(row=0, column=1, padx=5)
        
        tk.Button(frame_model, text="加载模型", command=self._load_model, 
                  bg="#4CAF50", fg="white").grid(row=0, column=2, padx=5)
        
        self.lbl_model_info = tk.Label(frame_model, text="未加载模型", fg="gray")
        self.lbl_model_info.grid(row=1, column=0, columnspan=3, sticky="w", pady=5)
        
        # 评估区域
        frame_eval = tk.LabelFrame(self.root, text="评估设置", padx=10, pady=10)
        frame_eval.pack(fill="x", padx=20, pady=5)
        
        tk.Label(frame_eval, text="评估集路径:").grid(row=0, column=0, sticky="w")
        self.val_path_var = tk.StringVar(value="datasets/classification/test")
        tk.Entry(frame_eval, textvariable=self.val_path_var, width=40).grid(row=0, column=1, padx=5)
        tk.Button(frame_eval, text="浏览...", command=self._browse_val_dir).grid(row=0, column=2)
        
        # 快捷切换按钮
        frame_quick = tk.Frame(frame_eval)
        frame_quick.grid(row=1, column=0, columnspan=3, sticky="w", pady=(4, 0))
        tk.Label(frame_quick, text="快捷切换:", fg="gray").pack(side="left")
        tk.Button(frame_quick, text="📋 测试集（推荐）", bg="#e3f2fd",
                  command=lambda: self.val_path_var.set("datasets/classification/test")).pack(side="left", padx=4)
        tk.Button(frame_quick, text="📂 验证集", bg="#fff3e0",
                  command=lambda: self.val_path_var.set("datasets/classification/val")).pack(side="left", padx=4)
        tk.Label(frame_quick, text="  ⚠️ 建议用测试集（模型从未见过），验证集会高估性能",
                 fg="#e65100", font=("Microsoft YaHei", 9)).pack(side="left")
        
        # 操作按钮
        frame_btn = tk.Frame(self.root)
        frame_btn.pack(pady=10)
        
        self.btn_eval = tk.Button(frame_btn, text="开始评估", command=self._start_eval,
                                   bg="#2196F3", fg="white", font=("Microsoft YaHei", 12), width=15)
        self.btn_eval.pack(side="left", padx=5)
        
        self.btn_save = tk.Button(frame_btn, text="保存结果", command=self._save_results,
                                   bg="#FF9800", fg="white", font=("Microsoft YaHei", 12), width=15)
        self.btn_save.pack(side="left", padx=5)
        self.btn_save.config(state="disabled")
        
        # 结果显示区域
        frame_result = tk.LabelFrame(self.root, text="评估结果", padx=10, pady=10)
        frame_result.pack(fill="both", expand=True, padx=20, pady=5)
        
        self.txt_result = tk.Text(frame_result, height=12, font=("Consolas", 10))
        self.txt_result.pack(fill="both", expand=True)
        
        scrollbar = tk.Scrollbar(self.txt_result)
        scrollbar.pack(side="right", fill="y")
        self.txt_result.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.txt_result.yview)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        tk.Label(self.root, textvariable=self.status_var, bd=1, relief="sunken", anchor="w").pack(fill="x", padx=5, pady=2)
    
    def _load_versions(self):
        """加载可用的模型版本"""
        model_dir = os.path.join(os.path.dirname(__file__), "models")
        versions = ["自动选择"]
        
        # 检查 latest
        if os.path.exists(os.path.join(model_dir, "lost_item_model.pth")):
            versions.append("latest")
        
        # 检查版本化模型
        for f in os.listdir(model_dir) if os.path.exists(model_dir) else []:
            if f.startswith("lost_item_model_V") and f.endswith(".pth"):
                ver = f.replace("lost_item_model_", "").replace(".pth", "")
                versions.append(ver)
        
        self.combo_version["values"] = versions
    
    def _browse_val_dir(self):
        """浏览评估集目录"""
        path = filedialog.askdirectory(title="选择评估集目录（建议选 test/）")
        if path:
            self.val_path_var.set(path)
    
    def _load_model(self):
        """加载模型"""
        version = self.version_var.get()
        if version == "自动选择":
            version = None
        
        self.status_var.set("正在加载模型...")
        self.root.update()
        
        try:
            self.ai = LostItemAI(version=version)
            if not self._model_ready():
                messagebox.showerror("错误", "模型加载失败，请检查模型文件是否存在")
                self.status_var.set("模型加载失败")
                return
            
            info = f"版本: {self.ai.version}, 模式: {'V0基线' if self.ai.prototype_mode else '微调模型'}, 类别数: {len(self.ai.idx_to_class)}"
            self.lbl_model_info.config(text=info, fg="green")
            self.status_var.set(f"模型 {self.ai.version} 加载成功")
            messagebox.showinfo("成功", f"模型 {self.ai.version} 加载成功！")
            
        except Exception as e:
            messagebox.showerror("错误", f"模型加载失败: {e}")
            self.status_var.set("模型加载失败")
    
    def _start_eval(self):
        """开始评估"""
        if not self._model_ready():
            messagebox.showwarning("警告", "请先加载模型")
            return
        
        val_dir = self.val_path_var.get()
        if not os.path.exists(val_dir):
            messagebox.showerror("错误", f"评估集目录不存在: {val_dir}")
            return
        
        self.btn_eval.config(state="disabled")
        self.status_var.set("正在评估...")
        self.root.update()
        
        # 清空结果显示
        self.txt_result.delete(1.0, tk.END)
        self.txt_result.insert(tk.END, "开始评估...\n")
        self.root.update()
        
        # 执行评估
        self.results = self._evaluate(val_dir)
        
        # 显示结果
        self._display_results()
        
        self.btn_eval.config(state="normal")
        self.btn_save.config(state="normal")
        self.status_var.set("评估完成")
    
    def _evaluate(self, val_dir):
        """执行评估"""
        class_correct = defaultdict(int)
        class_total = defaultdict(int)
        confusion = defaultdict(lambda: defaultdict(int))
        
        total_correct = 0
        total_samples = 0
        errors = []  # 记录错误案例
        
        # 获取所有类别
        categories = [d for d in os.listdir(val_dir) if os.path.isdir(os.path.join(val_dir, d))]
        
        for class_name in categories:
            class_dir = os.path.join(val_dir, class_name)
            if not os.path.isdir(class_dir):
                continue
            
            # 获取该类别所有图片
            images = [f for f in os.listdir(class_dir) 
                     if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            
            for img_name in images:
                img_path = os.path.join(class_dir, img_name)
                
                try:
                    pred_class, conf = self.ai.predict(img_path)
                    
                    class_total[class_name] += 1
                    total_samples += 1
                    
                    if pred_class == class_name:
                        class_correct[class_name] += 1
                        total_correct += 1
                    else:
                        errors.append({
                            "image": img_path,
                            "true": class_name,
                            "predicted": pred_class,
                            "confidence": conf
                        })
                    
                    confusion[class_name][pred_class] += 1
                    
                except Exception as e:
                    self.txt_result.insert(tk.END, f"  错误: {img_path} - {e}\n")
                    self.txt_result.see(tk.END)
                    self.root.update()
        
        return {
            "total_accuracy": total_correct / total_samples if total_samples > 0 else 0,
            "total_samples": total_samples,
            "total_correct": total_correct,
            "class_accuracy": {
                cls: class_correct[cls] / class_total[cls] if class_total[cls] > 0 else 0
                for cls in class_total.keys()
            },
            "class_total": dict(class_total),
            "class_correct": dict(class_correct),
            "confusion_matrix": {k: dict(v) for k, v in confusion.items()},
            "errors": errors,
            "model_version": self.ai.version,
            "timestamp": datetime.now().isoformat()
        }
    
    def _display_results(self):
        """显示评估结果"""
        if not self.results:
            return
        
        r = self.results
        categories = sorted(r['class_total'].keys())
        class_metrics, macro_metrics = calc_class_metrics(r['confusion_matrix'], categories)
        text = []
        text.append("=" * 60)
        text.append("模型性能评估报告")
        text.append("=" * 60)
        text.append(f"模型版本: {r['model_version']}")
        text.append(f"评估时间: {r['timestamp']}")
        text.append("")
        text.append(f"总体准确率: {r['total_correct']}/{r['total_samples']} = {r['total_accuracy']:.2%}")
        text.append(f"宏平均 Precision: {macro_metrics['precision']:.2%}")
        text.append(f"宏平均 Recall   : {macro_metrics['recall']:.2%}")
        text.append(f"宏平均 F1       : {macro_metrics['f1']:.2%}")
        text.append("")
        text.append("各类别指标:")
        text.append("-" * 60)
        
        for class_name in categories:
            correct = r['class_correct'].get(class_name, 0)
            total = r['class_total'][class_name]
            acc = r['class_accuracy'][class_name]
            precision = class_metrics[class_name]["precision"]
            recall = class_metrics[class_name]["recall"]
            f1 = class_metrics[class_name]["f1"]
            text.append(
                f"{class_name:20s}: Acc={acc:6.2%} | P={precision:6.2%} | R={recall:6.2%} | F1={f1:6.2%} | {correct:3d}/{total:3d}"
            )

        self.results["class_metrics"] = class_metrics
        self.results["macro_metrics"] = macro_metrics
        
        if r['errors']:
            text.append("")
            text.append(f"错误案例 ({len(r['errors'])} 个):")
            text.append("-" * 60)
            for err in r['errors'][:10]:  # 只显示前10个
                text.append(f"  {err['image']}")
                text.append(f"    真实: {err['true']} | 预测: {err['predicted']} (置信度: {err['confidence']:.2%})")
        
        self.txt_result.delete(1.0, tk.END)
        self.txt_result.insert(tk.END, "\n".join(text))
    
    def _save_results(self):
        """保存评估结果"""
        if not self.results:
            return
        
        default_name = f"eval_{self.results['model_version']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        path = filedialog.asksaveasfilename(
            title="保存评估结果",
            defaultextension=".json",
            initialfile=default_name,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("成功", f"结果已保存到:\n{path}")


def main():
    root = tk.Tk()
    app = EvaluateGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

