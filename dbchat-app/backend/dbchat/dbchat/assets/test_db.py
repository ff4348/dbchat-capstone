from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from assets import execute_query

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
'host': '172.17.0.2',
'port': 3306,
'usr': 'newuser',
'pwd': 'newpassword',
'db': 'sakila'
}
connection_str = f"mysql+pymysql://{config.get('usr')}:{config.get('pwd')}@{config.get('host')}:{config.get('port')}/{config.get('db')}"

# test connection
print('test connection...')
request = '"SELECT * \nFROM customer limit 10"'
request = request.replace('\n','')
request = request.replace('"','')
engine = create_engine(connection_str)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()
result = execute_query(db, request)

print(result)