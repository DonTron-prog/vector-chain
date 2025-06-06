"""
Deep Research Tool Module

This module provides comprehensive web research capabilities by combining:
- Intelligent search query generation
- Web search using SearxNG
- Content scraping and analysis
- AI-powered answer synthesis

Main components:
- DeepResearchTool: The main tool class for performing research
- DeepResearchToolConfig: Configuration for the tool
- DeepResearchToolInputSchema: Input schema for research queries
- DeepResearchToolOutputSchema: Output schema with research results
"""

from .tool import (
    DeepResearchTool,
    DeepResearchToolConfig,
    DeepResearchToolInputSchema,
    DeepResearchToolOutputSchema,
)

__all__ = [
    "DeepResearchTool",
    "DeepResearchToolConfig",
    "DeepResearchToolInputSchema",
    "DeepResearchToolOutputSchema",
]