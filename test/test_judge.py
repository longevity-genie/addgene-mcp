import json
import pytest
import os
from pathlib import Path

from dotenv import load_dotenv
from just_agents import llm_options
from just_agents.base_agent import BaseAgent
from addgene_mcp.server import AddgeneMCP

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
TEST_DIR = PROJECT_ROOT / "test"

# Load judge prompt
with open(TEST_DIR / "judge_prompt.txt", "r", encoding="utf-8") as f:
    JUDGE_PROMPT = f.read().strip()

# System prompt for test agent
SYSTEM_PROMPT = """You are an expert assistant for the Addgene plasmid repository. You help researchers find and understand plasmids for their molecular biology and genetic engineering projects.

You have access to comprehensive search tools for the Addgene repository containing thousands of research plasmids. Use these tools to:

1. Search for plasmids with various filters (expression systems, vector types, resistance markers, etc.)
2. Get sequence information for specific plasmids
3. Find popular plasmids in the research community

Always provide detailed, accurate information about plasmids including:
- Plasmid IDs, names, and depositors
- Expression systems and vector types
- Resistance markers and selection methods
- Applications and research uses
- Availability for industry use when relevant

Be specific with plasmid details and provide actionable information for researchers."""

# Load reference Q&A data
with open(TEST_DIR / "test_qa.json", "r", encoding="utf-8") as f:
    QA_DATA = json.load(f)

answers_model = {
    "model": "gemini/gemini-2.5-flash-preview-05-20",
    "temperature": 0.0
}

judge_model = {
    "model": "gemini/gemini-2.5-flash-preview-05-20", 
    "temperature": 0.0
}

# Initialize agents
def get_test_agent():
    """Get test agent with Addgene MCP tools."""
    addgene_server = AddgeneMCP()
    
    # Get the actual MCP tools from the server
    tools = [
        addgene_server.search_plasmids,
        addgene_server.get_sequence_info,
        addgene_server.get_popular_plasmids
    ]
    
    return BaseAgent(
        llm_options=answers_model,
        tools=tools,
        system_prompt=SYSTEM_PROMPT
    )

judge_agent = BaseAgent(
    llm_options=judge_model,
    tools=[],
    system_prompt=JUDGE_PROMPT
)

@pytest.mark.skipif(
    os.getenv("CI") in ("true", "1", "True") or 
    os.getenv("GITHUB_ACTIONS") in ("true", "1", "True") or 
    os.getenv("GITLAB_CI") in ("true", "1", "True") or 
    os.getenv("JENKINS_URL") is not None,
    reason="Skipping expensive LLM tests in CI to save costs. Run locally with: pytest test/test_judge.py"
)
@pytest.mark.parametrize("qa_item", QA_DATA, ids=[f"Q{i+1}" for i in range(len(QA_DATA))])
def test_question_with_judge(qa_item):
    """Test each question by generating an answer and evaluating it with the judge."""
    load_dotenv(override=True)
    
    question = qa_item["question"]
    reference_answer = qa_item["answer"]
    
    # Get test agent with tools
    test_agent = get_test_agent()
    
    # Generate answer
    generated_answer = test_agent.query(question)
    
    # Judge evaluation
    judge_input = f"""
QUESTION: {question}

REFERENCE ANSWER: {reference_answer}

GENERATED ANSWER: {generated_answer}
"""
    
    judge_result = judge_agent.query(judge_input).strip().upper()
    
    # Print for debugging
    print(f"\nQuestion: {question}")
    print(f"Generated: {generated_answer[:200]}...")
    print(f"Judge: {judge_result}")
    
    if "PASS" not in judge_result:
        print(f"\n=== JUDGE FAILED ===")
        print(f"Question: {question}")
        print(f"Reference Answer: {reference_answer}")
        print(f"Current Answer: {generated_answer}")
        print(f"Judge Result: {judge_result}")
        judge_agent.memory.pretty_print_all_messages()
        print(f"===================")
    
    assert "PASS" in judge_result, f"Judge failed for question: {question}" 