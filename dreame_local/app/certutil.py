"""Zertifikats-Material aufloesen und die lokale API-CA erzeugen.

Die API (:13267) braucht ein Leaf mit SAN <region>.iot.dreame.tech, das HA
vertraut. Beim ersten Start wird eine eigene CA + Leaf nach /data/certs
generiert; api_cert/api_key aus den Optionen ueberschreiben das Ergebnis.
"""
from __future__ import annotations

import datetime
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID


def resolve_material(value: str, fallback: str, data_dir: Path, filename: str) -> str:
    value = (value or "").strip()
    if not value:
        return fallback
    if "-----BEGIN" in value:
        target = data_dir / "generated"
        target.mkdir(parents=True, exist_ok=True)
        out = target / filename
        out.write_text(value + "\n")
        return str(out)
    return value


def _pem_key(key) -> bytes:
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    )


def ensure_api_cert(data_dir: Path, region: str = "eu") -> tuple[str, str, str]:
    """CA + Leaf unter data_dir/certs erzeugen (falls noch nicht vorhanden).

    Rueckgabe: (api_chain.pem, api.key, ca.pem).
    """
    certs = data_dir / "certs"
    certs.mkdir(parents=True, exist_ok=True)
    chain = certs / "api_chain.pem"
    leaf_key_p = certs / "api.key"
    ca_pem_p = certs / "ca.pem"
    if chain.is_file() and leaf_key_p.is_file() and ca_pem_p.is_file():
        return str(chain), str(leaf_key_p), str(ca_pem_p)

    region = (region or "eu").strip().lower() or "eu"
    host = f"{region}.iot.dreame.tech"
    sans = []
    for name in (host, "*.iot.dreame.tech", f"*.mt.{region}.iot.dreame.tech"):
        if name not in sans:
            sans.append(name)

    now = datetime.datetime.now(datetime.timezone.utc)
    ca_key = ec.generate_private_key(ec.SECP256R1())
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Dreame Local CA")])
    ca_cert = (
        x509.CertificateBuilder()
        .subject_name(ca_name)
        .issuer_name(ca_name)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=3650))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=True,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .sign(ca_key, hashes.SHA256())
    )

    leaf_key = ec.generate_private_key(ec.SECP256R1())
    leaf = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, host)]))
        .issuer_name(ca_cert.subject)
        .public_key(leaf_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=3650))
        .add_extension(x509.SubjectAlternativeName([x509.DNSName(s) for s in sans]), critical=False)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=True,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
        .sign(ca_key, hashes.SHA256())
    )

    ca_pem_p.write_bytes(ca_cert.public_bytes(serialization.Encoding.PEM))
    (certs / "ca.key").write_bytes(_pem_key(ca_key))
    leaf_key_p.write_bytes(_pem_key(leaf_key))
    leaf_pem = leaf.public_bytes(serialization.Encoding.PEM)
    (certs / "api.pem").write_bytes(leaf_pem)
    chain.write_bytes(leaf_pem + ca_pem_p.read_bytes())
    return str(chain), str(leaf_key_p), str(ca_pem_p)
