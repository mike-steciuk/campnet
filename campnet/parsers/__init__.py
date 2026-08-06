"""Parsers that normalize provider-specific responses."""

from campnet.parsers.quectel import parse_quectel_snapshot

__all__ = ["parse_quectel_snapshot"]
