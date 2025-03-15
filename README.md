# ndn-compute

## Distributed Data Processing Engine (over Named Domain Networking)

### Introduction

ndn-compute is a prototype distributed computing system for processing distributed datasets. Typically, these datasets 
are tabular data. Similar to Spark, transformations and reductions are run over a base dataset (called an RDD) to 
lazily obtain a new RDD with the operation applied.

Through this prototype, we aim to showcase the capability of Named Data Networking to fit and fulfill application needs.
Exploiting features such as routing over names, caching, and data security, we aim to use NDN as a more natural 
paradigm to express communication-intensive big data applications.

ndn-compute runs on a Docker cluster, with Python as the primary language. A driver node communicates with various 
worker nodes as well as the NFD router.  

### Installation / Running

ndn-compute is tested on Python 3.11 and Docker.

Please see `notebooks/getting-started.ipynb` for a guide on how to initialize and run the cluster.
