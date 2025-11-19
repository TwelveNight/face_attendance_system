-- 添加示例部门数据（MySQL版本）
-- 适用于高校考勤系统

-- 一级部门（学院）
INSERT INTO department (name, code, parent_id, level, sort_order, description, is_active, created_at) VALUES
('计算机学院', 'CS', NULL, 1, 1, '计算机科学与技术相关专业', 1, NOW()),
('电子信息学院', 'EE', NULL, 1, 2, '电子信息工程相关专业', 1, NOW()),
('机械工程学院', 'ME', NULL, 1, 3, '机械工程相关专业', 1, NOW()),
('经济管理学院', 'EM', NULL, 1, 4, '经济管理相关专业', 1, NOW());

-- 二级部门（专业/系）
-- 注意：这里的parent_id需要根据实际插入后的ID调整
-- 假设一级部门的ID从1开始依次递增

INSERT INTO department (name, code, parent_id, level, sort_order, description, is_active, created_at) VALUES
-- 计算机学院下的专业（假设计算机学院ID=1）
('计算机科学与技术', 'CS_CST', (SELECT id FROM department WHERE code='CS'), 2, 1, '计算机科学与技术专业', 1, NOW()),
('软件工程', 'CS_SE', (SELECT id FROM department WHERE code='CS'), 2, 2, '软件工程专业', 1, NOW()),
('网络工程', 'CS_NE', (SELECT id FROM department WHERE code='CS'), 2, 3, '网络工程专业', 1, NOW()),
('人工智能', 'CS_AI', (SELECT id FROM department WHERE code='CS'), 2, 4, '人工智能专业', 1, NOW()),

-- 电子信息学院下的专业（假设电子信息学院ID=2）
('电子信息工程', 'EE_EIE', (SELECT id FROM department WHERE code='EE'), 2, 1, '电子信息工程专业', 1, NOW()),
('通信工程', 'EE_CE', (SELECT id FROM department WHERE code='EE'), 2, 2, '通信工程专业', 1, NOW()),
('自动化', 'EE_AUTO', (SELECT id FROM department WHERE code='EE'), 2, 3, '自动化专业', 1, NOW()),

-- 机械工程学院下的专业（假设机械工程学院ID=3）
('机械设计制造及其自动化', 'ME_MD', (SELECT id FROM department WHERE code='ME'), 2, 1, '机械设计制造及其自动化专业', 1, NOW()),
('车辆工程', 'ME_VE', (SELECT id FROM department WHERE code='ME'), 2, 2, '车辆工程专业', 1, NOW()),

-- 经济管理学院下的专业（假设经济管理学院ID=4）
('工商管理', 'EM_BA', (SELECT id FROM department WHERE code='EM'), 2, 1, '工商管理专业', 1, NOW()),
('会计学', 'EM_ACC', (SELECT id FROM department WHERE code='EM'), 2, 2, '会计学专业', 1, NOW());

-- 三级部门（班级）
INSERT INTO department (name, code, parent_id, level, sort_order, description, is_active, created_at) VALUES
-- 计算机科学与技术专业的班级
('计科2021级1班', 'CS_CST_2021_1', (SELECT id FROM department WHERE code='CS_CST'), 3, 1, '计算机科学与技术2021级1班', 1, NOW()),
('计科2021级2班', 'CS_CST_2021_2', (SELECT id FROM department WHERE code='CS_CST'), 3, 2, '计算机科学与技术2021级2班', 1, NOW()),
('计科2022级1班', 'CS_CST_2022_1', (SELECT id FROM department WHERE code='CS_CST'), 3, 3, '计算机科学与技术2022级1班', 1, NOW()),

-- 软件工程专业的班级
('软工2021级1班', 'CS_SE_2021_1', (SELECT id FROM department WHERE code='CS_SE'), 3, 1, '软件工程2021级1班', 1, NOW()),
('软工2021级2班', 'CS_SE_2021_2', (SELECT id FROM department WHERE code='CS_SE'), 3, 2, '软件工程2021级2班', 1, NOW()),
('软工2022级1班', 'CS_SE_2022_1', (SELECT id FROM department WHERE code='CS_SE'), 3, 3, '软件工程2022级1班', 1, NOW()),

-- 人工智能专业的班级
('人工智能2021级1班', 'CS_AI_2021_1', (SELECT id FROM department WHERE code='CS_AI'), 3, 1, '人工智能2021级1班', 1, NOW()),
('人工智能2022级1班', 'CS_AI_2022_1', (SELECT id FROM department WHERE code='CS_AI'), 3, 2, '人工智能2022级1班', 1, NOW());

-- 查看插入结果
SELECT 
    d1.name as '一级部门',
    d2.name as '二级部门', 
    d3.name as '三级部门'
FROM department d1
LEFT JOIN department d2 ON d2.parent_id = d1.id
LEFT JOIN department d3 ON d3.parent_id = d2.id
WHERE d1.parent_id IS NULL
ORDER BY d1.sort_order, d2.sort_order, d3.sort_order;
