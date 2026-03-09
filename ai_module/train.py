import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.applications import ResNet18
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

# 数据集路径
data_dir = os.path.join(os.path.dirname(__file__), 'datasets')
train_dir = os.path.join(data_dir, 'train')
val_dir = os.path.join(data_dir, 'validation')

# 图像参数
img_height, img_width = 224, 224
batch_size = 32

# 数据增强
train_datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=20,
    width_shift_range=0.2,
    height_shift_range=0.2,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True,
    fill_mode='nearest'
)

val_datagen = ImageDataGenerator(rescale=1./255)

# 数据加载器
train_generator = train_datagen.flow_from_directory(
    train_dir,
    target_size=(img_height, img_width),
    batch_size=batch_size,
    class_mode='categorical'
)

val_generator = val_datagen.flow_from_directory(
    val_dir,
    target_size=(img_height, img_width),
    batch_size=batch_size,
    class_mode='categorical'
)

# 类别数量
class_names = train_generator.class_indices
num_classes = len(class_names)

# 加载预训练的ResNet18模型（不包含顶层）
base_model = ResNet18(weights='imagenet', include_top=False, input_shape=(img_height, img_width, 3))

# 冻结基础模型层
for layer in base_model.layers:
    layer.trainable = False

# 添加自定义顶层
x = base_model.output
x = GlobalAveragePooling2D()(x)
feature_layer = Dense(512, activation='relu')(x)  # 特征层
x = Dropout(0.5)(feature_layer)
predictions = Dense(num_classes, activation='softmax')(x)

# 创建完整模型
model = Model(inputs=base_model.input, outputs=predictions)

# 创建特征提取模型（使用特征层作为输出）
feature_extractor = Model(inputs=base_model.input, outputs=feature_layer)

# 编译模型
model.compile(
    optimizer='adam',
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

# 回调函数
early_stopping = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
checkpoint = ModelCheckpoint(
    os.path.join(os.path.dirname(__file__), 'models', 'lost_item_model.h5'),
    monitor='val_accuracy',
    save_best_only=True,
    mode='max'
)

# 训练模型
history = model.fit(
    train_generator,
    steps_per_epoch=train_generator.samples // batch_size,
    epochs=20,
    validation_data=val_generator,
    validation_steps=val_generator.samples // batch_size,
    callbacks=[early_stopping, checkpoint]
)

# 保存特征提取模型
feature_extractor.save(os.path.join(os.path.dirname(__file__), 'models', 'feature_extractor.h5'))

# 保存类别信息
import json
with open(os.path.join(os.path.dirname(__file__), 'models', 'class_names.json'), 'w') as f:
    json.dump(class_names, f)

print('训练完成，模型已保存！')
print(f'分类模型输入形状: {model.input_shape}')
print(f'分类模型输出形状: {model.output_shape}')
print(f'特征提取模型输入形状: {feature_extractor.input_shape}')
print(f'特征提取模型输出形状: {feature_extractor.output_shape}')