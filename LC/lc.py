#!/usr/bin/env python3
"""
LC - quad chain builder.

Rules
-----
* The q-array starts with the royal / initial quad  2, 3, 5, 7.
* Every later quad is the next group of four primes ending in 1, 3, 7, 9
  that sit together:  p, p+2, p+6, p+8   (a prime quadruplet).
* Quad 1 (11, 13, 17, 19) is written purely with + and * over royal members.
* Every prime of quad k (k >= 2) is derived as

        one member of the LAST quad (quad k-1)        -> the "base"
      + a difference, written as
            members of earlier non-royal quads, every prime used at most once
          + optionally an expression in royal members using only + and *

  Quad members are exhausted with addition before any multiplication among
  royal members is used, and nested royal expressions are a last resort.
  Candidates are ranked by (depth of the royal part, number of
  multiplications, number of terms, larger primes first):
      13001 = 9439 + 3461 + 101                      plain addition, 2 terms
      1871  = 1489 + 109 + 107 + 103 + 19 + 17 + 13 + 11 + 3
                                                     addition only, any length
      101   = 19 + 17 + 13 + 11 + (5*7) + (2*3)      flat products, only when
                                                     addition cannot reach it
      not   19 + 17 + (5*(7 + (2*3)))                nested, rejected

Three ways
----------
Besides the additive way (A, the default) every difference also gets
* M, multiplicative: any members (quad primes and royal members, each used
  once) may be multiplied in pairs, and multiplication is preferred over
  addition:            101 = 19 + (17*3) + (13*2) + 5
* E, exponential: members may also be raised to a member power; powers are
  preferred, then products, then addition.  Two options are shown:
      E1  largest base first      5651 = 3469 + (19^2) + (11^3) + (17*7) + ...
      E2  largest power first     5651 = 3469 + (2^11) + (19*5) + (13*3)
                       101 = 19 + (7^2) + (11*3)      (same under both)
Both follow the user's greedy: take the largest unused member, combine it
with the largest member that still fits (power, then product), repeat; plain
addition only when nothing can be multiplied; backtrack on a dead end.
* M1: the M search for the WHOLE prime, without the base term.  The pool
  is every quad prime below the target plus the royal members, so the
  biggest products do the work:
      M1  854921 = (427249*2) + (109*3) + (17*5) + 11
* E3: powers first, one at a time: the largest b^e below the prime (base
  and exponent distinct members), then again the largest power below what
  is left as long as it covers at least half of it; the rest the additive
  way: quad primes added, largest first, closed by a flat royal +/*
  expression:
      E3  854921 = (829^2) + (11^5) + (17^3) + 1489 + 107 + 101 + 19
      E3  19497221 = (11^7) + (2^13) + 829 + 827 + 199 + 3
      E3  31204931 = (11^7) + (3259^2) + (103^3) + 3467 + 193 + 191 + 101
  (7^7 would be closer to 854921 but uses 7 twice.)  If no choice of
  primes closes the remainder, the chain loses its last power, and finally
  the next largest first power is tried.
  -M prints M and M1, -E prints E1, E2 and E3; a line identical to an
  earlier one for the same prime is not repeated.

Storage (qarray.json next to this script)
-----------------------------------------
* "quads": for every quad its primes and, per prime, the base and the
  difference  (191 = 109 + 82  is stored as base 109, diff 82).
* "diffs": one entry per UNIQUE difference with the equations that build
  the difference (82 -> terms 17 + 13 + 11 + (5*7) + (2*3);  "mul", "exp"
  and "expv" hold the M, E1 and E2 term lists).  When a later quad produces
  a difference that is already in the table its equations are reused; only
  a new difference triggers a new search.
* M1 and E3 depend on the prime itself, not on the difference, so they are
  stored with the member ("mul_nb", "exp_nb" in the derivation record).

Usage
-----
    python3 lc.py                 # asks for a number
    python3 lc.py 25              # show the first 25 quads after the royal quad
    python3 lc.py 2000 2005       # quads 2000 to 2005 (both ends included)
    python3 lc.py --upto 35551421 # every quad whose first prime is <= value
    python3 lc.py 25 -M           # multiplicative ways M, M1;  -E exponential E1, E2, E3
    python3 lc.py 25 -AME         # all ways, labeled A:, M:, M1:, E1:, E2:, E3:
    python3 lc.py 2000 -o         # only the 2000th quad (-one and --only work too)
    python3 lc.py 2000 2005 -o    # only quads 2000 and 2005
    python3 lc.py 2000 2005 1223 -o    # only those three, in the order typed
    python3 lc.py 2000 2005 1223 -o -s # the same three, sorted
    python3 lc.py --upto 35551421 -o   # only the last quad at or below the value
    python3 lc.py 1 200 -c 5      # of quads 1 to 200, only the 5-column equations
    python3 lc.py 1 200 -c 3 8    # ... anything from three to eight columns
    python3 lc.py 25 --all        # equations for all four primes, not just the first
    python3 lc.py 25 -v           # also show which quad each term came from
    python3 lc.py 25 --one-per-quad   # stricter rule: at most one member per quad
    python3 lc.py -d 53           # derive any integer from the quad members below it:
                                  #   53 = 19 + 17 + 13 + 7 - 3   (quad primes added,
                                  #   + - * only among royal members)
    python3 lc.py -d 53 83        # the same for every integer from 53 to 83
"""

import argparse
import bisect
import json
import math
import os
import sys
import time

ROYAL = (2, 3, 5, 7)
FORMAT = 13
# Folder that holds the cache: next to the script, or next to the binary
# when packaged with PyInstaller.
if getattr(sys, "frozen", False):
    HERE = os.path.dirname(os.path.abspath(sys.executable))
else:
    HERE = os.path.dirname(os.path.abspath(__file__))
CACHE_DEFAULT = os.path.join(HERE, "qarray.json")
CACHE_STRICT = os.path.join(HERE, "qarray_one_per_quad.json")


# --------------------------------------------------------------------------
# Royal expressions: every value reachable from distinct royal members
# --------------------------------------------------------------------------
def royal_expressions(allow_minus=False):
    """Map value -> list of expression strings (best first).

    Expressions use each royal member at most once and the operators
    + and * (and binary - when allow_minus is set)."""
    n = len(ROYAL)
    memo = {}

    # An expression is (text, top, parts): top is 'atom', '+', '*' or '-';
    # parts lists the (value, text, top) operands of a flat sum / product so
    # that 2 + 5 + 7 and 5 + 2 + 7 collapse into one canonical string.
    def flat(val, text, top, parts, op):
        return parts if top == op else [(val, text, top)]

    def combine(op, a, b):
        # Layout: larger terms first (like the rest of the equation), every
        # product wrapped in parentheses, e.g.  (5*7) + (2*3)
        va, ta, topa, pa = a
        vb, tb, topb, pb = b
        parts = flat(va, ta, topa, pa, op) + flat(vb, tb, topb, pb, op)
        if op == "+":
            parts.sort(key=lambda t: (-t[0], t[1]))      # big terms first
        else:
            parts.sort(key=lambda t: (t[0], t[1]))       # (2*3), (5*7)
        if op == "+":
            text = " + ".join(t for _, t, _ in parts)
            return va + vb, text, "+", parts
        text = "(" + "*".join("(" + t + ")" if tp == "+" else t
                              for _, t, tp in parts) + ")"
        return va * vb, text, "*", parts

    def exprs(mask):
        if mask in memo:
            return memo[mask]
        members = [ROYAL[i] for i in range(n) if mask >> i & 1]
        res = {}
        if len(members) == 1:
            v = members[0]
            res[v] = {(str(v), "atom", ((v, str(v), "atom"),))}
            memo[mask] = res
            return res
        sub = (mask - 1) & mask
        while sub:
            other = mask ^ sub
            if sub < other:                      # each unordered split once
                left, right = exprs(sub), exprs(other)
                for va, sa in left.items():
                    for vb, sb in right.items():
                        for (ta, topa, pa) in sa:
                            for (tb, topb, pb) in sb:
                                if topa == "-" or topb == "-":
                                    continue      # minus only outermost
                                a = (va, ta, topa, list(pa))
                                b = (vb, tb, topb, list(pb))
                                for op in "+*":
                                    val, text, top, parts = combine(op, a, b)
                                    res.setdefault(val, set()).add((text, top, tuple(parts)))
                                if allow_minus and va != vb:
                                    big, small = (a, b) if va > vb else (b, a)
                                    rhs = "(" + small[1] + ")" if small[2] == "+" else small[1]
                                    res.setdefault(big[0] - small[0], set()).add(
                                        (f"{big[1]} - {rhs}", "-", ()))
            sub = (sub - 1) & mask
        memo[mask] = res
        return res

    table = {}
    for mask in range(1, 1 << n):
        for val, forms in exprs(mask).items():
            table.setdefault(val, set()).update(t for t, _, _ in forms)
    return {v: sorted(forms, key=lambda s: (len(s), s)) for v, forms in table.items()}


def paren_depth(text):
    depth = deepest = 0
    for ch in text:
        if ch == "(":
            depth += 1
            deepest = max(deepest, depth)
        elif ch == ")":
            depth -= 1
    return deepest


def top_terms(text):
    """Number of operands of the outermost sum (1 for an atom or product)."""
    depth, count = 0, 1
    for i, ch in enumerate(text):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif depth == 0 and text.startswith(" + ", i):
            count += 1
    return count


def royal_key(text):
    """(nesting depth, number of multiplications, top-level terms).
    Lower is better: plain addition first, then as few multiplications as
    possible, then fewer terms."""
    return (paren_depth(text), text.count("*"), top_terms(text))


ROYAL_PT = royal_expressions(False)          # + and * only (the rule)
ROYAL_PM = royal_expressions(True)           # + * - (alternatives for quad 1)
# value -> {key: shortest expression with that key}
ROYAL_FORMS = {}
for _v, _forms in ROYAL_PT.items():
    for _f in _forms:                        # forms are sorted shortest first
        ROYAL_FORMS.setdefault(_v, {}).setdefault(royal_key(_f), _f)
ROYAL_BEST = {v: forms[min(forms)] for v, forms in ROYAL_FORMS.items()}
MIN_ROYAL = min(ROYAL_BEST)
# key -> set of royal values that have an expression with that key
ROYAL_SETS = {}
for _v, _forms in ROYAL_FORMS.items():
    for _k in _forms:
        ROYAL_SETS.setdefault(_k, set()).add(_v)
MAX_DEPTH = max(k[0] for k in ROYAL_SETS)
MAX_MULTS = max(k[1] for k in ROYAL_SETS)


# --------------------------------------------------------------------------
# Royal expressions with minus allowed anywhere (used by -d / derive):
# every value 0 <= v <= 210 reachable with + - * over distinct royal members
# --------------------------------------------------------------------------
def top_terms_signed(text):
    """Operands of the outermost sum/difference (1 for an atom or product)."""
    depth, count = 0, 1
    for i, ch in enumerate(text):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif depth == 0 and (text.startswith(" + ", i) or text.startswith(" - ", i)):
            count += 1
    return count


def royal_expressions_signed():
    """Map value -> best expression text over distinct royal members with
    +, - and *, minus allowed anywhere.  Best = fewest multiplications, then
    fewest minus signs, then fewest terms, then least nesting, then shortest.
    Only values 0..210 are kept."""
    n = len(ROYAL)
    memo = {}

    def wrap(text, top):                       # operand of * or right of -
        return "(" + text + ")" if top in "+-" else text

    # entry: (value, text, top, parts); parts = operands of a flat sum or
    # product so that 7 + 5 + 2 and 5 + 2 + 7 collapse to one canonical text
    def exprs(mask):
        if mask in memo:
            return memo[mask]
        members = [ROYAL[i] for i in range(n) if mask >> i & 1]
        res = set()
        if len(members) == 1:
            v = members[0]
            res.add((v, str(v), "atom", ((v, str(v), "atom"),)))
            memo[mask] = res
            return res
        sub = (mask - 1) & mask
        while sub:
            other = mask ^ sub
            if sub < other:
                for a in exprs(sub):
                    for b in exprs(other):
                        va, ta, topa, pa = a
                        vb, tb, topb, pb = b
                        # sum: flat, big terms first; a difference is never a
                        # summand because x + (a - b) is written (x + a) - b
                        if topa != "-" and topb != "-":
                            parts = tuple(sorted(
                                (pa if topa == "+" else ((va, ta, topa),))
                                + (pb if topb == "+" else ((vb, tb, topb),)),
                                key=lambda t: (-t[0], t[1])))
                            res.add((va + vb, " + ".join(t for _, t, _ in parts),
                                     "+", parts))
                        # product: flat, small factors first, sums wrapped
                        factors = tuple(sorted(
                            (pa if topa == "*" else ((va, ta, topa),))
                            + (pb if topb == "*" else ((vb, tb, topb),)),
                            key=lambda t: (t[0], t[1])))
                        res.add((va * vb,
                                 "(" + "*".join(wrap(t, tp) for _, t, tp in factors) + ")",
                                 "*", factors))
                        # differences, both orders; the left operand is
                        # inlined (left-associative reading keeps the value)
                        for (x, tx, topx), (y, ty, topy) in (((va, ta, topa), (vb, tb, topb)),
                                                             ((vb, tb, topb), (va, ta, topa))):
                            text = f"{tx} - {wrap(ty, topy)}"
                            res.add((x - y, text, "-", ((x - y, text, "-"),)))
            sub = (sub - 1) & mask
        memo[mask] = res
        return res

    def rank(text):
        # flat before nested, then fewest multiplications, fewest minus
        # signs, fewest terms:  (3*7) - 5  rather than  (2*(5 + 3))
        return (paren_depth(text), text.count("*"), text.count(" - "),
                top_terms_signed(text), len(text), text)

    best = {}
    for mask in range(1, 1 << n):
        for v, text, _, _ in exprs(mask):
            if 0 <= v <= 210 and (v not in best or rank(text) < rank(best[v])):
                best[v] = text
    return best


ROYAL_SIGNED = royal_expressions_signed()
# values whose best form is flat (no product containing a sum); -d closes
# with one of these whenever the quad primes can be chosen to allow it
ROYAL_SIGNED_FLAT = {v: t for v, t in ROYAL_SIGNED.items() if paren_depth(t) <= 1}
# the coverage argument in the paper relies on 0..38 being reachable
assert all(v in ROYAL_SIGNED for v in range(39)), "royal coverage broken"


# --------------------------------------------------------------------------
# M / E term lists:  ["p", 5]  ["*", 17, 3]  ["^", 7, 2]
# --------------------------------------------------------------------------
def ops_value(terms):
    total = 0
    for t in terms:
        if t[0] == "p":
            total += t[1]
        elif t[0] == "*":
            total += t[1] * t[2]
        else:
            total += t[1] ** t[2]
    return total


def ops_text(terms):
    parts = []
    for t in terms:
        if t[0] == "p":
            parts.append(str(t[1]))
        elif t[0] == "*":
            parts.append(f"({t[1]}*{t[2]})")
        else:
            parts.append(f"({t[1]}^{t[2]})")
    return " + ".join(parts)


def ops_members(terms):
    out = []
    for t in terms:
        out.extend(t[1:])
    return out


def additive_to_ops(entry):
    """Convert an additive diffs entry to M terms (plain primes, royal flat
    sums and 2-member royal products).  None if the royal part is nested or
    has a product of three members."""
    terms = [["p", p] for p in entry["terms"]]
    text = entry.get("royal")
    if text:
        if paren_depth(text) > 1:
            return None
        for part in text.split(" + "):
            factors = [int(x) for x in part.strip("()").split("*")]
            if len(factors) == 1:
                terms.append(["p", factors[0]])
            elif len(factors) == 2:
                terms.append(["*", max(factors), min(factors)])
            else:
                return None
    return terms


# Exact reachability of small remainders.  Members >= 101 cannot take part
# in a remainder < 101, so a remainder below SMALL_LIMIT is reachable iff it
# is reachable from the still-unused members among SMALL with the mode's
# vocabulary.  REACH[mode][mask] is a bitset over values 0..100.
SMALL = (2, 3, 5, 7, 11, 13, 17, 19)
SMALL_LIMIT = 101


def _build_reach(mode):
    n = len(SMALL)
    keep = (1 << SMALL_LIMIT) - 1
    memo = [None] * (1 << n)

    def rec(mask):
        if memo[mask] is not None:
            return memo[mask]
        bits = 1                                   # 0 is always reachable
        idx = [i for i in range(n) if mask >> i & 1]
        for i in idx:
            p = SMALL[i]
            rest = mask & ~(1 << i)
            bits |= (rec(rest) << p) & keep
            for j in idx:
                if j == i:
                    continue
                q = SMALL[j]
                rest2 = rest & ~(1 << j)
                if q < p:
                    bits |= (rec(rest2) << (p * q)) & keep
                if mode == "exp" and p ** q < SMALL_LIMIT:
                    bits |= (rec(rest2) << (p ** q)) & keep
        memo[mask] = bits
        return bits

    for mask in range(1 << n):
        rec(mask)
    return memo


REACH = {"mul": _build_reach("mul"), "exp": _build_reach("exp")}


# --------------------------------------------------------------------------
# Prime quadruplets p, p+2, p+6, p+8  (segmented sieve)
# --------------------------------------------------------------------------
def simple_sieve(limit):
    flags = bytearray([1]) * (limit + 1)
    flags[0:2] = b"\x00\x00"
    for i in range(2, math.isqrt(limit) + 1):
        if flags[i]:
            flags[i * i::i] = bytes(len(range(i * i, limit + 1, i)))
    return [i for i, f in enumerate(flags) if f]


def quadruplets_from(start, segment=1 << 20):
    """Yield prime quadruplets (p, p+2, p+6, p+8) with p >= start, ascending.
    Every quadruplet above 5 has p = 11 (mod 30), so only those p are tested."""
    lo = max(start, 11)
    base, base_limit = [], 0
    while True:
        hi = lo + segment
        top = hi + 8                          # sieve [lo, top)
        need = math.isqrt(top) + 1
        if need > base_limit:
            base_limit = max(need, 2 * base_limit, 1000)
            base = simple_sieve(base_limit)
        seg = bytearray([1]) * (top - lo)
        for p in base:
            if p * p >= top:
                break
            first = max(p * p, (lo + p - 1) // p * p)
            seg[first - lo::p] = bytes(len(range(first - lo, top - lo, p)))
        p = lo + (11 - lo) % 30
        while p < hi:
            i = p - lo
            if seg[i] and seg[i + 2] and seg[i + 6] and seg[i + 8]:
                yield (p, p + 2, p + 6, p + 8)
            p += 30
        lo = hi


# --------------------------------------------------------------------------
# Difference search:  diff = (quad primes) + (royal expression)
# --------------------------------------------------------------------------
class Deriver:
    """Ranks candidate equations for a difference by

        1. depth of the royal part: 0 = none or plain addition of royal
           members, 1 = flat products such as (5*7) + 3, 2 and 3 =
           products that contain sums (nested parentheses);
        2. number of multiplications in the royal part - addition takes
           precedence, multiply only when addition is not possible
           (1871 = 1489 + 199 + 109 + 19 + 17 + (5*7) + 3, one product,
           rather than ... + 19 + 13 + (2*3*7) with two);
        3. total number of terms (quad primes + top-level royal terms) -
           no matter how long, an addition-only equation beats one with a
           product (1871 = 1489 + 109 + 107 + 103 + 19 + 17 + 13 + 11 + 3);
        4. larger primes first, compared term by term - so a quad's
           9-member is used before its 7, 3 and 1 members
           (3461 = 3259 + 199 + 3, not 3259 + 191 + 11)."""

    MAX_TERMS = 16

    def __init__(self, one_per_quad=False, node_limit=300_000):
        self.one_per_quad = one_per_quad
        self.node_limit = node_limit

    def solve(self, diff, avail, base, quad_of):
        """avail: ascending list of primes of all earlier quads (incl. last).
        base: the last-quad member already used, never a term.
        Returns (terms, royal_value, royal_text) or None
        (royal_value 0 / royal_text None = no royal part)."""
        if diff < MIN_ROYAL:
            return None
        cand = [p for p in avail[:bisect.bisect_right(avail, diff)] if p != base]
        prefix = [0]
        for p in cand:
            prefix.append(prefix[-1] + p)
        base_quad = quad_of[base]

        for depth in range(0, MAX_DEPTH + 1):
            for mults in range(0, MAX_MULTS + 1):
                if (depth == 0) != (mults == 0):
                    continue
                for total in range(1, self.MAX_TERMS + 1):
                    best = None
                    for k in range(total, -1, -1):          # quad primes
                        royal_terms = total - k
                        if royal_terms == 0:
                            if depth != 0:
                                continue
                            allowed, key = {0}, None
                        else:
                            key = (depth, mults, royal_terms)
                            allowed = ROYAL_SETS.get(key)
                            if not allowed:
                                continue
                        terms = self._fixed(diff, k, allowed, cand, prefix,
                                            quad_of, base_quad)
                        # same rank so far: larger leading primes win,
                        # so 199 + 3 beats 191 + 11
                        if terms is not None and (best is None or terms > best[0]):
                            best = (terms, key)
                    if best is not None:
                        terms, key = best
                        rv = diff - sum(terms)
                        text = ROYAL_FORMS[rv][key] if rv else None
                        return terms, rv, text
        # fall back to the greedy chain (never needed so far)
        for stop_first in (False, True):
            terms = self._search(diff, avail, base, quad_of, stop_first)
            if terms is not None:
                rv = diff - sum(terms)
                return terms, rv, ROYAL_BEST[rv] if rv else None
        return None

    def _fixed(self, diff, count, allowed, cand, prefix, quad_of, base_quad):
        """Exactly `count` distinct primes from cand, largest first, whose
        remainder lies in `allowed`.  Returns the primes or None."""
        if count == 0:
            return [] if diff in allowed else None
        if len(cand) < count:
            return None
        r_min, r_max = min(allowed), max(allowed)
        used = {base_quad} if self.one_per_quad else None
        chosen = []
        budget = [self.node_limit]

        def ok(p):
            return used is None or quad_of[p] not in used

        def rec(rem, j, hi):
            if j == 1:
                lo_i = bisect.bisect_left(cand, rem - r_max, 0, hi)
                hi_i = bisect.bisect_right(cand, rem - r_min, 0, hi)
                for i in range(hi_i - 1, lo_i - 1, -1):
                    p = cand[i]
                    if ok(p) and (rem - p) in allowed:
                        chosen.append(p)
                        return True
                return False
            if j == 2:
                # pairs by bisect: for each larger prime find the window
                # of smaller partners that leaves an allowed remainder
                for i2 in range(hi - 1, 0, -1):
                    p2 = cand[i2]
                    if rem - r_max - p2 > cand[i2 - 1]:
                        break                 # p2 already too small
                    if not ok(p2):
                        continue
                    lo_i = bisect.bisect_left(cand, rem - r_max - p2, 0, i2)
                    hi_i = bisect.bisect_right(cand, rem - r_min - p2, 0, i2)
                    budget[0] -= 1
                    if budget[0] < 0:
                        return False
                    if used is not None:
                        used.add(quad_of[p2])
                    for i3 in range(hi_i - 1, lo_i - 1, -1):
                        p3 = cand[i3]
                        if ok(p3) and (rem - p2 - p3) in allowed:
                            chosen.append(p2)
                            chosen.append(p3)
                            return True
                    if used is not None:
                        used.discard(quad_of[p2])
                return False
            for i in range(hi - 1, j - 2, -1):
                p = cand[i]
                r2 = rem - p
                # the j-1 remaining primes are all smaller than p
                if r2 > r_max + prefix[i] - prefix[i - (j - 1)]:
                    break                     # p already too small
                if r2 < r_min + prefix[j - 1]:
                    continue                  # p too big
                if not ok(p):
                    continue
                budget[0] -= 1
                if budget[0] < 0:
                    return False
                chosen.append(p)
                if used is not None:
                    used.add(quad_of[p])
                if rec(r2, j - 1, i):
                    return True
                chosen.pop()
                if used is not None:
                    used.discard(quad_of[p])
            return False

        if rec(diff, count, len(cand)):
            return list(chosen)
        return None

    OPS_BUDGET = 50_000
    NB_BUDGET = 1_000_000        # M1 / E3: whole-chain pool, deeper search

    def _nb_pool(self, avail):
        """ROYAL + avail as one ascending list, kept between calls and only
        extended when avail grew: the no-base searches (M1 / E3) use the
        whole pool, and rebuilding it per call would dominate the run."""
        m = getattr(self, "_nb_members", None)
        k = len(m) - 4 if m else 0
        if m is None or k > len(avail) or (k and (m[4] != avail[0] or m[-1] != avail[k - 1])):
            m = list(ROYAL) + list(avail)
            self._nb_members = m
        elif k < len(avail):
            m.extend(avail[k:])
        return m

    def solve_ops(self, diff, avail, base, quad_of, mode):
        """M ("mul") or E ("exp" / "expv") way for a difference.

        Members = quad primes <= diff (base excluded) plus the royal members,
        each usable once.  With base None and diff above every prime of
        avail (M1 / E3) the pool is the whole q-array, cached in _nb_pool.  Depth-first in a fixed key order, so every
        combination of terms is tried once and the first complete one wins:
            powers  b^e   (E only)  "exp":  b descending, then e descending
                                    "expv": value descending, then b
            products a*m            a descending, then m descending
            plain    p              p descending
        Returns a list of tagged terms or None when the node budget runs out.
        """
        nobase = base is None and (not avail or diff > avail[-1])
        if nobase:
            members = self._nb_pool(avail)            # M1 / E3: whole pool, cached
        else:
            primes = [p for p in avail[:bisect.bisect_right(avail, diff)] if p != base]
            members = list(ROYAL) + primes            # ascending
        n = len(members)
        small_idx = []
        for s in SMALL:
            i = bisect.bisect_left(members, s)
            small_idx.append(i if i < n and members[i] == s else None)
        exp_mode = mode in ("exp", "expv")
        by_value = mode == "expv"                     # largest power first
        reach = REACH["exp" if exp_mode else "mul"]
        one_per = self.one_per_quad
        used_quads = set()
        if one_per and base is not None:
            used_quads.add(quad_of[base])
        chosen = []
        used = set()                                  # indices of members in use
        budget = [self.NB_BUDGET if nobase else self.OPS_BUDGET]

        def quad(i):
            return quad_of.get(members[i]) if one_per else None

        def rec(rem, mc, mb, me):
            if rem == 0:
                return True
            budget[0] -= 1
            if budget[0] < 0 or len(used) == n:
                return False
            low = 0
            while low in used:
                low += 1
            lowest = members[low]
            if rem < lowest:
                return False
            if rem < SMALL_LIMIT:
                smask = 0
                for k, si in enumerate(small_idx):
                    if si is not None and si not in used:
                        smask |= 1 << k
                if not reach[smask] >> rem & 1:
                    return False
            # --- powers ---------------------------------------------------
            # rank = (b, e, value) for "exp" (largest base first) or
            #        (value, b, e) for "expv" (largest power first); the
            # first two rank fields are the ordering key.
            if exp_mode and mc <= 0:
                cands = []
                b_hi = bisect.bisect_right(members, math.isqrt(rem))
                for bi in range(b_hi - 1, -1, -1):
                    if bi in used:
                        continue
                    b = members[bi]
                    qb = quad(bi)
                    if qb is not None and qb in used_quads:
                        continue
                    e_max, v = 1, b
                    while v * b <= rem:
                        v *= b
                        e_max += 1
                    e_hi = bisect.bisect_right(members, e_max)
                    for ei in range(e_hi - 1, -1, -1):
                        if ei == bi or ei in used:
                            continue
                        e = members[ei]
                        qe = quad(ei)
                        if qe is not None and (qe in used_quads or qe == qb):
                            continue
                        val = b ** e
                        if val > rem:
                            continue
                        rank = (val, b, e) if by_value else (b, e, val)
                        if mc == 0 and rank[:2] >= (-mb, -me):
                            continue
                        cands.append((rank, bi, ei, qb, qe))
                cands.sort(key=lambda c: (-c[0][0], -c[0][1], -c[0][2]))
                for rank, bi, ei, qb, qe in cands:
                    b, e = members[bi], members[ei]
                    chosen.append(["^", b, e])
                    used.add(bi)
                    used.add(ei)
                    for qq in (qb, qe):
                        if qq is not None:
                            used_quads.add(qq)
                    if rec(rem - b ** e, 0, -rank[0], -rank[1]):
                        return True
                    chosen.pop()
                    used.discard(bi)
                    used.discard(ei)
                    for qq in (qb, qe):
                        if qq is not None:
                            used_quads.discard(qq)
                    if budget[0] < 0:
                        return False
            # --- products -------------------------------------------------
            if mc <= 1:
                a_hi = bisect.bisect_right(members, rem // lowest)
                if mc == 1:
                    a_hi = min(a_hi, bisect.bisect_right(members, -mb))
                for ai in range(a_hi - 1, 0, -1):
                    if ai in used:
                        continue
                    a = members[ai]
                    qa = quad(ai)
                    if qa is not None and qa in used_quads:
                        continue
                    m_hi = min(ai, bisect.bisect_right(members, rem // a))
                    if mc == 1 and a == -mb:
                        m_hi = min(m_hi, bisect.bisect_left(members, -me))
                    used.add(ai)
                    if qa is not None:
                        used_quads.add(qa)
                    for mi in range(m_hi - 1, -1, -1):
                        if mi in used:
                            continue
                        m = members[mi]
                        qm = quad(mi)
                        if qm is not None and qm in used_quads:
                            continue
                        chosen.append(["*", a, m])
                        used.add(mi)
                        if qm is not None:
                            used_quads.add(qm)
                        if rec(rem - a * m, 1, -a, -m):
                            return True
                        chosen.pop()
                        used.discard(mi)
                        if qm is not None:
                            used_quads.discard(qm)
                        if budget[0] < 0:
                            return False
                    used.discard(ai)
                    if qa is not None:
                        used_quads.discard(qa)
            # --- plain ----------------------------------------------------
            p_hi = bisect.bisect_right(members, rem)
            if mc == 2:
                p_hi = min(p_hi, bisect.bisect_left(members, -mb))
            for pi in range(p_hi - 1, -1, -1):
                if pi in used:
                    continue
                p = members[pi]
                qp = quad(pi)
                if qp is not None and qp in used_quads:
                    continue
                chosen.append(["p", p])
                used.add(pi)
                if qp is not None:
                    used_quads.add(qp)
                if rec(rem - p, 2, -p, 0):
                    return True
                chosen.pop()
                used.discard(pi)
                if qp is not None:
                    used_quads.discard(qp)
                if budget[0] < 0:
                    return False
            return False

        if rec(diff, -1, 0, 0):
            return [list(t) for t in chosen]
        return None

    def solve_greedy(self, n, pool, quad_of):
        """Derivation of an arbitrary integer n >= 0 (the -d switch):
        largest pool prime <= remainder first, each prime once, keep adding
        while a prime fits, close with a royal expression that may use
        + - * (ROYAL_SIGNED); backtrack when the remainder has no royal
        form.  pool: ascending primes < n.  Returns the primes or None.
        A flat royal closing (no product containing a sum) is preferred:
        nested forms are used only when no choice of primes avoids them."""
        for allowed in (ROYAL_SIGNED_FLAT, ROYAL_SIGNED):
            terms = self._search(n, pool, None, quad_of, False,
                                 allowed=allowed, min_allowed=0)
            if terms is not None:
                return terms
        return None

    def _search(self, rem0, avail, base, quad_of, stop_first,
                allowed=None, min_allowed=None, exclude=()):
        if allowed is None:
            allowed, min_allowed = ROYAL_BEST, MIN_ROYAL
        used_quads = None
        if self.one_per_quad:
            used_quads = {quad_of[base]} if base is not None else set()
        chosen = []
        budget = self.node_limit

        def first_idx(rem, bound):
            return bisect.bisect_right(avail, rem - min_allowed, 0, bound) - 1

        # frame: [remaining, next candidate index, accepted-own-remainder flag]
        stack = [[rem0, first_idx(rem0, len(avail)), False]]
        while stack:
            frame = stack[-1]
            rem, idx, checked = frame
            if stop_first and not checked:
                frame[2] = True
                if rem in allowed:
                    return list(chosen)
            while idx >= 0:
                p = avail[idx]
                if p != base and p not in exclude and (
                        used_quads is None or quad_of[p] not in used_quads):
                    break
                idx -= 1
            if idx >= 0:
                p = avail[idx]
                frame[1] = idx - 1
                chosen.append(p)
                if used_quads is not None:
                    used_quads.add(quad_of[p])
                budget -= 1
                if budget < 0:
                    return None
                nrem = rem - p
                stack.append([nrem, first_idx(nrem, idx), False])
                continue
            # no more extensions from this frame
            if not stop_first and rem in allowed:
                return list(chosen)
            stack.pop()
            if chosen:
                last = chosen.pop()
                if used_quads is not None:
                    used_quads.discard(quad_of[last])
        return None


# --------------------------------------------------------------------------
# Cache
# --------------------------------------------------------------------------
def empty_cache(mode):
    return {"royal": list(ROYAL), "mode": mode, "format": FORMAT,
            "quads": [], "diffs": {}}


def load_cache(path, mode):
    if os.path.exists(path):
        with open(path) as fh:
            data = json.load(fh)
        if (data.get("royal") == list(ROYAL) and data.get("mode") == mode
                and data.get("format") == FORMAT):
            return data
        print(f"note: {os.path.basename(path)} is in an older layout; "
              f"rebuilding it", file=sys.stderr)
    return empty_cache(mode)


def save_cache(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump({k: v for k, v in data.items() if not k.startswith("_")},
                  fh, indent=1)
    os.replace(tmp, path)


# --------------------------------------------------------------------------
# Building the chain
# --------------------------------------------------------------------------
def diff_text(entry):
    parts = [str(t) for t in entry["terms"]]
    if entry["royal"]:
        parts.append(entry["royal"])
    return " + ".join(parts)


def ops_ways(deriver, diff, avail, base, quad_of, additive_entry):
    """M and E entries for a difference; each is {"terms": [...]} plus
    "fallback": True when the search gave up and a simpler way was copied."""
    mul = deriver.solve_ops(diff, avail, base, quad_of, "mul")
    if mul is None:
        conv = additive_to_ops(additive_entry)
        mul_entry = {"terms": conv, "fallback": True} if conv else None
    else:
        mul_entry = {"terms": mul}
    exp = deriver.solve_ops(diff, avail, base, quad_of, "exp")
    if exp is None:
        exp_entry = ({"terms": mul_entry["terms"], "fallback": True}
                     if mul_entry else None)
    else:
        exp_entry = {"terms": exp}
    expv = deriver.solve_ops(diff, avail, base, quad_of, "expv")
    if expv is None:
        expv_entry = ({"terms": exp_entry["terms"], "fallback": True}
                      if exp_entry else None)
    else:
        expv_entry = {"terms": expv}
    for e in (mul_entry, exp_entry, expv_entry):
        if e is not None and ops_value(e["terms"]) != diff:
            raise AssertionError(f"bad term list for {diff}: {e}")
    return mul_entry, exp_entry, expv_entry


def _royal_ops_forms():
    """Flat royal +,* forms that the term encoding can hold: distinct royal
    members added, some of them grouped in 2-member products.
    value -> [(members, terms)] ranked like the additive way: fewer
    products, then fewer terms, then larger terms first."""
    forms = {}

    def pairings(items):
        if not items:
            yield []
            return
        first, rest = items[0], items[1:]
        for rest_terms in pairings(rest):
            yield [["p", first]] + rest_terms
        for j in range(len(rest)):
            for rest_terms in pairings(rest[:j] + rest[j + 1:]):
                yield [["*", rest[j], first]] + rest_terms

    n = len(ROYAL)
    for mask in range(1, 1 << n):
        subset = [ROYAL[i] for i in range(n) if mask >> i & 1]
        for terms in pairings(subset):
            products = sorted((t for t in terms if t[0] == "*"), key=lambda t: -t[1] * t[2])
            plains = sorted((t for t in terms if t[0] == "p"), key=lambda t: -t[1])
            ordered = products + plains
            value = ops_value(ordered)
            rank = (len(products), len(ordered),
                    tuple(-(t[1] if t[0] == "p" else t[1] * t[2]) for t in ordered))
            forms.setdefault(value, []).append((rank, frozenset(subset), ordered))
    out = {v: [(m, t) for _, m, t in sorted(entries, key=lambda x: x[0])]
           for v, entries in forms.items()}
    out[0] = [(frozenset(), [])]
    return out


ROYAL_OPS = _royal_ops_forms()
_ROYAL_OPS_ALLOWED = {}


def royal_ops_allowed(used):
    """value -> best flat royal terms that avoid the royal members in used."""
    key = frozenset(m for m in used if m in ROYAL)
    table = _ROYAL_OPS_ALLOWED.get(key)
    if table is None:
        table = {}
        for v, entries in ROYAL_OPS.items():
            for members, terms in entries:
                if not (members & key):
                    table[v] = terms
                    break
        _ROYAL_OPS_ALLOWED[key] = table
    return table


def iroot(n, e):
    """Largest r with r**e <= n."""
    r = int(round(n ** (1.0 / e)))
    while r > 0 and r ** e > n:
        r -= 1
    while (r + 1) ** e <= n:
        r += 1
    return r


def largest_power(rem, members, used):
    """Largest b**e <= rem with b, e distinct members not in used, or None."""
    best = None
    for e in SMALL:
        if e in used or e > rem.bit_length():
            continue
        i = bisect.bisect_left(members, e)
        if i >= len(members) or members[i] != e:
            continue
        hi = bisect.bisect_right(members, iroot(rem, e))
        for j in range(hi - 1, -1, -1):
            b = members[j]
            if b == e or b in used:
                continue
            value = b ** e
            if best is None or value > best[0]:
                best = (value, b, e)
            break
    return best


def power_chain_way(deriver, target, avail, quad_of, per_exponent=8):
    """E3: powers first, one at a time.  The largest b^e below the prime,
    then again the largest power below what is left as long as it covers at
    least half of it; then the remainder the additive way: quad primes
    below the target added, largest first, closed by a flat royal +,*
    expression.  Base, exponents, primes and royal members are all
    distinct.  If the remainder cannot be closed, the chain is shortened by
    one power at a time, and finally the next largest first power is tried.
    Returns the equation text or None."""
    members = deriver._nb_pool(avail)            # ROYAL + avail, ascending
    firsts = []
    for e in SMALL:
        if e > target.bit_length():
            break
        i = bisect.bisect_left(members, e)
        if i >= len(members) or members[i] != e:
            continue
        hi = bisect.bisect_right(members, iroot(target, e))
        taken = 0
        for j in range(hi - 1, -1, -1):
            b = members[j]
            if b == e:
                continue
            firsts.append((b ** e, b, e))
            taken += 1
            if taken >= per_exponent:
                break
    firsts.sort(reverse=True)
    for value, b, e in firsts:
        chain = [(value, b, e)]
        used = {b, e}
        rem = target - value
        while True:
            nxt = largest_power(rem, members, used)
            if nxt is None or 2 * nxt[0] < rem:
                break
            chain.append(nxt)
            used |= {nxt[1], nxt[2]}
            rem -= nxt[0]
        for k in range(len(chain), 0, -1):
            powers = chain[:k]
            used = {m for _, pb, pe in powers for m in (pb, pe)}
            rem = target - sum(v for v, _, _ in powers)
            allowed = royal_ops_allowed(used)
            if rem in allowed:
                primes = []
            else:
                primes = deriver._search(rem, avail, None, quad_of, False,
                                         allowed=allowed, min_allowed=0, exclude=used)
                if primes is None:
                    continue
            royal_value = rem - sum(primes)
            terms = ([["^", pb, pe] for _, pb, pe in powers]
                     + [["p", p] for p in primes] + allowed[royal_value])
            if ops_value(terms) != target:
                raise AssertionError(f"bad E3 for {target}: {terms}")
            return ops_text(terms)
    return None


def ops_parse(text):
    """Inverse of ops_text: "(829^2) + (13009*11) + 199" -> tagged terms."""
    terms = []
    for part in text.split(" + "):
        part = part.strip("()")
        if "^" in part:
            b, e = part.split("^")
            terms.append(["^", int(b), int(e)])
        elif "*" in part:
            a, m = part.split("*")
            terms.append(["*", int(a), int(m)])
        else:
            terms.append(["p", int(part)])
    return terms


def columns_of(quad, der, diffs):
    """How many terms the additive equation of this member shows on the right,
    counting the base and every top-level piece of the royal expression:
        15731 = 15649 + 17 + 13 + 11 + (5*7) + (2*3)      ->  6 columns
    Quad 1 has no base, so only its royal pieces are counted."""
    if quad["n"] == 1:
        return top_terms(der["royal"])
    e = diffs[str(der["diff"])]
    return 1 + len(e["terms"]) + (top_terms(e["royal"]) if e["royal"] else 0)


def ops_ways_nobase(deriver, target, avail, quad_of):
    """M1 and E3 for the whole prime, no base term.  M1 is the M greedy
    over the whole pool (deeper node budget); E3 is power_chain_way, with
    the old power-first greedy as a fallback when no power chain closes (11
    and 17).  Returns the equation text (see ops_parse) or None for each;
    text keeps the cache small, one entry per member."""
    terms = deriver.solve_ops(target, avail, None, quad_of, "mul")
    if terms is not None and ops_value(terms) != target:
        raise AssertionError(f"bad no-base term list for {target}: {terms}")
    mul_text = ops_text(terms) if terms is not None else None
    exp_text = power_chain_way(deriver, target, avail, quad_of)
    if exp_text is None:                  # no power chain closes: old greedy
        for mode in ("exp", "expv"):
            terms = deriver.solve_ops(target, avail, None, quad_of, mode)
            if terms is not None:
                exp_text = ops_text(terms)
                break
    return mul_text, exp_text


def entry_members(entry):
    """Every member used by any of the three ways of a diffs entry."""
    out = set(entry["terms"])
    for way in ("mul", "exp", "expv"):
        if entry.get(way):
            out.update(ops_members(entry[way]["terms"]))
    return out


def derive_quad_one(deriver):
    out = []
    for t in (11, 13, 17, 19):
        alt_pt = [f for f in ROYAL_PT[t] if f != ROYAL_BEST[t]]
        alt_pm = [f for f in ROYAL_PM.get(t, []) if "-" in f]
        rec = {
            "target": t, "base": None, "diff": t, "reused": False,
            "royal": ROYAL_BEST[t], "terms": [],
            "alternatives": alt_pt[:4],
            "alternatives_with_minus": alt_pm[:4],
        }
        rec["mul"], rec["exp"], rec["expv"] = ops_ways(deriver, t, [], None, {}, rec)
        rec["mul_nb"], rec["exp_nb"] = ops_ways_nobase(deriver, t, [], {})
        out.append(rec)
    return out


def extend_chain(data, want_count=None, upto=None, one_per_quad=False,
                 progress=True):
    quads, diffs = data["quads"], data["diffs"]
    deriver = Deriver(one_per_quad=one_per_quad)

    if not quads:
        quads.append({"n": 1, "primes": [11, 13, 17, 19],
                      "derivations": derive_quad_one(deriver)})
        save_cache(data["_path"], data)

    if want_count is not None and len(quads) >= want_count:
        return 0
    if upto is not None and want_count is None and quads[-1]["primes"][0] >= upto:
        return 0

    avail = [p for q in quads for p in q["primes"]]
    quad_of = {p: q["n"] for q in quads for p in q["primes"]}
    stream = quadruplets_from(quads[-1]["primes"][0] + 1)
    added = 0
    t0 = last_save = time.time()
    while True:
        if want_count is not None and len(quads) >= want_count:
            break
        quad = next(stream)
        if upto is not None and quad[0] > upto:
            break
        last = quads[-1]["primes"]
        n = len(quads) + 1
        derivs = []
        for target in quad:
            record = None
            for base in sorted(last, reverse=True):
                diff = target - base
                if diff < MIN_ROYAL:
                    continue
                key = str(diff)
                entry = diffs.get(key)
                if entry is not None and base not in entry_members(entry):
                    record = {"target": target, "base": base, "diff": diff,
                              "reused": True}
                    break
                res = deriver.solve(diff, avail, base, quad_of)
                if res is not None:
                    terms, rv, text = res
                    new_entry = {"terms": terms, "royal_value": rv,
                                 "royal": text, "first": [n, target]}
                    new_entry["mul"], new_entry["exp"], new_entry["expv"] = ops_ways(
                        deriver, diff, avail, base, quad_of, new_entry)
                    diffs[key] = new_entry
                    record = {"target": target, "base": base, "diff": diff,
                              "reused": False}
                    break
            if record is None:
                record = {"target": target, "base": None, "diff": None,
                          "reused": False, "failed": True}
            # M1 / E3: the whole prime without the base term (per member,
            # because they depend on the target, not on the difference)
            record["mul_nb"], record["exp_nb"] = ops_ways_nobase(
                deriver, target, avail, quad_of)
            derivs.append(record)
        quads.append({"n": n, "primes": list(quad), "derivations": derivs})
        for p in quad:
            avail.append(p)
            quad_of[p] = n
        added += 1
        now = time.time()
        if now - last_save >= 15:            # checkpoint, keeps big runs safe
            save_cache(data["_path"], data)
            last_save = now
            if progress:
                print(f"  ... {len(quads)} quads (last {quad[0]}), "
                      f"{now - t0:.0f}s", file=sys.stderr)
    if added:
        save_cache(data["_path"], data)
    return added


# --------------------------------------------------------------------------
# Display
# --------------------------------------------------------------------------
WAY_NAMES = {"A": "additive", "M": "multiplicative", "M1": "multiplicative",
             "E1": "exponential", "E2": "exponential", "E3": "exponential"}
# label -> cache key.  M / E1 / E2 write the difference from the base
# (stored per unique difference); M1 / E3 write the whole prime without
# the base (stored per member).  E1 tries the largest base first, E2 the
# largest power value first, E3 is a chain of largest powers plus an additive rest.
WAY_LINES = {"A": [("A", None)], "M": [("M", "mul"), ("M1", "mul_nb")],
             "E": [("E1", "exp"), ("E2", "expv"), ("E3", "exp_nb")]}
NOBASE_KEYS = {"mul_nb", "exp_nb"}


def show(data, start=None, end=None, upto=None, picks=None, cols=None,
         verbose=False, all_members=False, ways="A", only=False, out=sys.stdout):
    """start / end are quad numbers (1-based, inclusive); either may be None.
    One number N from the command line means end=N, the first N quads.
    picks is the -o list: show exactly those quads, in that order.
    cols is the -c filter: (low, high) terms in the additive equation."""
    quads, diffs = data["quads"], data["diffs"]
    if start is not None:
        quads = [q for q in quads if q["n"] >= start]
    if end is not None:
        quads = [q for q in quads if q["n"] <= end]
    if upto is not None:
        quads = [q for q in quads if q["primes"][0] <= upto]
    if picks is not None:               # in the order asked for, not chain order
        by_n = {q["n"]: q for q in quads}
        quads = [by_n[n] for n in picks if n in by_n]
    elif only and quads:                # -o with no numbers: the last quad
        quads = quads[-1:]
    w = out.write
    w("Royal quad (0): " + ", ".join(map(str, ROYAL)) + "\n\n")
    quad_of = {p: q["n"] for q in data["quads"] for p in q["primes"]}
    reused = new = 0
    labeled = len(ways) > 1

    def sources(d, entry, members, royal_note, fallback):
        src = [f"diff {d['diff']}"]
        if d["reused"]:
            fq, ft = entry["first"]
            src[0] += f", same as quad {fq} ({ft}), equation reused"
        src.append(f"base from quad {quad_of[d['base']]}")
        by_quad, royal = {}, []
        for m in members:
            if m in ROYAL:
                royal.append(m)
            else:
                by_quad.setdefault(quad_of[m], []).append(m)
        for qn in sorted(by_quad, reverse=True):
            src.append(f"quad {qn}: " + ", ".join(map(str, by_quad[qn])))
        if royal_note:
            src.append(royal_note)
        elif royal:
            src.append("royal: " + ", ".join(map(str, royal)))
        if fallback:
            src.append("search gave up, simpler way copied")
        return "      [" + "; ".join(src) + "]\n"

    scanned = len(quads)
    tally = {}
    rows = []
    for q in quads:                     # decide what survives before printing
        ders = q["derivations"] if all_members else q["derivations"][:1]
        for d in ders:
            n = columns_of(q, d, diffs)
            tally[n] = tally.get(n, 0) + 1
        if cols is not None:
            ders = [d for d in ders if cols[0] <= columns_of(q, d, diffs) <= cols[1]]
            if not ders:
                continue
        rows.append((q, ders))
    quads = [q for q, _ in rows]

    for q, shown in rows:
        primes = [d["target"] for d in shown]
        w(f"Quad {q['n']}: " + ", ".join(map(str, primes)) + "\n")
        for d in shown:
            first = q["n"] == 1
            entry = None
            if not first and not d.get("failed"):
                entry = diffs[str(d["diff"])]
                if d["reused"]:
                    reused += 1
                else:
                    new += 1
            e1_terms = None
            printed = []          # canonical term lists already shown for this prime
            for way in "AME":
                if way not in ways:
                    continue
                for label, key in WAY_LINES[way]:
                    pre = f"{label}: " if (labeled or way != "A") else ""
                    if key in NOBASE_KEYS:
                        e = d.get(key)
                        if e is None:
                            w(f"  {pre}{d['target']} = (no {WAY_NAMES[label]} form found)\n")
                        else:
                            canon = sorted(map(tuple, ops_parse(e)))
                            if canon in printed:
                                continue          # repeats an earlier line
                            printed.append(canon)
                            w(f"  {pre}{d['target']} = {e}\n")
                            if verbose and not first:
                                by_quad = {}
                                for m in ops_members(ops_parse(e)):
                                    if m not in ROYAL:
                                        by_quad.setdefault(quad_of[m], []).append(m)
                                src = [f"no base; quad {qn}: " + ", ".join(map(str, by_quad[qn]))
                                       for qn in sorted(by_quad, reverse=True)]
                                w("      [" + "; ".join(src) + "]\n")
                        continue
                    if d.get("failed"):
                        w(f"  {pre}{d['target']} = (no derivation found)\n")
                        continue
                    if way == "A":
                        if first:
                            w(f"  {pre}{d['target']} = {d['royal']}\n")
                            if d.get("alternatives"):
                                w("      also (+,*): "
                                  + "  |  ".join(d["alternatives"]) + "\n")
                            if d.get("alternatives_with_minus"):
                                w("      also (with -): "
                                  + "  |  ".join(d["alternatives_with_minus"]) + "\n")
                            continue
                        w(f"  {pre}{d['target']} = {d['base']} + {diff_text(entry)}\n")
                        if verbose:
                            note = (f"royal: {entry['royal']} = {entry['royal_value']}"
                                    if entry["royal"] else "no royal part needed")
                            w(sources(d, entry, entry["terms"], note, False))
                        continue
                    e = (d if first else entry).get(key)
                    if e is None:
                        w(f"  {pre}{d['target']} = (no {WAY_NAMES[label]} form found)\n")
                        continue
                    if label == "E1":
                        e1_terms = e["terms"]
                    elif label == "E2" and e["terms"] == e1_terms:
                        continue                  # identical: show E1 only
                    printed.append(sorted(list(map(tuple, e["terms"]))
                                          + ([] if first else [("p", d["base"])])))
                    text = ops_text(e["terms"])
                    if first:
                        w(f"  {pre}{d['target']} = {text}\n")
                        continue
                    w(f"  {pre}{d['target']} = {d['base']} + {text}\n")
                    if verbose:
                        w(sources(d, entry, ops_members(e["terms"]), None,
                                  e.get("fallback", False)))
        w("\n")
    held = len(data["quads"])
    tail = f" (of {scanned} scanned)" if cols is not None else ""
    w(f"{len(quads)} quad{'s' if len(quads) != 1 else ''} shown{tail}, "
      f"{held} quad{'s' if held != 1 else ''} in the cache\n")
    if verbose and tally:
        spread = ", ".join(f"{n}: {tally[n]}" for n in sorted(tally))
        w(f"(columns in the additive equation -> how many members: {spread})\n")
    if verbose:
        w(f"(differences shown: {new} new, {reused} reused; "
          f"{len(diffs)} unique differences stored)\n")


# --------------------------------------------------------------------------
# -d N : derive an arbitrary integer from the quad members below it
# --------------------------------------------------------------------------
def derive_numbers(data, first, last, deriver, verbose=False, out=sys.stdout):
    """Print  n = (quad primes below n, largest first) + (royal expression)
    for every n from first to last.  Quad primes are only added; minus and
    multiplication appear only in the royal expression, which may use
    + - * over 2, 3, 5, 7.  Returns True when every n was derived."""
    extend_chain(data, upto=last, one_per_quad=deriver.one_per_quad)
    allp = sorted(p for q in data["quads"] for p in q["primes"])
    quad_of = {p: q["n"] for q in data["quads"] for p in q["primes"]}
    w = out.write
    ok = True
    for n in range(first, last + 1):
        pool = allp[:bisect.bisect_left(allp, n)]          # primes below n
        terms = deriver.solve_greedy(n, pool, quad_of)
        if terms is None:
            w(f"{n} = (no derivation found)\n")
            ok = False
            continue
        rem = n - sum(terms)
        parts = [str(t) for t in terms]
        if rem or not terms:
            parts.append(ROYAL_SIGNED[rem])
        w(f"{n} = " + " + ".join(parts) + "\n")
        if verbose:
            by_quad = {}
            for t in terms:
                by_quad.setdefault(quad_of[t], []).append(t)
            src = [f"pool: royal members and {len(pool)} quad primes below {n}"]
            for qn in sorted(by_quad, reverse=True):
                src.append(f"quad {qn}: " + ", ".join(map(str, by_quad[qn])))
            src.append(f"royal: {ROYAL_SIGNED[rem]} = {rem}" if (rem or not terms)
                       else "no royal part needed")
            w("    [" + "; ".join(src) + "]\n")
    return ok


# --------------------------------------------------------------------------
def range_error(vals, only=False):
    """The message for a bad list of quad numbers, or None when it is good.
    Shared by the command line and the prompt so the two cannot drift.
    With -o the numbers are a list of quads to show, so any number of them is
    allowed and they need not be in order."""
    if any(v < 1 for v in vals):
        return "quad numbers must be whole numbers >= 1"
    if only:
        return None
    if len(vals) > 2:
        return ("give one number N (the first N quads), two numbers N M (quads N "
                "through M), or list the quads you want and add -o")
    if len(vals) == 2 and vals[0] > vals[1]:
        return "the first quad number must not be larger than the second (N <= M)"
    return None


def range_of(vals):
    """[] -> (None, None);  [N] -> (None, N);  [N, M] -> (N, M)."""
    if not vals:
        return None, None
    if len(vals) == 1:
        return None, vals[0]
    return vals[0], vals[1]


def ask_number(only=False):
    """Returns (vals, upto) from the prompt: the quad numbers typed, or an
    'upto' value.  main() turns them into a count, a range or a list."""
    while True:
        try:
            raw = input("How many quads after the royal quad? "
                        "(a count, a range 'N M', or 'upto <value>'): ").strip()
        except (EOFError, KeyboardInterrupt):
            sys.exit(0)
        if raw.lower().startswith("upto"):
            try:
                return [], int(raw[4:].strip().replace(",", ""))
            except ValueError:
                print("  please type: upto 35551421")
                continue
        try:
            vals = [int(t.replace(",", "")) for t in raw.split()]
        except ValueError:
            vals = None
        if vals:
            problem = range_error(vals, only)
            if problem is None:
                return vals, None
            print("  " + problem)
            continue
        print("  please type a count (25), a range (2000 2005), or 'upto 35551421'")


def main(argv=None):
    ap = argparse.ArgumentParser(
        usage="lc [-h] [--upto VALUE] [-d N [M]] [-v] [-A] [-M] [-E] [-o] [--all] "
              "[--one-per-quad] [--recompute] [--cache FILE] [N [M]]",
        description="Quad chain builder (royal quad 2,3,5,7).")
    ap.add_argument("count", nargs="*", type=int, metavar="N",
                    help="N: the first N quads after the royal quad.  "
                         "N M: quads N through M inclusive.  "
                         "With -o: the list of quads to show.")
    ap.add_argument("--upto", type=int, metavar="VALUE",
                    help="show every quad whose first prime is <= VALUE")
    ap.add_argument("-d", "--derive", type=int, nargs="+", metavar="N",
                    help="derive the integer N, or every integer from N to M "
                         "(-d N M), from the quad members below it (quad primes "
                         "added, + - * among royal members only)")
    ap.add_argument("-v", "--verbose", action="store_true",
                    help="show which quad each term of an equation came from")
    ap.add_argument("-A", "-a", dest="A", action="store_true",
                    help="additive way (the default when no way is given)")
    ap.add_argument("-M", "-m", dest="M", action="store_true",
                    help="multiplicative way: members multiplied in pairs, "
                         "multiplication preferred over addition")
    ap.add_argument("-E", "-e", dest="E", action="store_true",
                    help="exponential way, two options: E1 largest base first, "
                         "E2 largest power first; combine flags, e.g. -AME or -aem")
    ap.add_argument("-o", "-one", "--only", dest="only", action="store_true",
                    help="show only the quads named, in the order you type "
                         "them (2000 2005 1223 -o shows those three; add -s to "
                         "sort them); with --upto and no numbers, the last quad "
                         "whose first prime is <= VALUE")
    ap.add_argument("-c", "-cols", "--columns", dest="columns", type=int,
                    nargs="+", metavar="N",
                    help="keep only quads whose additive equation has N terms on "
                         "the right, counting the base; -c N M keeps a range, so "
                         "-c 3 8 is three to eight columns")
    ap.add_argument("-s", "-sort", "--sorted", dest="sort", action="store_true",
                    help="with -o, list the quads in ascending order instead of "
                         "the order you typed them")
    ap.add_argument("--all", action="store_true",
                    help="show the equation of all four primes of a quad "
                         "(default: only the first one, e.g. 101)")
    ap.add_argument("--one-per-quad", action="store_true",
                    help="stricter rule: an equation may take at most one member "
                         "from each quad (uses its own cache file)")
    ap.add_argument("--recompute", action="store_true",
                    help="ignore the saved equations and rebuild from scratch")
    ap.add_argument("--cache", metavar="FILE", help="cache file to use")
    args = ap.parse_args(argv)

    mode = "one-per-quad" if args.one_per_quad else "distinct-primes"
    path = args.cache or (CACHE_STRICT if args.one_per_quad else CACHE_DEFAULT)
    data = empty_cache(mode) if args.recompute else load_cache(path, mode)
    data["_path"] = path
    cached = len(data["quads"])

    if args.derive is not None:
        if len(args.derive) > 2:
            ap.error("-d takes one number N or a range N M")
        first, last = args.derive[0], args.derive[-1]
        if first < 0 or last < first:
            ap.error("-d needs whole numbers >= 0 with N <= M")
        ok = derive_numbers(data, first, last,
                            Deriver(one_per_quad=args.one_per_quad),
                            verbose=args.verbose)
        return 0 if ok else 1

    problem = range_error(args.count, args.only)
    if problem:
        ap.error(problem)
    cols = None
    if args.columns is not None:
        if len(args.columns) > 2:
            ap.error("-c takes one number N or a range N M")
        lo, hi = args.columns[0], args.columns[-1]
        if lo < 1 or hi < lo:
            ap.error("-c needs whole numbers >= 1 with N <= M")
        cols = (lo, hi)
    vals, upto = args.count, args.upto
    if not vals and upto is None:
        vals, upto = ask_number(args.only)

    picks = start = end = None
    if args.only and vals:              # -o: exactly the quads named
        picks = list(dict.fromkeys(vals))       # de-duplicate, keep the order typed
        if args.sort:
            picks.sort()
        end = max(picks)                        # build the chain to the largest
    else:
        start, end = range_of(vals)
    if start is not None and upto is not None:
        ap.error("--upto cannot be combined with a quad range N M")

    added = extend_chain(data, want_count=end, upto=upto,
                         one_per_quad=args.one_per_quad)
    ways = "".join(w for w, on in (("A", args.A), ("M", args.M), ("E", args.E)) if on)
    show(data, start=start, end=end, upto=upto, picks=picks, cols=cols,
         verbose=args.verbose,
         all_members=args.all, ways=ways or "A", only=args.only)
    if args.verbose:
        print(f"({cached} quads came from {os.path.basename(path)}, "
              f"{added} computed now)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:              # piped into head, less, grep -m ...
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        sys.exit(0)
    except KeyboardInterrupt:
        sys.exit(130)
