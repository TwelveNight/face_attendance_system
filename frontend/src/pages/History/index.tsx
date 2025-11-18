/**
 * 考勤历史页面
 */
import { useEffect, useState } from 'react';
import { Table, Card, Space, DatePicker, Select, Button, Tag } from 'antd';
import { ClockCircleOutlined, DownloadOutlined, ReloadOutlined } from '@ant-design/icons';
import { attendanceApi } from '../../api/client';
import type { Attendance } from '../../types';
import dayjs, { type Dayjs } from 'dayjs';

const { RangePicker } = DatePicker;

const History = () => {
  const [loading, setLoading] = useState(false);
  const [records, setRecords] = useState<Attendance[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs] | null>(null);
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined);

  useEffect(() => {
    loadRecords();
  }, [page, pageSize]);

  const loadRecords = async () => {
    setLoading(true);
    try {
      const params: any = {
        page,
        per_page: pageSize,
      };

      if (dateRange) {
        params.start_date = dateRange[0].format('YYYY-MM-DD');
        params.end_date = dateRange[1].format('YYYY-MM-DD');
      }

      if (statusFilter) {
        params.status = statusFilter;
      }

      const response = await attendanceApi.getHistory(params);
      setRecords(response.data.items);
      setTotal(response.data.total);
    } catch (error) {
      console.error('加载记录失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 筛选
  const handleFilter = () => {
    setPage(1);
    loadRecords();
  };

  // 重置
  const handleReset = () => {
    setDateRange(null);
    setStatusFilter(undefined);
    setPage(1);
    loadRecords();
  };

  // 导出CSV
  const handleExport = async () => {
    if (!dateRange) {
      return;
    }
    try {
      const blob = await attendanceApi.exportCSV(
        dateRange[0].format('YYYY-MM-DD'),
        dateRange[1].format('YYYY-MM-DD')
      );
      // 创建下载链接
      const url = window.URL.createObjectURL(blob as any);
      const a = document.createElement('a');
      a.href = url;
      a.download = `attendance_${dateRange[0].format('YYYYMMDD')}_${dateRange[1].format('YYYYMMDD')}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('导出失败:', error);
    }
  };

  // 表格列定义
  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
    },
    {
      title: '学号',
      dataIndex: 'student_id',
      key: 'student_id',
      render: (text: string) => text || '-',
    },
    {
      title: '打卡时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (text: string) => dayjs(text).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const colorMap: Record<string, string> = {
          present: 'success',
          late: 'warning',
          absent: 'error',
        };
        const textMap: Record<string, string> = {
          present: '正常',
          late: '迟到',
          absent: '缺勤',
        };
        return <Tag color={colorMap[status]}>{textMap[status] || status}</Tag>;
      },
    },
    {
      title: '置信度',
      dataIndex: 'confidence',
      key: 'confidence',
      render: (confidence: number) =>
        confidence ? `${(confidence * 100).toFixed(1)}%` : '-',
    },
  ];

  return (
    <div>
      <Card
        title={
          <Space>
            <ClockCircleOutlined />
            <span>考勤历史</span>
          </Space>
        }
      >
        {/* 筛选条件 */}
        <Space style={{ marginBottom: 16 }} wrap>
          <RangePicker
            value={dateRange}
            onChange={(dates) => setDateRange(dates as [Dayjs, Dayjs])}
            placeholder={['开始日期', '结束日期']}
          />
          <Select
            style={{ width: 120 }}
            placeholder="状态筛选"
            allowClear
            value={statusFilter}
            onChange={setStatusFilter}
            options={[
              { label: '正常', value: 'present' },
              { label: '迟到', value: 'late' },
              { label: '缺勤', value: 'absent' },
            ]}
          />
          <Button type="primary" onClick={handleFilter}>
            查询
          </Button>
          <Button icon={<ReloadOutlined />} onClick={handleReset}>
            重置
          </Button>
          <Button
            icon={<DownloadOutlined />}
            onClick={handleExport}
            disabled={!dateRange}
          >
            导出CSV
          </Button>
        </Space>

        {/* 数据表格 */}
        <Table
          columns={columns}
          dataSource={records}
          rowKey="id"
          loading={loading}
          pagination={{
            current: page,
            pageSize,
            total,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条记录`,
            onChange: (page, pageSize) => {
              setPage(page);
              setPageSize(pageSize);
            },
          }}
        />
      </Card>
    </div>
  );
};

export default History;
