#!/usr/bin/env bash
#
# setup.sh — Bootstrap the Alice & Bob demo PKI.
#
# Creates a self-signed Acme Quantum CA, then issues a certificate
# for Alice and one for Bob, all using Ladhe v3 keygen.
#
# Run from this folder:
#     ./setup.sh
#
# Idempotent: safe to re-run (uses --force to overwrite existing certs).
# Preserves purchase_order.txt and the README.

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
LADHE="$(cd "$HERE/.." && pwd)"
DIGITS="${DIGITS:-5}"     # decimal-digit count for the public prime P

cd "$LADHE"

mkdir -p "$HERE/ca" "$HERE/alice" "$HERE/bob"

echo ">> Bootstrapping Acme Quantum CA (--digits $DIGITS)..."
python3 ladhe_cert_cli.py init-ca \
    --cn "Acme Quantum CA" \
    --out "$HERE/ca" \
    --digits "$DIGITS" --force

echo ""
echo ">> Issuing Alice's certificate..."
python3 ladhe_cert_cli.py issue \
    --cn alice@acme.com \
    --ca-dir "$HERE/ca" \
    --out "$HERE/alice" \
    --digits "$DIGITS" --force

echo ""
echo ">> Issuing Bob's certificate..."
python3 ladhe_cert_cli.py issue \
    --cn bob@acme.com \
    --ca-dir "$HERE/ca" \
    --out "$HERE/bob" \
    --digits "$DIGITS" --force

echo ""
echo ">> Cleaning up stale runtime artefacts..."
rm -f "$HERE/alice/"*.sig \
      "$HERE/bob/purchase_order.txt"* \
      "$HERE/bob/alice.cert.pem"

# Make a copy of the document into Alice's directory for the demo.
cp "$HERE/purchase_order.txt" "$HERE/alice/purchase_order.txt"

echo ""
echo "==============================================="
echo "  Demo PKI ready."
echo "  CA:    $HERE/ca"
echo "  Alice: $HERE/alice"
echo "  Bob:   $HERE/bob"
echo ""
echo "  Next: ./run.sh"
echo "==============================================="
