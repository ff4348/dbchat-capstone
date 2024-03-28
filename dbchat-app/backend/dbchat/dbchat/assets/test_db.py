from sqlalchemy import create_engine, inspect, text, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.reflection import Inspector
from assets import execute_query
import requests

def get_schema(engine):
    metadata = MetaData()
    metadata.reflect(bind=engine)
    inspector = Inspector.from_engine(engine)
    tbl_info_str = ''
    tbl_info_dict = {"Tables":{}}
    for table_name in inspector.get_table_names():
        tbl_info_str += f'Table - {table_name}: '
        print(f"Table - {table_name}")
        tbl_info_dict['Tables'][table_name] = []
        for column in inspector.get_columns(table_name):
            tbl_info_dict['Tables'][table_name].append(str(column['name'])+'|'+str(column['type']))
            column_name = column['name']
            column_type = column['type']
            tbl_info_str += f"Column: {column_name}, Type: {column_type}"
            print(f"Column: {column_name}, Type: {column_type}")
        tbl_info_dict['Tables'][table_name].sort()

        pk_constraint = inspector.get_pk_constraint(table_name)
        pk_columns = pk_constraint['constrained_columns']
        tbl_info_str += f"Primary Key(s) for {table_name}: {pk_columns}"
        print(f"Primary Key(s) for {table_name}: {pk_columns}")

    return tbl_info_str, tbl_info_dict

# Pull docker image
## docker pull mysql/mysql-server:latest

# Run docker container
## docker run --name mysql-container -e MYSQL_ROOT_PASSWORD=your_password -d mysql/mysql-server:latest

# Find IP address of container
## docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' mysql-container
### This is what you should use for your host: host = 'mysql_container_ip'

# Copy files into docker container
## docker cp ./dummy.sql <container_id>:/

# Run SQL script in docker container
## docker exec <container_id> /bin/sh -c 'mysql -u root -pyour_password </sakila-schema.sql'

# Exec into docker container
## docker exec -it mysql-container mysql -uroot -pyour_password

# Create R-O user
## CREATE USER 'newuser' IDENTIFIED BY 'newpassword';

# Gran RO permissions
## GRANT SELECT, RELOAD on *.* TO 'newuser' WITH GRANT OPTION;


# specify database configurations
config = {
'host': '172.18.0.3',
'port': 3306,
'usr': 'newuser',
'pwd': 'newpassword',
'db': 'sakila'
}
connection_str = f"mysql+pymysql://{config.get('usr')}:{config.get('pwd')}@{config.get('host')}:{config.get('port')}/{config.get('db')}"

# test connection
print('test connection...')
request = '"SELECT * \nFROM customer limit 10 asjdflk"'
request = request.replace('\n','')
request = request.replace('"','')
engine = create_engine(connection_str,
    connect_args={'init_command': 'SET SESSION max_execution_time=30000'})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# result = execute_query(db, request)


# schema_inf, dict_inf = get_schema(engine)
# print("\n\nSCHEMA")
# print(dict_inf)

# Function that will hit backend API to get schema information to populate tables
def get_schema_api():
    print('hi')
    response = requests.post(url = "http://localhost:8000/schema")
    print('response:',response)
    return response

print(get_schema_api())