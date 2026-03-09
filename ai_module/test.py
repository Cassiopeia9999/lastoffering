import os
from predict import LostItemAI, DescriptionGenerator

class TestAIModules:
    def __init__(self):
        self.lost_item_ai = LostItemAI()
        self.description_generator = DescriptionGenerator()
    
    def test_classification(self, test_img_path):
        """测试分类功能"""
        if not os.path.exists(test_img_path):
            print(f'测试图像不存在: {test_img_path}')
            return False
        
        if self.lost_item_ai.classification_model is None:
            print('测试失败！分类模型未加载')
            return False
        
        class_name, score = self.lost_item_ai.predict(test_img_path)
        if class_name:
            print(f'测试通过！预测结果: {class_name} (置信度: {score:.2f})')
            return True
        else:
            print('测试失败！预测失败')
            return False
    
    def test_model_loading(self):
        """测试模型加载功能"""
        print('测试分类模型加载...')
        if self.lost_item_ai.classification_model is not None:
            print('测试通过！分类模型加载成功')
            print(f'类别数量: {len(self.lost_item_ai.class_names)}')
            print(f'类别列表: {list(self.lost_item_ai.class_names.values())}')
        else:
            print('测试失败！分类模型加载失败')
        
        print('\n测试特征提取模型加载...')
        if self.lost_item_ai.feature_extractor is not None:
            print('测试通过！特征提取模型加载成功')
            print(f'特征提取模型输入形状: {self.lost_item_ai.feature_extractor.input_shape}')
            print(f'特征提取模型输出形状: {self.lost_item_ai.feature_extractor.output_shape}')
        else:
            print('测试失败！特征提取模型加载失败')
    
    def test_feature_extraction(self, test_img_path):
        """测试特征提取功能"""
        if not os.path.exists(test_img_path):
            print(f'测试图像不存在: {test_img_path}')
            return False
        
        if self.lost_item_ai.feature_extractor is None:
            print('测试失败！特征提取模型未加载')
            return False
        
        features = self.lost_item_ai.extract_features(test_img_path)
        if features is not None:
            print(f'测试通过！特征提取成功')
            print(f'特征向量长度: {len(features)}')
            print(f'特征向量范数: {sum(features**2)**0.5:.4f}')
            return True
        else:
            print('测试失败！特征提取失败')
            return False
    
    def test_description_generation(self, test_img_path):
        """测试描述生成功能"""
        if not os.path.exists(test_img_path):
            print(f'测试图像不存在: {test_img_path}')
            return False
        
        class_name, _ = self.lost_item_ai.predict(test_img_path)
        if class_name:
            description = self.description_generator.generate_description(test_img_path, class_name)
            print(f'测试通过！描述生成成功')
            print(f'生成的描述: {description}')
            return True
        else:
            print('测试失败！无法生成描述')
            return False
    
    def test_similarity_calculation(self, test_img_path1, test_img_path2):
        """测试相似度计算功能"""
        if not os.path.exists(test_img_path1) or not os.path.exists(test_img_path2):
            print('测试图像不存在')
            return False
        
        features1 = self.lost_item_ai.extract_features(test_img_path1)
        features2 = self.lost_item_ai.extract_features(test_img_path2)
        
        if features1 is not None and features2 is not None:
            similarity = self.lost_item_ai.calculate_similarity(features1, features2)
            print(f'测试通过！相似度计算成功')
            print(f'两张图像的相似度: {similarity:.4f}')
            return True
        else:
            print('测试失败！相似度计算失败')
            return False
    
    def test_search_similar_items(self, test_img_path):
        """测试相似物品搜索功能"""
        if not os.path.exists(test_img_path):
            print(f'测试图像不存在: {test_img_path}')
            return False
        
        features = self.lost_item_ai.extract_features(test_img_path)
        if features is not None:
            # 模拟物品特征
            import numpy as np
            mock_items_features = {
                1: np.random.randn(len(features)) / np.linalg.norm(np.random.randn(len(features))),
                2: np.random.randn(len(features)) / np.linalg.norm(np.random.randn(len(features))),
                3: np.random.randn(len(features)) / np.linalg.norm(np.random.randn(len(features))),
                4: np.random.randn(len(features)) / np.linalg.norm(np.random.randn(len(features))),
                5: np.random.randn(len(features)) / np.linalg.norm(np.random.randn(len(features)))
            }
            
            # 搜索相似物品
            similar_items = self.lost_item_ai.search_similar_items(features, mock_items_features, top_k=3)
            print(f'测试通过！相似物品搜索成功')
            print('相似物品:')
            for item_id, similarity in similar_items:
                print(f'物品ID: {item_id}, 相似度: {similarity:.4f}')
            return True
        else:
            print('测试失败！相似物品搜索失败')
            return False

if __name__ == '__main__':
    tester = TestAIModules()
    
    print('测试模型加载...')
    tester.test_model_loading()
    
    # 测试分类功能（需要替换为实际测试图像路径）
    test_img = 'test_image.jpg'
    print(f'\n测试分类功能...')
    tester.test_classification(test_img)
    
    # 测试特征提取功能
    print(f'\n测试特征提取功能...')
    tester.test_feature_extraction(test_img)
    
    # 测试描述生成功能
    print(f'\n测试描述生成功能...')
    tester.test_description_generation(test_img)
    
    # 测试相似度计算功能（需要两张测试图像）
    test_img2 = 'test_image2.jpg'
    print(f'\n测试相似度计算功能...')
    tester.test_similarity_calculation(test_img, test_img2)
    
    # 测试相似物品搜索功能
    print(f'\n测试相似物品搜索功能...')
    tester.test_search_similar_items(test_img)