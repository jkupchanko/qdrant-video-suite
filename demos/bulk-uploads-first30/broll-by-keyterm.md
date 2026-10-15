# B-roll by key term: bulk_script.md against https://qdrant.tech/documentation/production-operations/bulk-data-import/

| call | score | line | key terms | section |
|---|---|---|---|---|
| none | 0.0 | Bulk Uploading Data to Qdrant | qdrant, uploading |  |
| none | 0.0 | When uploading large amounts of data, Qdrant isn't just storing vectors. | qdrant, uploading, vectors |  |
| none | 0.0 | It's also handling indexing, payloads, and much more in the background. | indexing |  |
| none | 0.0 | There's no single configuration for every workload. |  |  |
| none | 0.0 | So we will go over a few different options and best practices you can try. |  |  |
| none | 0.0 | Before we start, dense and sparse vectors. | dense, sparse, vectors |  |
| B-ROLL | 6.5 | Dense vectors typically use HNSW, while sparse vectors use a separate sparse index. | hnsw, sparse index | Defer HNSW Indexing During Ingestion |
| none | 0.0 | Because they're indexed differently, they can create different memory and performance considerations during bulk uploads. | memory, uploads |  |
| none | 0.0 | Now let's start with our first option for dense vectors. | dense, vectors |  |
| B-ROLL | 9.0 | The first option for dense vectors is storing the original vectors on disk. | on disk | Option 1: Reduce Memory Pressure |
| none | 0.0 | For large uploads, the raw vector data itself can consume a lot of RAM. | ram, uploads, vector |  |
| none | 0.0 | This reduces RAM usage as the collection grows. | collection, ram |  |
| none | 0.0 | Search may rely more on disk access, potentially increasing latency. | on disk |  |
| B-ROLL | 9.0 | The second dense-vector option is creating your payload indexes before uploading. | payload indexes | Option 2: Create Payload Indexes (Before Uploading) |
| hold | 1.5 | If you already know which fields you'll filter on, such as category, tenant ID, source, or user ID, create those indexes first. | filter, tenant | Option 2: Create Payload Indexes (Before Uploading) |
| none | 0.0 | This avoids creating those indexes after a large dataset is already populated. | indexes | Option 2: Create Payload Indexes (Before Uploading) |
| none | 0.0 | Only index fields you actually plan to filter on. | filter |  |
| B-ROLL | 9.0 | The final dense-vector option is quantization. | quantization | Option 3: Quantization to Balance Memory and Search Performance |
| hold | 7.9 | Quantization lets you keep the original vectors on disk while using a smaller compressed representation for search. | on disk, quantization | Option 3: Quantization to Balance Memory and Search Performance |
| none | 0.0 | This can significantly reduce memory usage while keeping search performance practical. | memory | Option 3: Quantization to Balance Memory and Search Performance |
| none | 0.0 | Compression may affect search quality, so test it with your own data. |  |  |
| none | 0.0 | Those first three options were for dense vectors. | dense, vectors |  |
| none | 0.0 | Now let's move to sparse vectors. | sparse, vectors |  |
| B-ROLL | 8.4 | For sparse vectors, you can store the sparse index itself on disk. | on disk, sparse index | Option 4: Reduce Sparse Index Memory During Uploads |
| hold | 0.0 | This can be useful when a large sparse index starts consuming too much memory. | sparse index | Option 4: Reduce Sparse Index Memory During Uploads |
| hold | 0.0 | This reduces RAM usage as the sparse index grows. | sparse index | Option 4: Reduce Sparse Index Memory During Uploads |
| hold | 0.0 | Sparse searches may become more dependent on disk performance. | on disk | Option 4: Reduce Sparse Index Memory During Uploads |
| none | 0.0 | So far, those options depended on whether you were using dense or sparse vectors. | dense, sparse, vectors | Option 4: Reduce Sparse Index Memory During Uploads |
| none | 0.0 | Now let's cover three best practices that apply to both. |  |  |
| B-ROLL | 7.0 | The first best practice is to batch your uploads. | batch | Batch Your Uploads |
| none | 0.0 | Uploading points one at a time creates unnecessary network and processing overhead. | uploading |  |
| hold | 6.5 | A batch size around 64 to 256 points is a good starting point. | batch | Batch Your Uploads |
| hold | 0.0 | Larger batches use more memory and are more expensive to retry if they fail. | batches | Batch Your Uploads |
| B-ROLL | 4.4 | The second best practice is using multiple upload workers. | workers | Parallelize Uploads |
| hold | 0.0 | This allows several batches to be sent at the same time instead of relying on one upload stream. | batches | Parallelize Uploads |
| hold | 0.0 | Start with a small number of workers and increase based on your deployment. | workers | Parallelize Uploads |
| hold | 0.0 | Too much parallelism can overwhelm CPU, memory, disk, or network resources. | parallelism | Parallelize Uploads |
| B-ROLL | 7.0 | And finally, for larger uploads, consider using multiple shards. | shards | Use Multiple Shards for Larger Uploads |
| hold | 0.0 | Each shard has its own write path, allowing more ingestion work to happen in parallel. | parallel, shard | Use Multiple Shards for Larger Uploads |
| hold | 0.0 | This can work especially well when combined with parallel upload workers. | parallel, workers | Use Multiple Shards for Larger Uploads |
| hold | 0.0 | Every shard adds overhead, so more shards are not always better. | shard, shards | Use Multiple Shards for Larger Uploads |
| none | 0.0 | The right combination depends on whether your priority is memory usage, ingestion speed, search performance, or a balance of all three. | memory |  |

## Markers for the recorder

[B-ROLL: https://qdrant.tech/documentation/production-operations/bulk-data-import/ | Dense vectors typically use HNSW, while sparse vectors use a separate sparse index. | section: Defer HNSW Indexing During Ingestion | 5s]
[B-ROLL: https://qdrant.tech/documentation/production-operations/bulk-data-import/ | The first option for dense vectors is storing the original vectors on disk. | section: Option 1: Reduce Memory Pressure | 5s]
[B-ROLL: https://qdrant.tech/documentation/production-operations/bulk-data-import/ | The second dense-vector option is creating your payload indexes before uploading. | section: Option 2: Create Payload Indexes (Before Uploading) | 5s]
[B-ROLL: https://qdrant.tech/documentation/production-operations/bulk-data-import/ | The final dense-vector option is quantization. | section: Option 3: Quantization to Balance Memory and Search Performance | 5s]
[B-ROLL: https://qdrant.tech/documentation/production-operations/bulk-data-import/ | For sparse vectors, you can store the sparse index itself on disk. | section: Option 4: Reduce Sparse Index Memory During Uploads | 5s]
[B-ROLL: https://qdrant.tech/documentation/production-operations/bulk-data-import/ | The first best practice is to batch your uploads. | section: Batch Your Uploads | 5s]
[B-ROLL: https://qdrant.tech/documentation/production-operations/bulk-data-import/ | The second best practice is using multiple upload workers. | section: Parallelize Uploads | 5s]
[B-ROLL: https://qdrant.tech/documentation/production-operations/bulk-data-import/ | And finally, for larger uploads, consider using multiple shards. | section: Use Multiple Shards for Larger Uploads | 5s]
