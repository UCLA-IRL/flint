# Flint

## Distributed Data Processing Engine (over Named Domain Networking)

### Introduction

Flint is a prototype distributed computing system for processing distributed datasets. Typically, these datasets 
are tabular data. Similar to Spark, transformations and reductions are run over a base dataset (called an RDD) to 
lazily obtain a new RDD with the operation applied.

Through this prototype, we aim to showcase the capability of Named Data Networking to fit and fulfill application needs.
Exploiting features such as routing over names, caching, and data security, we aim to use NDN as a more natural 
paradigm to express communication-intensive big data applications.

Flint runs on a Docker cluster, with Python as the primary language. A driver node communicates with various 
worker nodes as well as the NFD router.  

### Installation / Running

ndn-compute is tested on Python 3.11 and Docker.

#### Option 1 (Recommended): Interactive Notebook / Getting Started Guide

Please see `notebooks/getting-started.ipynb` for a guide on how to initialize and run the cluster.

#### Option 2: CLI

The commands done here are (mostly) equivalent to those in the notebook.

**Starting up (first time):**

```bash
echo "Installing Dependencies..."
git submodule update --init --recursive
bash -c 'for dir in ./pkg/*/; do [ -d "$dir" ] && pip install --find-links=./pkg "$dir"; done'

echo "Security Setup..."
python -m ndn_compute_key_creator --path sec_data/ --entities driver worker

echo "Generating Data..."
rm -rf generated_data
mkdir -p generated_data/flat/appA
mkdir -p generated_data/flat/appB

python -m ndn_compute_jsonl_generator "generated_data/flat/appA/events.log.jsonl" 200
python -m ndn_compute_jsonl_generator "generated_data/flat/appB/events.log.jsonl" 500

mkdir -p generated_data/distributed
python -m ndn_compute_fs_creator "generated_data/flat" "generated_data/distributed" --partitions 3 --copies 2 --chunk-size 64

echo "Starting Cluster..."
python -m ndn_compute_cluster_manager start 3

echo "Cluster ready! Dropping into Python REPL..."
python
```

**Starting up (after changing code or keys):**
```bash
echo "Starting Cluster..."
python -m ndn_compute_cluster_manager start 3 --rebuild

echo "Cluster ready! Dropping into Python REPL..."
python
```

**Starting up (normal):**
```bash
echo "Starting Cluster..."
python -m ndn_compute_cluster_manager start 3

echo "Cluster ready! Dropping into Python REPL..."
python
```

**Using in Python script/REPL:**
```py
from ndn_compute_client import NdnComputeClient
client = NdnComputeClient('http://localhost:5214')

dataset = client.create_dataset("appB/events.log.jsonl")

pred = lambda row: row['event_type'] == 'purchase' and row['device'] == 'tablet' and row['browser'] == 'safari'
ipad_purchases = dataset.filter(pred).collect()

print(ipad_purchases.head())

exit()
```

**Cleanup:**
```bash
echo "Stopping Cluster..."
python -m ndn_compute_cluster_manager stop
```
