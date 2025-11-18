/**
 * 仪表盘页面
 */
import { useEffect, useState } from 'react';
import { Row, Col, Card, Statistic, Alert, Spin, Space, Tag } from 'antd';
import {
  UserOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  RiseOutlined,
} from '@ant-design/icons';
import { systemApi, statisticsApi, userApi } from '../../api/client';
import type { Statistics, SystemStatus } from '../../types';

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [todayStats, setTodayStats] = useState<Statistics | null>(null);
  const [userCount, setUserCount] = useState(0);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      // 并行加载数据
      const [statusRes, statsRes, userStatsRes] = await Promise.all([
        systemApi.healthCheck(),
        statisticsApi.getDaily(),
        userApi.getUserStatistics(),
      ]);

      setSystemStatus(statusRes.data);
      setTodayStats(statsRes.data);
      setUserCount(userStatsRes.data.active || 0);
    } catch (error) {
      console.error('加载数据失败:', error);
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
      <h1>仪表盘</h1>

      {/* 系统状态提示 */}
      {systemStatus && (
        <Alert
          message={
            <Space>
              <span>系统状态:</span>
              <Tag color={systemStatus.models_loaded ? 'success' : 'error'}>
                {systemStatus.models_loaded ? '模型已加载' : '模型未加载'}
              </Tag>
              {systemStatus.gpu_available && (
                <Tag color="processing">GPU 加速已启用</Tag>
              )}
            </Space>
          }
          type={systemStatus.models_loaded ? 'success' : 'warning'}
          showIcon
          style={{ marginBottom: 24 }}
        />
      )}

      {/* 统计卡片 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="注册用户"
              value={userCount}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="今日打卡"
              value={todayStats?.total || 0}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="今日出勤人数"
              value={todayStats?.unique_users || 0}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="出勤率"
              value={todayStats?.attendance_rate || 0}
              precision={1}
              suffix="%"
              prefix={<RiseOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* GPU 信息 */}
      {systemStatus?.gpu_memory && (
        <Card title="GPU 内存使用" style={{ marginTop: 24 }}>
          <Row gutter={16}>
            <Col span={6}>
              <Statistic
                title="已分配"
                value={systemStatus.gpu_memory.allocated_mb}
                suffix="MB"
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="已保留"
                value={systemStatus.gpu_memory.reserved_mb}
                suffix="MB"
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="总内存"
                value={systemStatus.gpu_memory.total_mb}
                suffix="MB"
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="可用"
                value={systemStatus.gpu_memory.free_mb}
                suffix="MB"
                valueStyle={{ color: '#3f8600' }}
              />
            </Col>
          </Row>
        </Card>
      )}

      {/* 今日考勤状态分布 */}
      {todayStats?.status_distribution && (
        <Card title="今日考勤状态" style={{ marginTop: 24 }}>
          <Space size="large">
            {Object.entries(todayStats.status_distribution).map(([status, count]) => (
              <Statistic
                key={status}
                title={
                  status === 'present'
                    ? '正常'
                    : status === 'late'
                    ? '迟到'
                    : '缺勤'
                }
                value={count}
              />
            ))}
          </Space>
        </Card>
      )}
    </div>
  );
};

export default Dashboard;
