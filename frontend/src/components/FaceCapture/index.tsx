/**
 * 人脸采集组件
 */
import { useState, useRef, useEffect } from 'react';
import { Modal, Button, Space, Alert, Progress, Image } from 'antd';
import { CameraOutlined, DeleteOutlined, CheckOutlined } from '@ant-design/icons';

interface FaceCaptureProps {
  open: boolean;
  onCancel: () => void;
  onComplete: (images: string[]) => void;
  minImages?: number;
  maxImages?: number;
}

const FaceCapture = ({
  open,
  onCancel,
  onComplete,
  minImages = 3,
  maxImages = 10,
}: FaceCaptureProps) => {
  const [capturing, setCapturing] = useState(false);
  const [capturedImages, setCapturedImages] = useState<string[]>([]);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

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
      console.error('摄像头启动失败:', error);
      alert('无法访问摄像头，请检查权限设置');
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

  // 拍照
  const captureImage = () => {
    if (!videoRef.current || !canvasRef.current) return;

    if (capturedImages.length >= maxImages) {
      alert(`最多只能采集 ${maxImages} 张照片`);
      return;
    }

    const canvas = canvasRef.current;
    const video = videoRef.current;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    
    if (ctx) {
      ctx.drawImage(video, 0, 0);
      const imageData = canvas.toDataURL('image/jpeg', 0.8);
      setCapturedImages([...capturedImages, imageData]);
    }
  };

  // 删除照片
  const deleteImage = (index: number) => {
    setCapturedImages(capturedImages.filter((_, i) => i !== index));
  };

  // 完成采集
  const handleComplete = () => {
    if (capturedImages.length < minImages) {
      alert(`至少需要采集 ${minImages} 张照片`);
      return;
    }
    stopCamera();
    onComplete(capturedImages);
    setCapturedImages([]);
  };

  // 取消
  const handleCancel = () => {
    stopCamera();
    setCapturedImages([]);
    onCancel();
  };

  // 组件卸载时停止摄像头
  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  // 对话框打开时自动启动摄像头
  useEffect(() => {
    if (open && !capturing) {
      startCamera();
    }
  }, [open]);

  const progress = (capturedImages.length / minImages) * 100;

  return (
    <Modal
      title="人脸采集"
      open={open}
      onCancel={handleCancel}
      width={800}
      footer={[
        <Button key="cancel" onClick={handleCancel}>
          取消
        </Button>,
        <Button
          key="complete"
          type="primary"
          icon={<CheckOutlined />}
          onClick={handleComplete}
          disabled={capturedImages.length < minImages}
        >
          完成采集 ({capturedImages.length}/{minImages})
        </Button>,
      ]}
    >
      <Alert
        message="采集说明"
        description={`请从不同角度拍摄您的面部照片，至少需要 ${minImages} 张，最多 ${maxImages} 张。确保面部清晰可见，光线充足。`}
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

      <Progress
        percent={Math.min(progress, 100)}
        status={capturedImages.length >= minImages ? 'success' : 'active'}
        style={{ marginBottom: 16 }}
      />

      <div style={{ display: 'flex', gap: 16 }}>
        {/* 视频预览 */}
        <div style={{ flex: 1 }}>
          <div
            style={{
              width: '100%',
              backgroundColor: '#000',
              borderRadius: 8,
              overflow: 'hidden',
              position: 'relative',
            }}
          >
            <video
              ref={videoRef}
              autoPlay
              playsInline
              style={{ width: '100%', display: 'block' }}
            />
            <canvas ref={canvasRef} style={{ display: 'none' }} />
          </div>
          <div style={{ marginTop: 16, textAlign: 'center' }}>
            <Button
              type="primary"
              size="large"
              icon={<CameraOutlined />}
              onClick={captureImage}
              disabled={!capturing || capturedImages.length >= maxImages}
            >
              拍照 ({capturedImages.length}/{maxImages})
            </Button>
          </div>
        </div>

        {/* 已采集照片 */}
        <div style={{ width: 200, maxHeight: 400, overflowY: 'auto' }}>
          <div style={{ marginBottom: 8, fontWeight: 'bold' }}>
            已采集照片:
          </div>
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            {capturedImages.map((img, index) => (
              <div
                key={index}
                style={{
                  position: 'relative',
                  border: '2px solid #d9d9d9',
                  borderRadius: 4,
                  overflow: 'hidden',
                }}
              >
                <Image
                  src={img}
                  alt={`照片 ${index + 1}`}
                  style={{ width: '100%', display: 'block' }}
                  preview={false}
                />
                <Button
                  type="primary"
                  danger
                  size="small"
                  icon={<DeleteOutlined />}
                  style={{
                    position: 'absolute',
                    top: 4,
                    right: 4,
                  }}
                  onClick={() => deleteImage(index)}
                />
              </div>
            ))}
          </Space>
        </div>
      </div>
    </Modal>
  );
};

export default FaceCapture;
