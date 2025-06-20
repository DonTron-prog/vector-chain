#!/usr/bin/env python3
"""Test script for adaptive memory system."""

import asyncio
from models.schemas import ResearchStep, ExecutionFeedback, PlanUpdateRequest
from agents.planning_agent import create_research_plan, evaluate_plan_update
from agents.memory_processors import adaptive_memory_processor
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart

async def test_memory_system():
    """Test the adaptive memory and planning system."""
    print("🧠 Testing Adaptive Memory System\n")
    
    # Test 1: Create initial plan
    print("1. Creating initial research plan...")
    try:
        plan = await create_research_plan(
            query="Should I invest in AAPL for growth?",
            context="5-year horizon, moderate risk tolerance"
        )
        print(f"✅ Plan created with {len(plan.steps)} steps")
        for i, step in enumerate(plan.steps, 1):
            print(f"   {i}. {step.description}")
    except Exception as e:
        print(f"❌ Plan creation failed: {e}")
        return
    
    # Test 2: Create mock feedback for plan update
    print("\n2. Creating execution feedback...")
    mock_feedback = ExecutionFeedback(
        step_completed="Gathered financial data for AAPL",
        findings_quality=0.7,
        data_gaps=["Missing recent earnings guidance", "No competitor comparison"],
        unexpected_findings=["Strong services revenue growth", "Supply chain improvements"],
        suggested_adjustments=["Add competitive analysis step", "Focus on services segment"],
        confidence_level=0.6,
        next_step_recommendation="Analyze competitive position vs MSFT and GOOGL"
    )
    print(f"✅ Feedback created - Quality: {mock_feedback.findings_quality}, Confidence: {mock_feedback.confidence_level}")
    
    # Test 3: Create update request
    print("\n3. Testing plan update evaluation...")
    if len(plan.steps) > 1:
        update_request = PlanUpdateRequest(
            current_step=1,
            feedback=mock_feedback,
            remaining_steps=plan.steps[1:]  # Remaining steps after first one
        )
        
        try:
            update_response, message_history = await evaluate_plan_update(update_request)
            print(f"✅ Update evaluation completed")
            print(f"   Should update: {update_response.should_update}")
            print(f"   Reasoning: {update_response.reasoning}")
            print(f"   Confidence: {update_response.confidence}")
            if update_response.updated_steps:
                print(f"   Updated steps: {len(update_response.updated_steps)}")
            print(f"   Message history length: {len(message_history) if message_history else 0}")
        except Exception as e:
            print(f"❌ Plan update failed: {e}")
            return
    
    # Test 4: Test memory processing
    print("\n4. Testing memory processors...")
    try:
        # Create mock message history
        mock_messages = [
            ModelRequest(parts=[UserPromptPart(content="Create a research plan for AAPL")]),
            ModelResponse(parts=[TextPart(content="I'll create a comprehensive research plan with financial analysis...")]),
            ModelRequest(parts=[UserPromptPart(content="Update the plan based on feedback")]),
            ModelResponse(parts=[TextPart(content="Based on the execution feedback, I recommend updating...")]),
        ]
        
        processed = adaptive_memory_processor(mock_messages)
        print(f"✅ Memory processing completed")
        print(f"   Original messages: {len(mock_messages)}")
        print(f"   Processed messages: {len(processed)}")
        
    except Exception as e:
        print(f"❌ Memory processing failed: {e}")
    
    print("\n🎯 Adaptive memory system test completed!")

if __name__ == "__main__":
    asyncio.run(test_memory_system())