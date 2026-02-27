"""
测试 Step8（后台自动匹配通知）和 Step9（管理员接口）
"""
import time
import requests
from PIL import Image
import io

BASE = "http://localhost:8000/api/v1"


def make_img(color=(100, 100, 100)) -> bytes:
    img = Image.new("RGB", (224, 224), color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


# ── 登录普通用户 ──────────────────────────────────────────
r = requests.post(f"{BASE}/users/login", json={"username": "testuser", "password": "test123"})
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print(f"普通用户登录: {'成功' if token else '失败'}")

# ── 注册并登录第二个用户（模拟拾得者）────────────────────
r = requests.post(f"{BASE}/users/register", json={
    "username": "finder01", "password": "find123", "contact": "18900000001"
})
if r.status_code not in (201, 400):
    print(f"注册finder01失败: {r.json()}")
r2 = requests.post(f"{BASE}/users/login", json={"username": "finder01", "password": "find123"})
token2 = r2.json()["access_token"]
headers2 = {"Authorization": f"Bearer {token2}"}
print(f"拾得者登录: {'成功' if token2 else '失败'}")

print("\n" + "=" * 55)
print("【Step 8】后台自动匹配通知测试")
print("=" * 55)

print("\n1. testuser 发布一条失物信息（带图片）")
r = requests.post(f"{BASE}/items", headers=headers, data={
    "type": "lost",
    "title": "遗失红色钱包",
    "category": "钱包/包",
    "location": "食堂一楼",
}, files={"image": ("lost_wallet.jpg", make_img((180, 30, 30)), "image/jpeg")})
lost_item = r.json()
print(f"   [{r.status_code}] 失物 id={lost_item['id']} 类别={lost_item['category']}")

print("\n2. finder01 发布招领信息（带图片）→ 触发后台自动匹配")
r = requests.post(f"{BASE}/items", headers=headers2, data={
    "type": "found",
    "title": "捡到一个红色钱包",
    "category": "钱包/包",
    "location": "食堂附近",
}, files={"image": ("found_wallet.jpg", make_img((200, 40, 40)), "image/jpeg")})
found_item = r.json()
print(f"   [{r.status_code}] 招领 id={found_item['id']} 类别={found_item['category']}")
print("   后台匹配任务已触发，等待 2 秒...")
time.sleep(2)

print("\n3. testuser 查看通知（应收到自动匹配推送）")
r = requests.get(f"{BASE}/notifications", headers=headers)
data = r.json()
print(f"   共 {data['total']} 条通知，未读 {data['unread']} 条")
for n in data["notifications"]:
    print(f"   [{n['type']}] {'未读' if not n['is_read'] else '已读'} - {n['content'][:50]}...")

print("\n" + "=" * 55)
print("【Step 9】管理员接口测试")
print("=" * 55)

print("\n4. 创建管理员账号（直接写库）")
import pymysql
conn = pymysql.connect(host="localhost", user="root", password="123456", database="lostfound")
cur = conn.cursor()
cur.execute("SELECT id FROM users WHERE username='admin01'")
if not cur.fetchone():
    from passlib.context import CryptContext
    pwd = CryptContext(schemes=["bcrypt"], deprecated="auto").hash("admin123")
    cur.execute(
        "INSERT INTO users (username, password_hash, contact, is_admin, is_active, created_at, updated_at) "
        "VALUES ('admin01', %s, 'admin@school.edu', 1, 1, NOW(), NOW())", (pwd,)
    )
    conn.commit()
    print("   管理员 admin01 创建成功")
else:
    print("   管理员 admin01 已存在")
conn.close()

r = requests.post(f"{BASE}/users/login", json={"username": "admin01", "password": "admin123"})
admin_token = r.json()["access_token"]
admin_headers = {"Authorization": f"Bearer {admin_token}"}
print(f"   管理员登录: {'成功' if admin_token else '失败'}")

print("\n5. 获取系统统计概览")
r = requests.get(f"{BASE}/admin/stats", headers=admin_headers)
stats = r.json()
print(f"   [{r.status_code}] 统计数据:")
for k, v in stats.items():
    print(f"     {k}: {v}")

print("\n6. 获取用户列表")
r = requests.get(f"{BASE}/admin/users", headers=admin_headers)
data = r.json()
print(f"   [{r.status_code}] 共 {len(data)} 个用户")
for u in data:
    print(f"     id={u['id']} {u['username']} 管理员={u['is_admin']} 启用={u['is_active']}")

print("\n7. 禁用 finder01")
r_find = requests.get(f"{BASE}/admin/users?keyword=finder01", headers=admin_headers)
finder = r_find.json()[0]
r = requests.patch(f"{BASE}/admin/users/{finder['id']}", headers=admin_headers,
                   json={"is_active": False})
print(f"   [{r.status_code}] finder01 is_active={r.json()['is_active']}")

print("\n8. finder01 尝试登录（应被拒绝）")
r = requests.post(f"{BASE}/users/login", json={"username": "finder01", "password": "find123"})
print(f"   [{r.status_code}] {r.json()}")

print("\n9. 重新启用 finder01")
r = requests.patch(f"{BASE}/admin/users/{finder['id']}", headers=admin_headers,
                   json={"is_active": True})
print(f"   [{r.status_code}] finder01 is_active={r.json()['is_active']}")

print("\n10. 管理员重置 finder01 密码")
r = requests.patch(f"{BASE}/admin/users/{finder['id']}", headers=admin_headers,
                   json={"new_password": "newpass456"})
print(f"    [{r.status_code}] 密码重置成功")
r = requests.post(f"{BASE}/users/login", json={"username": "finder01", "password": "newpass456"})
print(f"    用新密码登录: {r.status_code} {'成功' if r.status_code == 200 else '失败'}")

print("\n11. 获取所有物品（管理员视角）")
r = requests.get(f"{BASE}/admin/items", headers=admin_headers)
data = r.json()
print(f"    [{r.status_code}] 共 {data['total']} 条物品")

print("\n12. 各类别统计")
r = requests.get(f"{BASE}/admin/stats/category", headers=admin_headers)
print(f"    [{r.status_code}] {r.json()}")

print("\n13. 近30天每日发布量")
r = requests.get(f"{BASE}/admin/stats/daily", headers=admin_headers)
print(f"    [{r.status_code}] {r.json()}")

print("\n14. 普通用户访问管理员接口（应被拒绝）")
r = requests.get(f"{BASE}/admin/stats", headers=headers)
print(f"    [{r.status_code}] {r.json()}")

print("\n" + "=" * 55)
print("全部测试完成！")
