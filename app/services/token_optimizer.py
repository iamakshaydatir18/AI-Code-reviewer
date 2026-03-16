"""
Token optimization and cost management for LLM calls
Critical for production AI systems
"""
import tiktoken
from typing import Dict, Optional
from app.utils.logger import logger


class TokenOptimizer:
    """
    Optimize token usage and manage costs for LLM calls.
    Shows understanding of AI economics and production concerns.
    """
    
    # Cost per 1M tokens (as of 2024)
    COST_PER_1M_TOKENS = {
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
        "claude-3-haiku": {"input": 0.25, "output": 1.25},
    }
    
    def __init__(self):
        self.encodings = {
            "gpt-4o-mini": tiktoken.encoding_for_model("gpt-4o-mini"),
            "gpt-4o": tiktoken.encoding_for_model("gpt-4"),
            "gpt-3.5-turbo": tiktoken.encoding_for_model("gpt-3.5-turbo"),
        }
        self.total_tokens_used = 0
        self.total_cost = 0.0
    
    def count_tokens(self, text: str, model: str = "gpt-4o-mini") -> int:
        """Count tokens in text"""
        encoding = self.encodings.get(model, self.encodings["gpt-4o-mini"])
        return len(encoding.encode(text))
    
    def estimate_cost(
        self, 
        prompt: str, 
        estimated_output_tokens: int = 500,
        model: str = "gpt-4o-mini"
    ) -> float:
        """
        Estimate cost for a request.
        Critical for budget management in production.
        """
        input_tokens = self.count_tokens(prompt, model)
        
        if model not in self.COST_PER_1M_TOKENS:
            logger.warning(f"Unknown model {model}, using gpt-4o-mini pricing")
            model = "gpt-4o-mini"
        
        costs = self.COST_PER_1M_TOKENS[model]
        
        input_cost = (input_tokens / 1_000_000) * costs["input"]
        output_cost = (estimated_output_tokens / 1_000_000) * costs["output"]
        
        total_cost = input_cost + output_cost
        
        logger.info(
            f"Cost estimate: ${total_cost:.4f} "
            f"({input_tokens} input + {estimated_output_tokens} output tokens)"
        )
        
        return total_cost
    
    def select_model(
        self, 
        code: str, 
        complexity: float,
        budget_per_request: Optional[float] = None
    ) -> str:
        """
        Intelligently select model based on code complexity and budget.
        Shows cost optimization thinking.
        """
        # Simple code = cheaper model
        if complexity < 5:
            model = "gpt-3.5-turbo"
            logger.info(f"Using {model} for simple code (complexity: {complexity})")
        else:
            model = "gpt-4o-mini"
            logger.info(f"Using {model} for complex code (complexity: {complexity})")
        
        # Check budget constraint
        if budget_per_request:
            estimated_cost = self.estimate_cost(code, model=model)
            if estimated_cost > budget_per_request:
                # Try cheaper model
                if model != "gpt-3.5-turbo":
                    model = "gpt-3.5-turbo"
                    logger.info(f"Switched to {model} due to budget constraint")
        
        return model
    
    def chunk_code(
        self, 
        code: str, 
        max_tokens: int = 8000,
        model: str = "gpt-4o-mini"
    ) -> list[str]:
        """
        Split large code into chunks that fit token limits.
        Important for handling large codebases.
        """
        lines = code.split('\n')
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for line in lines:
            line_tokens = self.count_tokens(line, model)
            
            if current_tokens + line_tokens > max_tokens and current_chunk:
                # Save current chunk
                chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
                current_tokens = line_tokens
            else:
                current_chunk.append(line)
                current_tokens += line_tokens
        
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        logger.info(f"Split code into {len(chunks)} chunks")
        return chunks
    
    def track_usage(self, input_tokens: int, output_tokens: int, model: str):
        """Track token usage and costs"""
        self.total_tokens_used += input_tokens + output_tokens
        
        if model in self.COST_PER_1M_TOKENS:
            costs = self.COST_PER_1M_TOKENS[model]
            cost = (
                (input_tokens / 1_000_000) * costs["input"] +
                (output_tokens / 1_000_000) * costs["output"]
            )
            self.total_cost += cost
    
    def get_usage_stats(self) -> Dict:
        """Get usage statistics"""
        return {
            "total_tokens": self.total_tokens_used,
            "total_cost_usd": round(self.total_cost, 4),
            "average_cost_per_request": round(
                self.total_cost / max(1, self.total_tokens_used / 1000), 
                4
            )
        }


# Global instance
token_optimizer = TokenOptimizer()

