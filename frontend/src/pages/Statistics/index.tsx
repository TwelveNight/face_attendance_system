/**
 * 统计分析页面
 */
import { useEffect, useState } from 'react';
import { Card, Row, Col, Statistic, DatePicker, Space, Spin, Select, Progress, Divider } from 'antd';
import { 
  BarChartOutlined, 
  UserOutlined, 
  CheckCircleOutlined, 
  ClockCircleOutlined,
  CloseCircleOutlined,
  LoginOutlined,
  LogoutOutlined,
  TeamOutlined
} from '@ant-design/icons';
import { statisticsApi, departmentApi, attendanceApi } from '../../api/client';
import type { Statistics as StatsType, Department, Attendance } from '../../types';
import dayjs, { type Dayjs } from 'dayjs';

const Statistics = () => {
  const [loading, setLoading] = useState(false);
  const [dailyStats, setDailyStats] = useState<StatsType | null>(null);
  const [attendanceList, setAttendanceList] = useState<Attendance[]>([]);
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
      
      // 加载统计数据
      const statsResponse = await statisticsApi.getDailyWithDept(dateStr, departmentFilter);
      setDailyStats(statsResponse.data);
      
      // 加载当天考勤记录
      const params: any = {
        start_date: dateStr,
        end_date: dateStr,
        page: 1,
        per_page: 1000
      };
      if (departmentFilter) {
        params.department_id = departmentFilter;
      }
      
      console.log('🔍 请求参数:', params);
      const attendanceResponse = await attendanceApi.getHistory(params);
      console.log('📦 API完整响应:', attendanceResponse);
      
      const items = attendanceResponse.data?.items || [];
      console.log('📊 考勤记录加载:', {
        日期: dateStr,
        总数: items.length,
        上班打卡: items.filter((a: Attendance) => a.check_type === 'checkin').length,
        下班打卡: items.filter((a: Attendance) => a.check_type === 'checkout').length,
        示例数据: items.slice(0, 2),
        完整数据: items
      });
      setAttendanceList(items);
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
        {/* 基本统计 */}
        <Divider orientation="left">📊 基本统计 - {selectedDate.format('YYYY年MM月DD日')}</Divider>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} lg={6}>
            <Card hoverable>
              <Statistic
                title="总打卡次数"
                value={dailyStats?.total || 0}
                prefix={<BarChartOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>

          <Col xs={24} sm={12} lg={6}>
            <Card hoverable>
              <Statistic
                title="出勤人数"
                value={dailyStats?.unique_users || 0}
                prefix={<TeamOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>

          <Col xs={24} sm={12} lg={6}>
            <Card hoverable>
              <Statistic
                title="出勤率"
                value={dailyStats?.attendance_rate || 0}
                precision={1}
                suffix="%"
                prefix={<UserOutlined />}
                valueStyle={{ color: '#722ed1' }}
              />
              <Progress 
                percent={dailyStats?.attendance_rate || 0} 
                strokeColor={{
                  '0%': '#108ee9',
                  '100%': '#87d068',
                }}
                showInfo={false}
                style={{ marginTop: 8 }}
              />
            </Card>
          </Col>

          <Col xs={24} sm={12} lg={6}>
            <Card hoverable>
              <Statistic
                title="应到人数"
                value={Math.ceil((dailyStats?.unique_users || 0) / ((dailyStats?.attendance_rate || 100) / 100))}
                prefix={<TeamOutlined />}
                valueStyle={{ color: '#13c2c2' }}
              />
            </Card>
          </Col>
        </Row>

        {/* 打卡类型统计 */}
        <Divider orientation="left">🕒 打卡类型统计</Divider>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} lg={6}>
            <Card hoverable>
              <Statistic
                title="上班打卡"
                value={attendanceList.filter(a => a.check_type === 'checkin').length}
                prefix={<LoginOutlined />}
                valueStyle={{ color: '#1890ff' }}
                suffix="次"
              />
            </Card>
          </Col>

          <Col xs={24} sm={12} lg={6}>
            <Card hoverable>
              <Statistic
                title="下班打卡"
                value={attendanceList.filter(a => a.check_type === 'checkout').length}
                prefix={<LogoutOutlined />}
                valueStyle={{ color: '#722ed1' }}
                suffix="次"
              />
            </Card>
          </Col>

          <Col xs={24} sm={12} lg={6}>
            <Card hoverable>
              <Statistic
                title="上班打卡率"
                value={dailyStats?.unique_users ? 
                  (attendanceList.filter(a => a.check_type === 'checkin').length / dailyStats.unique_users * 100).toFixed(1) 
                  : 0}
                suffix="%"
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>

          <Col xs={24} sm={12} lg={6}>
            <Card hoverable>
              <Statistic
                title="下班打卡率"
                value={dailyStats?.unique_users ? 
                  (attendanceList.filter(a => a.check_type === 'checkout').length / dailyStats.unique_users * 100).toFixed(1) 
                  : 0}
                suffix="%"
                valueStyle={{ color: '#13c2c2' }}
              />
            </Card>
          </Col>
        </Row>

        {/* 考勤状态分布 */}
        <Divider orientation="left">📋 考勤状态分布</Divider>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} lg={6}>
            <Card hoverable>
              <Statistic
                title="正常打卡"
                value={dailyStats?.status_distribution?.present || 0}
                prefix={<CheckCircleOutlined />}
                valueStyle={{ color: '#52c41a' }}
                suffix="次"
              />
              <Progress 
                percent={dailyStats?.total ? (dailyStats.status_distribution?.present || 0) / dailyStats.total * 100 : 0}
                strokeColor="#52c41a"
                showInfo={false}
                style={{ marginTop: 8 }}
              />
            </Card>
          </Col>

          <Col xs={24} sm={12} lg={6}>
            <Card hoverable>
              <Statistic
                title="迟到次数"
                value={dailyStats?.status_distribution?.late || 0}
                prefix={<ClockCircleOutlined />}
                valueStyle={{ color: '#faad14' }}
                suffix="次"
              />
              <Progress 
                percent={dailyStats?.total ? (dailyStats.status_distribution?.late || 0) / dailyStats.total * 100 : 0}
                strokeColor="#faad14"
                showInfo={false}
                style={{ marginTop: 8 }}
              />
            </Card>
          </Col>

          <Col xs={24} sm={12} lg={6}>
            <Card hoverable>
              <Statistic
                title="缺勤次数"
                value={dailyStats?.status_distribution?.absent || 0}
                prefix={<CloseCircleOutlined />}
                valueStyle={{ color: '#ff4d4f' }}
                suffix="次"
              />
              <Progress 
                percent={dailyStats?.total ? (dailyStats.status_distribution?.absent || 0) / dailyStats.total * 100 : 0}
                strokeColor="#ff4d4f"
                showInfo={false}
                style={{ marginTop: 8 }}
              />
            </Card>
          </Col>

          <Col xs={24} sm={12} lg={6}>
            <Card hoverable>
              <Statistic
                title="早退次数"
                value={attendanceList.filter(a => a.is_early).length}
                prefix={<ClockCircleOutlined />}
                valueStyle={{ color: '#fa8c16' }}
                suffix="次"
              />
            </Card>
          </Col>
        </Row>
      </Card>
    </div>
  );
};

export default Statistics;
