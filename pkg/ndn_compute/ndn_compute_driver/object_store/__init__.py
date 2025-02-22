"""
Library to store callables and shared variables for use by the worker.
Contains a server (an NDN app not to be confused with the executor's NDN app) that listens to workers' interests
for the objects. New objects are added by ndn_compute_remote and stored in sqlite.
"""

__all__ = ['DriverObjectStore']

from .object_store import DriverObjectStore
