/**
 * 考勤打卡页面
 */
import { useState, useRef, useEffect } from 'react';
import { Card, Button, Space, Alert, message, Spin, Result, Upload, Tag } from 'antd';
import { CameraOutlined, CheckCircleOutlined, UploadOutlined, ClockCircleOutlined } from '@ant-design/icons';
import { useAttendanceStore } from '../../store/attendanceStore';
import { attendanceApi, attendanceRuleApi } from '../../api/client';
import { useAuthStore } from '../../store/authStore';

const Attendance = () => {
  const [loading, setLoading] = useState(false);
  const [capturing, setCapturing] = useState(false);
  const [checkInResult, setCheckInResult] = useState<any>(null);
  const [previewResult, setPreviewResult] = useState<any>(null); // 实时识别结果
  const [currentRule, setCurrentRule] = useState<any>(null); // 当前生效的规则
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const previewIntervalRef = useRef<number | null>(null); // 预览定时器

  const { checkIn } = useAttendanceStore();
  const { currentUser } = useAuthStore();

  // 加载当前用户的考勤规则
  useEffect(() => {
    const loadCurrentRule = async () => {
      if (currentUser?.id) {
        try {
          const response = await attendanceRuleApi.getByUser(currentUser.id);
          setCurrentRule(response.data);
        } catch (error) {
          console.error('获取考勤规则失败:', error);
        }
      }
    };
    loadCurrentRule();
  }, [currentUser]);

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
          // 根据状态显示不同的消息
          if (result.is_late) {
            message.warning(`${result.message} - ${result.username}`);
          } else {
            message.success(`${result.message} - ${result.username}`);
          }
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
        style={{ marginBottom: 16 }}
      />

      {/* 当前规则提示 */}
      {currentRule && (
        <Alert
          message={
            <Space>
              <ClockCircleOutlined />
              <span>当前考勤规则：{currentRule.name}</span>
              {currentRule.is_open_mode && <Tag color="green">开放模式</Tag>}
            </Space>
          }
          description={
            <div>
              <p>
                <strong>规定时间：</strong>
                {currentRule.work_start_time?.substring(0, 5)} - {currentRule.work_end_time?.substring(0, 5)}
              </p>
              {!currentRule.is_open_mode && (
                <p>
                  <strong>容忍时间：</strong>
                  迟到 {currentRule.late_threshold} 分钟 / 早退 {currentRule.early_threshold} 分钟
                </p>
              )}
              {currentRule.is_open_mode && (
                <p style={{ color: '#52c41a' }}>
                  <strong>提示：</strong>开放打卡模式，任何时间打卡都算正常
                </p>
              )}
            </div>
          }
          type="success"
          showIcon
          style={{ marginBottom: 24 }}
        />
      )}

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
              {capturing && previewResult && (() => {
                // 计算是否太早打卡
                let isTooEarly = false;
                let earliestTime = '';
                if (previewResult.recognized && previewResult.rule && 
                    previewResult.rule.checkin_before_minutes > 0 &&
                    previewResult.status_preview?.check_type === 'checkin' &&
                    !previewResult.rule.is_open_mode) {
                  const [h, m] = previewResult.rule.work_start_time.split(':');
                  const totalMinutes = parseInt(h) * 60 + parseInt(m) - previewResult.rule.checkin_before_minutes;
                  const earliestH = Math.floor(totalMinutes / 60);
                  const earliestM = totalMinutes % 60;
                  earliestTime = `${earliestH.toString().padStart(2, '0')}:${earliestM.toString().padStart(2, '0')}`;
                  
                  // 获取当前时间
                  const now = new Date();
                  const currentMinutes = now.getHours() * 60 + now.getMinutes();
                  isTooEarly = currentMinutes < totalMinutes;
                }
                
                // 计算背景颜色
                let bgColor = 'rgba(255, 77, 79, 0.9)'; // 默认红色（未检测到）
                if (previewResult.recognized) {
                  if (isTooEarly) {
                    bgColor = 'rgba(250, 173, 20, 0.95)'; // 黄色（太早打卡）
                  } else if (previewResult.status_preview?.is_late || previewResult.status_preview?.is_early) {
                    bgColor = 'rgba(250, 173, 20, 0.95)'; // 黄色（迟到/早退）
                  } else {
                    bgColor = 'rgba(82, 196, 26, 0.95)'; // 绿色（正常）
                  }
                } else if (previewResult.detected) {
                  bgColor = 'rgba(250, 173, 20, 0.9)'; // 黄色（检测到但未识别）
                }
                
                return (
                <div
                  style={{
                    position: 'absolute',
                    top: 10,
                    left: 10,
                    right: 10,
                    padding: '12px 16px',
                    background: bgColor,
                    color: '#fff',
                    borderRadius: 8,
                    fontSize: 14,
                    textAlign: 'left',
                    zIndex: 10,
                  }}
                >
                  {previewResult.recognized ? (
                    <>
                      <div style={{ fontSize: 16, fontWeight: 'bold', marginBottom: 8 }}>
                        ✓ {previewResult.username} ({previewResult.student_id})
                      </div>
                      <div style={{ fontSize: 13, opacity: 0.95 }}>
                        置信度: {(previewResult.confidence * 100).toFixed(1)}%
                      </div>
                      {previewResult.rule && (
                        <>
                          <div style={{ marginTop: 8, paddingTop: 8, borderTop: '1px solid rgba(255,255,255,0.3)' }}>
                            <div style={{ fontSize: 13, marginBottom: 4 }}>
                              规则: {previewResult.rule.name}
                            </div>
                            {!previewResult.rule.is_open_mode && (
                              <div style={{ fontSize: 13 }}>
                                时间: {previewResult.rule.work_start_time.substring(0, 5)} - {previewResult.rule.work_end_time.substring(0, 5)}
                              </div>
                            )}
                            {previewResult.rule.checkin_before_minutes > 0 && (
                              <div style={{ fontSize: 12, opacity: 0.9, marginTop: 4 }}>
                                最早打卡: {(() => {
                                  const [h, m] = previewResult.rule.work_start_time.split(':');
                                  const totalMinutes = parseInt(h) * 60 + parseInt(m) - previewResult.rule.checkin_before_minutes;
                                  const earliestH = Math.floor(totalMinutes / 60);
                                  const earliestM = totalMinutes % 60;
                                  return `${earliestH.toString().padStart(2, '0')}:${earliestM.toString().padStart(2, '0')}`;
                                })()}
                              </div>
                            )}
                          </div>
                          {previewResult.status_preview && (
                            <div style={{ 
                              marginTop: 8, 
                              paddingTop: 8, 
                              borderTop: '1px solid rgba(255,255,255,0.3)',
                              fontSize: 15,
                              fontWeight: 'bold'
                            }}>
                              {previewResult.status_preview.check_type_name && (
                                <div style={{ fontSize: 13, marginBottom: 4, opacity: 0.9 }}>
                                  打卡类型: {previewResult.status_preview.check_type_name}打卡
                                </div>
                              )}
                              {isTooEarly ? (
                                <>⚠️ 现在还不能打卡，最早 {earliestTime} 可以打卡</>
                              ) : previewResult.status_preview.is_late ? (
                                <>⚠️ 预计状态: 迟到 {previewResult.status_preview.minutes} 分钟</>
                              ) : previewResult.status_preview.is_early ? (
                                <>⚠️ 预计状态: 早退 {previewResult.status_preview.minutes} 分钟</>
                              ) : (
                                <>✓ 预计状态: 正常打卡</>
                              )}
                            </div>
                          )}
                        </>
                      )}
                    </>
                  ) : previewResult.detected ? (
                    <div style={{ textAlign: 'center', fontWeight: 'bold' }}>
                      ⚠️ {previewResult.message}
                    </div>
                  ) : (
                    <div style={{ textAlign: 'center', fontWeight: 'bold' }}>
                      ❌ {previewResult.message}
                    </div>
                  )}
                </div>
                );})()}
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
            status={checkInResult.success ? (checkInResult.is_late || checkInResult.is_early ? 'warning' : 'success') : 'error'}
            title={
              checkInResult.success ? (
                checkInResult.is_late ? '打卡成功（迟到）' : 
                checkInResult.is_early ? '打卡成功（早退）' : 
                '打卡成功！'
              ) : '打卡失败'
            }
            subTitle={
              checkInResult.success ? (
                <div style={{ textAlign: 'left', display: 'inline-block', width: '100%', maxWidth: 500 }}>
                  <div style={{ 
                    background: checkInResult.is_late || checkInResult.is_early ? '#fff7e6' : '#f6ffed',
                    border: `1px solid ${checkInResult.is_late || checkInResult.is_early ? '#ffd591' : '#b7eb8f'}`,
                    borderRadius: 8,
                    padding: 16,
                    marginBottom: 16
                  }}>
                    <div style={{ 
                      fontSize: 18, 
                      fontWeight: 'bold', 
                      color: checkInResult.is_late || checkInResult.is_early ? '#fa8c16' : '#52c41a',
                      marginBottom: 8
                    }}>
                      {checkInResult.is_late ? '⚠️ 迟到' : 
                       checkInResult.is_early ? '⚠️ 早退' : 
                       '✓ 正常打卡'}
                    </div>
                    <div style={{ fontSize: 15, color: '#666' }}>
                      {checkInResult.message}
                    </div>
                  </div>

                  <div style={{ marginBottom: 16 }}>
                    <p><strong>用户：</strong>{checkInResult.username}</p>
                    <p><strong>学号：</strong>{checkInResult.student_id}</p>
                    <p><strong>识别置信度：</strong>{(checkInResult.confidence! * 100).toFixed(1)}%</p>
                    <p><strong>打卡时间：</strong>{new Date().toLocaleString('zh-CN')}</p>
                  </div>
                  
                  {checkInResult.rule && (
                    <div style={{ 
                      background: '#fafafa',
                      border: '1px solid #d9d9d9',
                      borderRadius: 8,
                      padding: 16,
                      marginTop: 16
                    }}>
                      <div style={{ fontSize: 15, fontWeight: 'bold', marginBottom: 12, color: '#1890ff' }}>
                        📋 应用的考勤规则
                      </div>
                      <p style={{ marginBottom: 8 }}>
                        <strong>规则名称：</strong>
                        <span style={{ color: '#1890ff' }}>{checkInResult.rule.name}</span>
                      </p>
                      {!checkInResult.rule.is_open_mode ? (
                        <p style={{ marginBottom: 0 }}>
                          <strong>规定时间：</strong>
                          {checkInResult.rule.work_start_time.substring(0, 5)} - {checkInResult.rule.work_end_time.substring(0, 5)}
                        </p>
                      ) : (
                        <p style={{ marginBottom: 0 }}>
                          <strong>模式：</strong>
                          <Tag color="green">开放打卡</Tag>
                          <span style={{ color: '#52c41a' }}>任何时间都算正常</span>
                        </p>
                      )}
                    </div>
                  )}
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
