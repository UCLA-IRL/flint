"""
ndn_compute_driver

Module callable from the command line, to be used as the entry point for the driver.

This module's logic lives in __main__. Its purpose is to host three components on the driver docker node:
- NDN app (used to send RDD interests)
- RPC server (for the remote NDN compute object NdnComputeRemote)
- NDN app (used to serve bytecode objects and shared variables)

Note that the RPC server and first NDN app live in the same process, thus requiring the use of nested asyncio.
"""