#!/usr/bin/env bash
#
# demo.sh — End-to-end demo of the Ladhe signature scheme (v3).
#
# Usage:
#   chmod +x demo.sh         # first time only
#   ./demo.sh                # run the whole demo
#
# Runs cleanly on macOS and Linux with Python 3.9+.
#

set -euo pipefail
cd "$(dirname "$0")"

banner() {
    printf "\n"
    printf "============================================================\n"
    printf "  %s\n" "$1"
    printf "============================================================\n"
}

pause() {
    if [ -t 1 ]; then
        printf "\n[press ENTER to continue] "
        read -r _
    fi
}

# -----------------------------------------------------------
banner "Demo 1 — End-to-end: KeyGen → Sign → Verify → Tamper → LDP"
# -----------------------------------------------------------
# 5-digit prime: KeyGen completes in milliseconds for the demo.
python3 ladhe_rsa.py demo 5
pause

# -----------------------------------------------------------
banner "Demo 2 — Timing benchmark at several prime sizes"
# -----------------------------------------------------------
python3 ladhe_rsa.py bench
pause

# -----------------------------------------------------------
banner "Demo 3 — The LDP challenge (for cryptanalysts)"
# -----------------------------------------------------------
# Generates a fresh (P, h) pair whose witness we hold but don't
# release. Anyone who can recover a valid prime decomposition
# faster than SHA-256 preimage has broken the scheme.
python3 -c "
import ladhe_rsa as LR
P, h = LR.generate_ldp_challenge(bits=32)
print('Your LDP challenge:')
print(f'  P = {P}')
print(f'  h = {h.hex()}')
print()
print('Task: find distinct odd primes (p_1 < p_2 < ... < p_k) with k odd')
print('      such that sum(p_i) = P  AND')
print('      sha256(encode_W(pair_compress(primes))) == h')
print()
print('encode_W and pair_compress are defined in ladhe_rsa.py.')
"
pause

# -----------------------------------------------------------
banner "Demo 4 — Unit tests"
# -----------------------------------------------------------
python3 -m unittest test_ladhe_rsa -v
pause

# -----------------------------------------------------------
banner "Demo 5 — One-liner sanity check"
# -----------------------------------------------------------
python3 -c "
import ladhe_rsa as LR
pk, sk = LR.keygen(up1=5)
sig = LR.sign(b'hi', sk)
print('genuine message verifies:', LR.verify(b'hi', sig, pk))
print('tampered message rejects:', not LR.verify(b'evil', sig, pk))
"
pause

# -----------------------------------------------------------
banner "Demo 6 — Practical software-signing example"
# -----------------------------------------------------------
# Bob signs a release, an attacker tampers (fails),
# Alice verifies the genuine release (succeeds).
python3 example_code_signing.py

printf "\n"
printf "============================================================\n"
printf "  All demos complete.\n"
printf "\n"
printf "  Next steps:\n"
printf "    * Run ./demo_x509.sh for the X.509 + OpenSSL demo.\n"
printf "    * Read SP_Paper_v3.pdf for the scheme specification.\n"
printf "    * If you break it, open an issue on the GitHub repo.\n"
printf "============================================================\n"
