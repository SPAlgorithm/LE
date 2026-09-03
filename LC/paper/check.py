#!/usr/bin/env python3
"""Independent re-verification of every equation stored by lc.py.

    python3 check.py qarray_1e9.json

For every quad member it checks the additive way (base + quad primes +
royal expression), the multiplicative way and both exponential ways, and
the two base-free ways M1 and E3 (the whole prime from members below it):
arithmetic, distinct members, base never used as a term, every term below
the target.  It also counts fallback flags and prints the SHA-256 of the
dataset so a reader can confirm the file is the published one.
"""
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import lc  # noqa: E402

ROYAL = set(lc.ROYAL)


def royal_value(text):
    """Evaluate a royal expression string with plain integer arithmetic."""
    return eval(text, {"__builtins__": {}}, {}) if text else 0


def main(path):
    with open(path) as fh:
        data = json.load(fh)
    quads, diffs = data["quads"], data["diffs"]
    checked = bad = fallbacks = 0
    problems = []

    def report(msg):
        nonlocal bad
        bad += 1
        if len(problems) < 20:
            problems.append(msg)

    for q in quads:
        for der in q["derivations"]:
            target = der["target"]
            first = q["n"] == 1
            src = der if first else diffs[str(der["diff"])]
            base = der["base"]
            want = target if first else der["diff"]
            # additive way
            checked += 1
            if first:
                if royal_value(der["royal"]) != target:
                    report(f"{target}: royal text {der['royal']} does not evaluate")
            else:
                rv = royal_value(src["royal"])
                if rv != src["royal_value"]:
                    report(f"{target}: royal text mismatch")
                if base + sum(src["terms"]) + rv != target:
                    report(f"{target}: additive arithmetic")
                if len(set(src["terms"])) != len(src["terms"]) or base in src["terms"]:
                    report(f"{target}: additive members not distinct")
                if any(t >= target for t in src["terms"]):
                    report(f"{target}: additive term not below target")
            # M, E1, E2
            for way in ("mul", "exp", "expv"):
                e = src.get(way)
                checked += 1
                if e is None:
                    report(f"{target}: missing {way}")
                    continue
                if e.get("fallback"):
                    fallbacks += 1
                members = lc.ops_members(e["terms"])
                if lc.ops_value(e["terms"]) != want:
                    report(f"{target}: {way} arithmetic")
                if len(set(members)) != len(members):
                    report(f"{target}: {way} members not distinct")
                if base is not None and base in members:
                    report(f"{target}: {way} uses the base")
                if any(m >= target for m in members if m not in ROYAL):
                    report(f"{target}: {way} member not below target")
            # M1, E3: the whole prime, no base term
            for way in ("mul_nb", "exp_nb"):
                e = der.get(way)
                checked += 1
                if e is None:
                    report(f"{target}: missing {way}")
                    continue
                terms = lc.ops_parse(e)               # stored as text
                members = lc.ops_members(terms)
                if lc.ops_value(terms) != target:
                    report(f"{target}: {way} arithmetic")
                if len(set(members)) != len(members):
                    report(f"{target}: {way} members not distinct")
                if any(m >= target for m in members if m not in ROYAL):
                    report(f"{target}: {way} member not below target")
    sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
    print(f"file      : {os.path.basename(path)}  ({os.path.getsize(path):,} bytes)")
    print(f"sha256    : {sha}")
    print(f"quads     : {len(quads):,}  (largest first prime {quads[-1]['primes'][0]:,})")
    print(f"equations : {checked:,} checked, {bad} bad, {fallbacks} fallback flags")
    for p in problems:
        print("  problem:", p)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "qarray_1e9.json"))
