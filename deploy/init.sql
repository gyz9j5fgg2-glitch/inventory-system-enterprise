-- 初始化数据库脚本
-- 在 PostgreSQL 容器启动时自动执行

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 创建初始数据（可选）
-- INSERT INTO organizations (name, code) VALUES ('总公司', 'HQ');
