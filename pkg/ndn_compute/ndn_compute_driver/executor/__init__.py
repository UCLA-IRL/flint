"""
Contains the logic to "materialize" RDDs through interests to the worker upon request by ndn_compute_remote.
"""

__all__ = ['DriverExecutor']

from .executor import DriverExecutor
