// 校园失物招领智能管理系统 — 概要设计说明书
// 参考标准：GB/T 8567-2006 计算机软件文档编制规范

#set page(
  paper: "a4",
  margin: (top: 2.54cm, bottom: 2.54cm, left: 3.17cm, right: 3.17cm),
)
#set text(font: ("Times New Roman", "SimSun"), size: 12pt, lang: "zh")
#set par(leading: 0.8em, spacing: 0.8em, first-line-indent: 2em, justify: true)
#set heading(numbering: "1.1.1")

#show heading.where(level: 1): it => {
  set align(center)
  set text(size: 15pt, font: ("Times New Roman", "SimHei"), weight: "regular")
  set block(above: 1.5em, below: 1em)
  it
}
#show heading.where(level: 2): it => {
  set text(size: 14pt, font: ("Times New Roman", "SimHei"), weight: "regular")
  set block(above: 1.2em, below: 0.8em)
  it
}
#show heading.where(level: 3): it => {
  set text(size: 12pt, font: ("Times New Roman", "SimHei"), weight: "regular")
  set block(above: 1em, below: 0.6em)
  it
}

// ===== 封面 =====
#align(center)[
  #v(3cm)
  #text(size: 18pt, font: ("Times New Roman", "SimHei"), weight: "bold")[
    成都信息工程大学
  ]
  #v(0.5cm)
  #text(size: 22pt, font: ("Times New Roman", "SimHei"), weight: "bold")[
    概要设计说明书
  ]
  #v(2cm)
  #set text(size: 14pt, font: ("Times New Roman", "KaiTi"))
  #table(
    columns: (4.5cm, 6cm),
    align: (right + horizon, left + horizon),
    stroke: (x, y) => if x == 1 { (bottom: 0.5pt) } else { none },
    inset: (x: 0.3em, y: 0.7em),
    [*项目名称：*], [校园失物招领智能管理系统],
    [*项目类型：*], [毕业设计（软件工程方向）],
    [*学　　院：*], [人工智能学院],
    [*专　　业：*], [人工智能],
    [*姓　　名：*], [刘埌铖],
    [*学　　号：*], [2022132019],
    [*指导教师：*], [尹庆（讲师）],
    [*完成日期：*], [2026年3月],
  )
]

#pagebreak()

// ===== 目录 =====
#align(center)[
  #text(size: 16pt, font: ("Times New Roman", "SimHei"))[*目　录*]
]
#v(0.5em)
#outline(title: none, depth: 3, indent: 1.5em)

#pagebreak()

// ===== 正文开始 =====

= 引言

== 编写目的

本文档为"校园失物招领智能管理系统"的概要设计说明书，依据需求分析阶段的成果，对系统总体架构、模块划分、接口规范及核心处理流程进行说明。本文档的主要读者为项目开发人员、测试人员及指导教师，是后续详细设计与编码实现的重要依据。

== 项目背景

在高校校园中，学生遗失物品的情况十分普遍，而传统的失物招领方式（公告栏、微信群等）存在信息分散、匹配效率低、依赖人工核对等问题。本项目旨在利用人工智能图像识别技术，构建一套智能化的校园失物招领管理平台，实现物品信息的快速发布、自动分类识别、以图搜物、智能匹配推荐及消息通知等功能，从而提高失物与招领信息的匹配效率，方便广大师生。

本系统由成都信息工程大学人工智能学院学生刘埌铖作为毕业设计项目开发，指导教师为尹庆讲师。

== 定义与缩略语

#table(
  columns: (3cm, 9cm),
  table.header([*术语 / 缩略语*], [*定义说明*]),
  [API], [应用程序编程接口（Application Programming Interface）],
  [REST], [表述性状态传递（Representational State Transfer）],
  [JWT], [JSON Web Token，用于无状态身份认证],
  [AI], [人工智能（Artificial Intelligence）],
  [EfficientNet-B0], [谷歌提出的轻量级图像分类卷积神经网络],
  [特征向量], [由AI模型提取的512维数值向量，用于图像相似度计算],
  [余弦相似度], [衡量两个向量方向一致性的数学指标，取值范围[-1, 1]],
  [CORS], [跨域资源共享（Cross-Origin Resource Sharing）],
  [ORM], [对象关系映射（Object Relational Mapping）],
  [Vue 3], [渐进式前端JavaScript框架],
  [FastAPI], [基于Python的高性能异步Web框架],
  [SQLAlchemy], [Python ORM框架，用于数据库操作],
  [失物], [用户发布的已遗失物品信息（type = lost）],
  [招领], [用户发布的已拾到物品信息（type = found）],
)

== 参考资料

- GB/T 8567-2006 计算机软件文档编制规范
- FastAPI 官方文档：https://fastapi.tiangolo.com
- PyTorch EfficientNet 官方文档：https://pytorch.org/vision/stable/models.html
- Vue 3 官方文档：https://v3.vuejs.org
- Element Plus 组件库文档：https://element-plus.org

#pagebreak()

= 总体设计

== 系统需求概述

根据需求分析，系统需实现以下核心功能：

+ *用户管理*：注册、登录、个人资料维护（含头像、昵称、学院、班级等）、密码修改；
+ *物品发布*：支持失物和招领两种类型的物品信息发布，包含图片上传；
+ *AI智能识别*：上传图片后自动调用AI分类模型，识别物品类别并预填充信息；
+ *以图搜物*：用户上传图片，系统通过特征向量余弦相似度搜索数据库中的相似物品；
+ *智能匹配*：新物品入库后自动与数据库中反向类型物品进行特征比对，生成匹配推荐；
+ *消息留言*：用户可在物品详情页留言，与物品发布者沟通；
+ *通知系统*：系统自动推送匹配成功、被留言等站内通知；
+ *管理后台*：管理员可对用户、物品进行审核、禁用、删除等管理操作。

== 运行环境

=== 服务端运行环境

#table(
  columns: (4cm, 8cm),
  table.header([*环境要素*], [*说明*]),
  [操作系统], [Windows 10/11 或 Linux（Ubuntu 20.04+）],
  [Python 版本], [Python 3.10+，conda 虚拟环境管理],
  [Web 框架], [FastAPI 0.110+，Uvicorn ASGI 服务器],
  [数据库], [MySQL 8.0+，PyMySQL + SQLAlchemy 连接],
  [AI 推理], [PyTorch 2.x，torchvision，CPU 或 CUDA 均可],
  [文件存储], [本地磁盘（media/images/ 目录）],
  [端口], [后端监听 8000，前端开发服务器监听 5173],
)

=== 客户端运行环境

#table(
  columns: (4cm, 8cm),
  table.header([*环境要素*], [*说明*]),
  [浏览器], [Chrome 90+ / Firefox 88+ / Edge 90+（现代浏览器）],
  [前端框架], [Vue 3 + Vite 5，Element Plus UI 组件库],
  [网络要求], [能访问后端 API（localhost:8000）即可],
)

== 总体架构设计

系统采用前后端分离的三层架构，分为展示层、业务逻辑层和数据层，各层之间通过 RESTful API 进行通信。

*展示层（前端）*：基于 Vue 3 + Element Plus 构建的单页面应用（SPA），运行在用户浏览器中，通过 HTTP/JSON 与后端 API 交互，提供用户界面。

*业务逻辑层（后端）*：基于 FastAPI 框架开发，处理所有业务逻辑，包括用户认证（JWT）、物品管理、AI 服务调用、匹配计算、通知推送等。

*数据层*：MySQL 8.0 关系型数据库，存储所有结构化业务数据；本地文件系统存储用户上传的图片文件；AI 模型文件（.pth 格式）存储于服务器本地。

*AI 模块*：独立的 ai_module，包含 EfficientNet-B0 分类模型和特征提取器，作为服务被后端调用，提供图像分类（14类）和512维特征向量提取功能。

== 模块划分与功能说明

系统共划分为以下六个主要功能模块：

=== 用户模块（User Module）

负责用户账号的全生命周期管理。

- 用户注册：输入账号、密码、联系方式，系统校验唯一性后创建账号；
- 用户登录：账号密码验证，验证通过后颁发 JWT Token（有效期60分钟）；
- 个人资料管理：查看和编辑昵称、真实姓名、学院、班级、邮箱、个性签名；
- 头像上传：上传图片文件，保存至 media/images/ 目录，更新数据库中的头像路径；
- 密码修改：验证当前密码后更新密码哈希。

=== 物品管理模块（Item Module）

负责失物/招领信息的增删改查。

- 发布物品：上传图片（可选）、填写标题、描述、类别、地点、时间后提交；
- 图片裁剪：前端集成 vue-cropper 对上传图片进行裁剪处理；
- AI自动识别：上传图片时自动调用分类接口，识别14个类别并预填充；
- 物品列表：支持按类型（lost/found）、类别、关键词过滤，分页返回；
- 物品详情：展示物品完整信息、发布者联系方式、AI匹配推荐等；
- 状态变更：支持标记物品为已匹配（matched）或已关闭（closed）；
- 软删除：用户下架物品不物理删除，仅设置 is_deleted 标志位。

=== AI 服务模块（AI Module）

提供图像智能处理能力。

- 图像分类：将上传图片通过 EfficientNet-B0 分类模型推理，返回物品类别及置信度（Top-3 候选）；
- 特征提取：提取图片的512维特征向量，L2归一化后存入数据库；
- 以图搜物：对查询图片提取特征向量，与数据库中所有物品特征向量计算余弦相似度，返回 Top-N 相似物品；
- 自动匹配：新物品入库后，后台自动比对反向类型物品，生成相似度≥0.5的匹配推荐记录。

=== 匹配模块（Match Module）

管理系统生成的智能匹配结果。

- 查看推荐：用户可查看系统为自己的物品自动推荐的潜在匹配项；
- 确认匹配：用户确认后，双方物品状态更新为 matched，并发送通知；
- 拒绝匹配：用户拒绝后，匹配记录状态更新为 rejected。

=== 消息与通知模块（Message & Notification Module）

支持用户间的沟通及系统消息推送。

- 留言功能：用户在物品详情页留言，留言与物品关联存储；
- 通知推送：物品匹配成功、收到留言时，系统自动向相关用户创建站内通知；
- 通知类型：match_found（有新匹配）、item_matched（匹配确认）、contact_shared（联系方式共享）、system（系统通知）；
- 已读标记：用户查看通知后，通知状态更新为已读。

=== 管理后台模块（Admin Module）

为管理员提供系统监控与运维能力。

- 用户管理：查看所有用户列表，支持启用/禁用账号、设置/取消管理员、重置密码、删除用户；
- 物品管理：查看全部物品，支持按类型筛选，支持强制下架；
- 统计概览：展示用户总数、物品总数、匹配成功数等关键统计指标。

== 核心处理流程

=== 物品发布与AI识别流程

+ 用户选择本地图片，前端对图片进行裁剪预处理；
+ 前端将处理后的图片以 multipart/form-data 格式上传至 `POST /api/v1/ai/classify`；
+ 后端 AI 分类服务（ai_classifier）加载 EfficientNet-B0 模型，对图片进行推理，返回 Top-3 类别及置信度；
+ 前端将识别到的最高置信度类别预填充至"物品类别"字段；
+ 同时，前端调用 `POST /api/v1/ai/extract-feature`（图片上传至服务器时自动调用），后端提取512维特征向量；
+ 用户确认/修改信息后，前端提交 `POST /api/v1/items`，后端将物品信息（含特征向量、图片路径）存入数据库；
+ 物品入库完成后，后台异步触发自动匹配流程。

=== 以图搜物流程

+ 用户在搜索页上传图片，前端将图片发送至 `POST /api/v1/search/by-image`；
+ 后端特征提取服务（ai_feature）提取查询图片的特征向量；
+ 对数据库中所有有特征向量的物品，逐一计算余弦相似度；
+ 按相似度降序排列，返回 Top-N 匹配结果；
+ 前端展示物品列表，用户可进一步查看详情与发布者联系。

=== 自动智能匹配流程

+ 新物品（失物/招领）入库后，系统自动调用 auto_match 服务；
+ 遍历数据库中状态为 pending、反向类型的物品；
+ 计算新物品与每件反向物品的特征向量余弦相似度；
+ 相似度 ≥ 0.5 时，创建 matches 表记录（status = pending）；
+ 系统向双方用户推送 match_found 类型的站内通知。

#pagebreak()

= 接口设计

== 用户界面设计

前端基于 Element Plus 组件库，按功能分为以下主要页面视图：

#table(
  columns: (4.5cm, 3.5cm, 5cm),
  table.header([*页面名称*], [*路由路径*], [*主要功能*]),
  [首页], [`/`], [系统简介与快速入口],
  [注册页], [`/register`], [用户注册表单],
  [登录页], [`/login`], [账号密码登录],
  [物品列表], [`/items`], [全部物品浏览与筛选],
  [物品详情], [`/items/:id`], [物品信息展示与留言],
  [发布物品], [`/publish`], [上传图片、填写信息发布],
  [搜索页], [`/search`], [关键词搜索与以图搜物],
  [我的物品], [`/my-items`], [查看自己发布的物品],
  [个人中心], [`/profile`], [查看和编辑个人资料],
  [通知中心], [`/notifications`], [查看站内通知],
  [管理后台-用户], [`/admin/users`], [管理员管理用户],
  [管理后台-物品], [`/admin/items`], [管理员管理物品],
  [管理后台-统计], [`/admin/stats`], [系统统计概览],
)

== 外部接口（REST API）

所有 API 均挂载于 `/api/v1` 前缀，采用 JSON 格式传输，需要身份认证的接口须在请求头携带 `Authorization: Bearer <token>`。

=== 用户相关接口

#table(
  columns: (4.5cm, 3.5cm, 5cm),
  table.header([*接口路径*], [*方法*], [*功能说明*]),
  [`/users/register`], [POST], [用户注册],
  [`/users/login`], [POST], [用户登录，返回 JWT Token],
  [`/users/me`], [GET], [获取当前登录用户信息],
  [`/users/me`], [PUT], [修改当前用户资料],
  [`/users/me/avatar`], [POST], [上传/更换头像（multipart）],
)

=== 物品相关接口

#table(
  columns: (4.5cm, 3.5cm, 5cm),
  table.header([*接口路径*], [*方法*], [*功能说明*]),
  [`/items`], [GET], [获取物品列表（支持过滤/分页）],
  [`/items`], [POST], [发布新物品（含图片上传）],
  [`/items/{id}`], [GET], [获取单个物品详情],
  [`/items/{id}`], [PUT], [修改物品信息],
  [`/items/{id}`], [DELETE], [下架物品（软删除）],
  [`/items/{id}/status`], [PATCH], [更新物品状态],
)

=== AI 服务接口

#table(
  columns: (4.5cm, 3.5cm, 5cm),
  table.header([*接口路径*], [*方法*], [*功能说明*]),
  [`/ai/classify`], [POST], [图片分类，返回 Top-3 类别],
  [`/ai/extract-feature`], [POST], [提取图片512维特征向量],
)

=== 搜索接口

#table(
  columns: (4.5cm, 3.5cm, 5cm),
  table.header([*接口路径*], [*方法*], [*功能说明*]),
  [`/search`], [GET], [关键词搜索物品],
  [`/search/by-image`], [POST], [以图搜物（返回相似物品列表）],
)

=== 匹配相关接口

#table(
  columns: (4.5cm, 3.5cm, 5cm),
  table.header([*接口路径*], [*方法*], [*功能说明*]),
  [`/matches/my`], [GET], [获取当前用户的匹配推荐],
  [`/matches/{id}/confirm`], [POST], [确认匹配],
  [`/matches/{id}/reject`], [POST], [拒绝匹配],
)

=== 消息与通知接口

#table(
  columns: (4.5cm, 3.5cm, 5cm),
  table.header([*接口路径*], [*方法*], [*功能说明*]),
  [`/items/{id}/messages`], [GET], [获取物品留言列表],
  [`/items/{id}/messages`], [POST], [发布留言],
  [`/notifications`], [GET], [获取通知列表],
  [`/notifications/{id}/read`], [POST], [标记通知为已读],
  [`/notifications/read-all`], [POST], [全部标记已读],
)

=== 管理员接口

#table(
  columns: (4.5cm, 3.5cm, 5cm),
  table.header([*接口路径*], [*方法*], [*功能说明*]),
  [`/admin/users`], [GET], [获取所有用户列表],
  [`/admin/users/{id}/toggle-active`], [POST], [启用/禁用账号],
  [`/admin/users/{id}/set-admin`], [POST], [设置/取消管理员],
  [`/admin/users/{id}/reset-password`], [POST], [重置用户密码],
  [`/admin/users/{id}`], [DELETE], [删除用户],
  [`/admin/items`], [GET], [获取所有物品（含已下架）],
  [`/admin/items/{id}/delete`], [POST], [强制下架物品],
  [`/admin/stats`], [GET], [获取系统统计数据],
)

== 内部模块接口

后端内部各服务模块通过 Python 函数调用进行交互，主要接口说明如下：

- `ai_classifier.classify_image(image_bytes) -> dict`：接受图片字节数据，返回分类结果（类别名称、置信度、Top-3候选）；
- `ai_feature.extract_feature(image_bytes) -> list[float]`：接受图片字节数据，返回512维特征向量；
- `ai_search.search_by_feature(query_vector, items) -> list`：对物品列表按余弦相似度排序；
- `auto_match.run_auto_match(db, item_id) -> None`：新物品入库后触发，自动生成匹配记录。

#pagebreak()

= 出错处理设计

== 错误响应规范

后端统一使用 HTTP 标准状态码，所有错误响应均返回 JSON 格式：

```json
{
  "detail": "错误描述信息（中文）"
}
```

主要错误码及含义：

#table(
  columns: (2.5cm, 4cm, 6cm),
  table.header([*状态码*], [*说明*], [*常见场景*]),
  [400], [Bad Request], [参数缺失、格式错误、业务逻辑校验失败],
  [401], [Unauthorized], [未登录或 Token 过期],
  [403], [Forbidden], [无权限操作（如非管理员访问后台）],
  [404], [Not Found], [资源不存在],
  [422], [Unprocessable Entity], [请求体字段类型不匹配（FastAPI 自动校验）],
  [500], [Internal Server Error], [服务端未预期异常],
)

== 异常处理策略

- *认证失败*：JWT 解析失败或过期时，返回 401，前端自动跳转登录页；
- *文件上传异常*：图片格式不合法或大小超限时，返回 400 并告知原因；
- *AI推理失败*：模型不存在或推理出错时，返回 500 并记录日志；分类失败不阻断物品发布流程，仅跳过自动填充；
- *数据库连接失败*：采用 SQLAlchemy 连接池，自动重连；启动时若连接失败，服务拒绝启动并输出错误日志；
- *软删除保护*：is_deleted=True 的物品不出现在公开列表中，但不物理删除，管理员仍可查看。

== 系统维护设计

- 后端启动时自动执行 AI 模型预热（后台线程加载），避免首次请求冷启动延迟（约10~30秒）；
- 数据库表结构通过 SQLAlchemy `Base.metadata.create_all()` 自动同步，首次启动时自动建表；
- 图片文件命名采用 UUID，避免文件名冲突；
- 系统日志由 Uvicorn 自动输出到控制台，记录每次请求的路径、状态码、耗时。
