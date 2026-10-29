#!/usr/bin/env python3
"""Reassemble the parts in this folder into the original file."""
import hashlib
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
manifest = json.loads((HERE / "manifest.json").read_text(encoding="utf-8"))

suggested = manifest["original_filename"]
answer = input(f"Output file name/path [{suggested}]: ").strip().strip('"')
output = Path(answer).expanduser() if answer else Path(suggested)
if not output.is_absolute():
    output = Path.cwd() / output
output.parent.mkdir(parents=True, exist_ok=True)
if output.exists():
    confirm = input(f"{output} already exists. Replace it? Type YES to replace: ").strip()
    if confirm != "YES":
        raise SystemExit("Cancelled; existing file was not changed.")

temp_output = output.with_name(output.name + ".assembling")
digest = hashlib.sha256()
written = 0
try:
    with temp_output.open("wb") as destination:
        for item in manifest["parts"]:
            part = HERE / item["filename"]
            part_digest = hashlib.sha256()
            part_size = 0
            with part.open("rb") as source:
                while True:
                    block = source.read(1024 * 1024)
                    if not block:
                        break
                    destination.write(block)
                    digest.update(block)
                    part_digest.update(block)
                    part_size += len(block)
                    written += len(block)
            if part_size != item["size_bytes"] or part_digest.hexdigest() != item["sha256"]:
                raise SystemExit(f"Part verification failed: {part.name}")
    if written != manifest["original_size_bytes"]:
        raise SystemExit("Reassembled size does not match the manifest.")
    if digest.hexdigest() != manifest["original_sha256"]:
        raise SystemExit("SHA-256 verification failed; the output was not finalized.")
    temp_output.replace(output)
    print(f"Success: {output}")
    print(f"Size: {written:,} bytes")
    print(f"SHA-256: {digest.hexdigest()}")
except Exception:
    try:
        temp_output.unlink(missing_ok=True)
    except Exception:
        pass
    raise
