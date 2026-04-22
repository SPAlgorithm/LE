"""
ladhe_cert_cli.py — argparse-based CLI around ladhe_cert.py.

Lets you bootstrap a CA, issue certs, and sign/verify documents
without touching any Python code.

Quick examples:

    # One-time: create a root CA
    python3 ladhe_cert_cli.py init-ca --cn "Ladhe Test Root CA"

    # Issue a cert for any subject by name
    python3 ladhe_cert_cli.py issue --cn xyz@example.com
    python3 ladhe_cert_cli.py issue --cn bob@example.com --days 180

    # Verify a cert against the CA
    python3 ladhe_cert_cli.py verify --cert demo_pki/xyz.cert.pem

    # Sign a document with a subject's key
    python3 ladhe_cert_cli.py sign --subject xyz --doc hello.txt

    # Verify a signed document
    python3 ladhe_cert_cli.py verify-doc --subject xyz \
        --doc hello.txt --sig hello.txt.sig
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import ladhe_rsa as LR
import ladhe_cert as LC


DEFAULT_DIR = Path("demo_pki")


def _safe_name(cn: str) -> str:
    """Turn a CN like 'alice@example.com' into a filesystem-safe stem."""
    stem = cn.split("@", 1)[0]
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("._-")
    return stem or "subject"


# ----------------------------------------------------------------------
# Sub-commands
# ----------------------------------------------------------------------
def cmd_init_ca(args: argparse.Namespace) -> int:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    ca_path  = out / "ca.cert.pem"
    key_path = out / "ca.key.pem"
    if (ca_path.exists() or key_path.exists()) and not args.force:
        print(f"refusing to overwrite existing CA in {out} "
              f"(use --force to replace)", file=sys.stderr)
        return 2

    ca_cert, ca_sk = LC.create_ca(
        common_name=args.cn,
        validity_days=args.days,
        min_prime_bits=args.bits,
    )
    LC.write_cert(ca_path, ca_cert)
    LC.write_private_key(key_path, ca_sk)
    print(f"CA created:   CN={args.cn}  valid_days={args.days}")
    print(f"  cert -> {ca_path}")
    print(f"  key  -> {key_path}  (keep secret)")
    return 0


def cmd_issue(args: argparse.Namespace) -> int:
    ca_dir = Path(args.ca_dir)
    out    = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    ca_cert_path = ca_dir / "ca.cert.pem"
    ca_key_path  = ca_dir / "ca.key.pem"
    if not ca_cert_path.exists() or not ca_key_path.exists():
        print(f"CA not found in {ca_dir} — run `init-ca` first.",
              file=sys.stderr)
        return 2

    ca_cert = LC.read_cert(ca_cert_path)
    ca_sk   = LC.read_private_key(ca_key_path)

    stem      = args.name or _safe_name(args.cn)
    cert_path = out / f"{stem}.cert.pem"
    key_path  = out / f"{stem}.key.pem"
    if (cert_path.exists() or key_path.exists()) and not args.force:
        print(f"refusing to overwrite existing files for "
              f"'{stem}' (use --force).", file=sys.stderr)
        return 2

    subject_pk, subject_sk = LR.keygen(min_prime_bits=args.bits)
    LC.write_private_key(key_path, subject_sk)

    subject_cert = LC.issue_certificate(
        ca_cert, ca_sk,
        subject_cn=args.cn,
        subject_pk=subject_pk,
        validity_days=args.days,
    )
    LC.write_cert(cert_path, subject_cert)

    ok, reason = LC.verify_certificate(subject_cert, ca_cert)
    print(f"issued:  CN={args.cn}  valid_days={args.days}")
    print(f"  cert -> {cert_path}")
    print(f"  key  -> {key_path}  (keep secret)")
    print(f"  self-check verify: {ok} ({reason})")
    return 0 if ok else 1


def cmd_verify(args: argparse.Namespace) -> int:
    cert = LC.read_cert(Path(args.cert))
    ca   = LC.read_cert(Path(args.ca))
    ok, reason = LC.verify_certificate(cert, ca)
    print(f"verify: {ok} ({reason})")
    return 0 if ok else 1


def _resolve_subject_files(args: argparse.Namespace):
    """Allow either --subject <stem> (looks in --dir) or explicit
    --cert / --key paths."""
    if args.subject:
        d = Path(args.dir)
        cert = d / f"{args.subject}.cert.pem"
        key  = d / f"{args.subject}.key.pem"
    else:
        cert = Path(args.cert) if args.cert else None
        key  = Path(args.key)  if args.key  else None
    return cert, key


def cmd_sign(args: argparse.Namespace) -> int:
    cert_path, key_path = _resolve_subject_files(args)
    if not cert_path or not key_path:
        print("need --subject NAME or both --cert and --key",
              file=sys.stderr)
        return 2
    cert = LC.read_cert(cert_path)
    sk   = LC.read_private_key(key_path)
    doc  = Path(args.doc).read_bytes()
    sig_bytes = LC.sign_document(doc, cert, sk)

    sig_path = Path(args.sig) if args.sig else Path(f"{args.doc}.sig")
    sig_path.write_bytes(sig_bytes)
    print(f"signed: {args.doc}  ({len(doc)} bytes)")
    print(f"  signer: {cert.subject.get('CN')}")
    print(f"  sig ->  {sig_path}  ({len(sig_bytes)} bytes)")
    return 0


def cmd_verify_doc(args: argparse.Namespace) -> int:
    cert_path, _ = _resolve_subject_files(args)
    if not cert_path:
        print("need --subject NAME or --cert PATH", file=sys.stderr)
        return 2
    cert = LC.read_cert(cert_path)
    doc  = Path(args.doc).read_bytes()
    sig  = Path(args.sig).read_bytes()
    ok = LC.verify_document(doc, sig, cert)
    print(f"document: {args.doc}")
    print(f"  signer:  {cert.subject.get('CN')}")
    print(f"  verify:  {ok}")
    return 0 if ok else 1


# ----------------------------------------------------------------------
# Argument parser
# ----------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ladhe_cert_cli",
        description="CLI for Ladhe-RSA certificate operations.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    # init-ca
    q = sub.add_parser("init-ca", help="create a self-signed root CA")
    q.add_argument("--cn",   required=True, help="CA common name")
    q.add_argument("--days", type=int, default=3650)
    q.add_argument("--bits", type=int, default=24,
                   help="min prime bits for keygen (default 24)")
    q.add_argument("--out",  default=str(DEFAULT_DIR))
    q.add_argument("--force", action="store_true",
                   help="overwrite existing CA files")
    q.set_defaults(func=cmd_init_ca)

    # issue
    q = sub.add_parser("issue", help="issue a cert for a new subject")
    q.add_argument("--cn",    required=True,
                   help="subject common name, e.g. xyz@example.com")
    q.add_argument("--name",  default=None,
                   help="filename stem (default: derived from --cn)")
    q.add_argument("--days",  type=int, default=365)
    q.add_argument("--bits",  type=int, default=24)
    q.add_argument("--ca-dir", default=str(DEFAULT_DIR),
                   help="directory containing ca.cert.pem + ca.key.pem")
    q.add_argument("--out",   default=str(DEFAULT_DIR),
                   help="where to write <name>.cert.pem + <name>.key.pem")
    q.add_argument("--force", action="store_true")
    q.set_defaults(func=cmd_issue)

    # verify
    q = sub.add_parser("verify", help="verify a cert against a CA cert")
    q.add_argument("--cert", required=True)
    q.add_argument("--ca",   default=str(DEFAULT_DIR / "ca.cert.pem"))
    q.set_defaults(func=cmd_verify)

    # sign
    q = sub.add_parser("sign", help="sign a document with a subject key")
    q.add_argument("--subject", help="subject stem (reads <dir>/<stem>.cert.pem + .key.pem)")
    q.add_argument("--dir",     default=str(DEFAULT_DIR))
    q.add_argument("--cert",    help="explicit cert path (overrides --subject)")
    q.add_argument("--key",     help="explicit key path  (overrides --subject)")
    q.add_argument("--doc",     required=True)
    q.add_argument("--sig",     default=None,
                   help="output signature path (default: <doc>.sig)")
    q.set_defaults(func=cmd_sign)

    # verify-doc
    q = sub.add_parser("verify-doc",
                       help="verify a document + signature under a cert")
    q.add_argument("--subject", help="subject stem (reads <dir>/<stem>.cert.pem)")
    q.add_argument("--dir",     default=str(DEFAULT_DIR))
    q.add_argument("--cert",    help="explicit cert path (overrides --subject)")
    q.add_argument("--key",     help=argparse.SUPPRESS)  # unused, kept for symmetry
    q.add_argument("--doc",     required=True)
    q.add_argument("--sig",     required=True)
    q.set_defaults(func=cmd_verify_doc)

    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
