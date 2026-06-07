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

import paho.mqtt.client as mqtt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Publish a test heartbeat message")
    parser.add_argument("--host", default="localhost", help="MQTT broker host")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port")
    parser.add_argument(
        "--topic",
        default="acoupi/test-device-001",
        help="MQTT topic used as canonical device identifier",
    )
    parser.add_argument(
        "--payload-device-id",
        default="raspi-internal-001",
        help="Device-reported payload device_id for heartbeat messages",
    )
    parser.add_argument("--status", default="OK", help="Heartbeat status value")
    parser.add_argument("--username", default=None, help="MQTT username")
    parser.add_argument("--password", default=None, help="MQTT password")
    parser.add_argument(
        "--client-id",
        default="acoupi-test-heartbeat-publisher",
        help="MQTT client id for the publisher",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    payload = {
        "sent_on": datetime.now(timezone.utc).isoformat(),
        "device_id": args.payload_device_id,
        "status": args.status,
    }

    client = mqtt.Client(client_id=args.client_id)
    if args.username:
        client.username_pw_set(args.username, args.password)

    client.connect(args.host, args.port, keepalive=60)
    result = client.publish(args.topic, json.dumps(payload), qos=0, retain=False)
    result.wait_for_publish()
    client.disconnect()

    print(f"published heartbeat to topic={args.topic}")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
