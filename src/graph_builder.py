from neo4j import GraphDatabase
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Neo4jGraphBuilder:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI")
        self.user = os.getenv("NEO4J_USER")
        self.password = os.getenv("NEO4J_PASSWORD")

        if not all([self.uri, self.user, self.password]):
            raise ValueError("Lỗi")
        
        self.driver = GraphDatabase.driver(
            self.uri, 
            auth=(self.user, self.password)
        )
        
        self._test_connection()
    
    def _test_connection(self):
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 AS test")
                result.single()
        except Exception as e:
            raise ConnectionError()
        
    def close(self):
        if self.driver:
            self.driver.close()
    
    def clear_database(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            
    def create_document_node(
        self,
        doc_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        with self.driver.session() as session:
            query = """
            MERGE (d:Document {id: $doc_id})
            SET d.content = $content
            SET d.updated_at = datetime()
            """
            params = {
                "doc_id": doc_id,
                "content": content
            }

            if metadata:
                for key, value in metadata.items():
                    query += f"SET d.{key} = ${key}\n"
                    params[key] = value
                    
            query += "RETURN d"
            
            result = session.run(query, **params)
            record = result.single()
            
            return record["d"]
    
    def create_entity_node(
        self, 
        entity_name: str,
        entity_type: str,
        properties: Optional[Dict[str, Any]] = None
    ):
        with self.driver.session() as session:
            query = """
            MERGE (e:Entity {name: $name})
            SET e.type = $type
            SET e.updated_at = datetime()
            """
            params = {
                "name": entity_name,
                "type": entity_type
            }

            if properties:
                for key, value in properties.items():
                    query += f"SET e.{key} = ${key}\n"
                    params[key] = value
                    
            query += "RETURN e"
            
            result = session.run(query, **params)
            record = result.single()
            
            return record["e"]
        
    def create_relationship(
        self,
        entity1_name: str,
        entity2_name: str,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None
    ):
        with self.driver.session() as session:
            rel_type = relationship_type.upper().replace(" ", "_")
            
            query = f"""
            MATCH (e1:Entity {{name: $entity1}})
            MATCH (e2:Entity {{name: $entity2}})
            MERGE (e1)-[r:{rel_type.upper()}]->(e2)
            SET r.created_at = datetime()
            """ 
            
            params = {
                "entity1": entity1_name,
                "entity2": entity2_name
            }

            if properties:
                for key, value in properties.items():
                    query += f"SET r.{key} = ${key}\n"
                    params[key] = value
                    
            query += "RETURN r"
            
            result = session.run(query, **params)
            record = result.single()
                
            return record["r"] if record else None
        
    def link_document_to_entity(
        self,
        doc_id: str,
        entity_name: str
    ):
        with self.driver.session() as session:
            query = """
            MATCH (d:Document {id: $doc_id})
            MATCH (e:Entity {name: $entity_name})
            MERGE (d)-[r:MENTIONS]->(e)
            RETURN d,e
            """
            
            result = session.run(query, doc_id=doc_id, entity_name=entity_name)
            record = result.single()
                
    def query_graph(
        self, 
        cypher_query: str, 
        parameters: Optional[Dict] = None) -> List[Dict]:
        
        with self.driver.session() as session:
            result = session.run(cypher_query, parameters or {})
            return [record.data() for record in result]
    
    def get_entity_context(self, entity_name: str) -> List[Dict]:
        query = """
        MATCH (e:Entity {name: $name})
        OPTIONAL MATCH (e)-[r]-(related:Entity)
        RETURN
            e.name as entity,
            e.type as type,
            collect(DISTINCT {
                relationship: type(r),
                direction: CASE
                    WHEN startNode(r) = e THEN 'outgoing'
                    ELSE 'incoming'
                END,
                related_entity: related.name,
                related_type: related.type
            }) as connections
        """
        
        return self.query_graph(query, {"name": entity_name})
    
    def get_statistics(self) -> Dict[str, int]:
        with self.driver.session() as session:
            node_result = session.run("MATCH (n) RETURN count(n) as count")
            node_count = node_result.single()["count"]
            
            rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            rel_count = rel_result.single()["count"]
            
            entity_result = session.run("MATCH (e:Entity) RETURN count(e) as count")
            entity_count = entity_result.single()["count"]
            
            doc_result = session.run("MATCH (d:Document) RETURN count(d) as count")
            doc_count = doc_result.single()["count"]
            
            return {
                "total_nodes": node_count,
                "total_relationships": rel_count,
                "entity_count": entity_count,
                "documents": doc_count
            }
        
if __name__ == "__main__":    
    builder = Neo4jGraphBuilder()
    