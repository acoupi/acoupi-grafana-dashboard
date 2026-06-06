from datetime import datetime
from pathlib import Path
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Tag(BaseModel):
    model_config = ConfigDict(extra="allow")

    key: str
    value: str


class PredictedTag(BaseModel):
    model_config = ConfigDict(extra="allow")

    tag: Tag
    confidence_score: float = 1.0


class BoundingBox(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str = "BoundingBox"
    coordinates: tuple[float, float, float, float]


class Detection(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: UUID
    location: BoundingBox | None = None
    detection_score: float = 1.0
    tags: list[PredictedTag] = Field(default_factory=list)


class Deployment(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: UUID
    name: str
    latitude: float | None = None
    longitude: float | None = None
    started_on: datetime
    ended_on: datetime | None = None


class Recording(BaseModel):
    model_config = ConfigDict(extra="allow")

    created_on: datetime
    duration: float
    samplerate: int
    deployment: Deployment
    path: Path | None = None
    audio_channels: int | None = 1
    chunksize: int | None = 4096
    id: UUID


class ModelOutput(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: UUID
    name_model: str
    recording: Recording
    tags: list[PredictedTag] = Field(default_factory=list)
    detections: list[Detection] = Field(default_factory=list)
    created_on: datetime


class Heartbeat(BaseModel):
    model_config = ConfigDict(extra="allow")

    sent_on: datetime
    device_id: str
    status: str = "OK"
