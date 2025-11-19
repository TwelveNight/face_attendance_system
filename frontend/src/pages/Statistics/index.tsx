/**
 * 统计分析页面
 */
import { useEffect, useState } from 'react';
import { Card, Row, Col, Statistic, DatePicker, Space, Spin, Select } from 'antd';
import { BarChartOutlined } from '@ant-design/icons';
import { statisticsApi, departmentApi } from '../../api/client';
import type { Statistics as StatsType, Department } from '../../types';
import dayjs, { type Dayjs } from 'dayjs';

const Statistics = () => {
  const [loading, setLoading] = useState(false);
  const [dailyStats, setDailyStats] = useState<StatsType | null>(null);
  const [selectedDate, setSelectedDate] = useState<Dayjs>(dayjs());
  const [departmentFilter, setDepartmentFilter] = useState<number | undefined>(undefined);
  const [departments, setDepartments] = useState<Department[]>([]);

  useEffect(() => {
    loadStatistics();
    loadDepartments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDate, departmentFilter]);

  const loadDepartments = async () => {
    try {
      const response = await departmentApi.getAll(false);
      const depts = response.data || [];
      
      // 按层级和排序字段排序，确保父部门在子部门前面
      const sortedDepts = sortDepartments(depts);
      setDepartments(sortedDepts);
    } catch (error: any) {
      console.error('获取部门列表失败:', error);
    }
  };

  // 递归排序部门，确保树形结构的顺序
  const sortDepartments = (depts: Department[]) => {
    const result: Department[] = [];
    
    // 找出所有根部门（一级部门）
    const roots = depts.filter(d => !d.parent_id).sort((a, b) => a.sort_order - b.sort_order);
    
    // 递归添加部门及其子部门
    const addDeptWithChildren = (dept: Department) => {
      result.push(dept);
      // 找出当前部门的所有子部门
      const children = depts
        .filter(d => d.parent_id === dept.id)
        .sort((a, b) => a.sort_order - b.sort_order);
      children.forEach(child => addDeptWithChildren(child));
    };
    
    // 从根部门开始递归添加
    roots.forEach(root => addDeptWithChildren(root));
    
    return result;
  };

  const loadStatistics = async () => {
    setLoading(true);
    try {
      const dateStr = selectedDate.format('YYYY-MM-DD');
      const response = await statisticsApi.getDailyWithDept(dateStr, departmentFilter);
      setDailyStats(response.data);
    } catch (error) {
      console.error('加载统计数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" tip="加载中..." />
      </div>
    );
  }

  return (
    <div>
      <Card
        title={
          <Space>
            <BarChartOutlined />
            <span>统计分析</span>
          </Space>
        }
        extra={
          <Space>
            <Select
              style={{ width: 200 }}
              placeholder="部门筛选"
              allowClear
              showSearch
              optionFilterProp="children"
              value={departmentFilter}
              onChange={setDepartmentFilter}
            >
              {departments.map(dept => {
                const indent = dept.level === 1 ? '' : dept.level === 2 ? '├─ ' : '│  └─ ';
                return (
                  <Select.Option key={dept.id} value={dept.id}>
                    {indent}{dept.name}
                  </Select.Option>
                );
              })}
            </Select>
            <DatePicker
              value={selectedDate}
              onChange={(date) => date && setSelectedDate(date)}
              placeholder="选择日期"
            />
          </Space>
        }
      >
        <h3>日期: {selectedDate.format('YYYY年MM月DD日')}</h3>

        {/* 统计卡片 */}
        <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="总打卡次数"
                value={dailyStats?.total || 0}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>

          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="出勤人数"
                value={dailyStats?.unique_users || 0}
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>

          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="出勤率"
                value={dailyStats?.attendance_rate || 0}
                precision={1}
                suffix="%"
                valueStyle={{ color: '#cf1322' }}
              />
            </Card>
          </Col>
        </Row>

        {/* 状态分布 */}
        {dailyStats?.status_distribution && (
          <Card title="考勤状态分布" style={{ marginTop: 24 }}>
            <Row gutter={16}>
              {Object.entries(dailyStats.status_distribution).map(([status, count]) => {
                const statusMap: Record<string, { label: string; color: string }> = {
                  present: { label: '正常', color: '#3f8600' },
                  late: { label: '迟到', color: '#faad14' },
                  absent: { label: '缺勤', color: '#cf1322' },
                };
                const info = statusMap[status] || { label: status, color: '#666' };

                return (
                  <Col key={status} xs={24} sm={8}>
                    <Statistic
                      title={info.label}
                      value={count}
                      valueStyle={{ color: info.color }}
                    />
                  </Col>
                );
              })}
            </Row>
          </Card>
        )}
      </Card>
    </div>
  );
};

export default Statistics;
