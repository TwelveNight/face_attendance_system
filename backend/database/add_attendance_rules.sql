-- 考勤规则初始化数据
-- 删除现有规则（如果需要）
-- DELETE FROM attendance_rule;

-- 1. 默认规则 - 标准工作日考勤
INSERT INTO attendance_rule (
    name, 
    work_start_time, 
    work_end_time, 
    late_threshold, 
    early_threshold, 
    work_days, 
    department_id, 
    is_default, 
    is_active, 
    is_open_mode, 
    description,
    created_at
) VALUES (
    '标准工作日规则',
    '09:00:00',
    '18:00:00',
    15,  -- 允许迟到15分钟
    15,  -- 允许早退15分钟
    '1,2,3,4,5',  -- 周一到周五
    NULL,  -- 不关联特定部门，作为默认规则
    TRUE,  -- 设为默认规则
    TRUE,  -- 启用
    FALSE,  -- 非开放模式
    '标准工作日考勤规则：9:00上班，18:00下班，允许迟到/早退15分钟。适用于所有未设置专属规则的部门。',
    NOW()
);

-- 2. 弹性工作制 - 适用于技术类部门
INSERT INTO attendance_rule (
    name, 
    work_start_time, 
    work_end_time, 
    late_threshold, 
    early_threshold, 
    work_days, 
    department_id, 
    is_default, 
    is_active, 
    is_open_mode, 
    description,
    created_at
) VALUES (
    '弹性工作制',
    '10:00:00',
    '19:00:00',
    30,  -- 允许迟到30分钟
    30,  -- 允许早退30分钟
    '1,2,3,4,5',  -- 周一到周五
    (SELECT id FROM department WHERE code = 'CS' LIMIT 1),  -- 计算机科学与技术专业
    FALSE,  -- 非默认规则
    TRUE,  -- 启用
    FALSE,  -- 非开放模式
    '弹性工作制：10:00上班，19:00下班，允许迟到/早退30分钟。适用于技术类专业，提供更灵活的工作时间。',
    NOW()
);

-- 3. 早班制度 - 适用于行政管理部门
INSERT INTO attendance_rule (
    name, 
    work_start_time, 
    work_end_time, 
    late_threshold, 
    early_threshold, 
    work_days, 
    department_id, 
    is_default, 
    is_active, 
    is_open_mode, 
    description,
    created_at
) VALUES (
    '早班制度',
    '08:30:00',
    '17:30:00',
    10,  -- 允许迟到10分钟
    10,  -- 允许早退10分钟
    '1,2,3,4,5',  -- 周一到周五
    NULL,  -- 暂不关联部门，可后续指定
    FALSE,  -- 非默认规则
    FALSE,  -- 暂不启用，需要时再启用
    FALSE,  -- 非开放模式
    '早班制度：8:30上班，17:30下班，允许迟到/早退10分钟。适用于行政管理类部门。',
    NOW()
);

-- 4. 开放模式 - 用于特殊活动或节假日
INSERT INTO attendance_rule (
    name, 
    work_start_time, 
    work_end_time, 
    late_threshold, 
    early_threshold, 
    work_days, 
    department_id, 
    is_default, 
    is_active, 
    is_open_mode, 
    description,
    created_at
) VALUES (
    '开放打卡模式',
    '00:00:00',
    '23:59:59',
    0,  -- 不判断迟到
    0,  -- 不判断早退
    '1,2,3,4,5,6,7',  -- 全周
    NULL,  -- 不关联特定部门
    FALSE,  -- 非默认规则
    FALSE,  -- 默认不启用，需要时手动启用
    TRUE,  -- 开放模式
    '开放打卡模式：任何时间打卡都算正常，不判断迟到早退。适用于特殊活动、节假日或测试期间。',
    NOW()
);

-- 5. 严格考勤 - 用于重要项目期间
INSERT INTO attendance_rule (
    name, 
    work_start_time, 
    work_end_time, 
    late_threshold, 
    early_threshold, 
    work_days, 
    department_id, 
    is_default, 
    is_active, 
    is_open_mode, 
    description,
    created_at
) VALUES (
    '严格考勤模式',
    '09:00:00',
    '18:00:00',
    0,  -- 不允许迟到
    0,  -- 不允许早退
    '1,2,3,4,5',  -- 周一到周五
    NULL,  -- 不关联特定部门
    FALSE,  -- 非默认规则
    FALSE,  -- 默认不启用
    FALSE,  -- 非开放模式
    '严格考勤模式：9:00上班，18:00下班，不允许迟到早退。适用于重要项目期间或考试周。',
    NOW()
);
