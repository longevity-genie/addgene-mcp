import asyncio
from src.addgene_mcp.scrapy_addgene.runner import ScrapyRunner

async def debug_fields():
    runner = ScrapyRunner()
    results = await runner.run_spider('plasmids', query='alzheimer', page_size=5)
    print('First 5 results:')
    for i, result in enumerate(results[:5]):
        print(f'Result {i+1}:')
        for key, value in result.items():
            if value:  # Only show non-empty fields
                print(f'  {key}: {value}')
        print()

if __name__ == "__main__":
    asyncio.run(debug_fields()) 