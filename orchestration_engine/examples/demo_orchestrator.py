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
            "query": "Analyze NVIDIA's competitive position in AI chips market including market share and technological advantages",
            "context": "Focus on Q3 2024 earnings, compare with AMD and Intel, assess impact of new Blackwell architecture on competitive moat"
        },
        {
            "query": "Evaluate Tesla's valuation premium compared to traditional automakers",
            "context": "Compare P/E ratios, growth prospects, and market positioning. Focus on autonomous driving capabilities and energy business contribution to justify premium"
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