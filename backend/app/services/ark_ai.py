"""
火山方舟 AI 服务
用于生成物品描述
"""
import os
import base64
import requests
from typing import Optional
import urllib3

# 禁用 SSL 警告（如果需要）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 火山方舟配置
ARK_API_KEY = os.getenv("ARK_API_KEY", "4c959869-bac4-4ad3-a8f0-b0801d450773")
ARK_ENDPOINT_ID = os.getenv("ARK_ENDPOINT_ID", "ep-20260309135223-6ktnt")
ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"


def generate_item_description(
    image_path: Optional[str] = None,
    item_type: str = "lost",
    category: Optional[str] = None,
    title: Optional[str] = None,
) -> str:
    """
    根据图片和物品信息生成描述文本
    
    Args:
        image_path: 图片路径（可选）
        item_type: lost=失物, found=招领
        category: 物品类别
        title: 物品标题
    
    Returns:
        生成的描述文本
    """
    type_text = "丢失" if item_type == "lost" else "捡到"
    
    # 构建系统提示词
    system_prompt = """你是一位专业的失物招领信息撰写助手。请根据用户提供的物品信息，生成一段简洁、清晰、有用的描述。

要求：
1. 描述应包含物品的品牌、颜色、型号、特征等关键信息
2. 如果是失物，描述在哪里丢失、什么时间丢失
3. 如果是招领，描述在哪里捡到、什么时间捡到
4. 语气友好、专业
5. 控制在100-200字之间
6. 不要添加任何格式标记，只返回纯文本"""

    # 构建用户提示词
    user_prompt = f"我{type_text}了一个物品"
    if title:
        user_prompt += f"，物品名称是：{title}"
    if category:
        user_prompt += f"，类别是：{category}"
    user_prompt += f"。请帮我写一段描述信息。"

    # 准备消息
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    # 如果有图片，添加图片内容
    if image_path and os.path.exists(image_path):
        try:
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            
            # 多模态消息格式
            messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }
            ]
        except Exception as e:
            print(f"[ARK AI] 图片处理失败: {e}")
    
    try:
        print(f"[ARK AI] 调用API: model={ARK_ENDPOINT_ID}")
        
        # 配置 session 以处理 SSL 问题
        session = requests.Session()
        session.verify = False  # 临时禁用 SSL 验证
        
        response = session.post(
            f"{ARK_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {ARK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": ARK_ENDPOINT_ID,
                "messages": messages,
                "max_tokens": 300,
                "temperature": 0.7
            },
            timeout=60
        )
        
        print(f"[ARK AI] 响应状态: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[ARK AI] 错误响应: {response.text}")
            return ""
        
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            description = result["choices"][0]["message"]["content"].strip()
            print(f"[ARK AI] 生成成功，长度: {len(description)}")
            return description
        else:
            print(f"[ARK AI] 无choices返回: {result}")
            return ""
            
    except requests.exceptions.RequestException as e:
        print(f"[ARK AI] API请求失败: {e}")
        return ""
    except Exception as e:
        print(f"[ARK AI] 处理失败: {e}")
        import traceback
        traceback.print_exc()
        return ""
