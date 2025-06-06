#!/usr/bin/env python3
"""
Demo script for testing the investment research orchestrator with example scenarios.
This file contains investment research query examples for testing the orchestrator.
"""

import sys
from rich.console import Console
from rich.panel import Panel

from orchestration_engine import ConfigManager, create_orchestrator_agent, OrchestratorCore, ToolManager


def setup_environment_and_client(config):
    """Set up environment variables and initialize the OpenAI client."""
    import openai
    import instructor
    client = instructor.from_openai(openai.OpenAI(api_key=config["openai_api_key"]))
    return client


def process_single_query(agent, tools, query_data, console, generate_final_answer_flag=False, reset_memory=True):
    """Process a single investment research query through the complete orchestration pipeline."""
    # Create tool manager and orchestrator core for enhanced functionality
    tool_manager = ToolManager(tools)
    orchestrator_core = OrchestratorCore(agent, tool_manager, console)
    
    # Use the new orchestrator core method
    return orchestrator_core.process_single_query(
        query_data=query_data,
        generate_final_answer_flag=generate_final_answer_flag,
        reset_memory=reset_memory,
        verbose=True
    )


def run_example_scenarios(agent, tools, example_data, console, generate_final_answer_flag=False, reset_memory=True):
    """Run through a list of example investment research scenarios."""
    console.print(Panel(
        agent.system_prompt_generator.generate_prompt(),
        title="System Prompt",
        expand=False
    ))
    console.print("\n")
    
    for query_input in example_data:
        process_single_query(
            agent=agent,
            tools=tools,
            query_data=query_input,
            console=console,
            generate_final_answer_flag=generate_final_answer_flag,
            reset_memory=reset_memory
        )


def main():
    """Main execution flow for demo investment research scenarios."""
    # Define example investment research queries
    example_queries = [
        {
            "query": "Summarize Apple's financial performance in Q3 2023 and key risk factors mentioned in their 2023 10-K.",
            "context": "Utilize information from AAPL's Q3 2023 10-Q, 2023 10-K, and the Q3 2023 earnings call transcript. Focus on revenue, net income, segment performance, and explicitly stated risks."
        },
        {
            "query": "What were Microsoft's key growth drivers in Intelligent Cloud for Q1 FY2024, and what is their strategy regarding AI services like Azure OpenAI?",
            "context": "Refer to MSFT's Q1 FY2024 10-Q, the corresponding earnings call transcript, and recent analyst reports. Specifically look for Azure growth numbers and commentary on AI product adoption."
        },
        {
            "query": "Research emerging risks in the semiconductor industry supply chain",
            "context": "Analyze geopolitical tensions, China-Taiwan relations impact, and alternative supply chain strategies. Focus on companies with high Asia exposure"
        },
        {
            "query": "Assess Apple's iPhone market share trends and competitive threats",
            "context": "Focus on Q4 2024 earnings, compare with Samsung and emerging Chinese brands. Analyze impact of AI features on upgrade cycles"
        }
    ]
    
    # Standard orchestration mode
    config = ConfigManager.load_configuration()
    
    openai_client = setup_environment_and_client(config)
    
    agent = create_orchestrator_agent(
        client=openai_client,
        model_name=config["model_name"]
    )
    
    tool_instances = ConfigManager.initialize_tools(config)
    
    console_instance = Console()
    
    run_example_scenarios(
        agent=agent,
        tools=tool_instances,
        example_data=example_queries,
        console=console_instance,
        generate_final_answer_flag=True
    )


if __name__ == "__main__":
    main()