-- 达梦 DM8：为已有库补充资源可预约数量上限（新库请直接用 init_db.sql）
-- 若列已存在可跳过

ALTER TABLE LAB_RESOURCE ADD MAX_QUANTITY INT DEFAULT 1 NOT NULL;
