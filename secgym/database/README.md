# Database Setup

## Data Download

The data can be downloaded from the following sources:
- Directly from Hugging Face
- From Azure

### 1. Download from Hugging Face or provided data source

Please download the data from the proivided link.


### 2. Original Handling Process
1. Register an account at Alphine Ski House.
2. Login in to the azure account.
```bash
az login
```
3. Uncomment the code in `download_data.py` to download the Alphine Ski House data or for 8 different incidents.
The `alphineskihouse` folder contains logs from Jun 20, 2024 to Jul 23, 2024. While each incident folder contains logs for that specific incident from the start of incident to the end of the incident.
```bash
python download_logs.py
```
4. Run process_logs.py to process the data. This will change the some file's entry from double quotes to single quotes.
```bash
python process_logs.py
```


## Environment Setup

We are using MYSQL docker container for the database. Please first install docker and docker-compose and then pull the mysql image:

```bash
docker pull mysql:9.0
```

Then run the following command to start the mysql container:


```bash
python setup_database.py --csv <path_to_csv_folder> --port <port> --sql_file <path_to_sql_file> --container_name <container_name> 
```


## Data Anonymization

1. Identify PII related columns and fields: `pii_col_identify.py`

2. With that, we run `pii_mapper.py` to map the PII fields to a anonymized value.

3. Finally, we run `pii_replace.py` to replace the PII fields with the anonymized value.
