from typing import List, Dict, Optional
from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_batches: int
    active_batches: int
    closed_batches: int
    total_products: int
    aggregated_products: int
    aggregation_rate: float


class DashboardResponse(BaseModel):
    summary: DashboardSummary


class BatchInfoSchema(BaseModel):
    id: int
    batch_number: int
    batch_date: str
    is_closed: bool


class ProductionStatsSchema(BaseModel):
    total_products: int
    aggregated: int
    remaining: int
    aggregation_rate: float


class TimelineSchema(BaseModel):
    shift_duration_hours: float
    elapsed_hours: float
    products_per_hour: float
    estimated_completion: Optional[str] = None


class TeamPerformanceSchema(BaseModel):
    team: str
    avg_products_per_hour: float
    efficiency_score: float


class BatchStatisticsResponse(BaseModel):
    batch_info: BatchInfoSchema
    production_stats: ProductionStatsSchema
    timeline: TimelineSchema
    team_performance: TeamPerformanceSchema


class CompareBatchesRequest(BaseModel):
    batch_ids: List[int]


class ComparedBatchSchema(BaseModel):
    batch_id: int
    batch_number: int
    total_products: int
    aggregated: int
    rate: float
    duration_hours: float
    products_per_hour: float


class CompareBatchesResponse(BaseModel):
    comparison: List[ComparedBatchSchema]
    average: Dict[str, float]
