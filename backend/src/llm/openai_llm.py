import logging
import re
from typing import List, Dict, Any
from backend.src import config
from backend.src.exceptions import LLMError

logger = logging.getLogger(__name__)

class OpenAILLM:
    """LLM client that integrates retrieved context into robust, sourced answers using OpenAI or a local mock generator."""

    def __init__(self):
        self.model = config.LLM_MODEL
        self.api_key = config.OPENAI_API_KEY
        self.client = None
        
        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                logger.info(f"Initialized OpenAILLM with model: {self.model}")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}. Falling back to mock generator.")
        else:
            logger.warning("No OPENAI_API_KEY found in configuration. Running in mock/offline mode.")

    def _generate_mock_response(self, query: str, retrieved_chunks: List[Dict[str, Any]]) -> str:
        """Create a logical summary response based directly on retrieved chunks, highlighting citation capacity."""
        if not retrieved_chunks:
            return "I couldn't find any relevant documents to answer your question. Please make sure the document is uploaded first."
            
        logger.info("Generating deterministic mock LLM response from retrieved chunks.")
        
        # Build a coherent response by extracting the first sentence of the top chunks and citing them
        sentences = []
        for idx, chunk in enumerate(retrieved_chunks[:3]):
            content = chunk["content"]
            meta = chunk["metadata"]
            source = meta.get("source", "unknown")
            page = meta.get("page", 1)
            
            # Extract first sentence or first 120 characters
            first_sentence = content.split(".")[0].strip()
            if len(first_sentence) < 10:
                first_sentence = content[:120].strip()
                if not first_sentence.endswith("."):
                    first_sentence += "..."
            else:
                first_sentence += "."
                
            sentences.append(f"Regarding the query, on page {page} of **{source}**, it is stated: \"{first_sentence}\" [Source: {source}, page {page}].")
            
        summary = "\n\n".join(sentences)
        return (
            f"**[MOCK LLM RESPONSE - OFFLINE MODE]**\n\n"
            f"Based on the provided document contexts, here is the answer:\n\n"
            f"{summary}\n\n"
            f"*(Note: Enable OPENAI_API_KEY in backend/.env for live GPT responses.)*"
        )

    def generate_response(self, query: str, retrieved_chunks: List[Dict[str, Any]]) -> str:
        """
        Generate answer based on query and retrieved contexts.
        
        Args:
            query: User's question.
            retrieved_chunks: List of retrieved text chunks with metadata.
            
        Returns:
            Cohesive string response with inline citations.
            
        Raises:
            LLMError: If API call fails.
        """
        if not query.strip():
            return "Please provide a valid query."
            
        if not self.client:
            return self._generate_mock_response(query, retrieved_chunks)
            
        try:
            # 1. Format retrieved chunks into context string
            context_blocks = []
            for idx, chunk in enumerate(retrieved_chunks):
                meta = chunk["metadata"]
                source = meta.get("source", "unknown")
                page = meta.get("page", 1)
                context_blocks.append(
                    f"--- CONTEXT CHUNK {idx+1} (Source: {source}, Page: {page}) ---\n"
                    f"{chunk['content']}"
                )
            context_str = "\n\n".join(context_blocks)
            
            # 2. Build system and user prompts
            system_prompt = (
                "You are an expert AI assistant specializing in Retrieval-Augmented Generation (RAG) systems.\n"
                "Your task is to answer the user's query accurately using ONLY the provided text contexts.\n"
                "For every claim or piece of information you retrieve, you MUST provide an inline citation indicating "
                "the source filename and page number, strictly formatted as: [Source: filename, page X].\n"
                "If the context does not contain the answer to the query, state clearly that you cannot answer based "
                "on the retrieved documents. Do not make up facts."
            )
            
            user_prompt = (
                f"Retrieved Document Contexts:\n"
                f"{context_str}\n\n"
                f"User Question: {query}\n\n"
                f"Helpful, Accurate, Sourced Answer:"
            )
            
            logger.info(f"Sending request to OpenAI using model {self.model}...")
            
            # 3. Call Chat Completion API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.0
            )
            
            answer = response.choices[0].message.content
            return answer
            
        except Exception as e:
            logger.error(f"OpenAI Chat Completion failed: {e}")
            raise LLMError(f"OpenAI Chat Completion failed: {str(e)}")
