#!/usr/bin/env python3
import argparse
import glob
import json
import sys
import time
from collections import Counter

try:
    import serial
except ImportError:
    print("Missing dependency! Install with: pip install pyserial")
    sys.exit(1)

COMMON_BAUDS = [115200, 57600, 921600, 38400, 19200, 9600, 230400, 460800]
RED = "\033[91m\033[1m"
GREEN = "\033[92m"
RESET = "\033[0m"


def cmd_scan(args):
    """Probe serial ports across common baud rates to detect active telemetry streams."""
    ports = args.ports if args.ports else sorted(glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*"))
    if not ports:
        print("No /dev/ttyUSB* or /dev/ttyACM* devices found.")
        return

    print(f"Scanning ports: {ports}\n")
    for port in ports:
        print(f"--- {port} ---")
        for baud in COMMON_BAUDS:
            try:
                with serial.Serial(port, baudrate=baud, timeout=0.4) as ser:
                    ser.reset_input_buffer()
                    time.sleep(0.35)
                    data = ser.read(128)
                    if data:
                        preview = " ".join(f"{b:02X}" for b in data[:24])
                        ascii_ratio = sum(32 <= b < 127 for b in data) / len(data)
                        kind = "ASCII" if ascii_ratio > 0.7 else "BINARY"
                        print(f"  {GREEN}[OK] {baud:>7} baud{RESET} | {len(data):>3} bytes ({kind}) | {preview}")
            except Exception as e:
                print(f"  [ERROR] {baud}: {e}")
                break


def read_packets(ser, header_bytes=None):
    """Split incoming stream into packets using a known sync header or a 15 ms idle gap."""
    buf = bytearray()
    while True:
        chunk = ser.read(256)
        if chunk:
            buf.extend(chunk)
            if header_bytes:
                while True:
                    idx = buf.find(header_bytes)
                    if idx == -1:
                        break
                    next_idx = buf.find(header_bytes, idx + len(header_bytes))
                    if next_idx != -1:
                        pkt = bytes(buf[idx:next_idx])
                        del buf[:next_idx]
                        yield pkt
                    else:
                        if idx > 0:
                            del buf[:idx]
                        break
        else:
            if not header_bytes and buf:
                pkt = bytes(buf)
                buf.clear()
                yield pkt


def cmd_sniff(args):
    """Print live hex packets, highlighting bytes that changed since the previous frame."""
    header_bytes = bytes.fromhex(args.header) if args.header else None
    out_file = open(args.out, "w", encoding="utf-8") if args.out else None
    prev_pkt = None
    count = 0

    print(f"[*] Sniffing {args.port} @ {args.baud} baud (Press Ctrl+C to stop)")
    if header_bytes:
        print(f"[*] Sync header filter: {header_bytes.hex(' ').upper()}")
    if out_file:
        print(f"[*] Recording packets to: {args.out}")

    try:
        with serial.Serial(args.port, baudrate=args.baud, timeout=0.015) as ser:
            ser.reset_input_buffer()
            for pkt in read_packets(ser, header_bytes):
                count += 1
                ts = time.time()
                if out_file:
                    out_file.write(json.dumps({"ts": ts, "hex": pkt.hex()}) + "\n")
                    out_file.flush()

                formatted = []
                for i, b in enumerate(pkt):
                    changed = prev_pkt is None or i >= len(prev_pkt) or prev_pkt[i] != b
                    if changed and prev_pkt is not None:
                        formatted.append(f"{RED}{b:02X}{RESET}")
                    else:
                        formatted.append(f"{b:02X}")

                print(f"[{count:04d}] (len={len(pkt):02d}) " + " ".join(formatted))
                prev_pkt = pkt
    except KeyboardInterrupt:
        print(f"\n[+] Stopped. Recorded {count} packets.")
    finally:
        if out_file:
            out_file.close()


def load_dominant_packets(path):
    """Load recorded JSONL packets matching the most frequent frame length."""
    packets = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            packets.append(bytes.fromhex(row["hex"]))
    if not packets:
        return [], 0
    common_len, _ = Counter(len(p) for p in packets).most_common(1)[0]
    filtered = [p for p in packets if len(p) == common_len]
    return filtered, common_len


def cmd_diff(args):
    """Compare idle vs. active captures (e.g. spinning wheels on a stand) to locate encoder bytes."""
    pkts_a, len_a = load_dominant_packets(args.baseline)
    pkts_b, len_b = load_dominant_packets(args.active)

    if not pkts_a or not pkts_b or len_a != len_b:
        print(f"Error: mismatched or empty packet lengths (baseline={len_a}, active={len_b}).")
        return

    print(f"Comparing {len(pkts_a)} baseline packets vs {len(pkts_b)} active packets (length: {len_a} bytes)\n")
    print(f"{'Idx':>3} | {'Baseline (min..max)':<19} | {'Active (min..max)':<19} | Classification")
    print("-" * 78)

    for i in range(len_a):
        vals_a = [p[i] for p in pkts_a]
        vals_b = [p[i] for p in pkts_b]
        uniq_a = len(set(vals_a))
        uniq_b = len(set(vals_b))
        range_a = f"0x{min(vals_a):02X}..0x{max(vals_a):02X}"
        range_b = f"0x{min(vals_b):02X}..0x{max(vals_b):02X}"

        if uniq_a == 1 and uniq_b == 1 and vals_a[0] == vals_b[0]:
            note = "Constant (header / reserved)"
        elif uniq_a == 1 and uniq_b > 1:
            note = f"{RED}>>> ENCODER / SENSOR CANDIDATE <<<{RESET}"
        elif uniq_b > uniq_a:
            note = f"{GREEN}Increased variance{RESET}"
        else:
            note = "Continuously changing (counter / CRC / noise)"

        print(f"{i:>3} | {range_a:<19} | {range_b:<19} | {note}")


def cmd_send(args):
    """Send raw hex bytes to test motor/LED commands safely while wheels are off the ground."""
    payload = bytes.fromhex(args.hex)
    print(f"[*] Sending to {args.port} @ {args.baud} baud: {payload.hex(' ').upper()}")
    with serial.Serial(args.port, baudrate=args.baud, timeout=0.1) as ser:
        if args.hz <= 0:
            ser.write(payload)
            time.sleep(0.1)
            reply = ser.read(128)
            if reply:
                print(f"[<] Reply ({len(reply)} B): {reply.hex(' ').upper()}")
        else:
            interval = 1.0 / args.hz
            print(f"[*] Repeating at {args.hz} Hz (Press Ctrl+C to stop)...")
            try:
                while True:
                    ser.write(payload)
                    reply = ser.read(128)
                    if reply:
                        print(f"[<] {reply.hex(' ').upper()}")
                    time.sleep(interval)
            except KeyboardInterrupt:
                print("\n[+] Stopped.")


def main():
    parser = argparse.ArgumentParser(description="D1 Serial Port Recon, Packet Analyzer & Command Tester")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_scan = sub.add_parser("scan", help="Scan serial ports across common baud rates")
    p_scan.add_argument("--ports", nargs="*", help="Optional explicit port list (e.g. /dev/ttyUSB0)")
    p_scan.set_defaults(func=cmd_scan)

    p_sniff = sub.add_parser("sniff", help="Live packet sniffer with byte-change highlighting")
    p_sniff.add_argument("--port", required=True, help="Serial device path (e.g. /dev/ttyUSB0)")
    p_sniff.add_argument("--baud", type=int, default=115200, help="Baud rate (default: 115200)")
    p_sniff.add_argument("--header", help="Hex sync header bytes (e.g. aa55)")
    p_sniff.add_argument("--out", help="Output JSONL file path (e.g. standing.jsonl)")
    p_sniff.set_defaults(func=cmd_sniff)

    p_diff = sub.add_parser("diff", help="Diff two recorded captures (idle vs. moving)")
    p_diff.add_argument("baseline", help="Idle capture file (e.g. standing.jsonl)")
    p_diff.add_argument("active", help="Active capture file (e.g. wheels.jsonl)")
    p_diff.set_defaults(func=cmd_diff)

    p_send = sub.add_parser("send", help="Send a raw hex packet to test controller commands")
    p_send.add_argument("--port", required=True, help="Serial device path (e.g. /dev/ttyUSB0)")
    p_send.add_argument("--baud", type=int, default=115200, help="Baud rate (default: 115200)")
    p_send.add_argument("--hex", required=True, help="Hex string to transmit (e.g. 'aa5500000000ff')")
    p_send.add_argument("--hz", type=float, default=0.0, help="Repeat rate in Hz (0 = send once)")
    p_send.set_defaults(func=cmd_send)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()