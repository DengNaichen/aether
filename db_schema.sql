-- db_schema.sql

-- 首先，如果表已存在，则删除它们，确保脚本可以重复运行
DROP TABLE IF EXISTS KnowledgeEdges;
DROP TABLE IF EXISTS KnowledgeNodes;
DROP TABLE IF EXISTS StudentNodeProgress;
DROP TABLE IF EXISTS Students;

-- 创建知识节点表
CREATE TABLE KnowledgeNodes (
    node_id SERIAL PRIMARY KEY,  -- SERIAL 类型会自动创建自增的整数ID
    topic_name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    subject VARCHAR(100)
);

-- 创建知识关联表
CREATE TABLE KnowledgeEdges (
    edge_id SERIAL PRIMARY KEY,
    source_node_id INT NOT NULL,
    target_node_id INT NOT NULL,
    relationship VARCHAR(50) NOT NULL,
    
    -- 设置外键约束，确保数据的完整性
    FOREIGN KEY (source_node_id) REFERENCES KnowledgeNodes (node_id) ON DELETE CASCADE,
    FOREIGN KEY (target_node_id) REFERENCES KnowledgeNodes (node_id) ON DELETE CASCADE
);

-- 为 topic_name 创建索引以加快查询速度
CREATE INDEX idx_topic_name ON KnowledgeNodes (topic_name);


CREATE TABlE Students (
    student_id SERIAL PRIMARY KEY,
    student_name VARCHAR(255) NOT NULL,
    student_email VARCHAR(255) UNIQUE NOT NULL,
    enrollment_date TIMESTAMP DEFAULT NOW()
);

CREATE TYPE Proficiency_level AS ENUM ('unseen', 'learning', 'good', 'mastered');

CREATE TABLE StudentNodeProgress(
    student_id INT NOT NULL REFERENCES Students(student_id) ON DELETE CASCADE,
    node_id INT NOT NULL REFERENCES KnowledgeNodes(node_id) ON DELETE CASCADE,
    mastery_level Proficiency_level NOT NULL DEFAULT 'unseen',
    is_studied BOOLEAN NOT NULL DEFAULT FALSE,
    last_reviewed_at TIMESTAMPTZ,
    next_review_date DATE, -- DATE 类型只存日期，适合用于“哪一天”复习
    PRIMARY KEY (student_id, node_id)
);