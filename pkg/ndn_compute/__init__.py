"""
ndn_compute

This package contains all logic, libraries and entry points for the following entities of the distributed system:
- worker
- driver
- client

Explanation of modules and submodules:
- ndn_compute_client: Client library used on local machine by end-users, "core interface", calls ndn_compute_remote via
  RPC
- ndn_compute_remote: Driver's version of the "core interface", exposed via RPC. Note that for marshalling simplicity,
  the interface is different than ndn_compute_client; it is accounted for in the client logic.
- ndn_compute_driver: Entry point for the node acting as a driver. The entry point is responsible for starting three
  "processes": the object store server, the RPC server, and the executor's NDN app. Note that the RPC server and NDN app
  live in the same process, thus requiring the use of nested asyncio. (Note that the previous sentences contradict with
  the hierarchy of the layered diagram, as the diagram shows module interaction and *not* the process tree). The
  aforementioned RPC server serves objects in the ndn_compute_remote module. In addition to serving ndn_compute_remote,
  its submodules are used by ndn_compute_remote's classes.
  - ndn_compute_driver.executor: Contains the logic to "materialize" RDDs through interests to the worker upon request
    by ndn_compute_remote.
  - ndn_compute_driver.lineage_manager: Library to keep track of the lineage tree, used by ndn_compute_remote.
  - ndn_compute_driver.object_store: Library to store callables and shared variables for use by the worker.
    Contains a server (an NDN app not to be confused with the executor's NDN app) that listens to workers' interests
    for the objects. New objects are added by ndn_compute_remote and stored in sqlite.
- ndn_compute_worker: Entry points for nodes acting as workers. The entry point is responsible for starting an NDN app
  listening for RDD interests.
  - ndn_compute_worker.handler: Contains interest handlers that perform computations upon interest in an RDD, also reads
    base files from underlying datastore.
- python_ndn_ext: Unofficial extensions for python-ndn for custom functionality when interfacing with other NDN nodes
  or the NFD router.


Layered architecture diagram of various modules and submodules (arrows indicate network traffic):

* = entry point
- = library

**********************
*    Client Code     *                   **********************************************************
**********************                   *                    ndn_compute_driver                  *
----------------------           ---------------------------------------------------------------- *
| ndn_compute_client | --RPC---> | ndn_compute_remote  ~~~ ~~~ ~~~ ~~~ ~~~ ~~~ ~~~ ~~~ ~~~ ~~~  | *
----------------------           ---------------------------------------------------------------- *
                                         * --------------------  -----------------  ------------- *           *********************
                                         * | .lineage_manager |  | .object_store |  | .executor |-----NDN---  *ndn_compute_worker *
                                         * --------------------  -------  ------ |  ------------- *        |---> ---------------  *
                                         ******************************| .server |*****************           *  |  .handler   |  *
                                                                       ------^----                       ------- ---------------  *
                                                                             |                           |    *********************
                                                                             ---------------NDN-----------       | (filesystem)|
                                                                                                                 ---------------
"""


__all__ = ['NdnComputeClient']


from .ndn_compute_client import NdnComputeClient
