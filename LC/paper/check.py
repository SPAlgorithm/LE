#!/usr/bin/env python3
"""Independent re-verification of every equation stored by lc.py.

    python3 check.py qarray_1e9.json

For the first prime of every quad it checks the additive way (base + quad
primes + royal expression), the multiplicative way and both exponential
ways, and the two base-free ways M1 and E3 (the whole prime from members
below it): arithmetic, distinct members, base never used as a term, every
term below the target.  Every royal expression must use each of 2, 3, 5, 7
at most once, with + and *, and multiply at most two of them.  For the
other three primes of a quad it checks the fixed forms

    p+2 = p + 2        p+6 = p + (2*3)        p+8 = (p+6) + 2

It also counts fallback flags and prints the SHA-256 of the dataset so a
reader can confirm the file is the published one.
"""
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import lc  # noqa: E402

ROYAL = set(lc.ROYAL)
# A royal expression: atoms and two-member products, joined by " + ".
ROYAL_OK = re.compile(r"^(\d+|\(\d+\*\d+\))( \+ (\d+|\(\d+\*\d+\)))*$")
# The fixed forms of the second, third and fourth prime of a quad:
# (index of the base within the quad, difference, royal text).
CANON = ((0, 2, "2"), (0, 6, "(2*3)"), (2, 2, "2"))
CANON_KEYS = {"target", "base", "diff", "reused"}


def royal_value(text):
    """Evaluate a royal expression string with plain integer arithmetic."""
    return eval(text, {"__builtins__": {}}, {}) if text else 0


def royal_ok(text):
    """+ and * over distinct royal members, no product of more than two."""
    if not text:
        return True
    if not ROYAL_OK.match(text):
        return False
    members = [int(x) for x in re.findall(r"\d+", text)]
    return all(m in ROYAL for m in members) and len(set(members)) == len(members)


def main(path):
    with open(path) as fh:
        data = json.load(fh)
    quads, diffs = data["quads"], data["diffs"]
    checked = bad = fallbacks = skipped = closings = canonical = 0
    problems = []

    def report(msg):
        nonlocal bad
        bad += 1
        if len(problems) < 20:
            problems.append(msg)

    def check_closing(text, where):
        nonlocal closings
        closings += 1
        if not royal_ok(text):
            report(f"{where}: royal expression {text!r} breaks the rule")

    # Every royal expression in the file, wherever it is stored.
    for key, entry in diffs.items():
        check_closing(entry.get("royal"), f"diff {key}")
    for q in quads:
        for der in q["derivations"]:
            if q["n"] == 1:
                check_closing(der.get("royal"), der["target"])
                for alt in der.get("alternatives", []):
                    check_closing(alt, f"{der['target']} alternative")
            elif "own" in der:
                check_closing(der["own"].get("royal"), f"{der['target']} own")

    for q in quads:
        for i, der in enumerate(q["derivations"]):
            target = der["target"]
            first = q["n"] == 1
            if not first and i >= 1:
                # p+2, p+6, p+8: the fixed form, nothing searched, nothing else stored
                canonical += 1
                bi, d, royal = CANON[i - 1]
                base = q["primes"][bi]
                if set(der) != CANON_KEYS:
                    report(f"{target}: later prime stores {sorted(set(der) - CANON_KEYS)}")
                if der.get("base") != base or der.get("diff") != d or target != base + d:
                    report(f"{target}: expected {base} + {d}")
                src = diffs.get(str(d))
                if src is None:
                    report(f"{target}: no shared entry for difference {d}")
                elif src["terms"] != [] or src["royal"] != royal or src["royal_value"] != d:
                    report(f"{target}: shared entry {d} is not the fixed form")
                # only the first quad to reach 103 and 107 creates the entries
                if der.get("reused") != (target not in (103, 107)):
                    report(f"{target}: reused flag")
                continue
            src = der if first else lc.der_entry(der, diffs)
            if src is None:                  # --one-per-quad leaves some members
                skipped += 1                 # without any derivation at all
                continue
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
    for d, first_target in ((2, 103), (6, 107)):
        entry = diffs.get(str(d))
        if entry is None or entry.get("first") != [2, first_target]:
            report(f"difference {d}: should first appear at quad 2 ({first_target})")
        elif lc.ops_value(entry["mul"]["terms"]) != d or lc.ops_value(entry["exp"]["terms"]) != d:
            report(f"difference {d}: M / E forms")
    sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
    print(f"file      : {os.path.basename(path)}  ({os.path.getsize(path):,} bytes)")
    print(f"sha256    : {sha}")
    print(f"quads     : {len(quads):,}  (largest first prime {quads[-1]['primes'][0]:,})")
    print(f"equations : {checked:,} checked, {bad} bad, {fallbacks} fallback flags"
          + (f", {skipped} members without a derivation" if skipped else ""))
    print(f"closings  : {closings:,} royal expressions checked "
          "(+ and * over distinct members of 2, 3, 5, 7; products of two)")
    print(f"by rule   : {canonical:,} later primes checked against "
          "p + 2, p + (2*3), (p+6) + 2")
    for p in problems:
        print("  problem:", p)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "qarray_1e9.json"))
