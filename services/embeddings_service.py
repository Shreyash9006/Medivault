import os
import json
import sqlite3
from datetime import datetime

class EmbeddingsService:
    """Semantic search using keyword matching (no API needed for demo)"""
    
    def __init__(self, api_key=None, db_path='database/medivault.db'):
        """Initialize Embeddings Service"""
        self.api_key = api_key or os.getenv('HUGGINGFACE_API_KEY')
        self.db_path = db_path
    
    def store_document_embedding(self, record_id, health_id, text_chunk):
        """
        Store document for search (simplified - stores text only)
        
        Args:
            record_id (int): Medical record ID
            health_id (str): Patient's Health ID
            text_chunk (str): Text to index
            
        Returns:
            bool: Success status
        """
        try:
            # Store as simple text (no embeddings needed)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Store text for keyword search
            cursor.execute('''
                INSERT INTO document_embeddings (record_id, health_id, text_chunk)
                VALUES (?, ?, ?)
            ''', (record_id, health_id, text_chunk[:2000]))  # Limit length
            
            conn.commit()
            conn.close()
            
            return True
        
        except Exception as e:
            print(f"Store embedding error: {e}")
            return False
    
    def semantic_search(self, health_id, query, top_k=3):
        """
        Search patient's medical records using keyword matching
        
        Args:
            health_id (str): Patient's Health ID
            query (str): Search query
            top_k (int): Number of results to return
            
        Returns:
            list: Top matching documents
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all documents for this patient
            cursor.execute('''
                SELECT id, record_id, text_chunk
                FROM document_embeddings
                WHERE health_id = ?
            ''', (health_id,))
            
            documents = cursor.fetchall()
            conn.close()
            
            if not documents:
                return []
            
            # Simple keyword matching
            query_words = set(query.lower().split())
            results = []
            
            for doc_id, record_id, text in documents:
                text_lower = text.lower()
                
                # Count keyword matches
                matches = sum(1 for word in query_words if word in text_lower)
                similarity = matches / len(query_words) if query_words else 0
                
                results.append({
                    'embedding_id': doc_id,
                    'record_id': record_id,
                    'text': text,
                    'similarity': similarity
                })
            
            # Sort by similarity
            results.sort(key=lambda x: x['similarity'], reverse=True)
            
            return results[:top_k]
        
        except Exception as e:
            print(f"Semantic search error: {e}")
            return []
    
    def search_with_context(self, health_id, query):
        """Enhanced semantic search with context"""
        try:
            base_results = self.semantic_search(health_id, query, top_k=5)
            
            if not base_results:
                return []
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            enriched_results = []
            
            for result in base_results:
                cursor.execute('''
                    SELECT m.document_type, m.upload_date, s.confidence
                    FROM medical_records m
                    LEFT JOIN ai_summaries s ON m.id = s.record_id
                    WHERE m.id = ?
                ''', (result['record_id'],))
                
                metadata = cursor.fetchone()
                
                if metadata:
                    enriched_results.append({
                        'text': result['text'][:300],
                        'similarity_score': round(result['similarity'], 3),
                        'document_type': metadata[0],
                        'date': metadata[1],
                        'confidence': metadata[2] or 'Medium',
                        'record_id': result['record_id']
                    })
            
            conn.close()
            
            return enriched_results
        
        except Exception as e:
            print(f"Search with context error: {e}")
            return []


# Test
if __name__ == '__main__':
    print("🧪 Testing Embeddings Service (Simplified)...")
    service = EmbeddingsService()
    print("✅ Embeddings service test complete!")