+--------------------+         +---------------------+         +----------------------+
|  Data Producers    | ----->  |   Kafka Cluster     | ----->  |   Data Consumers     |
| (arXiv API, etc.)  |         | (AWS MSK, multi-AZ) |         | (ETL, ML, Dashboard) |
+--------------------+         +---------------------+         +----------------------+
                                        |
                                        v
                             +-----------------------------+
                             |   Kafka Connect (MSK)       |
                             |   (Sink/Source Connectors)  |
                             +-----------------------------+
                                        |
                                        v
             +---------------------+   +-------------------+   +---------------------+
             | Amazon S3 (Data Lake)|   | OpenSearch (Search)|   | DynamoDB (NoSQL DB)|
             +---------------------+   +-------------------+   +---------------------+
                                        |
                                        v
                             +-----------------------------+
                             |   Analytics & Monitoring    |
                             | (SageMaker, QuickSight,     |
                             |  Prometheus, Grafana)       |
                             +-----------------------------+
