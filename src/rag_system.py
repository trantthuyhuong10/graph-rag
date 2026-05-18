from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain_ollama import OllamaLLM
from typing import Dict, List
import os
import json

class RAGSystem:
    def __init__(self, graph_builder):
        self.graph_builder = graph_builder
        self.embeddings = HuggingFaceEmbeddings(
            model_name='sentence-transformers/all-MiniLM-L6-v2'
        )
        
        self.vectorstore = None
        self.llm = OllamaLLM(model="llama3", temperature=0.8)
        
    def load_documents(self, file_path: str):
        with open(file_path, "r", encoding='utf-8') as f:
            documents = f.read()
        
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.split_text(documents)
        return chunks
    
    def create_vectorstore(self, chunks: List[str]):
        self.vectorstore = Chroma.from_texts(
            texts=chunks, 
            embedding=self.embeddings,
            persist_directory="./chroma_db"
        )
        
    def build_knowledge_graph(self, chunks: List[str]):
        for i, chunk in enumerate(chunks):
            doc_id = f"chunk_{i}"
            self.graph_builder.create_document_node(doc_id, chunk)
            entities = self.extract_entities(chunk)
            for entity in entities:
                entity_name, entity_type = entity
                self.graph_builder.create_entity_node(entity_name, entity_type)
                self.graph_builder.link_document_to_entity(doc_id, entity_name)
                
    def extract_entities(self, text: str) -> List[Dict[str, str]]:
        import re
        entities = []
        words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        for word in words:
            if len(word) > 2:
                entities.append((word, "Unknown"))        
        return list(set(entities))
    
    def hybrid_search(self, query: str, k: int = 3):
        vector_results = self.vectorstore.similarity_search(query, k=k)
        query_entities = self.extract_entities(query)
        graph_results = []
        for entity_name, _ in query_entities:
            context = self.graph_builder.get_entity_context(entity_name)
            graph_results.extend(context)
        combined_context = {
            "vector_results": [doc.page_content for doc in vector_results],
            "graph_results": graph_results
        }
        return combined_context
    
    def answer_query(self, query: str) -> str:
        context = self.hybrid_search(query)
        vector_context = "\n".join(context["vector_results"])
        graph_context = str(context["graph_results"])
        prompt = f"""
        Bạn là một trợ lý thông minh. Dựa trên thông tin sau, trả lời câu hỏi của người dùng.
        Câu hỏi được hỏi bằng ngôn ngữ nào thì trả lời bằng ngôn ngữ ấy.
        Trả lời thẳng vào vấn đề, không cần câu dẫn tương tự như:
        - Dựa vào vector search chúng tôi tìm thấy thông tin sau
        - Tôi có thể trả lời bạn rằng
        Thông tin từ vector search: {vector_context}
        Thông tin từ graph search: {graph_context}
        Question: {query}
        - Trả lời trực tiếp cho câu hỏi của người dùng, trả lời đầy đủ và tránh trả lời chung chung.
        - Bắt đầu ngay bằng nội dung câu trả lời
        Answer:
        """
        reponse = self.llm.invoke(prompt)
        return reponse
    
if __name__ == "__main__":
    from graph_builder import Neo4jGraphBuilder
    graph_builder = Neo4jGraphBuilder()
    rag_system = RAGSystem(graph_builder)
    chunks = rag_system.load_documents("data/documents.txt")
    if not os.path.exists("./chroma_db"):
        rag_system.create_vectorstore(chunks)
    rag_system.build_knowledge_graph(chunks)    
    while True:
        query = input("User: ")
        if query.lower() in ["exit", "quit"]:
            graph_builder.close()
            break
        answer = rag_system.answer_query(query)
        print("Chat: ", answer)
    