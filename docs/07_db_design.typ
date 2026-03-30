// 校园失物招领智能管理系统 — 数据库设计说明书
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
    数据库设计说明书
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

= 引言

== 编写目的

本文档为"校园失物招领智能管理系统"的数据库设计说明书，依据概要设计阶段的成果，对系统数据库的逻辑结构、物理结构、数据字典及安全性设计进行详细说明。本文档的主要读者为数据库管理员、后端开发人员及指导教师，是数据库建表、数据访问层开发的重要依据。

== 项目背景

校园失物招领智能管理系统需要持久化存储用户信息、物品信息、匹配记录、留言信息及通知记录等数据。系统选用 MySQL 8.0 作为关系型数据库，通过 SQLAlchemy ORM 框架进行数据访问，所有数据表在应用启动时自动创建（若不存在）。

== 定义与缩略语

#table(
  columns: (3.5cm, 9cm),
  table.header([*术语 / 缩略语*], [*定义说明*]),
  [MySQL], [开源关系型数据库管理系统，版本 8.0+],
  [SQLAlchemy], [Python ORM 框架，用于数据库操作],
  [PyMySQL], [Python 连接 MySQL 的驱动库],
  [ORM], [对象关系映射，将 Python 类映射为数据库表],
  [主键（PK）], [唯一标识表中每条记录的字段],
  [外键（FK）], [引用其他表主键的字段，用于建立表关联],
  [索引（Index）], [提高查询速度的数据结构],
  [软删除], [不物理删除记录，仅标记 is_deleted=True],
  [枚举（Enum）], [MySQL ENUM 类型，限定字段取值范围],
  [特征向量], [图片经 AI 模型提取的512维浮点数数组，以 JSON 字符串形式存储],
  [UTC 时间], [协调世界时，系统所有时间字段均存储 UTC 时间],
)

== 参考资料

- GB/T 8567-2006 计算机软件文档编制规范
- MySQL 8.0 官方参考手册：https://dev.mysql.com/doc/refman/8.0/en/
- SQLAlchemy 官方文档：https://docs.sqlalchemy.org
- 系统需求分析文档
- 系统概要设计说明书

#pagebreak()

= 数据库环境说明

== 数据库管理系统

本系统采用 *MySQL 8.0*（或更高版本）作为数据库管理系统，具体配置如下：

#table(
  columns: (4cm, 8cm),
  table.header([*配置项*], [*说明*]),
  [数据库名称], [`lostfound`],
  [字符集], [`utf8mb4`（支持完整 Unicode，含 emoji）],
  [排序规则], [`utf8mb4_unicode_ci`],
  [连接方式], [TCP/IP，默认端口 3306],
  [连接驱动], [PyMySQL 1.1+],
  [连接框架], [SQLAlchemy 2.x，采用连接池管理],
  [连接串格式], [`mysql+pymysql://user:pwd@host:3306/lostfound?charset=utf8mb4`],
)

== 数据库访问配置

数据库连接参数通过项目根目录的 `.env` 环境变量文件配置，由 `backend/app/core/config.py` 中的 `Settings` 类读取：

```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=<密码>
DB_NAME=lostfound
```

== 图片文件存储

用户上传的物品图片和头像图片不存入数据库，而是保存在服务器本地文件系统，路径格式为：

`media/images/<UUID>.jpg`

数据库中仅存储图片的相对路径字符串（如 `media/images/abc123.jpg`），前端通过拼接后端域名访问图片。

#pagebreak()

= 数据库命名规则

系统遵循以下统一命名规范：

#table(
  columns: (3.5cm, 9cm),
  table.header([*规范类型*], [*说明*]),
  [数据库名], [全小写英文，使用下划线分词：`lostfound`],
  [表名], [全小写英文，使用下划线分词，采用名词复数：`users`、`items`、`matches`、`messages`、`notifications`],
  [字段名], [全小写英文，使用下划线分词：`owner_id`、`created_at`、`is_deleted`],
  [主键], [统一命名为 `id`，自增整数类型],
  [外键], [以关联表单数形式命名：`user_id`、`item_id`、`sender_id`],
  [布尔字段], [以 `is_` 为前缀：`is_admin`、`is_active`、`is_deleted`、`is_read`],
  [时间字段], [以 `_at` 为后缀：`created_at`、`updated_at`],
  [枚举字段], [使用 MySQL ENUM 类型，取值为英文小写字符串],
)

#pagebreak()

= 逻辑结构设计

== 实体关系说明

系统共包含 5 个核心数据实体，实体间关系如下：

- *用户（User）* 与 *物品（Item）*：一对多关系。一个用户可发布多件物品（owner_id 外键）。
- *物品（Item）* 与 *匹配（Match）*：一个失物物品可参与多条匹配记录（lost_item_id 外键），一件招领物品也可参与多条匹配记录（found_item_id 外键）。
- *物品（Item）* 与 *留言（Message）*：一对多关系。一件物品可以有多条留言（item_id 外键）。
- *用户（User）* 与 *留言（Message）*：一对多关系。一个用户可以发送多条留言（sender_id 外键）。
- *用户（User）* 与 *通知（Notification）*：一对多关系。一个用户可以收到多条通知（user_id 外键）。
- *物品（Item）* 与 *通知（Notification）*：一对多关系。一件物品可以触发多条通知（related_item_id 外键）。

== 实体关系图（ER图）

```
┌─────────────────┐          ┌─────────────────────────────┐
│      users      │          │           items              │
│─────────────────│          │─────────────────────────────│
│ PK  id          │◄──────── │ FK  owner_id                │
│     username    │  1 : N   │ PK  id                      │
│     password_   │          │     type (lost/found)        │
│       hash      │          │     title                   │
│     contact     │          │     description             │
│     is_admin    │          │     category                │
│     is_active   │          │     location                │
│     avatar      │          │     happen_time             │
│     nickname    │          │     image_url               │
│     real_name   │          │     feature_vector          │
│     signature   │          │     status                  │
│     college     │          │     is_deleted              │
│     class_name  │          │     created_at              │
│     email       │          │     updated_at              │
│     created_at  │          └──────────────┬──────────────┘
│     updated_at  │                         │
└────────┬────────┘            ┌────────────┤
         │                     │            │
         │ 1:N                 │ 1:N        │ 1:N
         ▼                     ▼            ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  notifications  │  │    messages     │  │    matches      │
│─────────────────│  │─────────────────│  │─────────────────│
│ PK  id          │  │ PK  id          │  │ PK  id          │
│ FK  user_id     │  │ FK  item_id     │  │ FK  lost_item_id│
│     type        │  │ FK  sender_id──►│  │ FK  found_item_ │
│     content     │  │     content     │  │       id        │
│ FK  related_    │  │     created_at  │  │     similarity  │
│       item_id   │  └─────────────────┘  │     status      │
│     related_    │                       │     created_at  │
│       match_id  │                       │     updated_at  │
│     is_read     │                       └─────────────────┘
│     created_at  │
└─────────────────┘
```

#pagebreak()

= 物理结构设计

== users 表（用户表）

存储系统所有注册用户的账号信息及个人资料。

#table(
  columns: (3cm, 3cm, 1.5cm, 1.5cm, 1.5cm, 4cm),
  table.header([*字段名*], [*数据类型*], [*主键*], [*非空*], [*索引*], [*说明*]),
  [`id`], [INT], [PK], [✓], [主键], [用户唯一标识，自增],
  [`username`], [VARCHAR(32)], [], [✓], [唯一], [登录账号，全局唯一],
  [`password_hash`], [VARCHAR(128)], [], [✓], [], [bcrypt 哈希后的密码，长度约60位],
  [`contact`], [VARCHAR(64)], [], [✓], [], [联系方式（手机/微信/邮箱）],
  [`is_admin`], [BOOLEAN], [], [✓], [], [是否为管理员，默认 FALSE],
  [`is_active`], [BOOLEAN], [], [✓], [], [账号是否启用，默认 TRUE；FALSE 时禁止登录],
  [`avatar`], [VARCHAR(256)], [], [], [], [头像图片相对路径，可为空],
  [`nickname`], [VARCHAR(32)], [], [], [], [用户昵称，可为空],
  [`real_name`], [VARCHAR(32)], [], [], [], [真实姓名，可为空],
  [`signature`], [VARCHAR(128)], [], [], [], [个性签名，可为空],
  [`college`], [VARCHAR(64)], [], [], [], [所在学院，可为空],
  [`class_name`], [VARCHAR(32)], [], [], [], [班级，可为空],
  [`email`], [VARCHAR(64)], [], [], [], [电子邮箱，可为空],
  [`created_at`], [DATETIME], [], [✓], [], [账号创建时间（UTC）],
  [`updated_at`], [DATETIME], [], [✓], [], [信息最后更新时间（UTC），自动更新],
)

*约束说明*：`username` 字段设置唯一索引（UNIQUE INDEX），`id` 字段设置普通索引（INDEX）。

== items 表（物品信息表）

存储用户发布的所有失物与招领物品信息。

#table(
  columns: (3.5cm, 3cm, 1.5cm, 1.5cm, 1.5cm, 3.5cm),
  table.header([*字段名*], [*数据类型*], [*主键*], [*非空*], [*索引*], [*说明*]),
  [`id`], [INT], [PK], [✓], [主键], [物品唯一标识，自增],
  [`type`], [ENUM], [], [✓], [], [`lost`（失物）或 `found`（招领）],
  [`title`], [VARCHAR(100)], [], [✓], [], [物品标题],
  [`description`], [TEXT], [], [], [], [物品详细描述，可为空],
  [`category`], [VARCHAR(32)], [], [], [], [物品类别，AI识别或手动填写，可为空],
  [`location`], [VARCHAR(128)], [], [], [], [丢失/发现地点，可为空],
  [`happen_time`], [DATETIME], [], [], [], [丢失/发现时间，可为空],
  [`image_url`], [VARCHAR(256)], [], [], [], [图片相对路径，可为空],
  [`feature_vector`], [TEXT], [], [], [], [512维特征向量，JSON字符串格式，可为空],
  [`status`], [ENUM], [], [✓], [], [`pending`（待认领）/`matched`（已匹配）/`closed`（已关闭）；默认 `pending`],
  [`is_deleted`], [BOOLEAN], [], [✓], [], [软删除标志，默认 FALSE；TRUE 时不出现在公开列表],
  [`owner_id`], [INT], [], [✓], [外键], [发布者用户ID，外键关联 users.id],
  [`created_at`], [DATETIME], [], [✓], [], [发布时间（UTC）],
  [`updated_at`], [DATETIME], [], [✓], [], [最后更新时间（UTC），自动更新],
)

*约束说明*：`owner_id` 为外键，级联操作参考业务逻辑（发布者账号删除时需处理其物品）。`type` 字段枚举值为 `'lost'` 和 `'found'`。`status` 字段枚举值为 `'pending'`、`'matched'`、`'closed'`。

*物品类别枚举值*（存储为中文字符串）：

移动电子设备、笔记本电脑、耳机、充电器/数据线、包类、书籍、文具、证件、钥匙、眼镜、饰品、水杯、雨伞、衣物、其他

== matches 表（智能匹配记录表）

存储系统自动生成的失物与招领物品匹配推荐记录。

#table(
  columns: (3.5cm, 3cm, 1.5cm, 1.5cm, 1.5cm, 3.5cm),
  table.header([*字段名*], [*数据类型*], [*主键*], [*非空*], [*索引*], [*说明*]),
  [`id`], [INT], [PK], [✓], [主键], [匹配记录唯一标识，自增],
  [`lost_item_id`], [INT], [], [✓], [外键], [失物物品ID，外键关联 items.id],
  [`found_item_id`], [INT], [], [✓], [外键], [招领物品ID，外键关联 items.id],
  [`similarity`], [FLOAT], [], [], [], [余弦相似度值，取值范围 0~1，系统触发阈值为 0.5；可为空],
  [`status`], [ENUM], [], [✓], [], [`pending`（待确认）/`confirmed`（已确认）/`rejected`（已拒绝）；默认 `pending`],
  [`created_at`], [DATETIME], [], [✓], [], [匹配记录创建时间（UTC）],
  [`updated_at`], [DATETIME], [], [✓], [], [最后更新时间（UTC），自动更新],
)

*约束说明*：`lost_item_id` 和 `found_item_id` 均为外键，指向 `items` 表的不同记录，通过 `foreign_keys` 参数区分。`status` 字段枚举值为 `'pending'`、`'confirmed'`、`'rejected'`。

== messages 表（留言表）

存储用户在物品详情页发布的留言信息。

#table(
  columns: (3.5cm, 3cm, 1.5cm, 1.5cm, 1.5cm, 3.5cm),
  table.header([*字段名*], [*数据类型*], [*主键*], [*非空*], [*索引*], [*说明*]),
  [`id`], [INT], [PK], [✓], [主键], [留言唯一标识，自增],
  [`item_id`], [INT], [], [✓], [外键+索引], [所属物品ID，外键关联 items.id；添加普通索引加速查询],
  [`sender_id`], [INT], [], [✓], [外键], [发送者用户ID，外键关联 users.id],
  [`content`], [TEXT], [], [✓], [], [留言内容文本],
  [`created_at`], [DATETIME], [], [✓], [], [留言发布时间（UTC）],
)

*约束说明*：`item_id` 字段建立普通索引（INDEX），以提高按物品查询留言的效率。

== notifications 表（站内通知表）

存储系统向用户推送的各类站内通知记录。

#table(
  columns: (3.5cm, 3cm, 1.5cm, 1.5cm, 1.5cm, 3.5cm),
  table.header([*字段名*], [*数据类型*], [*主键*], [*非空*], [*索引*], [*说明*]),
  [`id`], [INT], [PK], [✓], [主键], [通知唯一标识，自增],
  [`user_id`], [INT], [], [✓], [外键+索引], [接收通知的用户ID，外键关联 users.id；添加普通索引],
  [`type`], [VARCHAR(32)], [], [✓], [], [通知类型（见下方说明）],
  [`content`], [TEXT], [], [✓], [], [通知文本内容],
  [`related_item_id`], [INT], [], [], [外键], [关联物品ID，外键关联 items.id，可为空],
  [`related_match_id`], [INT], [], [], [], [关联匹配记录ID，整数，可为空（未建外键约束）],
  [`is_read`], [BOOLEAN], [], [✓], [], [是否已读，默认 FALSE],
  [`created_at`], [DATETIME], [], [✓], [], [通知创建时间（UTC）],
)

*通知类型枚举值（type 字段）*：

#table(
  columns: (4cm, 8cm),
  table.header([*类型值*], [*触发场景*]),
  [`match_found`], [系统为该用户的物品找到了潜在匹配，提示用户查看],
  [`item_matched`], [匹配已被双方确认，通知用户物品已成功匹配],
  [`contact_shared`], [联系方式已共享给对方用户],
  [`system`], [系统级通知（如账号状态变更、管理员操作等）],
)

*约束说明*：`user_id` 字段建立普通索引（INDEX），以提高按用户查询通知的效率。

#pagebreak()

= 数据字典

== 枚举类型汇总

#table(
  columns: (3cm, 3cm, 7cm),
  table.header([*所属表*], [*字段名*], [*枚举取值及含义*]),
  [`items`], [`type`], [`lost`：失物（用户丢失的物品）；`found`：招领（用户拾到的物品）],
  [`items`], [`status`], [`pending`：待认领/未处理；`matched`：已匹配成功；`closed`：已关闭/不再处理],
  [`matches`], [`status`], [`pending`：等待用户确认；`confirmed`：双方已确认匹配；`rejected`：用户已拒绝匹配],
)

== 关键字段说明

=== feature_vector 字段

`items.feature_vector` 字段存储 EfficientNet-B0 模型提取的512维特征向量，格式为 JSON 数组字符串，示例：

```json
[0.0234, -0.1567, 0.0891, ..., 0.0412]
```

该字段长度较大（约 2.5KB），因此使用 TEXT 类型存储，而非 VARCHAR。以图搜物时，后端将该字段反序列化为 Python 列表后计算余弦相似度。

=== password_hash 字段

`users.password_hash` 字段存储 bcrypt 哈希处理后的密码。bcrypt 哈希结果固定为60个字符，格式如：

```
$2b$12$...（60位哈希字符串）
```

系统使用 passlib 库进行哈希生成与验证，原始密码不存入数据库。

#pagebreak()

= 安全性设计

== 访问控制

- *密码安全*：用户密码使用 bcrypt 算法进行哈希处理（工作因子12），原文密码不存储于数据库；
- *身份认证*：系统采用 JWT（JSON Web Token）进行无状态身份认证，Token 有效期60分钟，过期后需重新登录；
- *权限分级*：数据库层面通过 `is_admin` 字段区分普通用户与管理员，后端 API 通过依赖注入（`get_current_admin`）进行权限校验；
- *数据隔离*：用户只能修改/删除自己发布的物品，管理员操作通过独立的 `/admin/*` 接口路径进行，普通用户无权访问。

== 数据完整性

- *外键约束*：所有跨表引用均通过 SQLAlchemy relationship 建立 ORM 级别关联，确保关联数据一致性；
- *字段非空约束*：关键字段（如 username、password_hash、type、status 等）设置 NOT NULL 约束；
- *软删除机制*：物品删除采用软删除（is_deleted=TRUE），不物理删除记录，保留历史数据，支持数据恢复；
- *枚举约束*：type、status 等字段使用 MySQL ENUM 类型，限定合法取值范围，防止非法数据写入。

== 数据库连接安全

- 数据库连接参数（账号、密码）通过 `.env` 文件配置，不硬编码在源代码中；
- `.env` 文件已加入 `.gitignore`，不随代码提交到版本库；
- 生产环境建议为系统创建专用数据库账号，仅授予 `lostfound` 数据库的 SELECT/INSERT/UPDATE/DELETE 权限，不使用 root 账号。

#pagebreak()

= 数据库性能优化

== 索引策略

系统在以下字段上建立了索引：

#table(
  columns: (3cm, 4cm, 6cm),
  table.header([*表名*], [*索引字段*], [*原因*]),
  [`users`], [`id`（主键）], [主键自动建立聚簇索引],
  [`users`], [`username`（唯一索引）], [登录时按账号查询，需快速定位],
  [`items`], [`id`（主键）], [主键自动建立聚簇索引],
  [`messages`], [`item_id`（普通索引）], [查询某物品的所有留言时使用],
  [`notifications`], [`user_id`（普通索引）], [查询某用户的所有通知时使用],
)

== 大字段处理

- `feature_vector` 字段（TEXT类型，约2.5KB）：在列表查询时不返回该字段，仅在以图搜物时批量读取，减少不必要的大字段传输；
- `description`（TEXT类型）：列表接口不返回详情字段，仅在单条物品查询时返回。

== 连接池配置

SQLAlchemy 默认使用 QueuePool 连接池，系统未作额外调整。对于 MySQL，连接池可有效避免频繁建立/关闭连接的性能开销。在高并发场景下，可通过 `pool_size`、`max_overflow` 参数进一步优化。
