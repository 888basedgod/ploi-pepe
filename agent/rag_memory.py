"""
RAG (Retrieval Augmented Generation) Memory
Semantic search over past conversations for true learning
"""

import os
import json
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)


class RAGMemory:
    """
    Vector-based memory system that learns from interactions.
    Uses embeddings to semantically search past conversations.
    """
    
    def __init__(
        self,
        storage_path: str = "./data/rag_memory",
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize RAG memory with vector embeddings.
        
        Args:
            storage_path: Directory for vector database
            embedding_model: Sentence transformer model name
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.embedding_model_name = embedding_model
        self.embeddings_file = self.storage_path / "embeddings.npy"
        self.metadata_file = self.storage_path / "metadata.json"
        
        # Initialize components
        self.embeddings = []
        self.metadata = []
        self.encoder = None
        
        self._load_encoder()
        self._load_memory()
        
        logger.info(f"RAG Memory initialized with {len(self.embeddings)} stored memories")
    
    def _load_encoder(self):
        """Load sentence transformer model for embeddings"""
        try:
            from sentence_transformers import SentenceTransformer
            self.encoder = SentenceTransformer(self.embedding_model_name)
            logger.info(f"Loaded embedding model: {self.embedding_model_name}")
        except ImportError:
            logger.warning("sentence-transformers not installed. Install with: pip install sentence-transformers")
            self.encoder = None
        except Exception as e:
            logger.error(f"Failed to load encoder: {e}")
            self.encoder = None
    
    def _load_memory(self):
        """Load existing embeddings and metadata"""
        try:
            if self.embeddings_file.exists():
                self.embeddings = np.load(self.embeddings_file).tolist()
            
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    self.metadata = json.load(f)
            
            logger.info(f"Loaded {len(self.embeddings)} memories from disk")
        except Exception as e:
            logger.error(f"Failed to load memory: {e}")
            self.embeddings = []
            self.metadata = []
    
    def _save_memory(self):
        """Persist embeddings and metadata to disk"""
        try:
            if self.embeddings:
                np.save(self.embeddings_file, np.array(self.embeddings))
            
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
            
            logger.debug(f"Saved {len(self.embeddings)} memories to disk")
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")
    
    def add_interaction(
        self,
        user_message: str,
        agent_response: str,
        conversation_id: str,
        metadata: Optional[Dict] = None
    ):
        """
        Store a user-agent interaction with embeddings.
        
        Args:
            user_message: What the user said
            agent_response: How the agent responded
            conversation_id: Conversation identifier
            metadata: Additional context (platform, timestamp, etc.)
        """
        if not self.encoder:
            logger.warning("No encoder available, skipping embedding")
            return
        
        try:
            # Combine user message and response for context
            interaction_text = f"User: {user_message}\nAgent: {agent_response}"
            
            # Generate embedding
            embedding = self.encoder.encode(interaction_text).tolist()
            
            # Store embedding and metadata
            self.embeddings.append(embedding)
            self.metadata.append({
                "user_message": user_message,
                "agent_response": agent_response,
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            })
            
            # Auto-save every 10 interactions
            if len(self.embeddings) % 10 == 0:
                self._save_memory()
            
            logger.debug(f"Added interaction to RAG memory (total: {len(self.embeddings)})")
        
        except Exception as e:
            logger.error(f"Failed to add interaction: {e}")
    
    def search_similar(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.3
    ) -> List[Dict]:
        """
        Search for similar past interactions using semantic similarity.
        
        Args:
            query: Current user message or context
            top_k: Number of similar interactions to return
            threshold: Minimum similarity score (0-1)
        
        Returns:
            List of similar interactions with scores
        """
        if not self.encoder or not self.embeddings:
            return []
        
        try:
            # Encode query
            query_embedding = self.encoder.encode(query)
            
            # Calculate cosine similarity with all stored embeddings
            similarities = []
            for i, emb in enumerate(self.embeddings):
                similarity = self._cosine_similarity(query_embedding, np.array(emb))
                if similarity >= threshold:
                    similarities.append((i, similarity))
            
            # Sort by similarity (descending)
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Return top_k results with metadata
            results = []
            for idx, score in similarities[:top_k]:
                result = self.metadata[idx].copy()
                result["similarity_score"] = float(score)
                results.append(result)
            
            logger.debug(f"Found {len(results)} similar interactions for query")
            return results
        
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    def get_learning_context(
        self,
        current_message: str,
        max_examples: int = 3
    ) -> str:
        """
        Get relevant past interactions as context for the current message.
        This is what makes the agent "learn" from past conversations.
        
        Args:
            current_message: Current user input
            max_examples: Maximum number of past examples to include
        
        Returns:
            Formatted context string to add to prompt
        """
        similar = self.search_similar(current_message, top_k=max_examples)
        
        if not similar:
            return ""
        
        # Format as learning context
        context_parts = ["Here are some relevant past interactions you should remember:"]
        
        for i, interaction in enumerate(similar, 1):
            context_parts.append(
                f"\n{i}. User previously said: \"{interaction['user_message']}\""
                f"\n   You responded: \"{interaction['agent_response']}\""
                f"\n   (similarity: {interaction['similarity_score']:.2f})"
            )
        
        return "\n".join(context_parts)
    
    def get_stats(self) -> Dict:
        """Get memory statistics"""
        return {
            "total_interactions": len(self.embeddings),
            "storage_path": str(self.storage_path),
            "embedding_model": self.embedding_model_name,
            "has_encoder": self.encoder is not None
        }
    
    def save(self):
        """Force save all memories"""
        self._save_memory()
    
    def clear(self):
        """Clear all stored memories"""
        self.embeddings = []
        self.metadata = []
        if self.embeddings_file.exists():
            self.embeddings_file.unlink()
        if self.metadata_file.exists():
            self.metadata_file.unlink()
        logger.info("Cleared all RAG memories")


if __name__ == "__main__":
    # Test RAG memory
    print("Testing RAG Memory...")
    
    rag = RAGMemory()
    
    # Add some test interactions
    rag.add_interaction(
        "what's your favorite token?",
        "probably bonk or something chill",
        "test_1"
    )
    
    rag.add_interaction(
        "can you help me deploy a token?",
        "yeah just use /deploy command",
        "test_2"
    )
    
    rag.add_interaction(
        "how do i send sol?",
        "use /send command with address and amount",
        "test_3"
    )
    
    # Search for similar
    print("\nSearching for: 'how to deploy tokens'")
    results = rag.search_similar("how to deploy tokens", top_k=2)
    
    for r in results:
        print(f"\nSimilarity: {r['similarity_score']:.2f}")
        print(f"User: {r['user_message']}")
        print(f"Agent: {r['agent_response']}")
    
    # Get learning context
    context = rag.get_learning_context("i want to launch a token")
    print(f"\nLearning context:\n{context}")
    
    print(f"\nStats: {rag.get_stats()}")
