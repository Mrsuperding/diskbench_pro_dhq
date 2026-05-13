# fio 离线工具包清单

## 概述

在有网络的机器上准备 fio 及依赖库，用于部署到离线 CentOS 节点。

## 文件位置

```
diskbench_pro/
└── tools/                      # 离线工具存放目录
    ├── bin/                    # 可执行文件
    │   └── fio                 # fio 二进制（需支持 libaio）
    └── lib/                    # 依赖库
        └── libaio.so.1         # libaio 运行时库
```

## 必需文件

### 1. fio 二进制文件
- **路径**: `tools/bin/fio`
- **获取方式**:
  - 方式A（推荐）: 在有网络的 CentOS 上编译 fio 并启用 libaio 支持
  - 方式B: 使用支持 libaio 的预编译 fio

### 2. libaio 运行时库
- **路径**: `tools/lib/libaio.so.1`
- **包名**: `libaio` 或 `libaio1`
- **安装命令（CentOS）**:
  ```bash
  yum install -y libaio
  ```
- **安装命令（Ubuntu/Debian）**:
  ```bash
  apt-get install -y libaio1 libaio-dev
  ```

## 完整目录结构

```
tools/
├── bin/
│   └── fio                    # fio 主程序
└── lib/
    ├── libaio.so.1            # libaio 运行时库
    ├── libpthread.so.0        # POSIX 线程库
    ├── libc.so.6              # C 标准库
    └── ld-linux-x86-64.so.2   # 动态链接器
```

## 在 CentOS 上编译支持 libaio 的 fio

```bash
# 安装编译依赖
yum install -y gcc make autoconf automake libtool \
    flex bison libaio-devel zlib-devel

# 下载 fio 源码
wget https://github.com/axboe/fio/archive/refs/tags/fio-3.36.tar.gz
tar -xzf fio-3.36.tar.gz
cd fio-fio-3.36

# 编译（--enable-libaio 启用 libaio 支持）
./configure --enable-libaio
make -j$(nproc)

# 检查是否支持 libaio
./fio --enghelp 2>&1 | grep libaio
# 应该输出: libaio
```

## 快速收集脚本（Linux）

在有网络的 Linux 上运行 `scripts/fio_offline_tool_builder.sh` 或手动：

```bash
# 在有网络的 Linux 上运行
cd diskbench_pro/tools

# 创建目录
mkdir -p bin lib

# 复制 fio
cp /path/to/fio bin/

# 复制 libaio（根据系统路径）
cp /lib64/libaio.so.1 lib/ 2>/dev/null || \
cp /usr/lib64/libaio.so.1 lib/ 2>/dev/null || \
cp /usr/lib/libaio.so.1 lib/

# 打包（返回项目根目录）
cd ..
tar -czf fio_offline_tools.tar.gz -C tools bin lib
```

## 检查 fio 是否支持 libaio

```bash
# 检查输出是否包含 libaio
fio --enghelp 2>&1 | grep -i libaio

# 示例输出（有 libaio）:
# Available IO engines:
# ...
# libaio
# ...

# 示例输出（没有 libaio）:
# Available IO engines:
# ...
# psync
# ...
```

## 在离线节点上部署

### 方式 1: 通过 API 上传（推荐）

1. 打包：
   ```bash
   # 在项目根目录
   tar -czf fio_offline_tools.tar.gz -C tools bin lib
   ```

2. 调用 API：
   ```
   POST http://localhost:3000/api/nodes/{node_id}/upload-tool-bundle
   ```

   用 curl：
   ```bash
   curl -X POST "http://localhost:3000/api/nodes/44/upload-tool-bundle" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -F "file=@fio_offline_tools.tar.gz"
   ```

3. **前提**：节点已设置 `tool_path`（如 `/opt/diskbench_tools`）

4. API 会自动：
   - 上传到节点的 `tool_path` 目录
   - 自动解压
   - 配置 LD_LIBRARY_PATH

### 方式 2: 手动上传

1. 上传打包文件:
   ```bash
   scp fio_offline_tools.tar.gz root@<离线节点IP>:/opt/
   ```

2. 在节点上解压:
   ```bash
   cd /opt
   tar -xzf fio_offline_tools.tar.gz
   ```

3. 设置环境变量:
   ```bash
   export LD_LIBRARY_PATH=/opt/diskbench_tools/lib:$LD_LIBRARY_PATH
   ```

4. 验证:
   ```bash
   /opt/diskbench_tools/bin/fio --enghelp 2>&1 | grep libaio
   ```

5. 在平台设置节点的 tool_path 为 `/opt/diskbench_tools`

## 验证清单

- [ ] `tools/bin/fio` 存在且可执行
- [ ] `tools/lib/libaio.so.1` 存在
- [ ] `fio --enghelp 2>&1 | grep libaio` 有输出
- [ ] 节点 tool_path 已设置（如 `/opt/diskbench_tools`）
- [ ] 调用 upload-tool-bundle API 成功
