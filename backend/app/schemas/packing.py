from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class PackingEventCreate(BaseModel):
    sku: str
    scanned: bool = True
    station_id: str = "STATION-01"

class PackingEventResponse(PackingEventCreate):
    id: str
    package_id: str
    scanned_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PackageWeightCreate(BaseModel):
    order_id: str
    measured_weight_grams: float
    seal_intact: bool = True
    packing_events: List[PackingEventCreate]

class PackageResponse(BaseModel):
    id: str
    order_id: str
    package_barcode: str
    total_expected_weight_grams: float
    measured_weight_grams: float
    seal_intact: bool
    packed_at: datetime
    packing_events: List[PackingEventResponse]

    model_config = ConfigDict(from_attributes=True)
