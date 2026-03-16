import os
import json
from pathlib import Path
from openai import OpenAI, AsyncOpenAI
from openai import RateLimitError, APIError, APIConnectionError, APITimeoutError
from dotenv import load_dotenv
from app.utils.logger import logger
from app.utils.retry import retry_with_backoff

load_dotenv()

# Sync client (for backward compatibility)
client = OpenAI()

# Async client (for better performance)
async_client = AsyncOpenAI()

def load_prompt(language: str, code: str) -> str:
    
    base_dir = Path(__file__).parent.parent.parent
    prompt_path = base_dir / "app" / "prompts" / "code_review.txt"
    
    with open(prompt_path, "r") as f:
        prompt = f.read()
    return prompt.format(language=language, code=code)

async def review_with_llm_async(language: str, code: str) -> dict:
    """Async version of review_with_llm for better performance"""
    prompt = load_prompt(language, code)
    logger.info(f"Starting code review for {language} code ({len(code)} chars)")

    @retry_with_backoff(
        max_retries=3,
        initial_delay=1.0,
        backoff_factor=2.0,
        exceptions=(APIConnectionError, APITimeoutError, RateLimitError)
    )
    async def _call_llm():
        response = await async_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a strict code review engine."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        return response

    try:
        response = await _call_llm()
        raw_output = response.choices[0].message.content
        logger.info("Received response from OpenAI API")

        try:
            result = json.loads(raw_output)
            logger.info(f"Successfully parsed JSON response with {len(result.get('issues', []))} issues")
            return result
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {str(e)}")
            return {
                "summary": "LLM response could not be parsed.",
                "issues": [],
                "suggested_fix": None
            }
    except RateLimitError as e:
        error_msg = str(e)
        if hasattr(e, 'response') and e.response:
            try:
                error_data = e.response.json() if hasattr(e.response, 'json') else {}
                if 'error' in error_data and 'message' in error_data['error']:
                    error_msg = error_data['error']['message']
            except:
                pass
        logger.error(f"OpenAI API quota exceeded: {error_msg}")
        raise Exception(f"OpenAI API quota exceeded: {error_msg}")
    except APIConnectionError as e:
        logger.error(f"Failed to connect to OpenAI API: {str(e)}")
        raise Exception(f"Failed to connect to OpenAI API: {str(e)}")
    except APITimeoutError as e:
        logger.error(f"OpenAI API request timed out: {str(e)}")
        raise Exception(f"OpenAI API request timed out: {str(e)}")
    except APIError as e:
        logger.error(f"OpenAI API error: {str(e)}")
        raise Exception(f"OpenAI API error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during code review: {str(e)}")
        raise Exception(f"Unexpected error during code review: {str(e)}")


def review_with_llm(language: str, code: str) -> dict:
    """Sync version (for backward compatibility)"""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(review_with_llm_async(language, code))
