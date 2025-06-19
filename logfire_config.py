"""Logfire configuration for the investment research system."""

import logfire
import os


def configure_logfire():
    """Configure Logfire with proper instrumentation for the investment research system."""
    
    try:
        # Configure Logfire - it will automatically discover credentials from ~/.logfire/
        logfire.configure(
            service_name="investment-research-system",
            service_version="1.0.0"
        )
        
        # Instrument pydantic-ai agents (core functionality)
        try:
            logfire.instrument_pydantic_ai()
            print("✅ Pydantic-AI instrumentation enabled")
        except Exception as e:
            print(f"⚠️  Pydantic-AI instrumentation failed: {e}")
            print("   Manual tracing will be used instead")
        
        # Instrument HTTP libraries for web scraping and API calls
        try:
            logfire.instrument_httpx()
            logfire.instrument_aiohttp()
            print("✅ HTTP instrumentation enabled")
        except Exception as e:
            print(f"⚠️  HTTP instrumentation failed: {e}")
        
        # Optional: Instrument requests library if needed
        try:
            logfire.instrument_requests()
        except Exception:
            pass  # Not critical if requests instrumentation fails
        
        # Optional: Instrument OpenAI if using direct OpenAI calls
        try:
            logfire.instrument_openai()
            print("✅ OpenAI instrumentation enabled")
        except Exception:
            pass  # Not critical if OpenAI instrumentation fails
        
        print("✅ Logfire configured successfully!")
        
    except Exception as e:
        print(f"⚠️  Logfire configuration failed: {e}")
        print("   Continuing with console logging fallback.")
    
    return logfire


def create_logfire_span(name: str, **kwargs):
    """Create a Logfire span with consistent formatting."""
    return logfire.span(name, **kwargs)


def log_research_start(query: str, context: str = ""):
    """Log the start of investment research."""
    logfire.info(
        "Investment research started",
        query=query,
        context=context,
        stage="initialization"
    )


def log_research_complete(query: str, confidence_score: float, num_sources: int):
    """Log successful completion of investment research."""
    logfire.info(
        "Investment research completed successfully",
        query=query,
        confidence_score=confidence_score,
        num_sources=num_sources,
        stage="completion"
    )


def log_research_error(query: str, error: str, stage: str = "unknown"):
    """Log research errors."""
    logfire.error(
        "Investment research failed",
        query=query,
        error=error,
        stage=stage
    )


def log_tool_usage(tool_name: str, query: str, results_count: int = 0):
    """Log tool usage for debugging."""
    logfire.info(
        f"Tool used: {tool_name}",
        tool=tool_name,
        query=query,
        results_count=results_count
    )