import os
import json
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.resnet import preprocess_input

class LostItemAI:
    """失物识别AI类，集成分类和特征提取功能"""
    def __init__(self):
        # 加载分类模型和特征提取模型
        model_path = os.path.join(os.path.dirname(__file__), 'models', 'lost_item_model.h5')
        feature_extractor_path = os.path.join(os.path.dirname(__file__), 'models', 'feature_extractor.h5')
        class_names_path = os.path.join(os.path.dirname(__file__), 'models', 'class_names.json')
        
        if os.path.exists(model_path) and os.path.exists(feature_extractor_path) and os.path.exists(class_names_path):
            self.classification_model = load_model(model_path)
            self.feature_extractor = load_model(feature_extractor_path)
            with open(class_names_path, 'r') as f:
                self.class_names = json.load(f)
            # 反转类别字典，将键值对调换
            self.class_names = {v: k for k, v in self.class_names.items()}
            self.img_height, self.img_width = 224, 224
        else:
            self.classification_model = None
            self.feature_extractor = None
            self.class_names = None
            print('模型文件不存在，请先训练模型！')
    
    def predict(self, img_path):
        """预测图像中的失物类别"""
        if self.classification_model is None:
            return None, 0.0
        
        # 加载和预处理图像
        img = image.load_img(img_path, target_size=(self.img_height, self.img_width))
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)
        
        # 预测
        predictions = self.classification_model.predict(img_array)
        score = np.max(predictions)
        class_idx = np.argmax(predictions)
        class_name = self.class_names.get(class_idx, '未知类别')
        
        return class_name, score
    
    def extract_features(self, img_path):
        """提取图像特征向量"""
        if self.feature_extractor is None:
            return None
        
        # 加载和预处理图像
        img = image.load_img(img_path, target_size=(self.img_height, self.img_width))
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)
        
        # 提取特征
        features = self.feature_extractor.predict(img_array)
        # 展平特征向量
        features = features.flatten()
        # 归一化
        features = features / np.linalg.norm(features)
        
        return features
    
    def calculate_similarity(self, features1, features2):
        """计算两个特征向量的余弦相似度"""
        if features1 is None or features2 is None:
            return 0.0
        
        # 计算余弦相似度
        similarity = np.dot(features1, features2)
        
        return similarity
    
    def search_similar_items(self, query_features, all_items_features, top_k=5):
        """根据特征向量搜索相似物品"""
        if query_features is None:
            return []
        
        # 计算与所有物品的相似度
        similarities = []
        for item_id, item_features in all_items_features.items():
            similarity = self.calculate_similarity(query_features, item_features)
            similarities.append((item_id, similarity))
        
        # 按相似度排序
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # 返回前top_k个结果
        return similarities[:top_k]

class DescriptionGenerator:
    """描述生成器类，用于生成物品描述"""
    def __init__(self):
        # 这里可以初始化API客户端
        pass
    
    def generate_description(self, img_path, item_type):
        """使用API生成物品描述"""
        try:
            # 这里使用一个示例API，实际项目中需要替换为真实的API
            # 例如使用OpenAI的API或其他图像描述API
            # 由于是示例，我们返回一个模拟的描述
            descriptions = {
                '手机': '黑色 iPhone，屏幕有裂纹',
                '钱包': '棕色 leather钱包，内有身份证',
                '钥匙': '金属钥匙串，包含3把钥匙',
                '背包': '蓝色双肩背包，有拉链',
                '眼镜': '黑色边框眼镜，镜片完好'
            }
            
            return descriptions.get(item_type, f'一个{item_type}')
        except Exception as e:
            print(f'生成描述时出错: {e}')
            return f'一个{item_type}'

if __name__ == '__main__':
    # 示例用法
    lost_item_ai = LostItemAI()
    description_generator = DescriptionGenerator()
    
    test_img_path = 'test_image.jpg'  # 替换为实际测试图像路径
    
    if os.path.exists(test_img_path):
        # 预测类别
        class_name, score = lost_item_ai.predict(test_img_path)
        print(f'预测结果: {class_name} (置信度: {score:.2f})')
        
        # 生成描述
        description = description_generator.generate_description(test_img_path, class_name)
        print(f'生成描述: {description}')
        
        # 提取特征
        features = lost_item_ai.extract_features(test_img_path)
        if features is not None:
            print(f'特征向量长度: {len(features)}')
            
            # 模拟搜索相似物品
            # 实际项目中，这里应该从数据库中加载所有物品的特征
            mock_items_features = {
                1: np.random.randn(len(features)),
                2: np.random.randn(len(features)),
                3: np.random.randn(len(features)),
                4: np.random.randn(len(features)),
                5: np.random.randn(len(features))
            }
            # 归一化模拟特征
            for item_id in mock_items_features:
                mock_items_features[item_id] = mock_items_features[item_id] / np.linalg.norm(mock_items_features[item_id])
            
            # 搜索相似物品
            similar_items = lost_item_ai.search_similar_items(features, mock_items_features, top_k=3)
            print('相似物品:')
            for item_id, similarity in similar_items:
                print(f'物品ID: {item_id}, 相似度: {similarity:.4f}')
    else:
        print('测试图像不存在！')