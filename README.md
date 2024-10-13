# Security RL Playground

We present the first benchmark to test LLM-based agents on threat hunting in the form of security question-answering pairs.


## Enviroment Setup

1. Data download
Please pull data from hugging face and put in the `env/data_anonymized` folder.

2. We are using MYSQL docker container for the database. Please first install docker and docker-compose and then pull the mysql image:

```bash
docker pull mysql:9.0
```

Then run the following command to set up the mysql container for 8 different databases:

```bash
cd secgym/env
bash setup_docker.sh
```

This script will create 8 different containers. Note that these container are binded to the csv files in the `data_anonymized` folder. This will take up 10GB of disk space.
Check out volumes with `docker system df -v`.

To set docker for the full environment, please uncomment the first command in `setup_docker.sh`. Note that this will take up 33GB of disk space.


3. LLM setup
We are using [AutoGen](https://autogen-ai.github.io/autogen/) for API calling. Setup your API key in the `secgym/myconfig.py` file. You can follow the instructions [here](https://autogen-ai.github.io/autogen/docs/notebooks/autogen_uniformed_api_calling#config-list-setup).

4. Install the requirements
Setup the environment using conda or venv and install the requirements:
```bash
pip install -r requirements.txt
```

5. Run Baseline
```bash
cd secgym
python run_exp.py
```
