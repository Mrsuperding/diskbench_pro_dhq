# 部署指南

## 快速部署

### 1. 环境要求
- Python 3.10+
- MySQL 8.0+ 或 PostgreSQL 14+
- Node.js 18+

### 2. 数据库初始化

**方式一：使用 SQL 脚本（推荐 MySQL）**

```bash
mysql -u root -p < backend/database_init.sql
```

**方式二：使用 Python 脚本**

```bash
cd backend

# 创建所有表
python init_database.py

# 删除并重建所有表
python init_database.py --drop

# 创建表并插入初始数据
python init_database.py --with-data
```

### 3. 配置文件

复制 `.env.example` 为 `.env` 并修改配置：

```bash
cp .env.example .env
```

关键配置项：
- `DATABASE_URL`: 数据库连接字符串
- `SECRET_KEY`: JWT 密钥

### 4. 启动后端

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 5. 启动前端

```bash
cd frontend
pnpm install
pnpm dev
```

### 6. 默认账户

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 管理员 |
| user1 | user123 | 普通用户 |

## Docker 部署

```bash
# 构建并启动
docker-compose up -d
```

## 目录结构

```
backend/
├── database_init.sql      # MySQL 数据库初始化 SQL
├── init_database.py      # Python 数据库初始化脚本
├── core/
│   └── config.py        # 配置文件
└── ...
```
