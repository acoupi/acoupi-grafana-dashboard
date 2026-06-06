from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import paho.mqtt.client as mqtt

SPECIES = [
    "Turdus falcklandii",
    "Zonotrichia capensis",
    "Vanellus chilensis",
    "Troglodytes aedon",
    "Columba livia",
    "Passer domesticus",
    "Sicalis luteola",
    "Phrygilus patagonicus",
]


@dataclass
class GeneratedMessage:
    recording_time: datetime
    payload: dict


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate realistic detection payloads and optionally publish them"
    )
    parser.add_argument("--host", default="localhost", help="MQTT broker host")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port")
    parser.add_argument(
        "--topic",
        default="acoupi/test-device-001",
        help="MQTT topic used as canonical device identifier",
    )
    parser.add_argument(
        "--deployment-name",
        default="test-site",
        help="Deployment name shared by all generated recordings",
    )
    parser.add_argument(
        "--model-name",
        default="birdnet",
        help="Value for the detection payload name_model field",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=5,
        help="Number of historical days to generate",
    )
    parser.add_argument(
        "--recordings-per-day",
        type=int,
        default=12,
        help="Number of recordings generated per day",
    )
    parser.add_argument(
        "--max-detections-per-recording",
        type=int,
        default=4,
        help="Maximum number of detections per recording",
    )
    parser.add_argument(
        "--publish",
        action="store_true",
        help="Publish the generated payloads to MQTT",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory where generated payloads are written as JSON files",
    )
    parser.add_argument("--username", default=None, help="MQTT username")
    parser.add_argument("--password", default=None, help="MQTT password")
    parser.add_argument(
        "--client-id",
        default="acoupi-dataset-generator",
        help="MQTT client id for publishing mode",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible datasets",
    )
    return parser


def isoformat_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def random_confidence(
    rng: random.Random, low: float = 0.45, high: float = 0.99
) -> float:
    return round(rng.uniform(low, high), 3)


def build_detection(rng: random.Random) -> dict:
    species = rng.choice(SPECIES)
    start_time = round(rng.uniform(0.0, 4.2), 3)
    end_time = round(min(start_time + rng.uniform(0.15, 0.75), 5.0), 3)
    low_freq = round(rng.uniform(800, 3500), 1)
    high_freq = round(min(low_freq + rng.uniform(300, 2500), 8000), 1)

    species_tag = {
        "tag": {"key": "species", "value": species},
        "confidence_score": random_confidence(rng),
    }
    confidence_tag = {
        "tag": {
            "key": "confidence_band",
            "value": rng.choice(["low", "medium", "high"]),
        },
        "confidence_score": random_confidence(rng, 0.5, 1.0),
    }

    return {
        "id": str(uuid4()),
        "location": {
            "type": "BoundingBox",
            "coordinates": [start_time, low_freq, end_time, high_freq],
        },
        "detection_score": random_confidence(rng),
        "tags": [species_tag, confidence_tag],
    }


def build_messages(args: argparse.Namespace) -> list[GeneratedMessage]:
    rng = random.Random(args.seed)
    now = datetime.now(timezone.utc)
    deployment_started = now - timedelta(days=args.days + 14)
    deployment_id = str(uuid4())
    messages: list[GeneratedMessage] = []

    for day_offset in range(args.days):
        day_start = (now - timedelta(days=args.days - day_offset)).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        for recording_index in range(args.recordings_per_day):
            minute_offset = int(
                (24 * 60 / max(args.recordings_per_day, 1)) * recording_index
            )
            jitter = rng.randint(-15, 15)
            recording_time = day_start + timedelta(
                minutes=max(0, minute_offset + jitter)
            )
            created_on = recording_time + timedelta(seconds=rng.randint(20, 180))
            detections = [
                build_detection(rng)
                for _ in range(rng.randint(0, args.max_detections_per_recording))
            ]

            species_scores: dict[str, float] = defaultdict(float)
            for detection in detections:
                for predicted_tag in detection["tags"]:
                    if predicted_tag["tag"]["key"] == "species":
                        species = predicted_tag["tag"]["value"]
                        species_scores[species] = max(
                            species_scores[species], predicted_tag["confidence_score"]
                        )

            payload = {
                "id": str(uuid4()),
                "name_model": args.model_name,
                "recording": {
                    "created_on": isoformat_utc(recording_time),
                    "duration": 5.0,
                    "samplerate": 48000,
                    "deployment": {
                        "id": deployment_id,
                        "name": args.deployment_name,
                        "latitude": -33.45,
                        "longitude": -70.66,
                        "started_on": isoformat_utc(deployment_started),
                        "ended_on": None,
                    },
                    "path": f"/recordings/{recording_time:%Y-%m-%d}/rec-{uuid4().hex[:8]}.wav",
                    "audio_channels": 1,
                    "chunksize": 4096,
                    "id": str(uuid4()),
                },
                "tags": [
                    {
                        "tag": {"key": "species", "value": species},
                        "confidence_score": score,
                    }
                    for species, score in sorted(species_scores.items())
                ],
                "detections": detections,
                "created_on": isoformat_utc(created_on),
            }
            messages.append(
                GeneratedMessage(recording_time=recording_time, payload=payload)
            )

    return sorted(messages, key=lambda item: item.recording_time)


def write_messages(messages: list[GeneratedMessage], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = []

    for index, message in enumerate(messages, start=1):
        file_name = f"{index:04d}-{message.recording_time:%Y%m%dT%H%M%SZ}.json"
        file_path = output_dir / file_name
        file_path.write_text(json.dumps(message.payload, indent=2), encoding="utf-8")
        manifest.append(
            {
                "file": file_name,
                "recording_created_on": message.payload["recording"]["created_on"],
                "message_created_on": message.payload["created_on"],
                "detection_count": len(message.payload["detections"]),
            }
        )

    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )


def publish_messages(
    args: argparse.Namespace, messages: list[GeneratedMessage]
) -> None:
    client = mqtt.Client(client_id=args.client_id)
    if args.username:
        client.username_pw_set(args.username, args.password)

    client.connect(args.host, args.port, keepalive=60)
    for message in messages:
        result = client.publish(
            args.topic, json.dumps(message.payload), qos=0, retain=False
        )
        result.wait_for_publish()
    client.disconnect()


def main() -> None:
    args = build_parser().parse_args()
    if not args.publish and args.output_dir is None:
        raise SystemExit("Use --publish and/or --output-dir to choose an output mode")

    messages = build_messages(args)

    if args.output_dir is not None:
        write_messages(messages, args.output_dir)
        print(f"wrote {len(messages)} detection payloads to {args.output_dir}")

    if args.publish:
        publish_messages(args, messages)
        print(f"published {len(messages)} detection payloads to topic={args.topic}")

    if messages:
        first = messages[0].payload
        last = messages[-1].payload
        print("dataset summary:")
        print(
            f"- recordings span: {first['recording']['created_on']} -> {last['recording']['created_on']}"
        )
        print(f"- messages created span: {first['created_on']} -> {last['created_on']}")
        print(f"- publish time: {isoformat_utc(datetime.now(timezone.utc))}")


if __name__ == "__main__":
    main()
