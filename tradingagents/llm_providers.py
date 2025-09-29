"""Bedrock LLM Provider with dynamic model selection for TradingAgents."""

from typing import Any, Dict, Optional, Tuple
import boto3
from langchain_aws import ChatBedrock
from .dynamic_model_selector import DynamicModelSelector


class BedrockLLMFactory:
    """Factory for creating Bedrock LLM instances with optimized configuration."""

    @staticmethod
    def create_llm(
        model: str,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        aws_profile: Optional[str] = None,
        aws_region: str = "us-east-1",
        **kwargs
    ) -> ChatBedrock:
        """Create a Bedrock LLM instance.

        Args:
            model: The model name
            temperature: Model temperature
            max_tokens: Maximum tokens for response
            aws_profile: AWS profile name
            aws_region: AWS region
            **kwargs: Additional Bedrock-specific arguments

        Returns:
            Bedrock LLM instance
        """
        return BedrockLLMFactory._create_bedrock_llm(
            model, temperature, max_tokens, aws_profile, aws_region, **kwargs
        )

    @staticmethod
    def _create_bedrock_llm(
        model: str,
        temperature: float,
        max_tokens: Optional[int],
        aws_profile: Optional[str],
        aws_region: str,
        **kwargs
    ) -> ChatBedrock:
        """Create AWS Bedrock Claude instance."""
        # Set up AWS session with profile if specified
        session = None
        if aws_profile:
            session = boto3.Session(profile_name=aws_profile)

        # Map model names to Bedrock inference profile ARNs or available model IDs
        # Note: Some models require inference profiles instead of direct model IDs
        bedrock_model_mapping = {
            "claude-3-5-sonnet": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            "claude-3-5-sonnet-v2": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            "claude-3-5-sonnet-latest": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            "claude-3-5-haiku-latest": "us.anthropic.claude-3-5-haiku-20241022-v1:0",
            "claude-3-haiku": "us.anthropic.claude-3-haiku-20240307-v1:0",
            "claude-3-opus": "us.anthropic.claude-3-opus-20240229-v1:0",
            "claude-opus-4-0": "us.anthropic.claude-opus-4-0",
            # Use the us. prefixed models which should be available
            "claude-sonnet-4": "us.anthropic.claude-sonnet-4-20250514-v1:0",
        }

        # Use the mapped model ID or the model name as-is if not in mapping
        bedrock_model_id = bedrock_model_mapping.get(model, model)

        llm_kwargs = {
            "model_id": bedrock_model_id,
            "model_kwargs": {
                "temperature": temperature,
            },
            "region_name": aws_region,
        }

        if max_tokens:
            llm_kwargs["model_kwargs"]["max_tokens"] = max_tokens

        if session:
            # Use the session's credentials
            llm_kwargs.update({
                "credentials_profile_name": aws_profile,
            })

        # Add any additional Bedrock-specific kwargs
        bedrock_kwargs = {k: v for k, v in kwargs.items() if not k.startswith('openai_')}
        llm_kwargs.update(bedrock_kwargs)

        return ChatBedrock(**llm_kwargs)

    @staticmethod
    def create_dynamic_llm(
        task_type: str,
        context: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Tuple[ChatBedrock, str]:
        """Create a Bedrock LLM instance using dynamic model selection.

        Args:
            task_type: Type of task being performed
            context: Additional context for model selection
            config: Configuration dictionary
            **kwargs: Additional Bedrock-specific arguments

        Returns:
            Tuple of (Bedrock LLM instance, selection_reasoning)
        """
        if not config:
            raise ValueError("Config required for dynamic model selection")

        # Initialize model selector
        model_selector = DynamicModelSelector(config)

        # Get optimal model for the task
        selected_model, reasoning = model_selector.select_model_for_task(
            task_type, context
        )

        # Create Bedrock LLM with selected model
        llm = BedrockLLMFactory.create_llm(
            model=selected_model,
            aws_profile=config.get("aws_profile"),
            aws_region=config.get("aws_region", "us-east-1"),
            **kwargs
        )

        return llm, reasoning

    @staticmethod
    def create_agent_llm(
        agent_role: str,
        config: Dict[str, Any],
        **kwargs
    ) -> Tuple[ChatBedrock, str]:
        """Create a Bedrock LLM instance optimized for a specific agent role.

        Args:
            agent_role: Role of the agent (e.g., 'market_analyst', 'trader')
            config: Configuration dictionary
            **kwargs: Additional Bedrock-specific arguments

        Returns:
            Tuple of (Bedrock LLM instance, selection_reasoning)
        """
        model_selector = DynamicModelSelector(config)
        recommended_model = model_selector.get_recommended_model_for_agent(agent_role)

        reasoning = f"Agent '{agent_role}' assigned model '{recommended_model}' based on role requirements"

        llm = BedrockLLMFactory.create_llm(
            model=recommended_model,
            aws_profile=config.get("aws_profile"),
            aws_region=config.get("aws_region", "us-east-1"),
            **kwargs
        )

        return llm, reasoning


def get_configured_llms(config: Dict[str, Any]) -> Tuple[ChatBedrock, ChatBedrock]:
    """Get configured Bedrock LLM instances based on config.

    Args:
        config: Configuration dictionary

    Returns:
        Tuple of (quick_thinking_llm, deep_thinking_llm)
    """
    quick_model = config.get("quick_think_llm", "claude-3-5-sonnet")
    deep_model = config.get("deep_think_llm", "claude-sonnet-4")

    # AWS Bedrock specific configs
    aws_profile = config.get("aws_profile")
    aws_region = config.get("aws_region", "us-east-1")

    # Model temperature settings
    quick_temp = config.get("quick_think_temperature", 0.1)
    deep_temp = config.get("deep_think_temperature", 0.1)

    # Max tokens
    quick_max_tokens = config.get("quick_think_max_tokens", 4000)
    deep_max_tokens = config.get("deep_think_max_tokens", 8000)

    quick_thinking_llm = BedrockLLMFactory.create_llm(
        model=quick_model,
        temperature=quick_temp,
        max_tokens=quick_max_tokens,
        aws_profile=aws_profile,
        aws_region=aws_region,
    )

    deep_thinking_llm = BedrockLLMFactory.create_llm(
        model=deep_model,
        temperature=deep_temp,
        max_tokens=deep_max_tokens,
        aws_profile=aws_profile,
        aws_region=aws_region,
    )

    return quick_thinking_llm, deep_thinking_llm


def get_dynamic_llms(config: Dict[str, Any]) -> Tuple[ChatBedrock, ChatBedrock, DynamicModelSelector]:
    """Get dynamically configured Bedrock LLM instances with model selector.

    Args:
        config: Configuration dictionary

    Returns:
        Tuple of (quick_thinking_llm, deep_thinking_llm, model_selector)
    """
    aws_profile = config.get("aws_profile")
    aws_region = config.get("aws_region", "us-east-1")

    # Initialize model selector
    model_selector = DynamicModelSelector(config)

    # Get optimal models for different thinking levels
    quick_model, quick_reasoning = model_selector.select_model_for_task(
        "basic_calculations",  # Simple task
        context={"thinking_level": "quick"}
    )

    deep_model, deep_reasoning = model_selector.select_model_for_task(
        "investment_research",  # Complex task
        context={"thinking_level": "deep"}
    )

    print(f"Dynamic Model Selection:")
    print(f"  Quick thinking: {quick_reasoning}")
    print(f"  Deep thinking: {deep_reasoning}")

    # Create Bedrock LLM instances
    quick_thinking_llm = BedrockLLMFactory.create_llm(
        model=quick_model,
        temperature=config.get("quick_think_temperature", 0.1),
        max_tokens=config.get("quick_think_max_tokens", 4000),
        aws_profile=aws_profile,
        aws_region=aws_region,
    )

    deep_thinking_llm = BedrockLLMFactory.create_llm(
        model=deep_model,
        temperature=config.get("deep_think_temperature", 0.1),
        max_tokens=config.get("deep_think_max_tokens", 8000),
        aws_profile=aws_profile,
        aws_region=aws_region,
    )

    return quick_thinking_llm, deep_thinking_llm, model_selector