/**
 * 我的考勤页面
 * 显示当前登录用户的考勤记录
 */
import { useEffect, useState } from 'react';
import { Table, Card, DatePicker, Space, Tag, Statistic, Row, Col, message, Button } from 'antd';
import { ClockCircleOutlined, CheckCircleOutlined, CloseCircleOutlined, DownloadOutlined } from '@ant-design/icons';
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
    checkin: attendanceList.filter(a => a.check_type === 'checkin').length,
    checkout: attendanceList.filter(a => a.check_type === 'checkout').length,
  };

  const attendanceRate = statistics.total > 0 
    ? ((statistics.present + statistics.late) / statistics.total * 100).toFixed(1)
    : '0.0';

  // 导出Excel
  const handleExport = () => {
    if (attendanceList.length === 0) {
      message.warning('没有数据可导出');
      return;
    }

    // 生成CSV内容
    const headers = ['日期', '时间', '打卡类型', '状态', '置信度', '备注'];
    const rows = attendanceList.map(record => [
      dayjs(record.timestamp).format('YYYY-MM-DD'),
      dayjs(record.timestamp).format('HH:mm:ss'),
      record.check_type === 'checkin' ? '上班' : '下班',
      record.status === 'present' ? '正常' : record.status === 'late' ? '迟到' : '缺勤',
      record.confidence ? `${(record.confidence * 100).toFixed(1)}%` : '-',
      record.notes || '-'
    ]);

    // 添加统计信息
    const statsRows = [
      [],
      ['统计信息'],
      ['总打卡次数', statistics.total],
      ['正常打卡', statistics.present],
      ['迟到次数', statistics.late],
      ['缺勤次数', statistics.absent],
      ['上班打卡', statistics.checkin],
      ['下班打卡', statistics.checkout],
      ['出勤率', `${attendanceRate}%`]
    ];

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.join(',')),
      ...statsRows.map(row => row.join(','))
    ].join('\n');

    // 下载文件
    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `我的考勤_${dateRange[0].format('YYYYMMDD')}_${dateRange[1].format('YYYYMMDD')}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    message.success('导出成功');
  };

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
      title: '打卡类型',
      dataIndex: 'check_type',
      key: 'check_type',
      render: (type: string) => {
        const typeMap: Record<string, { color: string; text: string }> = {
          checkin: { color: 'blue', text: '上班' },
          checkout: { color: 'purple', text: '下班' },
        };
        const config = typeMap[type] || { color: 'default', text: '未知' };
        return <Tag color={config.color}>{config.text}</Tag>;
      },
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
          <Space>
            <RangePicker
              value={dateRange}
              onChange={(dates) => {
                if (dates && dates[0] && dates[1]) {
                  setDateRange([dates[0], dates[1]]);
                }
              }}
              format="YYYY-MM-DD"
            />
            <Button 
              type="primary" 
              icon={<DownloadOutlined />}
              onClick={handleExport}
              disabled={attendanceList.length === 0}
            >
              导出报表
            </Button>
          </Space>
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
                title="缺勤次数"
                value={statistics.absent}
                suffix="次"
                valueStyle={{ color: '#ff4d4f' }}
                prefix={<CloseCircleOutlined />}
              />
            </Card>
          </Col>
        </Row>

        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="上班打卡"
                value={statistics.checkin}
                suffix="次"
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="下班打卡"
                value={statistics.checkout}
                suffix="次"
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="出勤率"
                value={attendanceRate}
                suffix="%"
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="本月工作日"
                value={Math.floor(statistics.total / 2)}
                suffix="天"
                valueStyle={{ color: '#13c2c2' }}
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
