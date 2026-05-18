from src.graph_builder import Neo4jGraphBuilder
from src.rag_system import RAGSystem
from dotenv import load_dotenv
import os
import sys
import json

load_dotenv()

def initialize_system(force_rebuild=False):
    graph_builder = Neo4jGraphBuilder()
    rag_system = RAGSystem(graph_builder)
    data_file = "data/documents.txt"
    chunks = rag_system.load_documents(data_file)
    rag_system.create_vectorstore(chunks)
    rag_system.build_knowledge_graph(chunks)
    return graph_builder, rag_system

def test(rag_system):
    while True:
        try:
            query = input("User: ")
            if not query:
                continue
            if query.lower() in ["exit", "quit"]:
                break
            try: 
                answer = rag_system.answer_query(query)
                print("Chat: ", answer)
            except Exception as e:
                print(e)
            
        except KeyboardInterrupt:
            break
        
if __name__ == "__main__":
    force_rebuild = "--rebuild" in sys.argv
    graph_builder, rag_system = initialize_system()
    test(rag_system)
    graph_builder.close()