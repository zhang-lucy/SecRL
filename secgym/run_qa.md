# Run QA Gen

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