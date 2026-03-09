import fiftyone as fo
import fiftyone.zoo as foz
import os

# 你锁定的 14 类（映射到 OpenImages 类名）
classes = [
    "Mobile phone",
    "Laptop",
    "Headphones",
    "Charger",
    "Backpack",
    "Handbag",
    "Book",
    "Pen",
    "Pencil case",
    "Identity document",
    "Key",
    "Glasses",
    "Necklace",
    "Bracelet",
    "Bottle",
    "Umbrella",
    "Clothing"
]

# 去重说明：
# accessory = Necklace + Bracelet
# bag = Backpack + Handbag
# stationery = Pen + Pencil case
# clothes = Clothing
# 这些后续你可以手动合并为14类

dataset = foz.load_zoo_dataset(
    "open-images-v6",
    split="train",
    label_types=["detections"],
    classes=classes,
    max_samples=500,  # 每类最多500张
    shuffle=True
)

print("下载完成！")
print(dataset)

# 可选：打开可视化界面
session = fo.launch_app(dataset)
session.wait()