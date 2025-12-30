/**
 * 统计分析页面
 */
import { useEffect, useState } from 'react';
import { Card, Row, Col, Statistic, DatePicker, Space, Spin, Select, Progress, Divider, Button, message } from 'antd';
import { 
  BarChartOutlined, 
  UserOutlined, 
  CheckCircleOutlined, 
  ClockCircleOutlined,
  CloseCircleOutlined,
  LoginOutlined,
  LogoutOutlined,
  TeamOutlined,
  DownloadOutlined
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

  // 导出统计报表
  const handleExport = () => {
    if (!dailyStats || attendanceList.length === 0) {
      message.warning('没有数据可导出');
      return;
    }

    try {
      const dateStr = selectedDate.format('YYYY年MM月DD日');
      
      // 生成CSV内容
      const lines = [
        `考勤统计报表 - ${dateStr}`,
        '',
        '基本统计',
        `总打卡次数,${dailyStats.total}`,
        `出勤人数,${dailyStats.unique_users}`,
        `出勤率,${dailyStats.attendance_rate}%`,
        `应到人数,${dailyStats.total_users || 0}`,
        '',
        '打卡类型统计',
        `上班打卡,${attendanceList.filter(a => a.check_type === 'checkin' && a.status !== 'absent').length}次`,
        `下班打卡,${attendanceList.filter(a => a.check_type === 'checkout' && a.status !== 'absent').length}次`,
        `上班打卡率,${dailyStats.total_users ? (attendanceList.filter(a => a.check_type === 'checkin' && a.status !== 'absent').length / dailyStats.total_users * 100).toFixed(1) : 0}%`,
        `下班打卡率,${dailyStats.total_users ? (attendanceList.filter(a => a.check_type === 'checkout' && a.status !== 'absent').length / dailyStats.total_users * 100).toFixed(1) : 0}%`,
        '',
        '考勤状态分布',
        `正常打卡,${dailyStats.status_distribution?.present || 0}次`,
        `迟到次数,${dailyStats.status_distribution?.late || 0}次`,
        `缺勤次数,${dailyStats.status_distribution?.absent || 0}次`,
        `早退次数,${attendanceList.filter(a => a.is_early).length}次`,
        '',
        '详细记录',
        'ID,用户名,学号,打卡时间,打卡类型,状态,置信度',
        ...attendanceList.map(record => [
          record.id,
          record.username || '-',
          record.student_id || '-',
          dayjs(record.timestamp).format('YYYY-MM-DD HH:mm:ss'),
          record.check_type === 'checkin' ? '上班' : '下班',
          record.status === 'present' ? '正常' : record.status === 'late' ? '迟到' : '缺勤',
          record.confidence ? `${(record.confidence * 100).toFixed(1)}%` : '-'
        ].join(','))
      ];

      const csvContent = lines.join('\n');

      // 下载文件
      const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `考勤统计报表_${selectedDate.format('YYYYMMDD')}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      message.success('导出成功');
    } catch (error) {
      console.error('导出失败:', error);
      message.error('导出失败');
    }
  };

  const loadStatistics = async () => {
    setLoading(true);
    try {
      const dateStr = selectedDate.format('YYYY-MM-DD');
      
      // 加载统计数据
      const statsResponse = await statisticsApi.getDailyWithDept(dateStr, departmentFilter);
      console.log('后端统计数据:', statsResponse.data);
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
      
      const attendanceResponse = await attendanceApi.getHistory(params);
      setAttendanceList(attendanceResponse.data?.items || []);
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
            <Button
              type="primary"
              icon={<DownloadOutlined />}
              onClick={handleExport}
              disabled={!dailyStats || attendanceList.length === 0}
            >
              导出报表
            </Button>
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
                value={dailyStats?.total_users || 0}
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
                value={attendanceList.filter(a => a.check_type === 'checkin' && a.status !== 'absent').length}
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
                value={attendanceList.filter(a => a.check_type === 'checkout' && a.status !== 'absent').length}
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
                value={dailyStats?.total_users ? 
                  (attendanceList.filter(a => a.check_type === 'checkin' && a.status !== 'absent').length / dailyStats.total_users * 100).toFixed(1) 
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
                value={dailyStats?.total_users ? 
                  (attendanceList.filter(a => a.check_type === 'checkout' && a.status !== 'absent').length / dailyStats.total_users * 100).toFixed(1) 
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
