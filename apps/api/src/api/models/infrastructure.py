import uuid
import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime
from api.database.base import Base

class AIBackgroundJob(Base):
    __tablename__ = "background_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(255), index=True)
    name = Column(String(255), index=True)
    status = Column(String(50), default="PENDING")  # PENDING, STARTED, SUCCESS, FAILURE, RETRY
    args = Column(String(1000), nullable=True)
    kwargs = Column(String(1000), nullable=True)
    result = Column(String(4000), nullable=True)
    error = Column(String(4000), nullable=True)
    runtime = Column(Float, nullable=True)  # runtime in seconds
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

class AIJobHistory(Base):
    __tablename__ = "job_history"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), index=True)
    task_name = Column(String(255), index=True)
    status = Column(String(50))
    error_message = Column(String(4000), nullable=True)
    triggered_by = Column(String(255), nullable=True)
    execution_time = Column(DateTime, default=datetime.datetime.utcnow)

class AICacheMetadata(Base):
    __tablename__ = "cache_metadata"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    namespace = Column(String(100), index=True)
    hits = Column(Integer, default=0)
    misses = Column(Integer, default=0)
    hit_ratio = Column(Float, default=0.0)
    evictions = Column(Integer, default=0)
    keys_count = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class AIQueueMessage(Base):
    __tablename__ = "queue_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    queue_name = Column(String(100), index=True)
    size = Column(Integer, default=0)
    processed_count = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class AISchedulerHistory(Base):
    __tablename__ = "scheduler_history"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_name = Column(String(255), index=True)
    schedule = Column(String(255))
    status = Column(String(50))  # SUCCESS, FAILURE
    error_message = Column(String(4000), nullable=True)
    last_run = Column(DateTime, default=datetime.datetime.utcnow)
    next_run = Column(DateTime, nullable=True)

class AIWorkerMetric(Base):
    __tablename__ = "worker_metrics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    worker_name = Column(String(255), index=True)
    cpu_percent = Column(Float, default=0.0)
    ram_used_mb = Column(Float, default=0.0)
    ram_total_mb = Column(Float, default=0.0)
    active_tasks_count = Column(Integer, default=0)
    throughput = Column(Float, default=0.0)  # jobs per minute
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
