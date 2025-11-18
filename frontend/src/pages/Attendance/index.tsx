/**
 * 考勤打卡页面
 */
import { useState, useRef, useEffect } from 'react';
import { Card, Button, Space, Alert, message, Spin, Result } from 'antd';
import { CameraOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { useAttendanceStore } from '../../store/attendanceStore';

const Attendance = () => {
  const [loading, setLoading] = useState(false);
  const [capturing, setCapturing] = useState(false);
  const [checkInResult, setCheckInResult] = useState<any>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const { checkIn } = useAttendanceStore();

  // 启动摄像头
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480 },
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        streamRef.current = stream;
      }
      setCapturing(true);
    } catch (error) {
      message.error('无法访问摄像头，请检查权限设置');
      console.error('摄像头错误:', error);
    }
  };

  // 停止摄像头
  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    setCapturing(false);
  };

  // 拍照并打卡
  const handleCheckIn = async () => {
    if (!videoRef.current || !canvasRef.current) {
      message.error('摄像头未就绪');
      return;
    }

    setLoading(true);
    setCheckInResult(null);

    try {
      // 从视频流捕获图像
      const canvas = canvasRef.current;
      const video = videoRef.current;
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.drawImage(video, 0, 0);
        // 转换为base64
        const imageData = canvas.toDataURL('image/jpeg', 0.8);

        // 调用打卡API
        const result = await checkIn(imageData);

        if (result?.success) {
          message.success(`打卡成功！欢迎 ${result.username}`);
          setCheckInResult(result);
          // 停止摄像头
          stopCamera();
        } else {
          message.error(result?.message || '打卡失败');
          setCheckInResult(result);
        }
      }
    } catch (error) {
      message.error('打卡失败，请重试');
      console.error('打卡错误:', error);
    } finally {
      setLoading(false);
    }
  };

  // 重新打卡
  const handleRetry = () => {
    setCheckInResult(null);
    startCamera();
  };

  // 组件卸载时停止摄像头
  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  return (
    <div>
      <h1>考勤打卡</h1>

      <Alert
        message="打卡说明"
        description='请确保面部清晰可见，光线充足。点击"开启摄像头"后，对准摄像头，然后点击"立即打卡"按钮。'
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      <Card>
        {!checkInResult ? (
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            {/* 视频预览区域 */}
            <div
              style={{
                width: '100%',
                maxWidth: 640,
                margin: '0 auto',
                position: 'relative',
                backgroundColor: '#000',
                borderRadius: 8,
                overflow: 'hidden',
              }}
            >
              <video
                ref={videoRef}
                autoPlay
                playsInline
                style={{
                  width: '100%',
                  display: capturing ? 'block' : 'none',
                }}
              />
              <canvas ref={canvasRef} style={{ display: 'none' }} />

              {!capturing && (
                <div
                  style={{
                    minHeight: 480,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#fff',
                  }}
                >
                  <CameraOutlined style={{ fontSize: 64, opacity: 0.3 }} />
                </div>
              )}
            </div>

            {/* 操作按钮 */}
            <div style={{ textAlign: 'center' }}>
              <Space size="large">
                {!capturing ? (
                  <Button
                    type="primary"
                    size="large"
                    icon={<CameraOutlined />}
                    onClick={startCamera}
                  >
                    开启摄像头
                  </Button>
                ) : (
                  <>
                    <Button
                      type="primary"
                      size="large"
                      icon={<CheckCircleOutlined />}
                      onClick={handleCheckIn}
                      loading={loading}
                      disabled={loading}
                    >
                      立即打卡
                    </Button>
                    <Button size="large" onClick={stopCamera} disabled={loading}>
                      关闭摄像头
                    </Button>
                  </>
                )}
              </Space>
            </div>
          </Space>
        ) : (
          // 打卡结果显示
          <Result
            status={checkInResult.success ? 'success' : 'error'}
            title={checkInResult.success ? '打卡成功！' : '打卡失败'}
            subTitle={
              checkInResult.success ? (
                <div>
                  <p>用户：{checkInResult.username}</p>
                  <p>学号：{checkInResult.student_id}</p>
                  <p>识别置信度：{(checkInResult.confidence * 100).toFixed(1)}%</p>
                  <p>时间：{new Date(checkInResult.timestamp).toLocaleString('zh-CN')}</p>
                </div>
              ) : (
                <p>{checkInResult.message}</p>
              )
            }
            extra={[
              <Button type="primary" key="retry" onClick={handleRetry}>
                重新打卡
              </Button>,
            ]}
          />
        )}
      </Card>

      {loading && (
        <div style={{ textAlign: 'center', marginTop: 24 }}>
          <Spin size="large" tip="正在识别人脸，请稍候..." />
        </div>
      )}
    </div>
  );
};

export default Attendance;
