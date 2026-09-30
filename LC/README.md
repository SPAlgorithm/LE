# LC - quad chain builder

> **Ladhe's Quad Conjecture: every prime quadruplet after 2, 3, 5, 7 is a sum of the ones before it.**
>
> (Every first member's gap is written by one rule: the shortest sum of distinct earlier primes, larger primes preferred when several sums are equally short. That is a plain sum for all but 98 of the 28,386 gaps below 10^9; the 98 are the occurrences of the four gaps 22, 82, 172 and 382, which have no such sum and keep the largest-first form closed by a royal value, e.g. `101 = 19 + 17 + 13 + 11 + (5*7) + (2*3)`. The other three primes of a quad follow from the first one: `p + 2`, `p + (2*3)`, `(p+6) + 2`.)

`lc.py` grows a q-array of prime "quads" from the royal quad and shows how
the first prime of every quad is derived from earlier ones.

## Run it

```
python3 lc.py                  # asks: how many quads?
python3 lc.py 25               # first 25 quads after the royal quad
python3 lc.py 2000 2005        # quads 2000 to 2005, both ends included
python3 lc.py --upto 35551421  # every quad whose first prime is <= value
python3 lc.py 25 -v            # also show which quad each term came from
python3 lc.py 25 -M            # multiplicative ways M and M1 (see "Three ways")
python3 lc.py 25 -E            # exponential ways E1, E2 and E3
python3 lc.py 25 -AME          # every way, labeled A:, M:, M1:, E1:, E2:, E3: (-AM, -ME also work)
python3 lc.py 25 -aem          # lowercase works too, alone or combined (-a -e -m, -aeM)
python3 lc.py 2000 -o          # only the 2000th quad (-one and --only do the same)
python3 lc.py 2000 2005 -o     # only quads 2000 and 2005
python3 lc.py 2000 2005 1223 -o    # only those three, in the order you typed
python3 lc.py 2000 2005 1223 -o -s # the same three, sorted (-sort, --sorted too)
python3 lc.py --upto 35551421 -o   # only the last quad at or below the value
python3 lc.py 1210872 -o --near     # the two quads either side of any value
python3 lc.py 2000 -o --chain  # under the A line, the equation of every term
python3 lc.py 1 200 -c 5       # of quads 1 to 200, only the 5-column equations
python3 lc.py 1 200 -c 3 8     # ... three to eight columns (-cols, --columns too)
python3 lc.py -g 20 200        # every quad with the gap 22 or 202 (-g 20,200 too)
python3 lc.py 1 500 -g 82      # of quads 1 to 500, only those with the gap 82
python3 lc.py 25 --all         # list all four primes in each heading (equations are the first prime's)
python3 lc.py -d 53            # derive any integer from the quad members below it
python3 lc.py -d 53 83         # every integer from 53 to 83, one line each
python3 lc.py 25 --recompute   # ignore qarray.json and rebuild
python3 lc.py 25 --one-per-quad   # stricter rule, see below
```

## Asking at the prompt

Run `python3 lc.py` with no numbers and it asks. The prompt takes the same
grammar as the command line:

```
How many quads after the royal quad? (a count, a range 'N M', or 'upto <value>'):
```

| you type | you get |
| --- | --- |
| `25` | the first 25 quads |
| `2000 2005` | quads 2000 to 2005, six of them |
| `upto 200` | every quad whose first prime is at most 200 |
| `2 5 9` (with `-o` on the command line) | exactly those three quads |
| `1,000` | commas are ignored, so this is 1000 |

Every switch still applies, so `python3 lc.py -o -aem` asks for the numbers and
then prints those quads in all six ways. Bad input is explained rather than
accepted, and it asks again:

```
  please type a count (25), a range (2000 2005), or 'upto 35551421'
  quad numbers must be whole numbers >= 1
  the first quad number must not be larger than the second (N <= M)
  give one number N (the first N quads), two numbers N M (quads N through M),
  or list the quads you want and add -o
```

Ctrl-D or Ctrl-C leaves without building anything.


## All the switches

| switch | what it does |
| --- | --- |
| `N` | the first N quads |
| `N M` | quads N to M, both included |
| `--upto VALUE` | every quad whose first prime is at most VALUE |
| `-o`, `-one`, `--only` | the numbers are a list: show exactly those quads |
| `-s`, `-sort`, `--sorted` | with `-o`, list them in ascending order |
| `-n`, `-near`, `--near` | the numbers are values: show the quad either side of each |
| `--chain` | under each A line, the equation of every term it uses |
| `-c N`, `-cols`, `--columns` | keep only equations with N columns; `-c N M` for a range |
| `-g G`, `-gap`, `--gap` | keep only quads with the gap G, or the next valid gap above it; list several as `-g 20 200` or `-g 20,200` |
| `-A`, `-M`, `-E` | which ways to print; lower case works too, combine as `-AME` or `-aem` |
| `--all` | list all four primes of a quad in its heading (the equations are always the first prime's) |
| `-v`, `--verbose` | where each term came from, plus the column distribution |
| `-d N`, `--derive` | derive any integer; `-d N M` for a range of them |
| `--one-per-quad` | the stricter rule, at most one member per quad |
| `--recompute` | ignore the saved equations and rebuild |
| `--cache FILE` | read and write a particular cache |

`--chain` and `--near` both need `-o`, because they only make sense for quads
you have named. `-s` only matters with `-o`. Everything else combines freely.

## The rules

1. The q-array starts with the royal / initial quad `2, 3, 5, 7`.
2. Every later quad is the next four primes ending in 1, 3, 7, 9 that sit
   together: `p, p+2, p+6, p+8` (a prime quadruplet). Quad 1 is
   `11, 13, 17, 19`, quad 2 is `101, 103, 107, 109`, and so on.
3. Quad 1 is written with `+` and `*` over royal members only, e.g.
   `11 = (2*3) + 5`. Alternatives, including the ones that use `-`, are
   listed under it. Minus is not used anywhere else.
   Layout: products are wrapped in parentheses and larger terms come first,
   so `101 = 19 + 17 + 13 + 11 + (5*7) + (2*3)`.
4. The first prime `p` of quad k (k >= 2) is written as

   ```
   one member of the last quad (quad k-1)
   + members of earlier non-royal quads, each prime used at most once
   + optionally an expression in royal members using only + and *
   ```

   The other three primes of the quad need no search - they follow from
   the first one and are stored in exactly this form:

   ```
   p+2 = p + 2          p+6 = p + (2*3)          p+8 = (p+6) + 2
   ```

   A royal expression uses each of 2, 3, 5, 7 at most once, and a product
   may multiply only **two** of them: `(5*7) + (2*3)` is allowed, `(2*5*7)`
   and `5*(7 + (2*3))` are not. The terms are chosen by one rule, shortest
   first:

   1. take the shortest sum of distinct primes of earlier quads that equals
      the difference (the base is left out), trying 2, 4, 6 and 8 primes in
      turn - the difference is even and the primes odd, so the count is even;
   2. among equally short sums prefer the larger primes, compared term by
      term;
   3. only when no sum of at most eight primes exists - the differences 22,
      82, 172 and 382 - take the primes largest first, backing up when a
      choice leads to a remainder that cannot be finished, and close with a
      royal value.

   ```
   2081  = 1879 + 191 + 11                         two primes suffice
   13001 = 9439 + 3461 + 101                       two primes, not
                                                   3467 + 19 + 17 + 13 + 11 + (5*7)
   1871  = 1489 + 199 + 109 + 19 + 17 + 13 + 11 + 7 + 5 + 2
                                                   no sum of primes reaches 382
   101   = 19 + 17 + 13 + 11 + (5*7) + (2*3)       products, because no sum
                                                   of primes reaches 82
   ```

   The stored equation is a shortest one, so its length is the minimal
   length K that `paper/stats.py` computes; `paper/check.py` re-derives
   every stored equation by this rule with a search of its own.

5. Storage in `qarray.json` beside the script: each quad records, per
   prime, only the base and the difference, e.g. `191 = 109 + 82` is
   stored as base 109, diff 82, and `193 = 191 + 2` as base 191, diff 2.
   A separate `diffs` table holds one equation per unique difference
   (`82 = 19 + 17 + 13 + 11 + (3*5) + 7`; the entries `2` and `6` are the fixed
   forms shared by every quad's later primes). When a later quad produces
   a difference already in the table, its equation is reused and the output
   says so; only a new difference triggers a new search. The next run loads
   the file and computes only quads that are not there yet.

   The shortest-sum search leaves the base out, so the stored length is the
   minimal length K. The largest-first fallback of the four exceptional
   differences is searched over every member below the difference, the base
   included, because any quad reusing it has a base larger than its own
   difference. A member whose base is *below* its difference cannot use the
   base in any of its ways, so it keeps its own equations in the derivation
   record instead: quad 2 writes `101 = 19 + 17 + 13 + 11 + (5*7) + (2*3)`
   while quad 3, reusing the same difference 82 with the base 109, writes
   `191 = 109 + 19 + 17 + 13 + 11 + (3*5) + 7`. Below 10^9 exactly two
   members need their own equations, 101 (quad 2, base among the terms of
   82) and 821 (quad 4, base in the M way of 622).
6. The display shows one line per quad, the prime ending in 1 with its full
   equation (base first, then the difference written out):

   ```
   Quad 7: 2081
     2081 = 1879 + 191 + 11
   ```

   Pass `--all` to list all four primes in the heading (`Quad 7: 2081, 2083,
   2087, 2089`); the equation stays the first prime's, the other three being
   `p + 2`, `p + (2*3)` and `(p+6) + 2`. Pass `-v` to also see the
   difference, whether its equation was reused, and which quad each term
   came from.

   One number is a count, two numbers are a range: `./lc 25` shows the first
   25 quads and `./lc 2000 2005` shows the six quads from 2000 to 2005, both
   ends included.

   `-o` (also `-one` or `--only`) changes the numbers from a range into a list:
   it shows exactly the quads you name and nothing else, **in the order you type
   them**. `./lc 2000 -o` is quad 2000, `./lc 2000 2005 -o` is those two, and
   `./lc 2000 2005 1223 -o` prints 2000, 2005, 1223 in that order. Add `-s`
   (also `-sort` or `--sorted`) to list them in ascending order instead. With
   `--upto` and no numbers, `-o` is the last quad at or below the value. It
   combines with the other switches, so `./lc 2000 -o -AME --all` prints every
   way of quad 2000's first prime, under a heading that lists all four, and
   nothing else:

   ```
   Quad 2000: 31252931
     31252931 = 31210849 + 34849 + 5651 + 1481 + 101
   ```

## Where does a number sit?

Numbers on the command line are quad numbers, so `./lc 205` means the first 205
quads. `--near` (also `-n` or `-near`) reads them as **values** instead and shows
the quad at or below each one together with the quad above it:

```
$ ./lc 1210872 -o --near
Quad 205: 1210871
  1210871 = 1182289 + 25307 + 3251 + 13 + 11
Quad 206: 1228391
  1228391 = 1210879 + 15641 + 1871
```

The value needs no relation to the chain: it can be even, composite, or land
inside a quadruplet's span. `1210871`, `1210872` and `1210875` all give the same
pair, because quad 205 is the last one starting at or below each of them. A
value below 11 has no quad before it, so only quad 1 is shown. Several values
may be given at once; their neighbours are merged, and `-s` sorts them.

`--near` needs `-o`, and it combines with everything else, so
`./lc 1210872 -o -aem --chain --near` gives both quads in all six ways with the
chain lines underneath. A value past the end of the built chain is refused
rather than silently starting a long build:

```
$ ./lc 5000000000 -o --near
lc: error: 5000000000 is past the end of the chain (largest first member
999986171); build further first, for example  lc --upto 5000000000
```

## Following the chain

`--chain` prints, under each A line, the equation of every term that line uses,
so you can see one step further back without running the tool again:

```
$ ./lc 2000 -o --chain
Quad 2000: 31252931
  31252931 = 31210849 + 34849 + 5651 + 1481 + 101
      -> Q23: 34849 = 34847 + 2
      -> Q10: 5651 = 3469 + 2081 + 101
      -> Q5: 1481 = 829 + 197 + 191 + 103 + 101 + 19 + 17 + 13 + 11
      -> Q2: 101 = 19 + 17 + 13 + 11 + (5*7) + (2*3)
```

Four rules. It hangs off the **A line only**, so `-aem` still prints M, M1, E1,
E2 and E3 untouched. It goes **one level deep**; the sub-lines are not expanded
again. The **base is not expanded**, only the terms after it. And members below
**101** are left alone, which means the four members of quad 1 never appear:
their equations are royal expressions rather than chain links.

`--chain` needs `-o`, since expanding every quad of a long listing would bury
it. A sub-line may name a quad that `-c` filtered out of the listing, because
the lookups go through the whole cache rather than the rows on screen.

## Counting columns

`-c N` keeps only the quads whose additive equation has N terms on the right,
counting the base and each top-level piece of the royal expression:

```
15731 = 15649 + 19 + 17 + 13 + 11 + (3*5) + 7     7 columns
        ^base   ^1   ^2   ^3   ^4   ^5      ^6
```

`-c N M` keeps a range, so `-c 3 8` is three to eight columns. The footer says
how many quads survived out of how many were scanned, and `-v` prints the whole
distribution:

```
$ python3 lc.py 1 200 -c 5 -v | tail -2
115 quads shown (of 200 scanned), 2500 quads in the cache (qarray.json)
(columns in the additive equation -> how many members: 2: 1, 3: 44, 5: 115, 6: 1, 7: 31, 9: 6, 10: 2)
```

Two things are worth noticing in that distribution. There is no 4 and no 8,
and there never can be: the gap is even and every quadruplet member is odd,
so a pure sum has an even number of primes and, with the base, an odd column
count (3, 5, 7 or 9 for the shortest sums); an even count needs a royal part
of two pieces, which only the exceptional gaps have - the single 6-column
equation among the first 200 quads is quad 2 itself,
`101 = 19 + 17 + 13 + 11 + (5*7) + (2*3)`, the only quad there whose base
lies below its own difference (every later quad with the gap 82 can use 19
and shows seven columns), and the two 10-column equations are the gap 382,
which closes with `7 + 5 + 2`.

The filter looks at the first prime's equation; `--all` only widens the
heading.

## Filtering by gap

The gap of a quad is its first prime minus the base, the largest member of the
quad before it: `191 = 109 + 82` has the gap 82. It is the number stored as
the difference. `-g G` keeps only the quads with that gap.

Not every number is a gap: the smallest are 22, 82, 112, 172, 202, 232. A
value that is not a gap moves up to the next valid one, so you do not need to
know them:

```
$ python3 lc.py -g 20 200
Royal quad (0): 2, 3, 5, 7

Gap 20 -> next valid gap 22: 18 quads
Gap 200 -> next valid gap 202: 40 quads

Quad 7: 2081   (gap 202)
  2081 = 1879 + 191 + 11

Quad 9: 3461   (gap 202)
  3461 = 3259 + 191 + 11
...
58 quads shown (of 28387 scanned), 28387 quads in the cache (paper/qarray_1e9.json)
```

The numbers are separate values, not a range, and any number of them may be
listed. `-g 20,200` is the same as `-g 20 200`; for this switch a comma
separates two values, while everywhere else it is ignored (`1,000` is 1000).
The quads come in chain order, each heading naming its gap.

With no quad numbers `-g` searches the whole chain on disk and builds nothing:
the 28,387 quads below 10^9 when `paper/qarray_1e9.json` is there (in the
repository it ships as `qarray_1e9.json.gz`, so run `gunzip` on it first),
otherwise the quads of `qarray.json`. Quad numbers or `--upto` narrow the
search, and "valid" then means a gap that occurs among those quads:

```
$ python3 lc.py 1 500 -g 20 200 | tail -1
10 quads shown (of 500 scanned), 2500 quads in the cache (qarray.json)
```

A value above every gap in the search is reported, with the largest gap there
is, and the exit code is 1 when no value found a gap:

```
$ python3 lc.py -g 99999999
Gap 99999999: no gap at or above it in these quads (largest is 395512)
```

`-g` combines with the other switches (`-c`, `-aem`, `-v`, `--all`, `-o`,
`--chain`), but not with `-d`, which derives numbers rather than listing quads.

## Putting it together

The switches are meant to be combined. A few that answer real questions:

```
./lc 1210872 -o -aem --chain --near
```
Everything known about the two quadruplets surrounding a number: all six ways,
with each term of the additive equations expanded one level.

```
./lc 1 500 -c 3 -v
```
Every three-column equation in the first 500 quads, with the distribution of
column counts printed at the end. Change `-c 3` to `-c 7` to see the long ones.

```
./lc 2000 2005 1223 -o -s --all
```
Three quadruplets you picked out, sorted, each heading listing all four
members.

```
./lc --upto 999999999 -o -AME
```
The last quadruplet below a billion, in every way. Reads the published dataset,
so it answers at once.

```
./lc -d 53 83
```
Every integer from 53 to 83 built from the chain, one line each. This is the
other half of the story, described under "Derive any number".

## Three ways

Every difference is stored with an additive, a multiplicative and two
exponential equations, and every prime additionally gets a multiplicative
and an exponential equation that do not use the base at all. `-A` (default),
`-M` and `-E` pick which to print; combine them (`-AME`, `-ME`) to see
several, labeled `A:`, `M:`, `M1:`, `E1:`, `E2:`, `E3:`.

- **A, additive**: the rules above; the shortest sum of earlier primes, a
  royal value only for the four exceptional differences.
- **M, multiplicative**: any members, quad primes and royal members alike,
  may be multiplied in pairs, and multiplication is preferred over addition.
  Greedy: take the largest unused member, multiply it by the largest member
  that still fits, repeat; add plain members only when nothing can be
  multiplied; backtrack on a dead end.
  `101 = 19 + (17*3) + (13*2) + 5`
- **E, exponential**: members may also be raised to a member power (base and
  exponent are both members). Powers first, then products, then addition.
  Two options are printed, since the order in which powers are tried
  changes the result:
  - `E1` largest base first (then largest exponent that fits):
    `5651 = 3469 + (19^2) + (11^3) + (17*7) + (13*5) + 199 + 107`
  - `E2` largest power value first:
    `5651 = 3469 + (2^11) + (19*5) + (13*3)`

  When both orders give the same equation only the `E1` line is printed,
  e.g. `E1: 101 = 19 + (7^2) + (11*3)`.
- **M1, without the base**: the multiplicative search applied to the whole
  prime instead of the difference. No base term is required; the pool is
  every quad prime below the target plus the royal members, so the largest
  products carry the number.
- **E3, powers first**: the largest power `b^e` below the prime, with base
  and exponent distinct members, then again the largest power below what is
  left as long as it covers at least half of it, and then the remainder
  written the additive way: quad primes added, largest first, closed by a
  flat royal `+`/`*` expression. If no choice of primes closes the
  remainder, the chain loses its last power, and finally the next largest
  first power is tried (11, 17 and 19, written from the royal quad alone, have
  no such form and fall back to the power-first search).

  ```
  A:  854921 = 845989 + 5657 + 3251 + 13 + 11
  M:  854921 = 845989 + (3469*2) + (199*7) + (193*3) + 17 + 5
  M1: 854921 = (427249*2) + (109*3) + (17*5) + 11
  E1: 854921 = 845989 + (19^3) + (17^2) + (199*5) + (11*7) + 197 + 191 + 107 + 103 + 101 + 13
  E2: 854921 = 845989 + (2^13) + (7^3) + (19*11) + (17*5) + 103
  E3: 854921 = (829^2) + (11^5) + (17^3) + 1489 + 107 + 101 + 19
  E3: 19497221 = (11^7) + (2^13) + 829 + 827 + 199 + 3
  E3: 31204931 = (11^7) + (3259^2) + (103^3) + 3467 + 193 + 191 + 101
  ```

  (7^7 = 823543 is closer to 854921 than 829^2, but it would use 7 twice.)
  A line that repeats an earlier line of the same prime (quad 1, where
  there is no base anyway) is not printed twice.

Every member is used at most once in an equation, and in A, M, E1 and E2
the base is always the last quad's 9-member. Term lists are stored in
`qarray.json` under `mul`, `exp` (E1) and `expv` (E2) of each difference,
and under `mul_nb` (M1) and `exp_nb` (E3) of each prime, as `["p", 5]`,
`["*", 17, 3]`, `["^", 7, 2]`. If a search ever gives up, the entry copies a
simpler way and is marked `fallback`; `-v` mentions it.

## Derive any number

`-d N` writes any integer N as a sum of quad primes below N plus one
expression in the royal members. Quad primes are only added; `*` and `-`
appear only among 2, 3, 5, 7. The largest quad prime that fits is taken
first, then the next, and the remainder is closed with a royal expression
in the same vocabulary as the chain equations: royal members added if that
suffices, else one product of two members, else two. Primes are re-chosen
between those passes if that is what it takes, so `53 = 19 + 17 + 7 + 5 + 3 + 2`
rather than `19 + 17 + 13 + 7 - 3`, and `928 = 823 + 103 + 2` rather than
`829 + 19 + 13 + (2*5*7) - 3`. Only when no choice of primes closes with
`+` and `*` does a minus enter, and only when even that fails a product of
three; below 300,000 that is nine integers (0, 1, 4, 92, 93, 94, 96, 99,
102) and one (99), whose pool 11, 13, 17, 19 is too small for anything else.

```
python3 lc.py -d 16     16 = 13 + 3
python3 lc.py -d 53     53 = 19 + 17 + 7 + 5 + 3 + 2
python3 lc.py -d 55     55 = 19 + 17 + 11 + 5 + 3
python3 lc.py -d 76     76 = 19 + 17 + (5*7) + 3 + 2
python3 lc.py -d 99     99 = 19 + 13 + (2*5*7) - 3
python3 lc.py -d 101    101 = 19 + 17 + 13 + 11 + (5*7) + (2*3)
python3 lc.py -d 0      0 = 3 + 2 - 5
python3 lc.py -d 5      5 = 2 + 3
python3 lc.py -d 7      7 = 2 + 5
python3 lc.py -d 2      2 = 2
```

A royal member is written from the royal members *below* it, never from
itself and never from a larger one: `-d 5` gives `5 = 2 + 3` rather than
`5 = 5`, and `-d 7` gives `7 = 2 + 5`. Each of those two has exactly one
such form. `2` and `3` keep `2 = 2` and `3 = 3`, because nothing below them
adds up to them - they are where the chain starts. Any other target picks up
a quad prime first, so this affects only 5 and 7; the chain equations are
unchanged, and a royal closing there is still the shortest one (`... + 5`,
not `... + 2 + 3`).

Every integer from 0 up to the next quad's first prime has such a
derivation (with 2, 3, 5, 7, 11, 13, 17, 19 every integer up to 156, so in
particular up to 101); the paper proves this for the whole chain. `-v` adds
which quad each prime came from. Two numbers give a range: `-d 53 83`
prints one line for every integer from 53 to 83. If N lies beyond the cached chain, the
chain is extended first, which for N near 10^9 takes under a minute once.

## About "each quad can be used only once"

The tool applies this as "each prime is used at most once in an equation";
several members of one quad may appear together (the reference equation
above uses both 19 and 17 from quad 1). The stricter reading, at most one
member per quad, is available with `--one-per-quad` and keeps its own cache
file `qarray_one_per_quad.json`. Under that reading quad 2 has no valid
equation: every `101..109` minus a single member of `11..19` leaves a
remainder (82 to 98) that no `+`/`*` expression in `2, 3, 5, 7` produces.

## How far it can go

Output ends with `N quads shown, M quads in the cache (file)`, so you always
know how much of the chain is built and which file it came from; `-v` adds the
column distribution and reuse statistics.

Two caches ship with the tool. `qarray.json` beside `lc.py` is the working one,
small and fast to load, and it grows as you ask for more. `paper/qarray_1e9.json`
is the published dataset, all 28,387 quadruplets below 10^9. When a command asks
for more than the working cache holds, the tool reads the published dataset
instead of rebuilding what already exists, so `./lc 20000 -o` answers in under a
second rather than spending two minutes on a chain that is already on disk. The
published file is only ever read: anything computed beyond it is written to
`qarray.json`. Pass `--cache FILE` to choose a file yourself.

Building the chain from nothing, measured on this Mac (Intel, Python 3.13):

| upper bound | digits | quads | time to build | cache size |
| --- | --- | --- | --- | --- |
| 1,000,000,000 | 10 | 28,387 | 35 s | 23 MB |
| 10,000,000,000 | 11 | ~180,000 | ~6 min (est.) | ~160 MB |

(Since only the first prime of each quad is searched for, a full build is
about four times faster than it used to be and the cache is half the size.)
Recommended limit: 10 digits (`--upto 9999999999`) is comfortable in one
run. 11 digits works but the JSON cache gets large and slow to load; past
that the cache would need a database and the sieve a compiled helper. Most
of the cache size comes from the base-free M1 and E3 equations of the first
primes, which are stored per prime rather than per unique difference.
Progress is checkpointed to the cache every 15 seconds, so an interrupted
run resumes where it stopped.

## Videos and app

Two explainer videos, narrated and captioned:

- Ladhe's Quad Conjecture: A New Pattern in Prime Quadruplets (28 min): https://youtu.be/_XSOJ0Yj77Q
- Build Any Number From Prime Quadruplets, Part 2 (11 min): https://youtu.be/JNWvt3hS540

Companion iOS app (the authors' free LE-Games app: the chain, the QuadQuest matching game and a printable practice sheet): https://apps.apple.com/app/id6767880385

## Paper

`paper/` holds the Zenodo preprint *Ladhe's Quad Conjecture* (DOI
https://doi.org/10.5281/zenodo.22286846, which always resolves to the latest
version) and everything needed to reproduce its
figures:

| File | Purpose |
| --- | --- |
| `ladhe_quad_conjecture.tex`, `.pdf` | the paper (`pdflatex ladhe_quad_conjecture.tex`, run twice) |
| `qarray_1e9.json` | the chain up to 10^9 (28,387 quads, 23 MB), built with `python3 lc.py --upto 999999999 --cache paper/qarray_1e9.json`; in the repository it is shipped as `qarray_1e9.json.gz`, run `gunzip` before using it |
| `quads_1e9.csv` | one row per quad member: for a first prime the base, gap, the A/M/E1/E2 equations and minimal lengths (M1/E3 are in the JSON); for the other three primes only their fixed form |
| `check.py` | independent re-verification of every stored equation (a shortest pure sum, or the largest-first form for the four exceptional gaps), prints the dataset SHA-256 |
| `stats.py` | every number quoted in the paper, plus `appendix_rows.tex` and the CSV |

## Executable

`lc.py` already runs directly (`./lc.py 10`). A standalone binary `lc` that
needs no Python install is built with PyInstaller:

```
cd /Users/pankajladhe/Pankaj/2018/AIStuff/RSAL/LC
python3 -m PyInstaller --onefile --name lc --distpath ./dist \
        --workpath ./build --specpath ./build lc.py
mv dist/lc ./lc && rm -rf build dist
./lc 10
```

Keep `lc` next to `qarray.json`: the binary reads and writes the cache in
its own folder. Rebuild it after editing `lc.py`.

## Files

| File | Purpose |
| --- | --- |
| `lc.py` | the program, no dependencies beyond Python 3 |
| `lc` | standalone macOS binary built from `lc.py` with PyInstaller |
| `qarray.json` | saved q-array: quads with base + difference, plus the `diffs` table of unique-difference equations |
| `qarray_one_per_quad.json` | same, for `--one-per-quad` (created on first use) |
| `paper/` | the paper, its dataset and the reproduction scripts (see "Paper") |
| `videos/` | two explainer videos, on YouTube at https://youtu.be/_XSOJ0Yj77Q (the conjecture, 28 min) and https://youtu.be/JNWvt3hS540 (build any number, 11 min); `videos/LINKS.md` has the links and thumbnails, plus the narration scripts, the YouTube upload package and the `build/` pipeline that rendered them (the MP4 files are too large for GitHub) |
