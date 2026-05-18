from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()

uri = os.getenv("NEO4J_URI")
user = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")

print(f"Đang kết nối: {uri}")
print(f"Người dùng: {user}")

driver = GraphDatabase.driver(uri, auth=(user, password))

def test_connection(self):
    result = self.run("RETURN 'Thành công' AS result")
    return result.single()['result']

with driver.session() as session:
    result = session.execute_read(test_connection)
    print(result)
    
driver.close()
