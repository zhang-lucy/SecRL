# Data processing

- Need to decide: what tables are needed, confirm they are plugged in.

## Logging
**1. Download logs**

```bash
python download_logs.py
```
- Logs from a single attack from a certain time range.
- Benign user logs from a longer time range.

**2. Data synthesis**

- Latest: Remove this part
Synthesize data using LLMs
```bash
python synthesize_logs.py
```

**3. Data preprocessing**

    - TODO: need to reset the time
    - TODO: the logs may contain other attacks, we may need to filter them out.

Three level of logs:

- Easy: logs from the attack + data from one day of benign user logs.
- Medium: logs from the attack + logs from a week of benign user logs. # start from jun 27 to jul 3
- Hard: logs from the attack + logs from a month of benign user logs.


**4. Connect to database**

```bash
python setup_dtabase.py --csv_folder <path_to_csv_folder>
```