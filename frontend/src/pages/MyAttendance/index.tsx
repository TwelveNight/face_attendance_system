/**
 * 我的考勤页面
 * 显示当前登录用户的考勤记录
 */
import { useEffect, useState } from 'react';
import { Table, Card, DatePicker, Space, Tag, Statistic, Row, Col, message } from 'antd';
import { ClockCircleOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import { attendanceApi } from '../../api/client';
import { useAuthStore } from '../../store/authStore';
import type { Attendance } from '../../types';
import dayjs, { Dayjs } from 'dayjs';
import './style.css';

const { RangePicker } = DatePicker;

export default function MyAttendance() {
  const [loading, setLoading] = useState(false);
  const [attendanceList, setAttendanceList] = useState<Attendance[]>([]);
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs]>([
    dayjs().startOf('month'),
    dayjs().endOf('month')
  ]);
  const { currentUser } = useAuthStore();

  useEffect(() => {
    loadAttendance();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dateRange]);

  const loadAttendance = async () => {
    if (!currentUser) {
      message.error('请先登录');
      return;
    }

    setLoading(true);
    try {
      const response = await attendanceApi.getHistory({
        start_date: dateRange[0].format('YYYY-MM-DD'),
        end_date: dateRange[1].format('YYYY-MM-DD'),
        user_id: currentUser.id
      });
      setAttendanceList(response.data?.items || []);
    } catch (error: any) {
      message.error(error.message || '获取考勤记录失败');
    } finally {
      setLoading(false);
    }
  };

  // 计算统计数据
  const statistics = {
    total: attendanceList.length,
    present: attendanceList.filter(a => a.status === 'present').length,
    late: attendanceList.filter(a => a.status === 'late').length,
    absent: attendanceList.filter(a => a.status === 'absent').length,
  };

  const attendanceRate = statistics.total > 0 
    ? ((statistics.present + statistics.late) / statistics.total * 100).toFixed(1)
    : '0.0';

  // 表格列定义
  const columns = [
    {
      title: '日期',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (text: string) => dayjs(text).format('YYYY-MM-DD'),
    },
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'time',
      render: (text: string) => dayjs(text).format('HH:mm:ss'),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusMap: Record<string, { color: string; text: string; icon: any }> = {
          present: { color: 'success', text: '正常', icon: <CheckCircleOutlined /> },
          late: { color: 'warning', text: '迟到', icon: <ClockCircleOutlined /> },
          absent: { color: 'error', text: '缺勤', icon: <CloseCircleOutlined /> },
        };
        const config = statusMap[status] || statusMap.present;
        return (
          <Tag color={config.color} icon={config.icon}>
            {config.text}
          </Tag>
        );
      },
    },
    {
      title: '置信度',
      dataIndex: 'confidence',
      key: 'confidence',
      render: (confidence: number) => confidence ? `${(confidence * 100).toFixed(1)}%` : '-',
    },
    {
      title: '备注',
      dataIndex: 'notes',
      key: 'notes',
      render: (text: string) => text || '-',
    },
  ];

  return (
    <div className="my-attendance-container">
      <Card
        title={
          <Space>
            <ClockCircleOutlined />
            <span>我的考勤记录</span>
          </Space>
        }
        extra={
          <RangePicker
            value={dateRange}
            onChange={(dates) => {
              if (dates && dates[0] && dates[1]) {
                setDateRange([dates[0], dates[1]]);
              }
            }}
            format="YYYY-MM-DD"
          />
        }
      >
        {/* 统计卡片 */}
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="总打卡次数"
                value={statistics.total}
                suffix="次"
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="正常打卡"
                value={statistics.present}
                suffix="次"
                valueStyle={{ color: '#52c41a' }}
                prefix={<CheckCircleOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="迟到次数"
                value={statistics.late}
                suffix="次"
                valueStyle={{ color: '#faad14' }}
                prefix={<ClockCircleOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="出勤率"
                value={attendanceRate}
                suffix="%"
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
        </Row>

        {/* 考勤记录表格 */}
        <Table
          columns={columns}
          dataSource={attendanceList}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条记录`,
          }}
        />
      </Card>
    </div>
  );
}
