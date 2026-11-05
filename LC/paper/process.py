#!/usr/bin/env python3
"""The chain rule as a process: one pass, and with retreat.

    python3 paper/process.py paper/qarray_1e9.json
    python3 paper/process.py 10Billion/qarray_1e10.json

For every gap D = p_k - (p_{k-1} + 8), k >= 2, over the members of Q_1 .. Q_{k-1} below D
(the base never a term):
  one pass   take the largest unused member not above the remainder, repeat while any fits;
             closes if the remainder is 0 or a royal value (Definition 3 of the paper).
  retreat    when the close fails, undo the last member and take the next smaller one that
             fits (depth first, largest first); counts the retreats until the first close.
Prints how often one pass closes, the remainders it leaves when it does not, the retreat
counts and the number of members used.  Standard library only.
"""
import bisect, itertools, json, sys
from collections import Counter

def royal_values():
    out = set()
    def parts(items):
        if not items:
            yield []
            return
        a, rest = items[0], items[1:]
        for p in parts(rest):
            yield [(a,)] + p
        for i, b in enumerate(rest):
            for p in parts(rest[:i] + rest[i + 1:]):
                yield [(a, b)] + p
    for r in range(1, 5):
        for sub in itertools.combinations((2, 3, 5, 7), r):
            for p in parts(list(sub)):
                if sum(len(t) == 2 for t in p) <= 2:
                    out.add(sum(t[0] if len(t) == 1 else t[0] * t[1] for t in p))
    return out

R = royal_values() | {0}
MAX_MEMBERS, MAX_NODES = 16, 300000

def one_pass(D, pool):
    rem = D
    for m in reversed(pool):
        if m <= rem:
            rem -= m
    return rem

def retreat(D, pool):
    """(members, retreats) of the first close, or (None, retreats) within the caps."""
    sys.setrecursionlimit(10000)
    back = nodes = 0
    def rec(rem, hi, depth):
        nonlocal back, nodes
        nodes += 1
        if nodes > MAX_NODES:
            return None
        i = bisect.bisect_right(pool, rem, 0, hi) - 1
        if i < 0:
            return [] if rem in R else None
        if depth >= MAX_MEMBERS:
            return None
        while i >= 0:
            r = rec(rem - pool[i], i, depth + 1)
            if r is not None:
                return [pool[i]] + r
            back += 1
            i -= 1
        return None
    return rec(D, len(pool), 0), back

def main(path):
    quads = json.load(open(path))["quads"]
    f = [q["primes"][0] for q in quads]
    members = sorted(p for q in quads for p in q["primes"])
    fails, closes, backs, used, unsolved, first_fail = Counter(), 0, Counter(), Counter(), 0, None
    for k in range(1, len(f)):
        base = f[k - 1] + 8
        D = f[k] - base
        pool = [m for m in members[:bisect.bisect_left(members, D)] if m != base]
        rem = one_pass(D, pool)
        if rem in R:
            closes += 1
        else:
            fails[rem] += 1
            if first_fail is None:
                first_fail = (k + 1, f[k], D, rem)
        terms, back = retreat(D, pool)
        if terms is None:
            unsolved += 1
        else:
            backs[back] += 1
            used[len(terms)] += 1
    n = len(f) - 1
    print(f"{path}: {n:,} gaps")
    print(f"one pass closes {closes:,} ({closes / n:.1%}), fails {n - closes:,}; failing remainders "
          + ", ".join(f"{r} ({c:,})" for r, c in sorted(fails.items())) + f"; first failure Q{first_fail[0]} = {first_fail[1]} (D = {first_fail[2]}, remainder {first_fail[3]})")
    print("with retreat: unsolved within caps", unsolved, "; retreats needed " + ", ".join(f"{b}: {c:,}" for b, c in sorted(backs.items())))
    print("members used " + ", ".join(f"{m}: {c:,}" for m, c in sorted(used.items())) + f"; max {max(used)}")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "paper/qarray_1e9.json")
