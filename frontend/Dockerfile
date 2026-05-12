# =====================================================
# 前端 Dockerfile
# =====================================================
FROM node:18-alpine as builder

WORKDIR /app

# 复制 package.json
COPY frontend/package.json frontend/pnpm-lock.yaml* ./

# 安装依赖
RUN npm install -g pnpm && pnpm install

# 复制前端代码
COPY frontend/ ./

# 构建生产版本
RUN pnpm build

# =====================================================
# Nginx 运行阶段
# =====================================================
FROM nginx:alpine

# 复制 nginx 配置
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 暴露端口
EXPOSE 80

# 启动 nginx
CMD ["nginx", "-g", "daemon off;"]
