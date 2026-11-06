"""Сбор и разметка кадров планарной станции."""

from project.training.collector import (
    DEFAULT_CAMERA_ROLES,
    DEFAULT_DEFECT_CLASSES,
    BoundingBox,
    CameraFrameSource,
    CollectorCameraSource,
    CollectorError,
    FrameRecord,
    TrainingCollector,
    TrainingConfig,
    TrainingDatasetCollector,
    TrainingDatasetStore,
    ValidationError,
)
from project.training.yolo import (
    PolygonAnnotation,
    YoloExport,
    export_yolo_dataset,
)

__all__ = [
    "DEFAULT_CAMERA_ROLES",
    "DEFAULT_DEFECT_CLASSES",
    "BoundingBox",
    "CameraFrameSource",
    "CollectorCameraSource",
    "CollectorError",
    "FrameRecord",
    "TrainingCollector",
    "TrainingConfig",
    "TrainingDatasetCollector",
    "TrainingDatasetStore",
    "ValidationError",
    "PolygonAnnotation",
    "YoloExport",
    "export_yolo_dataset",
]
