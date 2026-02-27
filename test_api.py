import requests

BASE = "http://localhost:8000/api/v1"

print("=" * 50)
print("1. 注册用户")
r = requests.post(f"{BASE}/users/register", json={
    "username": "testuser",
    "password": "test123",
    "contact": "13800138000"
})
print(f"   状态码: {r.status_code}  响应: {r.json()}")

print("\n2. 登录")
r = requests.post(f"{BASE}/users/login", json={
    "username": "testuser",
    "password": "test123"
})
print(f"   状态码: {r.status_code}")
token = r.json().get("access_token", "")
print(f"   Token: {'获取成功' if token else '获取失败'}")

headers = {"Authorization": f"Bearer {token}"}

print("\n3. 获取当前用户信息")
r = requests.get(f"{BASE}/users/me", headers=headers)
print(f"   状态码: {r.status_code}  响应: {r.json()}")

print("\n4. 获取物品类别列表")
r = requests.get(f"{BASE}/items/categories", headers=headers)
print(f"   状态码: {r.status_code}  类别数: {len(r.json()['categories'])}")

print("\n5. 发布失物信息（不带图片）")
r = requests.post(f"{BASE}/items", headers=headers, data={
    "type": "lost",
    "title": "黑色钱包",
    "description": "在图书馆二楼丢失，内有学生证",
    "category": "钱包/包",
    "location": "图书馆二楼",
})
print(f"   状态码: {r.status_code}  响应: {r.json()}")
item_id = r.json().get("id")

print("\n6. 发布招领信息")
r = requests.post(f"{BASE}/items", headers=headers, data={
    "type": "found",
    "title": "捡到一个黑色钱包",
    "description": "在图书馆门口捡到",
    "category": "钱包/包",
    "location": "图书馆门口",
})
print(f"   状态码: {r.status_code}  响应: {r.json()}")
found_item_id = r.json().get("id")

print("\n7. 查询物品列表（全部）")
r = requests.get(f"{BASE}/items", headers=headers)
data = r.json()
total = data["total"]
print(f"   状态码: {r.status_code}  共 {total} 条")

print("\n8. 关键词搜索")
r = requests.get(f"{BASE}/items?keyword=钱包", headers=headers)
data = r.json()
print(f"   状态码: {r.status_code}  搜索'钱包'结果: {data['total']} 条")

print("\n9. 查询我的物品")
r = requests.get(f"{BASE}/items/my", headers=headers)
data = r.json()
print(f"   状态码: {r.status_code}  我发布了 {data['total']} 条")

print("\n10. 对物品留言")
r = requests.post(f"{BASE}/items/{found_item_id}/messages", headers=headers,
                  json={"content": "请问这个钱包是黑色的吗？"})
print(f"    状态码: {r.status_code}  响应: {r.json()}")

print("\n11. 查看通知")
r = requests.get(f"{BASE}/notifications", headers=headers)
data = r.json()
print(f"    状态码: {r.status_code}  共 {data['total']} 条通知，未读 {data['unread']} 条")

print("\n12. 创建匹配（疑似遗失）")
r = requests.post(f"{BASE}/matches", headers=headers, json={
    "lost_item_id": item_id,
    "found_item_id": found_item_id,
})
print(f"    状态码: {r.status_code}  响应: {r.json()}")
match_id = r.json().get("id")

print("\n13. 确认匹配（交换联系方式）")
r = requests.patch(f"{BASE}/matches/{match_id}/confirm", headers=headers)
print(f"    状态码: {r.status_code}  响应: {r.json()}")

print("\n14. 再次查看通知（应有联系方式）")
r = requests.get(f"{BASE}/notifications", headers=headers)
data = r.json()
print(f"    状态码: {r.status_code}  共 {data['total']} 条通知")
for n in data["notifications"]:
    print(f"    [{n['type']}] {n['content']}")

print("\n" + "=" * 50)
print("测试完成！")
