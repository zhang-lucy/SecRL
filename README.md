# Security RL Playground

We present the first benchmark to test LLM-based agents on threat hunting in the form of security question-answering pairs.


## Enviroment Setup

1. Data download
Please pull data from hugging face and put in the `env/data` folder.



We are using MYSQL docker container for the database. Please first install docker and docker-compose and then pull the mysql image:

```bash
docker pull mysql:9.0
```

