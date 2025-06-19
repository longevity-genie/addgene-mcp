import json
from pathlib import Path

import typer
from dotenv import load_dotenv
from eliot import start_action, log_call
from pycomfort.logging import to_nice_file, to_nice_stdout

from just_agents import llm_options
from just_agents.llm_options import LLMOptions
from just_agents.base_agent import BaseAgent
from addgene_mcp.server import AddgeneMCP

app = typer.Typer()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
TEST_DIR = PROJECT_ROOT / "test"
LOGS_DIR = PROJECT_ROOT / "logs"

# Create logs directory
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Test questions based on actual tested functionality
TEST_QUESTIONS = [
    "Search for plasmids containing 'pLKO' and return 5 results",
    "Find GFP plasmids with mammalian expression and high popularity, limit to 10 results",
    "Search for something that definitely doesn't exist like 'VERY_UNLIKELY_PLASMID_NAME_XYZVWTUP123456789'",
    "Test pagination by searching for 'GFP' with page size 1",
    "Test pagination by searching for 'GFP' with page size 10", 
    "Test pagination by searching for 'GFP' with page size 50",
    "Search for 'p53' plasmids on page 1 with 10 results",
    "Search for 'p53' plasmids on page 2 with 10 results",
    "Search for plasmids and show me the data structure with ID, name, and depositor",
    "Find plasmids with mammalian expression system",
    "Search for plasmids with single_insert plasmid type, mammalian expression, and high popularity",
    "Search for plasmids and show me the article_url and map_url fields",
    "Search for plasmids and check the is_industry boolean field",
    "Get sequence information for a plasmid with ID 12345 in snapgene format",
    "Get sequence information for a plasmid with ID 12345 in genbank format",
    "Get sequence information for a plasmid with ID 12345 in fasta format",
    "Get popular plasmids with page size 20",
    "Search for CRISPR plasmids with vector_types='crispr'",
    "Search for lentiviral plasmids with vector_types='lentiviral'",
    "Search for plasmids with bacterial expression system",
]

answers_model = {
    "model": "gemini/gemini-2.5-flash-preview-05-20",
    "temperature": 0.0
}

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

@log_call()
def run_query(query: str, options: LLMOptions = answers_model):
    """Run a query against the Addgene MCP server."""
    load_dotenv(override=True)

    addgene_server = AddgeneMCP()
    
    # Get the actual MCP tools from the server
    tools = [
        addgene_server.search_plasmids,
        addgene_server.get_sequence_info,
        addgene_server.get_popular_plasmids
    ]
    
    agent = BaseAgent(
        llm_options=options,
        tools=tools,
        system_prompt=SYSTEM_PROMPT
    )

    with start_action(action_type="run_query", query=query) as action:
        action.log(f"question sent to the agent: {query}")
        result = agent.query(query)
        action.log(f"LLM AGENT ANSWER: {result}")
        return result

@app.command()
def test_addgene():
    """Test the Addgene MCP server with predefined research questions."""
    
    to_nice_stdout()
    to_nice_file(LOGS_DIR / "test_addgene_human.json", LOGS_DIR / "test_addgene_human.log")

    # Collect question-answer pairs
    qa_pairs = []
    
    for query in TEST_QUESTIONS:
        print(f"\n{'='*60}")
        print(f"QUESTION: {query}")
        print(f"{'='*60}")
        
        answer = run_query(query)
        print(f"ANSWER: {answer}")
        
        qa_pairs.append({
            "question": query,
            "answer": answer
        })
    
    # Save question-answer pairs to JSON file
    qa_json_path = LOGS_DIR / "test_addgene_qa.json"
    with qa_json_path.open("w", encoding="utf-8") as f:
        json.dump(qa_pairs, f, indent=2, ensure_ascii=False)
    
    print(f"\nQuestion-answer pairs saved to: {qa_json_path}")

@app.command()
def test_single(question: str):
    """Test a single question against the Addgene MCP server."""
    
    to_nice_stdout()
    to_nice_file(LOGS_DIR / "test_addgene_single.json", LOGS_DIR / "test_addgene_single.log")

    print(f"\nQUESTION: {question}")
    print(f"{'='*60}")
    
    answer = run_query(question)
    print(f"ANSWER: {answer}")

@app.command()
def interactive():
    """Start an interactive session to test questions."""
    
    to_nice_stdout() 
    to_nice_file(LOGS_DIR / "test_addgene_interactive.json", LOGS_DIR / "test_addgene_interactive.log")

    print("Interactive Addgene MCP Testing")
    print("="*40)
    print("Type your questions about plasmids. Type 'quit' to exit.")
    print()
    
    while True:
        try:
            question = input("Question: ").strip()
            if question.lower() in ['quit', 'exit', 'q']:
                break
            if not question:
                continue
                
            print(f"\nSearching Addgene repository...")
            answer = run_query(question)
            print(f"\nAnswer: {answer}")
            print("-" * 60)
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    app() 