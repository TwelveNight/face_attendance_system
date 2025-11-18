/**
 * 统计分析页面
 */
import { useEffect, useState } from 'react';
import { Card, Row, Col, Statistic, DatePicker, Space, Spin } from 'antd';
import { BarChartOutlined } from '@ant-design/icons';
import { statisticsApi } from '../../api/client';
import type { Statistics as StatsType } from '../../types';
import dayjs, { type Dayjs } from 'dayjs';

const Statistics = () => {
  const [loading, setLoading] = useState(false);
  const [dailyStats, setDailyStats] = useState<StatsType | null>(null);
  const [selectedDate, setSelectedDate] = useState<Dayjs>(dayjs());

  useEffect(() => {
    loadStatistics();
  }, [selectedDate]);

  const loadStatistics = async () => {
    setLoading(true);
    try {
      const response = await statisticsApi.getDaily(selectedDate.format('YYYY-MM-DD'));
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
          <DatePicker
            value={selectedDate}
            onChange={(date) => date && setSelectedDate(date)}
            placeholder="选择日期"
          />
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
                title="总用户数"
                value={dailyStats?.total_users || 0}
                valueStyle={{ color: '#722ed1' }}
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
