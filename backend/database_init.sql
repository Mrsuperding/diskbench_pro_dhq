-- =====================================================
-- DiskBench Pro 数据库初始化脚本
-- 支持 MySQL 8.0+ / PostgreSQL 14+
-- 使用方法：
--   MySQL:    mysql -u root -p < database_init.sql
--   PostgreSQL: psql -U postgres -d diskbench_pro -f database_init.sql
-- =====================================================

-- -------------------- 用户表 --------------------
CREATE TABLE IF NOT EXISTS `users` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `username` VARCHAR(50) NOT NULL UNIQUE,
  `email` VARCHAR(100) NOT NULL UNIQUE,
  `hashed_password` VARCHAR(255) NOT NULL,
  `role` ENUM('admin', 'user') DEFAULT 'user',
  `is_active` BOOLEAN DEFAULT TRUE,
  `avatar` TEXT,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_username` (`username`),
  INDEX `idx_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------- 节点表 --------------------
CREATE TABLE IF NOT EXISTS `nodes` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `node_name` VARCHAR(100) NOT NULL UNIQUE,
  `host` VARCHAR(255) NOT NULL,
  `port` INT DEFAULT 22,
  `login_type` ENUM('password', 'private_key') DEFAULT 'password',
  `username` VARCHAR(100) DEFAULT 'root',
  `password` VARCHAR(255),
  `private_key` TEXT,
  `status` ENUM('online', 'offline', 'error') DEFAULT 'offline',
  `os_type` VARCHAR(50),
  `cpu_info` TEXT,
  `memory_info` TEXT,
  `disk_info` TEXT,
  `created_by` INT,
  `is_public` BOOLEAN DEFAULT FALSE,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_health_check_at` DATETIME,
  `last_online_at` DATETIME,
  `health_fail_count` INT DEFAULT 0,
  `health_message` TEXT,
  `has_password` BOOLEAN DEFAULT FALSE,
  `has_private_key` BOOLEAN DEFAULT FALSE,
  FOREIGN KEY (`created_by`) REFERENCES `users`(`id`) ON DELETE SET NULL,
  INDEX `idx_node_name` (`node_name`),
  INDEX `idx_status` (`status`),
  INDEX `idx_created_by` (`created_by`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------- 节点分区表 --------------------
CREATE TABLE IF NOT EXISTS `node_partitions` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `node_id` INT NOT NULL,
  `partition_name` VARCHAR(100) NOT NULL,
  `mount_point` VARCHAR(255) NOT NULL,
  `filesystem` VARCHAR(50),
  `total_size` INT,
  `available_size` INT,
  `is_active` BOOLEAN DEFAULT TRUE,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`node_id`) REFERENCES `nodes`(`id`) ON DELETE CASCADE,
  INDEX `idx_node_id` (`node_id`),
  INDEX `idx_mount_point` (`mount_point`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------- 测试用例表 --------------------
CREATE TABLE IF NOT EXISTS `test_cases` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `case_name` VARCHAR(200) NOT NULL,
  `description` TEXT,
  `test_type` VARCHAR(50),
  `block_size` VARCHAR(20),
  `io_depth` INT DEFAULT 32,
  `num_jobs` INT DEFAULT 1,
  `runtime` INT DEFAULT 60,
  `file_size` VARCHAR(20),
  `rw_mode` VARCHAR(20),
  `io_engine` VARCHAR(20) DEFAULT 'libaio',
  `is_template` BOOLEAN DEFAULT FALSE,
  `created_by` INT,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`created_by`) REFERENCES `users`(`id`) ON DELETE SET NULL,
  INDEX `idx_case_name` (`case_name`),
  INDEX `idx_created_by` (`created_by`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------- 任务表 --------------------
CREATE TABLE IF NOT EXISTS `tasks` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `task_name` VARCHAR(200) NOT NULL,
  `description` TEXT,
  `test_case_id` INT,
  `is_public` BOOLEAN DEFAULT FALSE,
  `status` ENUM('pending', 'running', 'completed', 'failed', 'cancelled') DEFAULT 'pending',
  `created_by` INT,
  `start_time` DATETIME,
  `end_time` DATETIME,
  `duration` INT DEFAULT 0,
  `total_io_ops` BIGINT DEFAULT 0,
  `avg_iops` DECIMAL(10,2) DEFAULT 0,
  `avg_latency` DECIMAL(10,2) DEFAULT 0,
  `avg_bw` DECIMAL(10,2) DEFAULT 0,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`test_case_id`) REFERENCES `test_cases`(`id`) ON DELETE SET NULL,
  FOREIGN KEY (`created_by`) REFERENCES `users`(`id`) ON DELETE SET NULL,
  INDEX `idx_task_name` (`task_name`),
  INDEX `idx_status` (`status`),
  INDEX `idx_created_by` (`created_by`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------- 任务节点表 --------------------
CREATE TABLE IF NOT EXISTS `task_nodes` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `task_id` INT NOT NULL,
  `node_id` INT NOT NULL,
  `partition_id` INT,
  `status` ENUM('pending', 'running', 'completed', 'failed', 'cancelled') DEFAULT 'pending',
  `start_time` DATETIME,
  `end_time` DATETIME,
  `duration` INT DEFAULT 0,
  `io_ops` BIGINT DEFAULT 0,
  `iops` DECIMAL(10,2) DEFAULT 0,
  `latency` DECIMAL(10,2) DEFAULT 0,
  `bandwidth` DECIMAL(10,2) DEFAULT 0,
  `error_message` TEXT,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`task_id`) REFERENCES `tasks`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`node_id`) REFERENCES `nodes`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`partition_id`) REFERENCES `node_partitions`(`id`) ON DELETE SET NULL,
  INDEX `idx_task_id` (`task_id`),
  INDEX `idx_node_id` (`node_id`),
  INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------- IO性能数据表 --------------------
CREATE TABLE IF NOT EXISTS `io_performance_data` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `task_node_id` INT NOT NULL,
  `iops` DECIMAL(10,2) DEFAULT 0,
  `bandwidth` DECIMAL(10,2) DEFAULT 0,
  `latency` DECIMAL(10,2) DEFAULT 0,
  `read_iops` DECIMAL(10,2) DEFAULT 0,
  `write_iops` DECIMAL(10,2) DEFAULT 0,
  `read_bw` DECIMAL(10,2) DEFAULT 0,
  `write_bw` DECIMAL(10,2) DEFAULT 0,
  `read_lat` DECIMAL(10,2) DEFAULT 0,
  `write_lat` DECIMAL(10,2) DEFAULT 0,
  `cpu_usage` DECIMAL(10,2) DEFAULT 0,
  `memory_usage` DECIMAL(10,2) DEFAULT 0,
  `timestamp` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`task_node_id`) REFERENCES `task_nodes`(`id`) ON DELETE CASCADE,
  INDEX `idx_task_node_id` (`task_node_id`),
  INDEX `idx_timestamp` (`timestamp`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------- iostat数据表 --------------------
CREATE TABLE IF NOT EXISTS `iostat_data` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `task_node_id` INT NOT NULL,
  `device` VARCHAR(50),
  `tps` DECIMAL(10,2) DEFAULT 0,
  `kB_read_s` DECIMAL(10,2) DEFAULT 0,
  `kB_wrtn_s` DECIMAL(10,2) DEFAULT 0,
  `kB_dscd_s` DECIMAL(10,2) DEFAULT 0,
  `kB_read` INT DEFAULT 0,
  `kB_wrtn` INT DEFAULT 0,
  `kB_dscd` INT DEFAULT 0,
  `rqmps` DECIMAL(10,2) DEFAULT 0,
  `await_time` DECIMAL(10,2) DEFAULT 0,
  `aqu_sz` DECIMAL(10,2) DEFAULT 0,
  `util` DECIMAL(10,2) DEFAULT 0,
  `timestamp` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`task_node_id`) REFERENCES `task_nodes`(`id`) ON DELETE CASCADE,
  INDEX `idx_task_node_id` (`task_node_id`),
  INDEX `idx_device` (`device`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------- 任务日志表 --------------------
CREATE TABLE IF NOT EXISTS `task_logs` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `task_id` INT NOT NULL,
  `log_level` ENUM('debug', 'info', 'warning', 'error') DEFAULT 'info',
  `message` TEXT,
  `source` VARCHAR(100),
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`task_id`) REFERENCES `tasks`(`id`) ON DELETE CASCADE,
  INDEX `idx_task_id` (`task_id`),
  INDEX `idx_log_level` (`log_level`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------- 任务节点分区表 --------------------
CREATE TABLE IF NOT EXISTS `task_node_partitions` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `task_id` INT NOT NULL,
  `node_id` INT NOT NULL,
  `partition_id` INT NOT NULL,
  `capacity_limit` INT DEFAULT 0,
  `init_status` ENUM('pending', 'running', 'completed', 'failed') DEFAULT 'pending',
  `init_start_time` DATETIME,
  `init_end_time` DATETIME,
  `init_error` TEXT,
  `status` ENUM('pending', 'running', 'completed', 'failed') DEFAULT 'pending',
  `start_time` DATETIME,
  `end_time` DATETIME,
  `duration` INT DEFAULT 0,
  `io_ops` BIGINT DEFAULT 0,
  `iops` DECIMAL(10,2) DEFAULT 0,
  `latency` DECIMAL(10,2) DEFAULT 0,
  `bandwidth` DECIMAL(10,2) DEFAULT 0,
  `error_message` TEXT,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`task_id`) REFERENCES `tasks`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`node_id`) REFERENCES `nodes`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`partition_id`) REFERENCES `node_partitions`(`id`) ON DELETE CASCADE,
  UNIQUE KEY `uk_task_node_partition` (`task_id`, `node_id`, `partition_id`),
  INDEX `idx_task_id` (`task_id`),
  INDEX `idx_node_id` (`node_id`),
  INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------- 测试结果百分位表 --------------------
CREATE TABLE IF NOT EXISTS `test_result_percentiles` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `task_node_id` INT NOT NULL,
  `percentile_name` VARCHAR(50),
  `latency_us` DECIMAL(10,2) DEFAULT 0,
  `test_type` VARCHAR(20),
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`task_node_id`) REFERENCES `task_nodes`(`id`) ON DELETE CASCADE,
  INDEX `idx_task_node_id` (`task_node_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------- 性能基线表 --------------------
CREATE TABLE IF NOT EXISTS `performance_baselines` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(100) NOT NULL,
  `description` TEXT,
  `test_type` VARCHAR(50),
  `block_size` VARCHAR(20),
  `config_json` TEXT,
  `is_active` BOOLEAN DEFAULT TRUE,
  `created_by` INT,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`created_by`) REFERENCES `users`(`id`) ON DELETE SET NULL,
  INDEX `idx_name` (`name`),
  INDEX `idx_is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------- 审计日志表 --------------------
CREATE TABLE IF NOT EXISTS `audit_logs` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT,
  `action` VARCHAR(100) NOT NULL,
  `resource` VARCHAR(100),
  `resource_id` INT,
  `details` TEXT,
  `ip_address` VARCHAR(45),
  `user_agent` TEXT,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE SET NULL,
  INDEX `idx_user_id` (`user_id`),
  INDEX `idx_action` (`action`),
  INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------- 告警规则表 --------------------
CREATE TABLE IF NOT EXISTS `alert_rules` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(100) NOT NULL,
  `description` TEXT,
  `metric_type` VARCHAR(50),
  `condition_type` VARCHAR(20),
  `threshold` DECIMAL(10,2),
  `comparison` VARCHAR(10),
  `enabled` BOOLEAN DEFAULT TRUE,
  `created_by` INT,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`created_by`) REFERENCES `users`(`id`) ON DELETE SET NULL,
  INDEX `idx_enabled` (`enabled`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------- 告警事件表 --------------------
CREATE TABLE IF NOT EXISTS `alert_events` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `rule_id` INT,
  `task_id` INT,
  `node_id` INT,
  `triggered_value` DECIMAL(10,2),
  `status` ENUM('triggered', 'acknowledged', 'resolved') DEFAULT 'triggered',
  `triggered_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `acknowledged_at` DATETIME,
  `acknowledged_by` INT,
  `resolved_at` DATETIME,
  FOREIGN KEY (`rule_id`) REFERENCES `alert_rules`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`task_id`) REFERENCES `tasks`(`id`) ON DELETE SET NULL,
  FOREIGN KEY (`node_id`) REFERENCES `nodes`(`id`) ON DELETE SET NULL,
  FOREIGN KEY (`acknowledged_by`) REFERENCES `users`(`id`) ON DELETE SET NULL,
  INDEX `idx_rule_id` (`rule_id`),
  INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------- 监控数据表 --------------------
CREATE TABLE IF NOT EXISTS `monitor` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `metric_name` VARCHAR(100) NOT NULL,
  `metric_type` VARCHAR(50),
  `value` DECIMAL(10,2),
  `unit` VARCHAR(20),
  `tags` JSON,
  `timestamp` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_metric_name` (`metric_name`),
  INDEX `idx_timestamp` (`timestamp`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------- 定时任务表 --------------------
CREATE TABLE IF NOT EXISTS `scheduled_tasks` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(100) NOT NULL,
  `task_type` VARCHAR(50),
  `cron_expression` VARCHAR(50),
  `task_config` JSON,
  `enabled` BOOLEAN DEFAULT TRUE,
  `last_run_at` DATETIME,
  `next_run_at` DATETIME,
  `created_by` INT,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`created_by`) REFERENCES `users`(`id`) ON DELETE SET NULL,
  INDEX `idx_enabled` (`enabled`),
  INDEX `idx_next_run_at` (`next_run_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------- 运行批次表 --------------------
CREATE TABLE IF NOT EXISTS `run_batches` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `batch_name` VARCHAR(100),
  `description` TEXT,
  `status` ENUM('pending', 'running', 'completed', 'failed') DEFAULT 'pending',
  `total_tasks` INT DEFAULT 0,
  `completed_tasks` INT DEFAULT 0,
  `failed_tasks` INT DEFAULT 0,
  `started_at` DATETIME,
  `completed_at` DATETIME,
  `created_by` INT,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`created_by`) REFERENCES `users`(`id`) ON DELETE SET NULL,
  INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------- 批次任务项表 --------------------
CREATE TABLE IF NOT EXISTS `run_batch_items` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `batch_id` INT NOT NULL,
  `task_id` INT NOT NULL,
  `order_index` INT DEFAULT 0,
  `status` ENUM('pending', 'running', 'completed', 'failed', 'skipped') DEFAULT 'pending',
  `started_at` DATETIME,
  `completed_at` DATETIME,
  `error_message` TEXT,
  FOREIGN KEY (`batch_id`) REFERENCES `run_batches`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`task_id`) REFERENCES `tasks`(`id`) ON DELETE CASCADE,
  INDEX `idx_batch_id` (`batch_id`),
  INDEX `idx_task_id` (`task_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================================================
-- 初始化数据
-- =====================================================

-- 插入默认管理员用户 (密码: admin123)
INSERT INTO `users` (`username`, `email`, `hashed_password`, `role`, `is_active`)
VALUES ('admin', 'admin@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyDAXCZ3aKjLXS', 'admin', TRUE)
ON DUPLICATE KEY UPDATE `username` = `username`;

-- 插入普通用户 (密码: user123)
INSERT INTO `users` (`username`, `email`, `hashed_password`, `role`, `is_active`)
VALUES ('user1', 'user1@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyDAXCZ3aKjLXS', 'user', TRUE)
ON DUPLICATE KEY UPDATE `username` = `username`;

COMMIT;
