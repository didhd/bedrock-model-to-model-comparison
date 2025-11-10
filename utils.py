"""
Utility functions for Amazon Bedrock model comparison.
"""

import boto3
from typing import Dict, Any


def get_bedrock_client(region_name: str = 'us-east-1'):
    """Initialize and return Bedrock Runtime client."""
    return boto3.client(
        service_name='bedrock-runtime',
        region_name=region_name
    )


def converse(
    client,
    model_id: str,
    prompt: str,
    system_prompt: str = "You are a helpful assistant.",
    temperature: float = 0.0,
    max_tokens: int = 2000,
    reasoning_effort: str = None,
    thinking_budget: int = None
) -> str:
    """
    Invoke a model using Bedrock Converse API with reasoning support.
    
    Args:
        client: Bedrock runtime client
        model_id: Model identifier
        prompt: User prompt
        system_prompt: System prompt
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        reasoning_effort: Reasoning effort level for GPT-OSS ("low", "medium", "high")
        thinking_budget: Maximum thinking tokens for Claude extended thinking (optional)
    
    Returns:
        Response text (final answer, excluding reasoning trace)
    """
    # Build base inference config
    inference_config = {
        "temperature": temperature,
        "maxTokens": max_tokens
    }
    
    # Build converse parameters
    converse_params = {
        "modelId": model_id,
        "messages": [
            {
                "role": "user",
                "content": [{"text": prompt}]
            }
        ],
        "system": [{"text": system_prompt}],
        "inferenceConfig": inference_config
    }
    
    # Add reasoning config for GPT-OSS models using additionalModelRequestFields
    if ('openai' in model_id.lower() or 'gpt' in model_id.lower()) and reasoning_effort:
        converse_params["additionalModelRequestFields"] = {
            "reasoning_effort": reasoning_effort
        }
    
    # Add thinking config for Claude models (in inferenceConfig)
    if 'claude' in model_id.lower() and thinking_budget is not None:
        inference_config["thinking"] = {
            "type": "enabled",
            "budget": thinking_budget
        }
    
    response = client.converse(**converse_params)
    
    # Extract response text
    content = response['output']['message']['content']
    
    # Handle reasoning models that return reasoning trace + final answer
    if len(content) > 1:
        # Return final text response (skip reasoning trace)
        for item in content:
            if 'text' in item:
                return item['text']
    
    # Standard response
    return content[0]['text']


def calculate_monthly_cost(
    requests_per_day: int,
    avg_input_tokens: int,
    avg_output_tokens: int,
    input_price_per_1k: float,
    output_price_per_1k: float
) -> float:
    """Calculate monthly cost based on usage and pricing."""
    monthly_requests = requests_per_day * 30
    monthly_input_tokens = monthly_requests * avg_input_tokens / 1000
    monthly_output_tokens = monthly_requests * avg_output_tokens / 1000
    
    return (
        monthly_input_tokens * input_price_per_1k +
        monthly_output_tokens * output_price_per_1k
    )
