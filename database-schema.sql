-- IO性能测试管理平台数据库设计
-- 创建数据库
create database if not exists io_test_platform character set utf8mb4 collate utf8mb4_unicode_ci;
use io_test_platform;

-- 用户表
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    role ENUM('admin', 'user') DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 节点信息表
CREATE TABLE nodes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    node_name VARCHAR(100) NOT NULL,
    host VARCHAR(255) NOT NULL,
    port INT DEFAULT 22,
    login_type ENUM('password', 'key') DEFAULT 'password',
    username VARCHAR(100) NOT NULL,
    password VARCHAR(255),
    private_key TEXT,
    status ENUM('online', 'offline', 'testing') DEFAULT 'offline',
    os_type VARCHAR(50),
    cpu_info VARCHAR(255),
    memory_info VARCHAR(255),
    disk_info TEXT,
    created_by INT,
    is_public BOOLEAN DEFAULT FALSE,
    tool_path VARCHAR(255) COMMENT '工具目录路径，用于存放 fio 等 IO 测试工具',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- 节点分区表
CREATE TABLE node_partitions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    node_id INT NOT NULL,
    partition_name VARCHAR(100) NOT NULL,
    mount_point VARCHAR(255) NOT NULL,
    filesystem VARCHAR(50),
    total_size BIGINT,
    available_size BIGINT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (node_id) REFERENCES nodes(id) ON DELETE CASCADE
);

-- FIO用例表
CREATE TABLE test_cases (
    id INT PRIMARY KEY AUTO_INCREMENT,
    case_name VARCHAR(200) NOT NULL,
    description TEXT,
    io_engine VARCHAR(50) DEFAULT 'libaio',
    block_size VARCHAR(20) DEFAULT '4k',
    queue_depth INT DEFAULT 32,
    io_size VARCHAR(20) DEFAULT '1G',
    runtime INT DEFAULT 60,
    rw_mode ENUM('read', 'write', 'randread', 'randwrite', 'rw', 'randrw') DEFAULT 'read',
    rw_ratio VARCHAR(10) DEFAULT '50/50',
    compression_ratio DECIMAL(3,2) DEFAULT 0.00,
    direct_io BOOLEAN DEFAULT TRUE,
    numjobs INT DEFAULT 1,
    time_based BOOLEAN DEFAULT TRUE,
    verify VARCHAR(20),
    verify_fatal BOOLEAN DEFAULT FALSE,
    group_reporting BOOLEAN DEFAULT TRUE,
    created_by INT,
    is_public BOOLEAN DEFAULT FALSE,
    is_template BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- 任务表
CREATE TABLE tasks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    task_name VARCHAR(200) NOT NULL,
    description TEXT,
    status ENUM('pending', 'running', 'completed', 'failed', 'cancelled') DEFAULT 'pending',
    created_by INT NOT NULL,
    test_case_id INT NOT NULL,
    is_public BOOLEAN DEFAULT FALSE,
    start_time TIMESTAMP NULL,
    end_time TIMESTAMP NULL,
    duration INT DEFAULT 0,
    total_io_ops BIGINT DEFAULT 0,
    avg_iops DECIMAL(10,2) DEFAULT 0,
    avg_latency DECIMAL(10,2) DEFAULT 0,
    avg_bw DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (test_case_id) REFERENCES test_cases(id) ON DELETE CASCADE
);

-- 任务节点关联表
CREATE TABLE task_nodes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    task_id INT NOT NULL,
    node_id INT NOT NULL,
    partition_id INT NOT NULL,
    status ENUM('pending', 'running', 'completed', 'failed', 'cancelled') DEFAULT 'pending',
    start_time TIMESTAMP NULL,
    end_time TIMESTAMP NULL,
    duration INT DEFAULT 0,
    io_ops BIGINT DEFAULT 0,
    iops DECIMAL(10,2) DEFAULT 0,
    latency DECIMAL(10,2) DEFAULT 0,
    bandwidth DECIMAL(10,2) DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (node_id) REFERENCES nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (partition_id) REFERENCES node_partitions(id) ON DELETE CASCADE
);

-- IO性能数据表
CREATE TABLE io_performance_data (
    id INT PRIMARY KEY AUTO_INCREMENT,
    task_node_id INT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    iops DECIMAL(10,2) NOT NULL,
    bandwidth DECIMAL(10,2) NOT NULL,
    latency DECIMAL(10,2) NOT NULL,
    read_iops DECIMAL(10,2) DEFAULT 0,
    write_iops DECIMAL(10,2) DEFAULT 0,
    read_bw DECIMAL(10,2) DEFAULT 0,
    write_bw DECIMAL(10,2) DEFAULT 0,
    read_lat DECIMAL(10,2) DEFAULT 0,
    write_lat DECIMAL(10,2) DEFAULT 0,
    cpu_usage DECIMAL(5,2) DEFAULT 0,
    memory_usage DECIMAL(5,2) DEFAULT 0,
    FOREIGN KEY (task_node_id) REFERENCES task_nodes(id) ON DELETE CASCADE,
    INDEX idx_task_node_timestamp (task_node_id, timestamp)
);

-- iostat监控数据表
CREATE TABLE iostat_data (
    id INT PRIMARY KEY AUTO_INCREMENT,
    task_node_id INT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    device VARCHAR(50) NOT NULL,
    tps DECIMAL(10,2) NOT NULL,
    kB_read_s DECIMAL(10,2) NOT NULL,
    kB_wrtn_s DECIMAL(10,2) NOT NULL,
    kB_dscd_s DECIMAL(10,2) DEFAULT 0,
    kB_read BIGINT DEFAULT 0,
    kB_wrtn BIGINT DEFAULT 0,
    kB_dscd BIGINT DEFAULT 0,
    rqmps DECIMAL(10,2) DEFAULT 0,
    await DECIMAL(10,2) DEFAULT 0,
    aqu_sz DECIMAL(10,2) DEFAULT 0,
    util DECIMAL(5,2) DEFAULT 0,
    FOREIGN KEY (task_node_id) REFERENCES task_nodes(id) ON DELETE CASCADE,
    INDEX idx_task_node_device_timestamp (task_node_id, device, timestamp)
);

-- 任务日志表
CREATE TABLE task_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    task_id INT NOT NULL,
    log_level ENUM('debug', 'info', 'warning', 'error') DEFAULT 'info',
    message TEXT NOT NULL,
    source VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    INDEX idx_task_timestamp (task_id, created_at)
);

-- 任务分享表
CREATE TABLE task_shares (
    id INT PRIMARY KEY AUTO_INCREMENT,
    task_id INT NOT NULL,
    shared_by INT NOT NULL,
    shared_to INT NOT NULL,
    permission ENUM('read', 'write') DEFAULT 'read',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (shared_by) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (shared_to) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_share (task_id, shared_to)
);

-- 系统配置表
CREATE TABLE system_configs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT,
    description VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 插入默认数据
INSERT INTO users (username, password, email, role) VALUES 
('admin', '$2b$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'admin@example.com', 'admin'),
('demo', '$2b$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'demo@example.com', 'user');

INSERT INTO system_configs (config_key, config_value, description) VALUES
('max_concurrent_tasks', '10', '最大并发任务数'),
('default_task_timeout', '3600', '默认任务超时时间（秒）'),
('data_retention_days', '30', '监控数据保留天数'),
('enable_realtime_monitor', 'true', '是否启用实时监控'),
('fio_path', '/usr/bin/fio', 'fio可执行文件路径');

-- 创建视图
CREATE VIEW task_overview AS
SELECT 
    t.id,
    t.task_name,
    t.status,
    t.created_by,
    u.username as creator_name,
    tc.case_name,
    t.start_time,
    t.end_time,
    t.duration,
    t.avg_iops,
    t.avg_latency,
    t.avg_bw,
    COUNT(tn.id) as node_count,
    t.is_public,
    t.created_at
FROM tasks t
LEFT JOIN users u ON t.created_by = u.id
LEFT JOIN test_cases tc ON t.test_case_id = tc.id
LEFT JOIN task_nodes tn ON t.id = tn.task_id
GROUP BY t.id;

CREATE VIEW node_overview AS
SELECT
    n.id,
    n.node_name,
    n.host,
    n.port,
    n.status,
    n.os_type,
    n.cpu_info,
    n.memory_info,
    u.username as creator_name,
    COUNT(np.id) as partition_count,
    n.is_public,
    n.created_at
FROM nodes n
LEFT JOIN users u ON n.created_by = u.id
LEFT JOIN node_partitions np ON n.id = np.node_id
GROUP BY n.id;

-- 任务节点分区关联表
CREATE TABLE task_node_partitions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    task_id INT NOT NULL,
    node_id INT NOT NULL,
    partition_id INT NOT NULL,
    capacity_limit INT DEFAULT 0 COMMENT '测试容量限制(MB),0表示无限制',
    init_status ENUM('pending', 'running', 'completed', 'failed', 'skipped') DEFAULT 'pending',
    init_start_time TIMESTAMP NULL,
    init_end_time TIMESTAMP NULL,
    init_error TEXT,
    status ENUM('pending', 'running', 'completed', 'failed', 'cancelled') DEFAULT 'pending',
    start_time TIMESTAMP NULL,
    end_time TIMESTAMP NULL,
    duration INT DEFAULT 0,
    io_ops BIGINT DEFAULT 0,
    iops DECIMAL(10,2) DEFAULT 0,
    latency DECIMAL(10,2) DEFAULT 0,
    bandwidth DECIMAL(10,2) DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (node_id) REFERENCES nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (partition_id) REFERENCES node_partitions(id) ON DELETE CASCADE,
    INDEX idx_task_node_partition (task_id, node_id, partition_id)
);

-- 基线配置表
CREATE TABLE baselines (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    test_type VARCHAR(50),
    block_size VARCHAR(20),
    config_json TEXT COMMENT '基线配置JSON，包含阈值规则',
    is_active BOOLEAN DEFAULT TRUE,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_baseline_name (name),
    INDEX idx_baseline_test_type (test_type)
);

-- 基线指标表
CREATE TABLE baseline_metrics (
    id INT PRIMARY KEY AUTO_INCREMENT,
    baseline_id INT NOT NULL,
    metric_name VARCHAR(50) NOT NULL,
    value DECIMAL(15,2) NOT NULL,
    unit VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (baseline_id) REFERENCES baselines(id) ON DELETE CASCADE,
    INDEX idx_baseline_metric (baseline_id, metric_name)
);

-- 测试结果百分位数表
CREATE TABLE test_result_percentiles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    task_node_id INT NOT NULL,
    percentile_name VARCHAR(20) NOT NULL,
    latency_us DECIMAL(15,2) NOT NULL,
    test_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_node_id) REFERENCES task_nodes(id) ON DELETE CASCADE,
    INDEX idx_task_node_percentile (task_node_id, percentile_name)
);