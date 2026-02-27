"""
测试 AI 层：以图搜物接口
先发布几条带图片的物品，再用图片搜索验证相似度检索流程
"""
import requests
import os
from PIL import Image
import io

BASE = "http://localhost:8000/api/v1"

# ── 登录获取 Token ────────────────────────────────────────
r = requests.post(f"{BASE}/users/login", json={"username": "testuser", "password": "test123"})
token = r.json().get("access_token", "")
headers = {"Authorization": f"Bearer {token}"}
print(f"登录: {'成功' if token else '失败'}")

# ── 创建测试图片（纯色占位图，文件名含关键词用于占位分类） ──
def make_test_image(filename: str, color=(255, 0, 0)) -> bytes:
    img = Image.new("RGB", (224, 224), color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

print("\n" + "=" * 50)
print("1. 发布 3 条带图片的招领信息（found）")

found_ids = []
test_items = [
    ("wallet_found.jpg", "捡到一个黑色钱包", "钱包/包", (50, 50, 50)),
    ("phone_found.jpg",  "捡到一部手机",     "电子产品", (0, 120, 255)),
    ("key_found.jpg",    "捡到一串钥匙",     "钥匙",    (200, 180, 0)),
]

for fname, title, cat, color in test_items:
    img_bytes = make_test_image(fname, color)
    r = requests.post(
        f"{BASE}/items",
        headers=headers,
        data={"type": "found", "title": title, "category": cat, "location": "教学楼A"},
        files={"image": (fname, img_bytes, "image/jpeg")},
    )
    item = r.json()
    found_ids.append(item["id"])
    print(f"   [{r.status_code}] id={item['id']} 类别={item['category']} 特征向量={'有' if item.get('feature_vector') is None else '已存储（不在响应中显示）'}")

# 验证特征向量是否存入数据库
import pymysql
conn = pymysql.connect(host="localhost", user="root", password="123456", database="lostfound")
cursor = conn.cursor()
cursor.execute("SELECT id, title, category, CHAR_LENGTH(feature_vector) as fv_len FROM items WHERE type='found'")
rows = cursor.fetchall()
print("\n   数据库中的招领物品：")
for row in rows:
    print(f"   id={row[0]} title={row[1]} category={row[2]} 特征向量长度={row[3]}字符")
conn.close()

print("\n" + "=" * 50)
print("2. 以图搜物测试（用钱包图片搜索招领库）")

wallet_img = make_test_image("wallet_search.jpg", color=(60, 60, 60))
r = requests.post(
    f"{BASE}/search/by-image",
    headers=headers,
    data={"search_type": "found", "top_k": 5, "threshold": 0.0},
    files={"image": ("wallet_search.jpg", wallet_img, "image/jpeg")},
)
print(f"   状态码: {r.status_code}")
data = r.json()
print(f"   AI识别类别: {data.get('query_category')} (置信度: {data.get('query_category_confidence')})")
print(f"   Top3候选类别: {data.get('top_categories')}")
print(f"   检索到 {data.get('total')} 条相似物品:")
for res in data.get("results", []):
    print(f"     相似度={res['similarity']:.4f}  [{res['item']['type']}] {res['item']['title']} ({res['item']['category']})")

print("\n" + "=" * 50)
print("3. 仅识别类别接口测试")
phone_img = make_test_image("phone_test.jpg", color=(0, 100, 200))
r = requests.post(
    f"{BASE}/search/classify",
    headers=headers,
    files={"image": ("phone_test.jpg", phone_img, "image/jpeg")},
)
print(f"   状态码: {r.status_code}")
data = r.json()
print(f"   建议类别: {data.get('suggested_category')} (置信度: {data.get('confidence')})")
print(f"   Top3: {data.get('top3')}")

print("\n" + "=" * 50)
print("测试完成！")
