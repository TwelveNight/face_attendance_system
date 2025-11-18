"""
Sklearn SVM情感识别训练脚本
基于MediaPipe面部特征
"""
import sys
from pathlib import Path

# 添加backend目录到路径
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

import numpy as np
import pickle
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import logging

from config import config
from train.train_emotion_sklearn.data import (
    load_data_from_folders,
    load_extracted_features
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SklearnEmotionTrainer:
    """Sklearn情感识别训练器"""
    
    def __init__(self):
        """初始化训练器"""
        self.scaler = StandardScaler()
        self.svm = None
        self.class_names = None
    
    def load_data(self, data_dir: str = None, features_file: str = None):
        """
        加载数据
        
        Args:
            data_dir: 数据目录(从图像提取特征)
            features_file: 特征文件(已提取的特征)
        """
        if features_file and Path(features_file).exists():
            logger.info(f"从文件加载特征: {features_file}")
            X, y, class_names = load_extracted_features(features_file)
        elif data_dir:
            logger.info("从图像提取特征...")
            X, y, class_names = load_data_from_folders(data_dir)
        else:
            raise ValueError("必须提供data_dir或features_file")
        
        self.class_names = class_names
        return X, y
    
    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        test_size: float = 0.2,
        use_grid_search: bool = False
    ):
        """
        训练SVM模型
        
        Args:
            X: 特征矩阵
            y: 标签
            test_size: 测试集比例
            use_grid_search: 是否使用网格搜索优化参数
        """
        logger.info("=" * 60)
        logger.info("开始训练SVM模型")
        logger.info("=" * 60)
        
        # 分割数据集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=test_size,
            random_state=42,
            stratify=y
        )
        
        logger.info(f"训练集: {len(X_train)} 样本")
        logger.info(f"测试集: {len(X_test)} 样本")
        logger.info(f"特征维度: {X_train.shape[1]}")
        
        # 标准化特征
        logger.info("\n标准化特征...")
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # 训练SVM
        if use_grid_search:
            logger.info("\n使用网格搜索优化参数...")
            param_grid = {
                'C': [0.1, 1, 10, 100],
                'gamma': ['scale', 'auto', 0.001, 0.01],
                'kernel': ['rbf', 'linear']
            }
            
            svm = SVC(probability=True, random_state=42)
            grid_search = GridSearchCV(
                svm,
                param_grid,
                cv=5,
                n_jobs=-1,
                verbose=2
            )
            
            grid_search.fit(X_train_scaled, y_train)
            self.svm = grid_search.best_estimator_
            
            logger.info(f"\n最佳参数: {grid_search.best_params_}")
        else:
            logger.info("\n训练SVM (默认参数)...")
            self.svm = SVC(
                kernel='rbf',
                C=10,
                gamma='scale',
                probability=True,
                random_state=42
            )
            self.svm.fit(X_train_scaled, y_train)
        
        # 评估
        logger.info("\n评估模型...")
        y_pred = self.svm.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        
        logger.info("\n" + "=" * 60)
        logger.info("训练完成!")
        logger.info(f"测试集准确率: {accuracy * 100:.2f}%")
        logger.info("=" * 60)
        
        # 详细报告
        logger.info("\n分类报告:")
        logger.info("\n" + classification_report(
            y_test, y_pred,
            target_names=self.class_names
        ))
        
        logger.info("混淆矩阵:")
        cm = confusion_matrix(y_test, y_pred)
        logger.info(f"\n{cm}")
        
        return accuracy
    
    def save_model(self):
        """保存模型"""
        save_path = config.EMOTION_SVM_SKLEARN
        
        model_data = {
            'svm': self.svm,
            'scaler': self.scaler,
            'class_names': self.class_names
        }
        
        with open(save_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"\n模型已保存: {save_path}")


def main():
    """训练入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Sklearn情感识别训练')
    parser.add_argument(
        '--data_dir',
        type=str,
        default='data',
        help='数据目录'
    )
    parser.add_argument(
        '--features_file',
        type=str,
        default=None,
        help='预提取的特征文件'
    )
    parser.add_argument(
        '--grid_search',
        action='store_true',
        help='使用网格搜索优化参数'
    )
    
    args = parser.parse_args()
    
    # 创建训练器
    trainer = SklearnEmotionTrainer()
    
    # 加载数据
    X, y = trainer.load_data(
        data_dir=args.data_dir,
        features_file=args.features_file
    )
    
    # 训练
    accuracy = trainer.train(
        X, y,
        test_size=0.2,
        use_grid_search=args.grid_search
    )
    
    # 保存模型
    trainer.save_model()


if __name__ == '__main__':
    main()
