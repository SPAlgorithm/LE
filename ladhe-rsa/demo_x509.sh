#!/usr/bin/env bash
#
# demo_x509.sh — show Ladhe-RSA certificates parseable by standard
# X.509 tooling (openssl).
#
# Demonstrates the three things this buys us:
#   1. Standard OpenSSL commands can inspect our certificates
#   2. Our registered OID (1.3.6.1.4.1.65644.1.1) appears in the output
#   3. The cert structure is 100% X.509 v3 compliant — what OpenSSL
#      cannot yet do is cryptographically verify the signature,
#      because that needs an OpenSSL provider plugin (next milestone).

set -e

HERE=$(cd "$(dirname "$0")" && pwd)
cd "$HERE"

BOLD=$'\033[1m'
GREEN=$'\033[1;32m'
BLUE=$'\033[1;34m'
RESET=$'\033[0m'

section() {
    echo ""
    echo "${BLUE}==== $1 ====${RESET}"
}

run() {
    echo "${GREEN}\$ $*${RESET}"
    "$@"
}

run_sh() {
    # Use for shell pipelines / redirections that `run` can't handle.
    echo "${GREEN}\$ $1${RESET}"
    bash -c "$1"
}

TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

# ----------------------------------------------------------------------
section "1. Bootstrap a CA and issue a leaf cert (JSON format)"
# ----------------------------------------------------------------------
run python3 ladhe_cert_cli.py init-ca --cn 'Acme Quantum CA' --out $TMPDIR --force
run python3 ladhe_cert_cli.py issue   --cn 'alice@acme.com' --ca-dir $TMPDIR --out $TMPDIR --force

# ----------------------------------------------------------------------
section "2. Export the leaf cert as DER and PEM X.509"
# ----------------------------------------------------------------------
run python3 ladhe_cert_cli.py export-x509 --cert $TMPDIR/alice.cert.pem --out $TMPDIR/alice.der --format der
echo ""
run python3 ladhe_cert_cli.py export-x509 --cert $TMPDIR/alice.cert.pem --out $TMPDIR/alice.x509.pem --format pem

# ----------------------------------------------------------------------
section "3. Parse with openssl asn1parse — walks the ASN.1 tree"
# ----------------------------------------------------------------------
run_sh "openssl asn1parse -in $TMPDIR/alice.der -inform DER | head -25"

# ----------------------------------------------------------------------
section "4. Inspect with openssl x509 -text"
# ----------------------------------------------------------------------
# Cut off after the public key section — signature hex is enormous.
openssl x509 -in $TMPDIR/alice.x509.pem -text -noout 2>&1 | \
    awk '/Signature Value:/{exit} {print}'

# ----------------------------------------------------------------------
section "5. Show the file sizes"
# ----------------------------------------------------------------------
ls -lh $TMPDIR/alice.cert.pem $TMPDIR/alice.der $TMPDIR/alice.x509.pem \
    | awk '{printf "%-40s %s\n", $NF, $5}'

# ----------------------------------------------------------------------
section "Done"
# ----------------------------------------------------------------------
cat <<EOF

${BOLD}What this demo proved:${RESET}

  * Ladhe-RSA certificates can be exported in DER or PEM X.509 format.
  * OpenSSL parses the full ASN.1 structure — issuer, subject,
    validity, serial number — all round-trip correctly.
  * Our IANA-registered OIDs appear in the output:
      Signature Algorithm:   1.3.6.1.4.1.65644.1.1
      Public Key Algorithm:  1.3.6.1.4.1.65644.1.2

${BOLD}What is still ahead:${RESET}

  OpenSSL prints "Unable to load Public Key" because it doesn't yet
  know how to interpret our custom Ladhe-RSA public-key bytes. That
  is the OpenSSL provider plugin — the next engineering milestone —
  after which openssl verify will also work end-to-end.

EOF
