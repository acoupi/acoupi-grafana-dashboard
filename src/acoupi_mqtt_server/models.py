from datetime import datetime
from pathlib import Path
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


LOCAL_TIMEZONE = datetime.now().astimezone().tzinfo


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

    @field_validator("started_on", "ended_on", mode="after")
    @classmethod
    def assume_utc_for_naive_datetimes(cls, value: datetime | None) -> datetime | None:
        if value is None or value.tzinfo is not None:
            return value
        return value.replace(tzinfo=LOCAL_TIMEZONE)


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

    @field_validator("created_on", mode="after")
    @classmethod
    def assume_utc_for_naive_created_on(cls, value: datetime) -> datetime:
        if value.tzinfo is not None:
            return value
        return value.replace(tzinfo=LOCAL_TIMEZONE)


class ModelOutput(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: UUID
    name_model: str
    recording: Recording
    tags: list[PredictedTag] = Field(default_factory=list)
    detections: list[Detection] = Field(default_factory=list)
    created_on: datetime

    @field_validator("created_on", mode="after")
    @classmethod
    def assume_utc_for_naive_created_on(cls, value: datetime) -> datetime:
        if value.tzinfo is not None:
            return value
        return value.replace(tzinfo=LOCAL_TIMEZONE)


class Heartbeat(BaseModel):
    model_config = ConfigDict(extra="allow")

    sent_on: datetime
    device_id: str
    status: str = "OK"

    @field_validator("sent_on", mode="after")
    @classmethod
    def assume_utc_for_naive_sent_on(cls, value: datetime) -> datetime:
        if value.tzinfo is not None:
            return value
        return value.replace(tzinfo=LOCAL_TIMEZONE)
