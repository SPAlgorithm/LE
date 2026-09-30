#!/usr/bin/env python3
"""Independent re-verification of every equation stored by lc.py.

    python3 check.py qarray_1e9.json

For the first prime of every quad it checks the additive way (base + quad
primes + royal expression), the multiplicative way and both exponential
ways, and the two base-free ways M1 and E3 (the whole prime from members
below it): arithmetic, distinct members, base never used as a term, every
term below the target.  Every royal expression must use each of 2, 3, 5, 7
at most once, with + and *, and multiply at most two of them.  Every
stored additive equation is also re-derived here with a search of its own,
and must agree: a pure equation (no royal part) must be a shortest sum of
distinct earlier primes, the base excluded, with the larger primes preferred
among equally short sums; a royal closing is allowed only when no pure sum
of at most eight primes exists, and its primes must then follow the
largest-first rule (from the remainder take the largest unused earlier
prime not above it, again and again; back up when a choice leads nowhere).
For the other three primes of a quad it checks the fixed forms

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


ROYAL_VALUES = set(lc.ROYAL_BEST)      # the 30 values of + and * expressions


def largest_first(diff, pool, excluded):
    """Independent re-derivation of the rule the chain stores its additive
    equations by.  pool: ascending earlier primes; excluded: the base when
    it may not be a term.  Returns the terms, or None."""
    pool = [p for p in pool if p <= diff]
    used = {excluded} if excluded is not None else set()
    budget = [2_000_000]

    def go(rem, hi):
        if rem == 0:
            return []
        i = hi - 1
        while i >= 0 and pool[i] > rem:
            i -= 1
        while i >= 0:
            p = pool[i]
            if p not in used:
                budget[0] -= 1
                if budget[0] < 0:
                    return None
                used.add(p)
                rest = go(rem - p, i)
                used.discard(p)
                if rest is not None:
                    return [p] + rest
            i -= 1
        return [] if rem in ROYAL_VALUES else None   # royal only when no prime fits

    return go(diff, len(pool))


def shortest_pure(diff, pool, excluded):
    """Independent shortest-sum search: the fewest distinct earlier primes
    (2, 4, 6 or 8 of them) that add up to diff exactly, tried in descending
    order so that the first solution found is the one with the larger
    primes.  pool: ascending earlier primes; excluded: the base.  Returns
    the terms, or None when no pure sum of at most eight primes exists."""
    cand = [p for p in pool if p <= diff and p != excluded]
    cand.reverse()                                   # descending
    suffix = [0] * (len(cand) + 1)                   # suffix[i] = sum(cand[i:])
    for i in range(len(cand) - 1, -1, -1):
        suffix[i] = suffix[i + 1] + cand[i]
    budget = [2_000_000]

    def go(rem, i, count):
        if count == 0:
            return [] if rem == 0 else None
        while i < len(cand) and cand[i] > rem:
            i += 1
        for j in range(i, len(cand) - count + 1):
            budget[0] -= 1
            if budget[0] < 0:
                return None
            p = cand[j]
            if p * count < rem and suffix[j] < rem:
                return None                          # too small from here on
            rest = go(rem - p, j + 1, count - 1)
            if rest is not None:
                return [p] + rest
        return None

    for count in (2, 4, 6, 8):
        terms = go(diff, 0, count)
        if terms is not None:
            return terms
    return None


def main(path):
    with open(path) as fh:
        data = json.load(fh)
    quads, diffs = data["quads"], data["diffs"]
    checked = bad = fallbacks = skipped = closings = canonical = 0
    rederived = 0
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
    # Every stored additive equation, re-derived by the stored-form rule:
    # a shortest pure sum (base excluded) when one exists, otherwise the
    # largest-first form with a royal value.
    all_primes = [p for q in quads for p in q["primes"]]
    n_pure = n_royal = 0

    def verify(label, diff, pool, base, terms, rv, royal, fallback_excluded):
        nonlocal n_pure, n_royal
        pure = shortest_pure(diff, pool, base)
        if not royal:
            if pure is None or pure != terms or rv != 0:
                report(f"{label}: stored {terms} + {rv}, shortest pure sum is {pure}")
            else:
                n_pure += 1
            return
        if pure is not None:
            report(f"{label}: stored royal closing {terms} + {rv}, but the pure sum {pure} exists")
            return
        want = largest_first(diff, pool, fallback_excluded)
        if want is None or want != terms or diff - sum(want) != rv:
            report(f"{label}: stored {terms} + {rv}, largest-first rule gives {want}")
        else:
            n_royal += 1

    for key, entry in diffs.items():
        n, target = entry["first"]
        if n == 2 and target in (103, 107):
            continue                              # the fixed forms
        pool = all_primes[:4 * (n - 1)]           # quads 1 .. n-1
        rederived += 1
        diff = int(key)
        verify(f"difference {key}", diff, pool, target - diff, entry["terms"],
               entry["royal_value"], entry.get("royal"), None)   # fallback: base allowed
    for q in quads:
        der = q["derivations"][0]
        if "own" not in der:
            continue
        pool = all_primes[:4 * (q["n"] - 1)]
        rederived += 1
        own = der["own"]
        verify(f"{der['target']} own", der["diff"], pool, der["base"], own["terms"],
               own["royal_value"], own.get("royal"), der["base"])
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
    print(f"stored    : {rederived:,} additive equations re-derived "
          f"({n_pure:,} shortest pure sums, {n_royal:,} royal closings by the "
          "largest-first rule with no pure sum of at most eight primes)")
    for p in problems:
        print("  problem:", p)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "qarray_1e9.json"))
