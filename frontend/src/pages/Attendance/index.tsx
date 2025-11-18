/**
 * 考勤打卡页面
 */
import { useState, useRef, useEffect } from 'react';
import { Card, Button, Space, Alert, message, Spin, Result, Upload } from 'antd';
import { CameraOutlined, CheckCircleOutlined, UploadOutlined } from '@ant-design/icons';
import { useAttendanceStore } from '../../store/attendanceStore';
import { attendanceApi } from '../../api/client';

const Attendance = () => {
  const [loading, setLoading] = useState(false);
  const [capturing, setCapturing] = useState(false);
  const [checkInResult, setCheckInResult] = useState<any>(null);
  const [previewResult, setPreviewResult] = useState<any>(null); // 实时识别结果
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const previewIntervalRef = useRef<number | null>(null); // 预览定时器

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
      // 注意：不在这里调用 startPreview，而是通过 useEffect 监听 capturing 变化
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
    // 停止预览
    if (previewIntervalRef.current) {
      clearInterval(previewIntervalRef.current);
      previewIntervalRef.current = null;
    }
    setCapturing(false);
    setPreviewResult(null);
  };

  // 实时预览识别
  const startPreview = () => {
    console.log('🎥 启动实时预览...');
    
    // 每500ms识别一次
    previewIntervalRef.current = window.setInterval(async () => {
      if (!videoRef.current || !canvasRef.current || !capturing) {
        console.log('⚠️ 预览条件不满足:', { 
          hasVideo: !!videoRef.current, 
          hasCanvas: !!canvasRef.current, 
          capturing 
        });
        return;
      }

      try {
        const canvas = canvasRef.current;
        const video = videoRef.current;
        
        // 检查视频是否准备好
        if (video.videoWidth === 0 || video.videoHeight === 0) {
          console.log('⏳ 等待视频加载...');
          return;
        }
        
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext('2d');
        
        if (ctx) {
          ctx.drawImage(video, 0, 0);
          const imageData = canvas.toDataURL('image/jpeg', 0.6);

          console.log('📤 发送预览请求...');
          // 调用预览API
          const response = await attendanceApi.preview(imageData);
          console.log('📥 预览结果:', response.data);
          setPreviewResult(response.data);
        }
      } catch (error) {
        console.error('❌ 预览识别错误:', error);
      }
    }, 500);
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

  // 文件上传打卡
  const handleFileUpload = async (file: File) => {
    setLoading(true);
    setCheckInResult(null);

    try {
      const reader = new FileReader();
      reader.onload = async (e) => {
        const imageData = e.target?.result as string;
        
        // 调用打卡API
        const result = await checkIn(imageData);

        if (result?.success) {
          message.success(`打卡成功！欢迎 ${result.username}`);
          setCheckInResult(result);
        } else {
          message.error(result?.message || '打卡失败');
          setCheckInResult(result);
        }
        setLoading(false);
      };
      reader.onerror = () => {
        message.error('图片读取失败');
        setLoading(false);
      };
      reader.readAsDataURL(file);
    } catch (error) {
      message.error('打卡失败，请重试');
      console.error('打卡错误:', error);
      setLoading(false);
    }

    return false; // 阻止默认上传行为
  };

  // 重新打卡
  const handleRetry = () => {
    setCheckInResult(null);
    startCamera();
  };

  // 监听 capturing 状态，启动/停止预览
  useEffect(() => {
    if (capturing) {
      console.log('📹 摄像头已启动，1秒后开始预览...');
      // 等待视频流稳定
      const timer = setTimeout(() => {
        startPreview();
      }, 1000);
      
      return () => clearTimeout(timer);
    } else {
      // 停止预览
      if (previewIntervalRef.current) {
        console.log('⏹️ 停止预览');
        clearInterval(previewIntervalRef.current);
        previewIntervalRef.current = null;
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [capturing]);

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
        message="打卡说明（测试模式）"
        description='请确保面部清晰可见，光线充足。可以点击"开启摄像头"使用摄像头打卡，或者点击"上传图片"使用本地图片测试打卡。'
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
                  borderRadius: 8,
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

              {/* 实时识别结果显示 */}
              {capturing && previewResult && (
                <div
                  style={{
                    position: 'absolute',
                    top: 10,
                    left: 10,
                    right: 10,
                    padding: '12px 16px',
                    background: previewResult.recognized 
                      ? 'rgba(82, 196, 26, 0.9)' 
                      : previewResult.detected 
                      ? 'rgba(250, 173, 20, 0.9)' 
                      : 'rgba(255, 77, 79, 0.9)',
                    color: '#fff',
                    borderRadius: 8,
                    fontSize: 16,
                    fontWeight: 'bold',
                    textAlign: 'center',
                    zIndex: 10,
                  }}
                >
                  {previewResult.recognized ? (
                    <>
                      ✓ {previewResult.username} ({previewResult.student_id})
                      <br />
                      <span style={{ fontSize: 14 }}>
                        置信度: {(previewResult.confidence * 100).toFixed(1)}%
                      </span>
                    </>
                  ) : previewResult.detected ? (
                    <>⚠️ {previewResult.message}</>
                  ) : (
                    <>❌ {previewResult.message}</>
                  )}
                </div>
              )}
            </div>

            {/* 操作按钮 */}
            <div style={{ textAlign: 'center' }}>
              <Space size="large">
                {!capturing ? (
                  <>
                    <Button
                      type="primary"
                      size="large"
                      icon={<CameraOutlined />}
                      onClick={startCamera}
                    >
                      开启摄像头
                    </Button>
                    <Upload
                      accept="image/*"
                      showUploadList={false}
                      beforeUpload={handleFileUpload}
                    >
                      <Button
                        size="large"
                        icon={<UploadOutlined />}
                        loading={loading}
                        disabled={loading}
                      >
                        上传图片打卡
                      </Button>
                    </Upload>
                  </>
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
