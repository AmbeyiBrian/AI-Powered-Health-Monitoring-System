"""
Anomaly Detection Module for Health Monitoring System
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
from typing import Dict, List, Tuple, Any, Optional
import joblib
import logging
from datetime import datetime, timezone
import json


class AnomalyDetector:
    """Base class for anomaly detection models"""
    
    def __init__(self, contamination: float = 0.1):
        self.contamination = contamination
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_columns = ['heart_rate', 'blood_oxygen']
        self.logger = logging.getLogger(__name__)
        
    def prepare_features(self, data: pd.DataFrame) -> np.ndarray:
        """Prepare features for anomaly detection"""
        # Select relevant features
        features = data[self.feature_columns].copy()
        
        # Handle missing values
        features = features.fillna(features.mean())
        
        # Add time-based features
        if 'timestamp' in data.columns:
            features['hour'] = pd.to_datetime(data['timestamp']).dt.hour
            features['day_of_week'] = pd.to_datetime(data['timestamp']).dt.dayofweek
        
        # Add derived features
        if 'activity_level' in data.columns:
            activity_map = {'low': 1, 'moderate': 2, 'high': 3}
            features['activity_numeric'] = data['activity_level'].map(activity_map).fillna(2)
        
        return features.values
    
    def train(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Train the anomaly detection model"""
        raise NotImplementedError("Subclasses must implement train method")
    
    def predict(self, data: pd.DataFrame) -> np.ndarray:
        """Predict anomalies in the data"""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        features = self.prepare_features(data)
        features_scaled = self.scaler.transform(features)
        predictions = self.model.predict(features_scaled)
        
        # Convert to binary (1 = normal, 0 = anomaly)
        return (predictions == 1).astype(int)
    
    def predict_proba(self, data: pd.DataFrame) -> np.ndarray:
        """Get anomaly scores"""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        features = self.prepare_features(data)
        features_scaled = self.scaler.transform(features)
        
        if hasattr(self.model, 'decision_function'):
            scores = self.model.decision_function(features_scaled)
            # Convert to probabilities (higher score = more normal)
            probabilities = 1 / (1 + np.exp(-scores))
            return probabilities
        else:
            # For models without decision_function, return binary predictions
            predictions = self.predict(data)
            return predictions.astype(float)
    
    def save_model(self, filepath: str) -> None:
        """Save the trained model"""
        if not self.is_trained:
            raise ValueError("No trained model to save")
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'contamination': self.contamination,
            'feature_columns': self.feature_columns,
            'model_type': self.__class__.__name__
        }
        
        joblib.dump(model_data, filepath)
        self.logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str) -> None:
        """Load a trained model"""
        model_data = joblib.load(filepath)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.contamination = model_data['contamination']
        self.feature_columns = model_data['feature_columns']
        self.is_trained = True
        
        self.logger.info(f"Model loaded from {filepath}")


class IsolationForestDetector(AnomalyDetector):
    """Isolation Forest based anomaly detector"""
    
    def __init__(self, contamination: float = 0.1, n_estimators: int = 100, 
                 random_state: int = 42):
        super().__init__(contamination)
        self.n_estimators = n_estimators
        self.random_state = random_state
        
    def train(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Train Isolation Forest model"""
        self.logger.info("Training Isolation Forest anomaly detector")
        
        # Prepare features
        features = self.prepare_features(data)
        
        # Scale features
        features_scaled = self.scaler.fit_transform(features)
        
        # Train model
        self.model = IsolationForest(
            contamination=self.contamination,
            n_estimators=self.n_estimators,
            random_state=self.random_state
        )
        
        self.model.fit(features_scaled)
        self.is_trained = True
        
        # Evaluate on training data
        predictions = self.model.predict(features_scaled)
        anomaly_count = np.sum(predictions == -1)
        
        training_results = {
            'model_type': 'IsolationForest',
            'total_samples': len(data),
            'anomalies_detected': anomaly_count,
            'anomaly_rate': anomaly_count / len(data),
            'contamination_setting': self.contamination
        }
        
        self.logger.info(f"Training completed. Detected {anomaly_count} anomalies in {len(data)} samples")
        return training_results


class OneClassSVMDetector(AnomalyDetector):
    """One-Class SVM based anomaly detector"""
    
    def __init__(self, contamination: float = 0.1, kernel: str = 'rbf', 
                 gamma: str = 'scale', nu: float = None):
        super().__init__(contamination)
        self.kernel = kernel
        self.gamma = gamma
        self.nu = nu or contamination
        
    def train(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Train One-Class SVM model"""
        self.logger.info("Training One-Class SVM anomaly detector")
        
        # Prepare features
        features = self.prepare_features(data)
        
        # Scale features
        features_scaled = self.scaler.fit_transform(features)
        
        # Train model
        self.model = OneClassSVM(
            kernel=self.kernel,
            gamma=self.gamma,
            nu=self.nu
        )
        
        self.model.fit(features_scaled)
        self.is_trained = True
        
        # Evaluate on training data
        predictions = self.model.predict(features_scaled)
        anomaly_count = np.sum(predictions == -1)
        
        training_results = {
            'model_type': 'OneClassSVM',
            'total_samples': len(data),
            'anomalies_detected': anomaly_count,
            'anomaly_rate': anomaly_count / len(data),
            'nu_setting': self.nu
        }
        
        self.logger.info(f"Training completed. Detected {anomaly_count} anomalies in {len(data)} samples")
        return training_results


class StatisticalAnomalyDetector(AnomalyDetector):
    """Statistical methods for anomaly detection"""
    
    def __init__(self, method: str = 'z_score', threshold: float = 3.0):
        super().__init__()
        self.method = method  # 'z_score', 'iqr', 'modified_z_score'
        self.threshold = threshold
        self.statistics = {}
        
    def train(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate statistical parameters"""
        self.logger.info(f"Training statistical anomaly detector using {self.method}")
        
        # Calculate statistics for each feature
        for column in self.feature_columns:
            if column in data.columns:
                values = data[column].dropna()
                
                if self.method == 'z_score':
                    self.statistics[column] = {
                        'mean': values.mean(),
                        'std': values.std()
                    }
                elif self.method == 'iqr':
                    q1 = values.quantile(0.25)
                    q3 = values.quantile(0.75)
                    iqr = q3 - q1
                    self.statistics[column] = {
                        'q1': q1,
                        'q3': q3,
                        'iqr': iqr,
                        'lower_bound': q1 - 1.5 * iqr,
                        'upper_bound': q3 + 1.5 * iqr
                    }
                elif self.method == 'modified_z_score':
                    median = values.median()
                    mad = np.median(np.abs(values - median))
                    self.statistics[column] = {
                        'median': median,
                        'mad': mad
                    }
        
        self.is_trained = True
        
        # Test on training data
        predictions = self.predict(data)
        anomaly_count = np.sum(predictions == 0)
        
        training_results = {
            'model_type': f'Statistical_{self.method}',
            'total_samples': len(data),
            'anomalies_detected': anomaly_count,
            'anomaly_rate': anomaly_count / len(data),
            'threshold': self.threshold,
            'statistics': self.statistics
        }
        
        return training_results
    
    def predict(self, data: pd.DataFrame) -> np.ndarray:
        """Predict anomalies using statistical methods"""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        predictions = np.ones(len(data))  # 1 = normal
        
        for column in self.feature_columns:
            if column in data.columns:
                values = data[column].fillna(data[column].mean())
                
                if self.method == 'z_score':
                    z_scores = np.abs((values - self.statistics[column]['mean']) / 
                                    self.statistics[column]['std'])
                    anomalies = z_scores > self.threshold
                    
                elif self.method == 'iqr':
                    anomalies = ((values < self.statistics[column]['lower_bound']) | 
                               (values > self.statistics[column]['upper_bound']))
                    
                elif self.method == 'modified_z_score':
                    modified_z_scores = 0.6745 * (values - self.statistics[column]['median']) / \
                                      self.statistics[column]['mad']
                    anomalies = np.abs(modified_z_scores) > self.threshold
                
                # Mark as anomaly if any feature is anomalous
                predictions[anomalies] = 0
        
        return predictions.astype(int)
    
    def predict_proba(self, data: pd.DataFrame) -> np.ndarray:
        """Get anomaly probability scores using statistical methods"""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        max_scores = np.zeros(len(data))  # Initialize with zeros
        
        for column in self.feature_columns:
            if column in data.columns:
                values = data[column].fillna(data[column].mean())
                
                if self.method == 'z_score':
                    z_scores = np.abs((values - self.statistics[column]['mean']) / 
                                    self.statistics[column]['std'])
                    # Convert z-scores to probabilities (higher z-score = higher anomaly probability)
                    probabilities = np.minimum(z_scores / self.threshold, 1.0)
                    
                elif self.method == 'iqr':
                    # Calculate distance from normal range
                    lower_bound = self.statistics[column]['lower_bound']
                    upper_bound = self.statistics[column]['upper_bound']
                    
                    # Distance from normal range (0 if within range)
                    distances = np.maximum(
                        lower_bound - values,  # Distance below lower bound
                        values - upper_bound   # Distance above upper bound
                    )
                    distances = np.maximum(distances, 0)  # Only positive distances
                    
                    # Normalize by IQR to get probability-like scores
                    iqr = self.statistics[column]['iqr']
                    probabilities = np.minimum(distances / iqr, 1.0) if iqr > 0 else np.zeros_like(distances)
                    
                elif self.method == 'modified_z_score':
                    modified_z_scores = np.abs(0.6745 * (values - self.statistics[column]['median']) / 
                                             self.statistics[column]['mad'])
                    # Convert to probabilities
                    probabilities = np.minimum(modified_z_scores / self.threshold, 1.0)
                
                # Take maximum anomaly score across all features
                max_scores = np.maximum(max_scores, probabilities)
        
        return max_scores


class EnsembleAnomalyDetector:
    """Ensemble of multiple anomaly detection methods"""
    
    def __init__(self, detectors: List[AnomalyDetector] = None, voting: str = 'majority'):
        self.detectors = detectors or [
            IsolationForestDetector(contamination=0.1),
            OneClassSVMDetector(contamination=0.1),
            StatisticalAnomalyDetector(method='z_score', threshold=3.0)
        ]
        self.voting = voting  # 'majority', 'unanimous', 'any'
        self.is_trained = False
        self.logger = logging.getLogger(__name__)
        
    def train(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Train all detectors in the ensemble"""
        self.logger.info("Training ensemble anomaly detector")
        
        training_results = {
            'ensemble_results': [],
            'individual_results': []
        }
        
        # Train each detector
        for i, detector in enumerate(self.detectors):
            self.logger.info(f"Training detector {i+1}/{len(self.detectors)}: {detector.__class__.__name__}")
            result = detector.train(data)
            training_results['individual_results'].append(result)
        
        self.is_trained = True
        
        # Evaluate ensemble performance on training data
        predictions = self.predict(data)
        anomaly_count = np.sum(predictions == 0)
        
        training_results['ensemble_results'] = {
            'total_samples': len(data),
            'anomalies_detected': anomaly_count,
            'anomaly_rate': anomaly_count / len(data),
            'voting_method': self.voting,
            'num_detectors': len(self.detectors)
        }
        
        self.logger.info(f"Ensemble training completed. Final prediction: {anomaly_count} anomalies")
        return training_results
    
    def predict(self, data: pd.DataFrame) -> np.ndarray:
        """Predict anomalies using ensemble voting"""
        if not self.is_trained:
            raise ValueError("Ensemble must be trained before making predictions")
        
        # Get predictions from all detectors
        all_predictions = []
        for detector in self.detectors:
            predictions = detector.predict(data)
            all_predictions.append(predictions)
        
        all_predictions = np.array(all_predictions)
        
        # Apply voting strategy
        if self.voting == 'majority':
            # Majority vote (more than half predict anomaly)
            anomaly_votes = np.sum(all_predictions == 0, axis=0)
            final_predictions = (anomaly_votes > len(self.detectors) / 2).astype(int)
            final_predictions = 1 - final_predictions  # Convert to 1=normal, 0=anomaly
            
        elif self.voting == 'unanimous':
            # All detectors must agree it's an anomaly
            final_predictions = np.all(all_predictions == 0, axis=0).astype(int)
            final_predictions = 1 - final_predictions
            
        elif self.voting == 'any':
            # Any detector finding anomaly counts
            final_predictions = np.any(all_predictions == 0, axis=0).astype(int)
            final_predictions = 1 - final_predictions
            
        else:
            raise ValueError(f"Unknown voting method: {self.voting}")
        
        return final_predictions
    
    def predict_proba(self, data: pd.DataFrame) -> np.ndarray:
        """Get anomaly probability scores using ensemble averaging"""
        if not self.is_trained:
            raise ValueError("Ensemble must be trained before making predictions")
        
        # Get probability scores from all detectors
        all_probabilities = []
        for detector in self.detectors:
            try:
                probabilities = detector.predict_proba(data)
                all_probabilities.append(probabilities)
            except AttributeError:
                # If a detector doesn't have predict_proba, use binary predictions
                predictions = detector.predict(data)
                # Convert binary predictions to probabilities (0=anomaly, 1=normal)
                probabilities = 1.0 - predictions.astype(float)
                all_probabilities.append(probabilities)
        
        # Average the probabilities
        all_probabilities = np.array(all_probabilities)
        ensemble_probabilities = np.mean(all_probabilities, axis=0)
        
        return ensemble_probabilities
    
    def get_detector_agreement(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Get agreement statistics between detectors"""
        if not self.is_trained:
            raise ValueError("Ensemble must be trained before analysis")
        
        # Get predictions from all detectors
        all_predictions = []
        detector_names = []
        
        for detector in self.detectors:
            predictions = detector.predict(data)
            all_predictions.append(predictions)
            detector_names.append(detector.__class__.__name__)
        
        all_predictions = np.array(all_predictions)
        
        # Calculate agreement statistics
        agreement_matrix = np.zeros((len(self.detectors), len(self.detectors)))
        
        for i in range(len(self.detectors)):
            for j in range(len(self.detectors)):
                agreement = np.mean(all_predictions[i] == all_predictions[j])
                agreement_matrix[i, j] = agreement
        
        # Calculate overall agreement
        anomaly_counts = np.sum(all_predictions == 0, axis=1)
        
        return {
            'detector_names': detector_names,
            'agreement_matrix': agreement_matrix.tolist(),
            'anomaly_counts': anomaly_counts.tolist(),
            'total_samples': len(data)
        }


def create_health_anomaly_detector(method: str = 'ensemble', **kwargs) -> AnomalyDetector:
    """Factory function to create anomaly detectors"""
    
    if method == 'isolation_forest':
        return IsolationForestDetector(**kwargs)
    elif method == 'one_class_svm':
        return OneClassSVMDetector(**kwargs)
    elif method == 'statistical':
        return StatisticalAnomalyDetector(**kwargs)
    elif method == 'ensemble':
        return EnsembleAnomalyDetector(**kwargs)
    else:
        raise ValueError(f"Unknown method: {method}")


def evaluate_anomaly_detector(detector: AnomalyDetector, test_data: pd.DataFrame, 
                             true_labels: np.ndarray = None) -> Dict[str, Any]:
    """Evaluate anomaly detector performance"""
    predictions = detector.predict(test_data)
    
    results = {
        'total_samples': len(test_data),
        'predicted_anomalies': np.sum(predictions == 0),
        'predicted_normal': np.sum(predictions == 1),
        'anomaly_rate': np.sum(predictions == 0) / len(test_data)
    }
    
    # If true labels are provided, calculate metrics
    if true_labels is not None:
        # Convert to same format (0 = anomaly, 1 = normal)
        true_binary = (true_labels == 1).astype(int)
        
        results.update({
            'accuracy': np.mean(predictions == true_binary),
            'precision': np.sum((predictions == 0) & (true_binary == 0)) / max(1, np.sum(predictions == 0)),
            'recall': np.sum((predictions == 0) & (true_binary == 0)) / max(1, np.sum(true_binary == 0)),
            'true_anomalies': np.sum(true_binary == 0),
            'true_normal': np.sum(true_binary == 1)
        })
        
        # Calculate F1 score
        precision = results['precision']
        recall = results['recall']
        if precision + recall > 0:
            results['f1_score'] = 2 * (precision * recall) / (precision + recall)
        else:
            results['f1_score'] = 0.0
    
    return results
