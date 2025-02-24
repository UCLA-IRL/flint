"""
Unofficial extensions for python-ndn for custom functionality when interfacing with other NDN nodes or the NFD router.
"""

__all__ = ["announce_prefix", "fetch_segments"]

from .routing_security import announce_prefix
from .segment_fetcher_v2 import fetch_segments
