#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# dependencies = ["paho-mqtt"]
# ///
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from uuid import uuid4

import paho.mqtt.client as mqtt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Publish a test detection message")
    parser.add_argument("--host", default="localhost", help="MQTT broker host")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port")
    parser.add_argument(
        "--topic",
        default="acoupi/test-device-001",
        help="MQTT topic used as canonical device identifier",
    )
    parser.add_argument(
        "--model-name",
        default="birdnet",
        help="Value for the detection payload name_model field",
    )
    parser.add_argument(
        "--deployment-name",
        default="test-site",
        help="Value for recording.deployment.name",
    )
    parser.add_argument("--username", default=None, help="MQTT username")
    parser.add_argument("--password", default=None, help="MQTT password")
    parser.add_argument(
        "--client-id",
        default="acoupi-test-detection-publisher",
        help="MQTT client id for the publisher",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    now = datetime.now(timezone.utc).isoformat()

    payload = {
        "id": str(uuid4()),
        "name_model": args.model_name,
        "recording": {
            "created_on": now,
            "duration": 5.0,
            "samplerate": 48000,
            "deployment": {
                "id": str(uuid4()),
                "name": args.deployment_name,
                "latitude": None,
                "longitude": None,
                "started_on": now,
                "ended_on": None,
            },
            "path": "/recordings/test.wav",
            "audio_channels": 1,
            "chunksize": 4096,
            "id": str(uuid4()),
        },
        "tags": [],
        "detections": [],
        "created_on": now,
    }

    client = mqtt.Client(client_id=args.client_id)
    if args.username:
        client.username_pw_set(args.username, args.password)

    client.connect(args.host, args.port, keepalive=60)
    result = client.publish(args.topic, json.dumps(payload), qos=0, retain=False)
    result.wait_for_publish()
    client.disconnect()

    print(f"published detection to topic={args.topic}")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
