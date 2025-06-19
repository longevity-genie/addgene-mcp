# Judge-Based Testing for Addgene MCP

This directory contains judge-based tests for evaluating the quality of answers provided by the Addgene MCP server. The testing system uses an LLM judge to automatically evaluate whether generated answers meet the quality standards compared to reference answers.

## Overview

The judge-based testing system includes:

- **`test_judge.py`** - Automated pytest tests using LLM judge evaluation
- **`judge_prompt.txt`** - Prompt for the LLM judge defining evaluation criteria
- **`test_qa.json`** - Reference questions and answers based on actual tested functionality
- **`manual_test_questions.py`** - Interactive testing tools for manual exploration

## Test Coverage

The test suite covers the core MCP functions that are actually tested in our comprehensive test suite:

### Core MCP Functions Tested
1. **`search_plasmids()`** - Search with various parameters and filters
2. **`get_sequence_info()`** - Get sequence download information
3. **`get_popular_plasmids()`** - Retrieve popular plasmids

### Test Scenarios Based on Actual Tests
- **Basic Search**: Testing search functionality with queries like 'pLKO'
- **Filtered Search**: Testing search with expression systems, popularity filters
- **Empty Results**: Testing handling of non-existent plasmids
- **Pagination**: Testing different page sizes and page numbers
- **Data Structure Validation**: Testing required fields (ID, name, depositor, is_industry)
- **Filter Validation**: Testing expression system filtering
- **URL Validation**: Testing article_url and map_url fields
- **Sequence Downloads**: Testing sequence info retrieval in different formats

## Setup

Install dev dependencies:
```bash
uv sync --group dev
```

Set up environment variables in `.env`:
```bash
# Required for LLM judge functionality
ANTHROPIC_API_KEY=your_key_here
# or
OPENAI_API_KEY=your_key_here
# or 
GOOGLE_API_KEY=your_key_here
```

## Running Tests

### Automated Judge Tests
```bash
# Run all judge-based tests
uv run pytest test/test_judge.py -v

# Run specific test
uv run pytest test/test_judge.py::test_question_with_judge -v

# Skip CI check and run locally
pytest test/test_judge.py -v
```

**Note**: Judge tests are automatically skipped in CI environments to save costs. Run them locally for development.

### Manual Testing
```bash
# Test all predefined questions
uv run python test/manual_test_questions.py test-addgene

# Test a single question
uv run python test/manual_test_questions.py test-single "Search for pLKO plasmids"

# Interactive testing
uv run python test/manual_test_questions.py interactive
```

## Understanding the Tests

### Test Questions Format
Each test question is designed to trigger specific MCP function calls:

```json
{
  "question": "Search for plasmids containing 'pLKO' and return 5 results",
  "answer": "I'll search for plasmids containing 'pLKO' with a page size of 5. This should return a SearchResult with valid plasmid data including IDs, names, depositors, and boolean industry availability flags."
}
```

### Judge Evaluation Criteria
The LLM judge evaluates answers based on:
- **Correctness**: Plasmid information accuracy
- **Completeness**: Required fields and data structure
- **Function Calls**: Whether appropriate MCP functions were called
- **Data Validation**: Proper handling of IDs, URLs, boolean fields

## Development

### Adding New Test Cases
1. Add test scenarios based on actual functionality in `test_comprehensive_mcp.py`
2. Create questions that trigger specific MCP function calls
3. Write expected behavior descriptions (not hallucinated data)
4. Test locally before committing

### Judge Prompt Tuning
Edit `judge_prompt.txt` to adjust evaluation criteria. Focus on:
- Technical accuracy over creative content
- Function call validation
- Data structure correctness
- Error handling appropriateness

## Files

- **`test_judge.py`**: Main test file with proper imports and MCP integration
- **`test_qa.json`**: 12 test cases covering all major functionality
- **`judge_prompt.txt`**: LLM judge evaluation criteria
- **`manual_test_questions.py`**: Interactive testing with 20 test questions
- **`README_JUDGE_TESTING.md`**: This documentation

## Cost Considerations

Judge-based tests use LLM APIs and incur costs. Tests are automatically skipped in CI environments. For development:

- Run tests selectively during development
- Use cheaper models for initial testing
- Run full test suite before major releases
- Consider caching responses for repeated tests 