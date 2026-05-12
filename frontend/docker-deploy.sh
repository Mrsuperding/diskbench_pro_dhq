#!/bin/bash

# Docker部署脚本

echo "🐳 开始Docker部署..."

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

# 构建项目
echo "🔨 构建项目..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ 项目构建失败"
    exit 1
fi

# 创建Dockerfile
cat > Dockerfile << EOF
FROM nginx:alpine
COPY dist/ /usr/share/nginx/html/
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
EOF

# 创建nginx配置
cat > nginx.conf << EOF
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    sendfile on;
    keepalive_timeout 65;
    
    server {
        listen 80;
        server_name localhost;
        
        location / {
            root /usr/share/nginx/html;
            index index.html;
            try_files \$uri \$uri/ /index.html;
        }
        
        location /api/ {
            proxy_pass http://backend:8000;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
    }
}
EOF

# 构建Docker镜像
echo "🐳 构建Docker镜像..."
docker build -t io-performance-platform-frontend .

if [ $? -ne 0 ]; then
    echo "❌ Docker镜像构建失败"
    exit 1
fi

# 创建docker-compose.yml
cat > docker-compose.yml << EOF
version: '3.8'

services:
  frontend:
    image: io-performance-platform-frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    networks:
      - io-platform

  backend:
    image: io-performance-platform-backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=mysql://user:password@db:3306/io_test_platform
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    networks:
      - io-platform

  db:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=rootpassword
      - MYSQL_DATABASE=io_test_platform
      - MYSQL_USER=user
      - MYSQL_PASSWORD=password
    volumes:
      - mysql_data:/var/lib/mysql
    networks:
      - io-platform

  redis:
    image: redis:alpine
    volumes:
      - redis_data:/data
    networks:
      - io-platform

volumes:
  mysql_data:
  redis_data:

networks:
  io-platform:
    driver: bridge
EOF

# 启动容器
echo "🚀 启动容器..."
docker-compose up -d

if [ $? -ne 0 ]; then
    echo "❌ 容器启动失败"
    exit 1
fi

echo "✅ Docker部署完成！"
echo "🌐 应用访问地址: http://localhost"
echo "📊 后端API地址: http://localhost:8000"
echo ""
echo "📋 常用命令:"
echo "  查看日志: docker-compose logs -f"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart"
echo "  查看状态: docker-compose ps"