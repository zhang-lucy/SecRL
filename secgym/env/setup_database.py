import mysql.connector
from mysql.connector import Error
import time
import os
import json
import docker
from docker.errors import ContainerError, ImageNotFound, APIError, NotFound
import pandas as pd
# from secgym.utils import find_most_similar
import argparse


def to_abs_path(path):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), path)

def create_container_per_attack(attack):
    # TODO
    attack_maps = {
        "attack 1" : "attack1container",
    }
    for i, key, value in enumerate(attack_maps.items()):
        create_container(
            csv_folder=to_abs_path(f"data/logs_jun3_30/"),
            sql_file_path=to_abs_path(f"data/logs_jun3_30/.sql"),
            database_name=f"env_monitor_db",
            container_name=value,
            port=str(3306 + i),
            respawn=True
        )


def create_container(
    csv_folder,
    sql_file_path,
    database_name,
    port="3306",
    container_name="mysql-container",
    respawn=False
):
    client = docker.from_env()
    if respawn:
        # delete the existing container if it exists
        try:
            container = client.containers.get(container_name)
            if container.status == "running":
                print(f"Stopping container {container_name}...")
                container.stop()
            container.remove()
            print(f"Stopped and removed existing container {container_name}")
            time.sleep(2)  # Wait for the container to be removed
        except NotFound:
            pass

    try:
        container = client.containers.get(container_name)
        if container.status == "running":
            print(f"Container {container_name} is already running.")
            return container, port
        else:
            container.start()
            print(f"Restarted stopped container with ID: {container.id}")
            return container, port
    except NotFound:
        print(f"Container {container_name} does not exist. Creating a new container...")
        try:
            container = client.containers.run(
                "mysql:9.0",
                name=container_name,
                environment={
                    "MYSQL_ROOT_PASSWORD": "admin",
                    "MYSQL_DATABASE": database_name,
                },
                ports={
                    "3306/tcp": port
                },
                volumes={
                    to_abs_path(sql_file_path): {
                        'bind': '/docker-entrypoint-initdb.d/init_data.sql',
                        'mode': 'ro'  # Mount the file as read-only
                    },
                    to_abs_path(csv_folder): {
                        'bind': '/var/lib/mysql-files',
                        'mode': 'rw'  # Mount the CSV folder as read-write
                    }
                },
                command=['--secure-file-priv=/var/lib/mysql-files'],
                detach=True
            )
            print(f"Started container {container_name} with ID: {container.id} on port {port}")
            container.reload()
            print(f"Waiting 30 seconds for the container to start...")
            time.sleep(30)  # Wait for the container to start
            return container, port
        except (ContainerError, ImageNotFound) as e:
            print(f"Error: {e}")
            raise



def process_csv(csv_folder):
    """Create a single .sql file from a folder of CSV and .meta files."""
    for file_name in os.listdir(csv_folder):
        print(file_name)
        if file_name.endswith(".meta"):
            meta_file_path = os.path.join(csv_folder, file_name)
            table_name = file_name.replace(".meta", "")

            # Read the .meta file
            with open(meta_file_path, 'r') as meta_file:
                meta_data = json.load(meta_file)
                columns = meta_data['columns']
                dtypes = meta_data['dtypes']
            json_columns = [col for col, dtype in zip(columns, dtypes) if dtype == "dynamic"]

            # process with pandas
            # for column that is dynamic, check if empty and convert to {}, and save to the origninal file
            csv_file_path = os.path.join(csv_folder, f"{table_name}.csv")
            with open(csv_file_path, 'r') as csv_file:
                df = pd.read_csv(csv_file, sep="¤", encoding='utf-8', on_bad_lines='skip', engine='python')
                for column in df.columns:

                    if column in json_columns:
                        print("Processing column:", column)
                        # convert empty string or None to {}
                        df[column] = df[column].apply(lambda x: "{}" if x == "" else x)
                        df[column] = df[column].apply(lambda x: "{}" if pd.isnull(x) else x)
                        print(df[column].head())
                # df.to_csv(csv_file_path, index=False)
                df.to_csv(csv_file_path, index=False, sep="¤", quotechar='"', encoding='utf-8')

            break

def create_sql_file_from_csv_folder(csv_folder, sql_file_path, database_name):
    """Create a single .sql file from a folder of CSV and .meta files."""
    sql_statements = [
        "CREATE USER 'admin'@'%' IDENTIFIED BY 'admin';",
        "GRANT ALL PRIVILEGES ON *.* TO 'admin'@'%';",
        "FLUSH PRIVILEGES;",
        f"CREATE DATABASE IF NOT EXISTS {database_name};",
        f"USE {database_name};"
    ]
    for file_name in os.listdir(csv_folder):    
        if file_name.endswith(".csv"):
            table_name = file_name.replace(".csv", "")
            # check meta file exists
            if os.path.exists(os.path.join(csv_folder, f"{table_name}_metadata.json")):
                with open(os.path.join(csv_folder, f"{table_name}_metadata.json"), 'r') as meta_file:
                    type_map = json.load(meta_file)
            else:
                print(f"Meta file not found for {table_name}. Inferring types from the CSV file...")
                df = pd.read_csv(os.path.join(csv_folder, f"{table_name}.csv"), sep="¤", encoding='utf-8-sig', on_bad_lines='skip', engine='python')
                type_map = {str(col): "string" for col in df.columns}
                # print(type_map)

            json_columns = [col for col, dtype in type_map.items() if dtype == "dynamic"]

            # Generate CREATE TABLE statement
            create_table_sql = generate_create_table_sql(table_name, type_map)
            sql_statements.append(create_table_sql)

            # Generate LOAD DATA INFILE statement
            load_data_sql = generate_load_data_sql(file_name, table_name, type_map.keys(), json_columns)
            sql_statements.append(load_data_sql)
        elif os.path.isdir(os.path.join(csv_folder, file_name)):
            # a folder of CSV files. file_name is the table name: SecurityAlert
            # In the folder, there are SecurityAlert_i.csv starting from 1 and a SecurityAlert.meta file
            # add the corresponding SQL statements: creating one table and loading all the data

            table_name = file_name
            with open(os.path.join(csv_folder, f"{file_name}/{file_name}_0_metadata.json"), 'r') as meta_file:
                type_map = json.load(meta_file)
            json_columns = [col for col, dtype in type_map.items() if dtype == "dynamic"]

            # get all the csv files
            csv_files = [f"{file_name}/{f}" for f in os.listdir(os.path.join(csv_folder, file_name)) if f.endswith(".csv")]
            
            # Generate CREATE TABLE statement
            create_table_sql = generate_create_table_sql(table_name, type_map)
            sql_statements.append(create_table_sql)

            # Generate LOAD DATA INFILE statement
            for i, csv_file in enumerate(csv_files):
                load_data_sql = generate_load_data_sql(csv_file, table_name, type_map.keys(), json_columns)
                sql_statements.append(load_data_sql)
           
    # Write all SQL statements to the output file
    with open(sql_file_path, 'w', encoding='utf-8') as sql_file:
        sql_file.write("\n\n".join(sql_statements))

def dtype_to_sql(dtype):
    """Convert a custom dtype to a SQL data type."""
    mapping = {
        "string": "TEXT",
        "long": "TEXT", # BIGINT
        "datetime": "TEXT",
        "bool": "TEXT", # BOOLEAN
        "dynamic": "TEXT" # JSON
    }
    return mapping.get(dtype, "TEXT")

def generate_create_table_sql(table_name, type_map):
    """Generate a CREATE TABLE SQL statement."""
    column_defs = [f"{col} {dtype_to_sql(dtype)}" for col, dtype in type_map.items()]
    columns_sql = ",\n    ".join(column_defs)
    sql = f"CREATE TABLE {table_name} (\n    {columns_sql}\n);"
    if table_name == "Usage":
        sql = sql.replace("Usage", "`Usage`")
    return sql

def generate_load_data_sql(file_name, table_name, columns, json_columns):
    """Generate LOAD DATA INFILE SQL statement."""
    load_data_sql = f"""
LOAD DATA INFILE '/var/lib/mysql-files/{file_name}'
INTO TABLE {table_name}
FIELDS TERMINATED BY '¤'
ENCLOSED BY '"'
LINES TERMINATED BY '\\n'
IGNORE 1 ROWS;
"""
    load_data_sql = load_data_sql.replace("INTO TABLE Usage", "INTO TABLE `Usage`")
    set_statements = []
    for column in columns:
        if column in json_columns:
            # convert to {} if the column is empty
            set_statements.append(f"CASE WHEN @{column} = '' THEN '{{}}' ELSE @{column} END,")
        else:
            set_statements.append(f"{column} = NULLIF(@{column}, '')")

    tmp_set = ','.join(set_statements)
    # load_data_sql += f"""SET {tmp_set};"""
    return load_data_sql

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Setup a MySQL database from CSV files')
    parser.add_argument('--port', type=str, default="3306", help='Port number for the MySQL container')
    parser.add_argument('--csv', type=str, help='Folder containing the CSV files')
    parser.add_argument('--sql_file', type=str, default=to_abs_path("data/secbench.sql"), help='Output SQL file')
    parser.add_argument('--container_name', type=str, default="mysql-container", help='Name of the MySQL container')
    parser.add_argument('--database_name', type=str, default="env_monitor_db", help='Name of the database')
    parser.add_argument('--respawn', action='store_true', help='Delete and recreate the container')
    args = parser.parse_args()
    # make sure the data is downloaded and stored in the 'large_data' folder

    csv_folder = to_abs_path(args.csv)
    sql_file_path = to_abs_path(args.sql_file)

    # 1. create a .sql file from the CSV  filesin the 'large_data' folder
    create_sql_file_from_csv_folder(
        csv_folder=csv_folder,
        sql_file_path=sql_file_path,
        database_name=args.database_name
    )
    print(f"> 1. SQL file created: {sql_file_path}")

    # 2. start a MySQL docker container
    print("> 2 Starting a MySQL container...")
    container, port = create_container(
        csv_folder=csv_folder,
        sql_file_path=sql_file_path,
        database_name=args.database_name,
        container_name=args.container_name,
        port=args.port,
        respawn=args.respawn
    )

    # # 3. test connection to the MySQL container
    connection = mysql.connector.connect(
        host='localhost',
        port=port,
        user='root',
        password='admin'
    )
    print("> 3. Successfully connected to the database")
    time.sleep(1)  

    print("> 4. Testing connection to the MySQL container...")
    if connection.is_connected():
        cursor = connection.cursor()
        # select the database
        cursor.execute(f"USE {args.database_name};")
        # list all tables in the database
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        print("Tables in the database:", tables)

    

