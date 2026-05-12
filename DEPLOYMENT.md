# 部署指南

## 快速部署 (Docker)

### 1. 环境要求
- Docker 20.10+
- Docker Compose 2.0+

### 2. 快速启动

```bash
# 克隆项目
git clone https://github.com/Mrsuperding/diskbench_pro_dhq.git
cd diskbench_pro_dhq

# 复制环境配置
cp .env.docker .env

# 启动所有服务 (首次运行会自动初始化数据库)
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

访问 http://localhost:3000

### 3. 默认账户

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 管理员 |
| user1 | user123 | 普通用户 |

### 4. 常用命令

```bash
# 停止服务
docker-compose down

# 重新构建并启动
docker-compose up -d --build

# 完全清除 (包括数据库数据)
docker-compose down -v

# 查看日志
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mysql
```

---

## 手动部署

### 1. 环境要求
- Python 3.10+
- MySQL 8.0+
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

---

## 项目结构

```
diskbench_pro/
├── docker-compose.yml      # Docker Compose 配置
├── .env.docker            # Docker 环境变量模板
├── DEPLOYMENT.md           # 本文档
├── backend/
│   ├── Dockerfile          # 后端 Docker 镜像
│   ├── database_init.sql   # MySQL 数据库初始化 SQL
│   ├── init_database.py   # Python 数据库初始化脚本
│   └── ...
├── frontend/
│   ├── Dockerfile          # 前端 Docker 镜像
│   ├── nginx.conf          # Nginx 配置
│   └── ...
└── ...
```

## Docker 服务说明

| 服务 | 端口 | 说明 |
|------|------|------|
| mysql | 3306 | MySQL 8.0 数据库 |
| backend | 8000 | FastAPI 后端服务 |
| frontend | 3000 | Vue3 前端 (Nginx) |

## 数据持久化

数据库数据存储在 Docker volume `diskbench_mysql_data` 中，不会因容器重启丢失。

如需完全清除数据：
```bash
docker-compose down -v
```
