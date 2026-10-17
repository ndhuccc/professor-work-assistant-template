#!/usr/bin/env python3
"""Offline preparation for OnlineQuiz-v2; never uploads or changes a database."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path

TOP = {"name", "description", "default_points", "default_timer_seconds", "questions"}
ROW = {"node", "question_type", "format", "question", "options", "correct_answer", "explanation"}
TAGS = {"Knowledge", "Comprehension", "Calculation", "Implementation", "Analysis", "Evaluation", "Creation"}
PROFILE = "ndhuccc/OnlineQuiz-v2@5f81609e0fb9ebaa1536384f6e4d58c9f2d90f17"

def fail(message):
    raise ValueError(message)

def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            fail(f"JSON has duplicate key: {key}")
        result[key] = value
    return result

def text(value, field, nonempty=True):
    if not isinstance(value, str) or (nonempty and not value.strip()):
        fail(f"{field}: expected {'nonempty ' if nonempty else ''}text")
    return value

def unwrap(value):
    # Mirrors the observed backend's one outer bracket wrapper.
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        return value[1:-1].strip()
    return value

def prepare(data, *, name=None, description=None, points=None, seconds=None, expected_count=None):
    warnings = []
    if isinstance(data, list):
        if not name:
            fail("Array input requires --name")
        data = {"name": name, "questions": data}
    if not isinstance(data, dict):
        fail("Expected a JSON object or Bloom question array")
    unknown = set(data) - TOP
    if unknown:
        fail(f"Unsupported bank fields; retain metadata separately: {sorted(unknown)}")
    result = dict(data)
    for key, value in [("name", name), ("description", description),
                       ("default_points", points), ("default_timer_seconds", seconds)]:
        if value is not None:
            result[key] = value
    result.setdefault("description", "")
    result.setdefault("default_points", 1)
    result.setdefault("default_timer_seconds", 90)
    text(result.get("name"), "name")
    if len(result["name"]) > 255:
        fail("name: maximum 255 characters")
    text(result["description"], "description", False)
    point_value = result["default_points"]
    if isinstance(point_value, bool) or not isinstance(point_value, (int, float)) or not math.isfinite(point_value) or point_value <= 0:
        fail("default_points: expected a finite positive number")
    timer = result["default_timer_seconds"]
    if type(timer) is not int or not 5 <= timer <= 3600:
        fail("default_timer_seconds: expected integer 5..3600")
    questions = result.get("questions")
    if not isinstance(questions, list) or not questions:
        fail("questions: expected a nonempty array")
    if expected_count is not None and len(questions) != expected_count:
        fail(f"Question count {len(questions)} differs from expected {expected_count}")
    cleaned = []
    stems = set()
    for index, row in enumerate(questions, 1):
        prefix = f"Q{index}"
        if not isinstance(row, dict):
            fail(f"{prefix}: expected object")
        if set(row) - ROW:
            fail(f"{prefix}: unsupported fields {sorted(set(row) - ROW)}")
        item = dict(row)
        text(item.get("node"), f"{prefix}.node")
        item.setdefault("question_type", "")
        text(item["question_type"], f"{prefix}.question_type", False)
        if item["question_type"] not in TAGS:
            warnings.append(f"{prefix}: question_type is not a Bloom export tag")
        if item.get("format") not in ("Single Choice", "Multiple Choice"):
            fail(f"{prefix}.format: only Single Choice / Multiple Choice supported")
        item["question"] = unwrap(text(item.get("question"), f"{prefix}.question"))
        text(item["question"], f"{prefix}.question after normalization")
        signature = re.sub(r"\s+", "", item["question"]).casefold()
        if signature in stems:
            fail(f"{prefix}: duplicate normalized question stem")
        stems.add(signature)
        opts = item.get("options")
        if not isinstance(opts, list) or not 2 <= len(opts) <= 10:
            fail(f"{prefix}.options: expected 2..10 choices")
        normalized = []
        for pos, option in enumerate(opts):
            option = unwrap(text(option, f"{prefix}.options[{pos}]"))
            match = re.match(r"^([A-Z])\.\s+(.*)$", option, re.S)
            if match:
                expected_letter = chr(65 + pos)
                if match[1] != expected_letter:
                    fail(f"{prefix}: option prefix {match[1]} mismatches position {expected_letter}; refusing to reorder")
                option = match[2].strip()
            text(option, f"{prefix}.options[{pos}] after normalization")
            normalized.append(option)
        if len(set(normalized)) != len(normalized):
            fail(f"{prefix}: duplicate option text")
        item["options"] = normalized
        answer = text(item.get("correct_answer"), f"{prefix}.correct_answer")
        if not re.fullmatch(r"[A-J]+", answer):
            fail(f"{prefix}: answer must contain uppercase A..J only")
        if len(set(answer)) != len(answer):
            fail(f"{prefix}: duplicate answer letters")
        if any(ord(letter) - 65 >= len(opts) for letter in answer):
            fail(f"{prefix}: answer refers to a nonexistent option")
        if item["format"] == "Single Choice" and len(answer) != 1:
            fail(f"{prefix}: single-choice requires exactly one correct letter")
        item["correct_answer"] = "".join(sorted(answer))
        item.setdefault("explanation", "")
        item["explanation"] = unwrap(text(item["explanation"], f"{prefix}.explanation", False))
        if not item["explanation"].strip():
            warnings.append(f"{prefix}: explanation missing; Bloom quality review required")
        combined = " ".join([item["question"], *normalized])
        if re.search(r"選項\s*[(（]?[A-J]|option\s+[A-J]\b|以上皆[是否]|all of the above|none of the above", combined, re.I):
            warnings.append(f"{prefix}: possible position-dependent option reference; review before shuffled delivery")
        cleaned.append(item)
    result["questions"] = cleaned
    return result, warnings

def encoded(data):
    return (json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--name")
    parser.add_argument("--description")
    parser.add_argument("--points", type=float)
    parser.add_argument("--seconds", type=int)
    parser.add_argument("--expected-count", type=int)
    parser.add_argument("--output", type=Path, help="New file only; existing files are never overwritten")
    args = parser.parse_args()
    try:
        original = args.input.read_bytes()
        data = json.loads(original.decode("utf-8-sig"), object_pairs_hook=no_duplicate_keys,
                          parse_constant=lambda value: fail(f"Invalid JSON constant: {value}"))
        bank, warnings = prepare(data, name=args.name, description=args.description,
                                 points=args.points, seconds=args.seconds, expected_count=args.expected_count)
        output_bytes = encoded(bank)
        if args.output:
            if args.output.resolve() == args.input.resolve():
                fail("Input and output must differ")
            with args.output.open("xb") as stream:
                stream.write(output_bytes)
        report = {
            "status": "prepared_with_review_warnings" if warnings else "format_valid",
            "profile": PROFILE, "bank_name": bank["name"], "question_count": len(bank["questions"]),
            "default_points": bank["default_points"], "default_timer_seconds": bank["default_timer_seconds"],
            "input_sha256": hashlib.sha256(original).hexdigest(),
            "output": str(args.output.resolve()) if args.output else None,
            "output_sha256": hashlib.sha256(output_bytes).hexdigest() if args.output else None,
            "warnings": warnings,
            "not_verified": ["answer correctness", "Bloom levels", "bilingual explanation completeness",
                             "KaTeX rendering", "current server compatibility", "professor approval"],
            "imported": False,
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, TypeError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc), "imported": False}, ensure_ascii=False), file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())

