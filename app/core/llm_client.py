import os
import logging
from langchain.chat_models import init_chat_model
from langsmith import Client
from .config import settings

# Configure logging
logger = logging.getLogger(__name__)

# LangSmith monitoring setup
os.environ["LANGCHAIN_TRACING_V2"] = settings.LANGCHAIN_TRACING_V2
os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT
os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY

# Azure OpenAI setup
os.environ["AZURE_OPENAI_API_KEY"] = settings.AZURE_OPENAI_API_KEY
os.environ["AZURE_OPENAI_ENDPOINT"] = settings.AZURE_OPENAI_ENDPOINT
os.environ["OPENAI_API_VERSION"] = settings.OPENAI_API_VERSION

# LangSmith client (optional direct usage)
langsmith_client = None
try:
    if settings.LANGCHAIN_API_KEY:
        langsmith_client = Client()
        logger.info("LangSmith client initialized successfully")
except Exception as e:
    logger.warning(f"Failed to initialize LangSmith client: {e}")

# Initialize LLM models
llm = None
gpt_4o_mini = None

try:
    llm = init_chat_model(
        "azure_openai:gpt-4o",
        azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
    )
    logger.info("GPT-4o model initialized successfully")
    
    gpt_4o_mini = init_chat_model(
        "azure_openai:gpt-4o-mini",
        azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
    )
    logger.info("GPT-4o-mini model initialized successfully")
    
except Exception as e:
    logger.error(f"Failed to initialize LLM models: {e}")
    raise


def get_gpt_4o_mini():
    """Get the GPT-4o-mini model instance."""
    if gpt_4o_mini is None:
        raise RuntimeError("GPT-4o-mini model not initialized")
    return gpt_4o_mini


def invokeLLM(messages, name="Video Analysis"):
    """
    Invoke GPT-4o with LangSmith monitoring.
    
    Args:
        messages: List of message dicts with 'role' and 'content' keys
        name: Run name for LangSmith tracing
        
    Returns:
        LLM response
    """
    if llm is None:
        raise RuntimeError("GPT-4o model not initialized")
    
    try:
        # LangSmith tracing is automatic with LANGCHAIN_TRACING_V2=true
        result = llm.invoke(messages, config={"run_name": name})
        logger.info(f"LLM invocation successful: {name}")
        return result
    except Exception as e:
        logger.error(f"LLM invocation failed for {name}: {e}")
        raise


def invoke_mini_llm(messages, name="Video Analysis Mini"):
    """
    Invoke GPT-4o-mini with LangSmith monitoring.
    
    Args:
        messages: List of message dicts with 'role' and 'content' keys
        name: Run name for LangSmith tracing
        
    Returns:
        LLM response
    """
    mini_model = get_gpt_4o_mini()
    
    try:
        result = mini_model.invoke(messages, config={"run_name": name})
        logger.info(f"Mini LLM invocation successful: {name}")
        return result
    except Exception as e:
        logger.error(f"Mini LLM invocation failed for {name}: {e}")
        raise
