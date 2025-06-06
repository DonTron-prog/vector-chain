"""Schemas for the Investment Research Orchestrator Agent."""

from typing import Union, List, Optional, Dict, Any
from datetime import datetime
from pydantic import Field
from atomic_agents.lib.base.base_io_schema import BaseIOSchema
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator

from orchestration_engine.tools.searxng_search import (
    SearxNGSearchToolInputSchema,
    SearxNGSearchToolOutputSchema,
)
from orchestration_engine.tools.calculator import (
    CalculatorToolInputSchema,
    CalculatorToolOutputSchema,
)
from orchestration_engine.tools.rag_search import (
    RAGSearchToolInputSchema,
    RAGSearchToolOutputSchema
)
from orchestration_engine.tools.deep_research import (
    DeepResearchToolInputSchema,
    DeepResearchToolOutputSchema,
)


class OrchestratorInputSchema(BaseIOSchema):
    """Input schema for the Investment Research Orchestrator Agent. Contains the investment query and its context."""

    investment_query: str = Field(..., description="Investment research query (e.g., 'Analyze NVDA's competitive position in AI chips')")
    research_context: str = Field(..., description="Research context and constraints (e.g., 'Focus on Q3 2024 earnings, compare with AMD/Intel')")


class OrchestratorOutputSchema(BaseIOSchema):
    """Combined output schema for the Orchestrator Agent. Contains the tool to use and its parameters."""

    tool: str = Field(..., description="The tool to use: 'search', 'calculator', 'rag', or 'deep-research'")
    tool_parameters: Union[SearxNGSearchToolInputSchema, CalculatorToolInputSchema, RAGSearchToolInputSchema, DeepResearchToolInputSchema] = Field(
        ..., description="The parameters for the selected tool"
    )


class FinalAnswerSchema(BaseIOSchema):
    """Schema for the final answer generated by the Orchestrator Agent."""

    final_answer: str = Field(..., description="The final investment research answer generated based on the tool output and investment query.")


def create_orchestrator_agent(client, model_name):
    """Create and configure the orchestrator agent instance."""
    system_prompt_generator = SystemPromptGenerator(
        background=[
            "You are an Investment Research Orchestrator Agent. Your primary role is to analyze an investment research query and its associated context. Based on this analysis, you must decide which tool (RAG, web-search, deep-research, or calculator) will provide the most valuable additional information or context for investment decision-making and analysis.",
            "Use the RAG (Retrieval Augmented Generation) tool for querying internal investment knowledge bases. This includes SEC filings, earnings reports, financial statements, analyst reports, company presentations, investment research documents, and historical market data related to the queried company, sector, or investment theme.",
            "Use the web-search tool for finding external financial information. This includes searching for recent news, market developments, regulatory changes, competitor analysis, industry trends, analyst opinions, earnings announcements, or general investment research from financial news sources and market data providers.",
            "Use the deep-research tool when you need comprehensive, multi-source research on complex investment topics. This tool automatically generates multiple search queries, scrapes content from multiple sources, and synthesizes comprehensive answers. Use this for complex investment thesis validation, emerging market analysis, new technology assessment, or when you need detailed analysis of unfamiliar companies, sectors, or investment strategies.",
            "Use the calculator tool if the investment query involves specific financial metrics, ratios, valuations, or requires calculations to determine investment attractiveness, risk metrics, portfolio allocation, or performance analysis (e.g., P/E ratios, DCF calculations, portfolio returns, risk-adjusted metrics).",
        ],
        output_instructions=[
            "Carefully analyze the provided 'investment_query' and 'research_context'.",
            "Determine if the most valuable next step is to: query internal investment knowledge (RAG), search for external market information (web-search), perform comprehensive investment research (deep-research), or perform a financial calculation (calculator).",
            "If RAG is chosen: use the 'rag' tool. Formulate a specific question for the RAG system based on the investment query and context to retrieve relevant internal investment documentation (e.g., 'Find SEC filings for NVDA Q3 2024 earnings', 'Retrieve analyst reports on semiconductor industry competitive landscape').",
            "If web-search is chosen: use the 'search' tool. Provide 1-3 concise and relevant search queries based on the investment query and context (e.g., 'NVDA AI chip market share 2024', 'Tesla valuation metrics vs traditional automakers', 'semiconductor industry supply chain risks').",
            "If deep-research is chosen: use the 'deep-research' tool. Provide a comprehensive research question that requires analysis of multiple sources and synthesis of information (e.g., 'Research NVDA competitive position in AI chips market including market share, technological advantages, and competitive threats from AMD and Intel', 'Analyze Tesla valuation premium compared to traditional automakers and justify based on growth prospects and market positioning').",
            "If calculator is chosen: use the 'calculator' tool. Provide the mathematical expression needed for financial analysis (e.g., if calculating P/E ratio with stock price $150 and EPS $5, expression would be '150 / 5', or for portfolio allocation calculations).",
            "Format your output strictly according to the OrchestratorOutputSchema.",
        ],
    )
    print(f"DEBUG: create_orchestrator_agent - SystemPromptGenerator background[0]: {system_prompt_generator.background[0][:100]}") # Print first 100 chars
    
    agent = BaseAgent(
        BaseAgentConfig(
            client=client,
            model=model_name,
            system_prompt_generator=system_prompt_generator,
            input_schema=OrchestratorInputSchema,
            output_schema=OrchestratorOutputSchema,
        )
    )
    return agent


if __name__ == "__main__":
    # Example usage for search decision
    # Note: This example might need adjustment depending on how `choice_agent` and `ChoiceAgentInputSchema` are defined and imported.
    # Assuming they are accessible in this context for demonstration.
    # search_example = choice_agent.run(
    #     ChoiceAgentInputSchema(user_message="Who won the nobel prize in physics in 2024?", decision_type="needs_search")
    # )
    # print(search_example)
    print("create_orchestrator_agent function is now part of orchestrator_schemas.py")
    print("Example usage would require client and model_name, e.g.:")
    # from your_openai_client_setup import client # Placeholder
    # agent = create_orchestrator_agent(client=client, model_name="gpt-4-turbo")
    # print(agent)
