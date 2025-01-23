# Security RL Playground

We present the first benchmark to test LLM-based agents on threat hunting in the form of security question-answering pairs.


## Enviroment Setup

1. Data download
Please pull data from hugging face and put in the `env/data_anonymized` folder.

2. Install the requirements
Setup the environment using conda or venv and install the requirements:
```bash
pip install -r requirements.txt
```

3. We are using MYSQL docker container for the database. Please first install docker and docker-compose and then pull the mysql image:

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


4. LLM setup
We are using [AutoGen](https://autogen-ai.github.io/autogen/) for API calling. Setup your API key in the `secgym/myconfig.py` file. You can follow the instructions [here](https://autogen-ai.github.io/autogen/docs/notebooks/autogen_uniformed_api_calling#config-list-setup).



5. Run Baseline
```bash
cd secgym
python run_exp.py
```


## Run QA Gen

1. Create an environment and install the requirements
```bash
pip install -r requirements.txt
pip install -e .
```

2. Setup up models in `secgym/myconfig.py`. Only config_list_4o is needed for QA Gen. Note 
`config_list_35` maybe needed later for running evaluations.

3. If you are using `token_provider`, login into your account:
```bash
az login
```

4. Go to QA folder
```bash
cd secgym/qagen
```

5. Run the QA Gen
```bash
python run_qa.py
```


6. After all the questions are generated, you should expect new files in `secgym/env/questions` folder like `incident_<i>_qa.json` where `i` is the incident number.
You can upload these files to the `secgym` repo.
