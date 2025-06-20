#!/usr/bin/env python3
"""Addgene MCP Server - API interface for Addgene plasmid repository."""

import asyncio
import os
from typing import List, Dict, Any, Optional, Union
from contextlib import asynccontextmanager
import sys
import typer

from fastmcp import FastMCP
from pydantic import BaseModel, Field, HttpUrl
from eliot import start_action
import httpx
from tenacity import retry, stop_after_attempt, retry_if_exception_type

# Import datatypes for proper type validation and LLM tool calling guidance
from addgene_mcp.datatypes import (
    Expression, 
    VectorType, 
    Species, 
    PlasmidType, 
    ResistanceMarker, 
    BacterialResistance, 
    Popularity, 
    SequenceFormat,
    PageSize,
    PageNumber
)

from addgene_mcp.scrapy_addgene.runner import get_scrapy_manager

# Get version from package metadata
from importlib.metadata import version
__version__ = version("addgene-mcp")

# Configuration
DEFAULT_HOST = os.getenv("MCP_HOST", "0.0.0.0")
DEFAULT_PORT = int(os.getenv("MCP_PORT", "3001"))
DEFAULT_TRANSPORT = os.getenv("MCP_TRANSPORT", "streamable-http")

ADDGENE_BASE_URL = "https://www.addgene.org"
ADDGENE_PLASMID_CATALOG_PATH = "/search/catalog/plasmids/"
ADDGENE_PLASMID_SEQUENCES_PATH = "/{plasmid_id}/sequences/"

# Pydantic models for responses
class PlasmidOverview(BaseModel):
    """Overview of a plasmid from search results."""
    id: int
    name: str
    depositor: str
    purpose: Optional[str] = None
    article_url: Optional[HttpUrl] = None
    insert: Optional[str] = None
    tags: Optional[str] = None
    mutation: Optional[str] = None
    plasmid_type: Optional[str] = None
    vector_type: Optional[str] = None
    popularity: Optional[str] = None
    expression: Optional[List[str]] = None
    promoter: Optional[str] = None
    map_url: Optional[HttpUrl] = None
    services: Optional[str] = None
    is_industry: bool = False

class SequenceDownloadInfo(BaseModel):
    """Information about downloading a plasmid sequence."""
    plasmid_id: int
    download_url: Optional[HttpUrl] = None
    format: str
    available: bool

class SequenceDownloadResult(BaseModel):
    """Result of downloading a plasmid sequence file."""
    plasmid_id: int
    format: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    download_success: bool
    error_message: Optional[str] = None

class SearchResult(BaseModel):
    """Search results for plasmids."""
    plasmids: List[PlasmidOverview]
    count: int
    query: str
    page: int
    page_size: int

class AddgeneMCP(FastMCP):
    """Addgene MCP Server with API tools that can be inherited and extended."""
    
    def __init__(
        self, 
        name: str = "Addgene MCP Server",
        prefix: str = "addgene_",
        **kwargs
    ):
        """Initialize the Addgene tools with API manager and FastMCP functionality."""
        # Initialize FastMCP with the provided name and any additional kwargs
        super().__init__(name=name, **kwargs)
        
        self.prefix = prefix
        
        # Register our tools and resources
        self._register_addgene_tools()
        self._register_addgene_resources()
        
        self.scraper = get_scrapy_manager()
    
    def _register_addgene_tools(self):
        """Register Addgene-specific tools."""
        @self.tool(name=f"{self.prefix}search_plasmids", description="Search for plasmids in the Addgene repository using text queries and filters. You MUST use the exact string values specified in the parameter documentation. Common use cases: find plasmids for gene expression (specify species and expression system), gene editing (vector_types='crispr'), cloning vectors (plasmid_type='empty_backbone'), or protein expression (expression='bacterial' or 'mammalian').")
        async def search_plasmids_tool(
            query: Optional[str] = None,
            page_size: int = 50,  # NOTE: Maximum page_size is 50. Values > 50 are not processed properly by Addgene's website
            page_number: int = 1,
            expression: Optional[Expression] = None,
            vector_types: Optional[VectorType] = None,
            species: Optional[Species] = None,
            plasmid_type: Optional[PlasmidType] = None,
            resistance_marker: Optional[ResistanceMarker] = None,
            bacterial_resistance: Optional[BacterialResistance] = None,
            popularity: Optional[Popularity] = None
        ) -> SearchResult:
            """Search for plasmids in the Addgene repository."""
            return await self.search_plasmids(
                query=query,
                page_size=page_size,
                page_number=page_number,
                expression=expression,
                vector_types=vector_types,
                species=species,
                plasmid_type=plasmid_type,
                resistance_marker=resistance_marker,
                bacterial_resistance=bacterial_resistance,
                popularity=popularity
            )
        
        @self.tool(name=f"{self.prefix}get_sequence_info", description="Get information about downloading a plasmid sequence file. Requires a valid Addgene plasmid ID. Returns download URL and availability status. Use EXACTLY format='snapgene' for SnapGene .dna files or format='genbank' for GenBank .gb files. These are the only two valid format values.")
        async def get_sequence_info_tool(plasmid_id: int, format: SequenceFormat = "snapgene") -> SequenceDownloadInfo:
            """Get information about downloading a plasmid sequence."""
            return await self.get_sequence_info(plasmid_id, format)
        
        @self.tool(name=f"{self.prefix}get_popular_plasmids", description="Get the most popular plasmids from Addgene (100+ requests each). This is a convenience method for finding widely-used, well-established plasmids. Returns up to 50 results.")
        async def get_popular_plasmids_tool(page_size: int = 20) -> SearchResult:
            """Get popular plasmids from Addgene."""
            return await self.get_popular_plasmids(page_size=page_size)
        
        @self.tool(name=f"{self.prefix}download_sequence", description="Download a plasmid sequence file to the local filesystem. This actually downloads the file from Addgene and saves it locally. Use EXACTLY format='genbank' for .gb files (default) or format='snapgene' for .dna files. These are the only two valid format values. Returns the local file path and download status.")
        async def download_sequence_tool(
            plasmid_id: int, 
            format: SequenceFormat = "genbank",
            download_directory: Optional[str] = None
        ) -> SequenceDownloadResult:
            """Download a plasmid sequence file to the local filesystem."""
            return await self.download_sequence(plasmid_id, format, download_directory)
    
    def _register_addgene_resources(self):
        """Register Addgene-specific resources."""
        @self.resource(f"resource://{self.prefix}api-info")
        def get_api_info() -> str:
            """Get API information about Addgene endpoints and parameters."""
            return """
            Addgene API Information:
            - This MCP interacts with Addgene through web scraping.
            - All search parameters are based on available filters on the Addgene website.
            - Available endpoints: search_plasmids, get_sequence_info, get_popular_plasmids
            - Please be respectful of their servers and use reasonable request rates.
            """

    async def search_plasmids(
        self,
        query: Optional[str] = None,
        page_size: int = 50,  # NOTE: Maximum page_size is 50. Values > 50 are not processed properly by Addgene's website
        page_number: int = 1,
        
        # EXPRESSION SYSTEM FILTERS - Controls where/how the plasmid is expressed
        # Use these EXACT string values for the expression parameter:
        # - "bacterial" for bacterial expression systems (E. coli, etc.)
        # - "mammalian" for mammalian cell expression (HEK293, CHO cells, etc.)
        # - "insect" for insect cell expression (Sf9, High Five cells, etc.)
        # - "plant" for plant expression systems (Arabidopsis, tobacco, etc.)
        # - "worm" for C. elegans expression
        # - "yeast" for yeast expression (S. cerevisiae, P. pastoris, etc.)
        # 
        # USAGE EXAMPLES:
        # - For protein expression in E. coli: expression="bacterial"
        # - For mammalian cell transfection: expression="mammalian"
        # - For C. elegans transgenes: expression="worm"
        # - For yeast two-hybrid assays: expression="yeast"
        # 
        # IMPORTANT: These are the ONLY valid values. Common incorrect values to avoid:
        # - DON'T use "prokaryotic" (use "bacterial" instead)
        # - DON'T use "eukaryotic" (specify "mammalian", "yeast", etc. instead)
        # - DON'T use organism names like "escherichia_coli" here (use species parameter for that)
        expression: Optional[Expression] = None,
        
        # VECTOR TYPE FILTERS - Controls the type of vector/delivery system
        # Use these EXACT string values for the vector_types parameter:
        # - "aav" for Adeno-Associated Virus vectors
        # - "cre_lox" for Cre-Lox recombination systems
        # - "crispr" for CRISPR/Cas9 gene editing vectors
        # - "lentiviral" for lentiviral expression vectors
        # - "luciferase" for luciferase reporter vectors
        # - "retroviral" for retroviral vectors (non-lentiviral)
        # - "rnai" for RNAi/shRNA knockdown vectors
        # - "synthetic_biology" for synthetic biology applications
        # - "talen" for TALEN gene editing vectors
        # - "unspecified" for general cloning vectors
        #
        # USAGE EXAMPLES:
        # - For CRISPR gene editing: vector_types="crispr"
        # - For stable cell line generation: vector_types="lentiviral"
        # - For gene knockdown studies: vector_types="rnai"
        # - For AAV-mediated gene therapy: vector_types="aav"
        # - For basic cloning: vector_types="unspecified"
        #
        # IMPORTANT: These are the ONLY valid values. Common incorrect values to avoid:
        # - DON'T use "adenoviral" (AAV is different, use "aav")
        # - DON'T use "cas9" (use "crispr")
        # - DON'T use "shrna" (use "rnai")
        vector_types: Optional[VectorType] = None,
        
        # SPECIES FILTERS - Controls the species/organism the plasmid is designed for
        # Use these EXACT string values for the species parameter:
        # - "arabidopsis_thaliana" for Arabidopsis thaliana (model plant)
        # - "danio_rerio" for zebrafish
        # - "drosophila_melanogaster" for fruit fly
        # - "escherichia_coli" for E. coli bacteria
        # - "homo_sapiens" for human
        # - "mus_musculus" for mouse
        # - "rattus_norvegicus" for rat
        # - "saccharomyces_cerevisiae" for baker's yeast
        # - "sars_cov_2" for SARS-CoV-2 coronavirus
        # - "synthetic" for synthetic/artificial sequences
        #
        # USAGE EXAMPLES:
        # - For human gene studies: species="homo_sapiens"
        # - For mouse models: species="mus_musculus"
        # - For yeast expression: species="saccharomyces_cerevisiae"
        # - For bacterial expression: species="escherichia_coli"
        # - For COVID-19 research: species="sars_cov_2"
        # - For plant biology: species="arabidopsis_thaliana"
        #
        # IMPORTANT: These are the ONLY valid values. Common incorrect values to avoid:
        # - DON'T use "human" (use "homo_sapiens")
        # - DON'T use "mouse" (use "mus_musculus") 
        # - DON'T use "rat" (use "rattus_norvegicus")
        # - DON'T use "yeast" (use "saccharomyces_cerevisiae")
        # - DON'T use "ecoli" or "e_coli" (use "escherichia_coli")
        # - DON'T use "mammalian" as species (use specific species like "homo_sapiens")
        species: Optional[Species] = None,
        
        # PLASMID TYPE FILTERS - Controls the type/structure of the plasmid
        # Use these EXACT string values for the plasmid_type parameter:
        # - "empty_backbone" for empty vector backbones without inserts
        # - "grna_shrna" for plasmids encoding guide RNAs or short hairpin RNAs
        # - "multiple_inserts" for plasmids with multiple gene inserts
        # - "single_insert" for plasmids with one gene insert
        #
        # USAGE EXAMPLES:
        # - For cloning vectors: plasmid_type="empty_backbone"
        # - For CRISPR guide RNAs: plasmid_type="grna_shrna"
        # - For RNAi knockdown: plasmid_type="grna_shrna"
        # - For single gene expression: plasmid_type="single_insert"
        # - For multi-gene constructs: plasmid_type="multiple_inserts"
        #
        # IMPORTANT: These are the ONLY valid values. Common incorrect values to avoid:
        # - DON'T use "backbone" (use "empty_backbone")
        # - DON'T use "grna" or "shrna" separately (use "grna_shrna")
        # - DON'T use "one_insert" (use "single_insert")
        plasmid_type: Optional[PlasmidType] = None,
        
        # EUKARYOTIC RESISTANCE MARKER FILTERS - Controls eukaryotic selection markers
        # Use these EXACT string values for the resistance_marker parameter:
        # - "basta" for Basta/glufosinate resistance
        # - "blasticidin" for blasticidin S resistance
        # - "his3" for histidine biosynthesis marker (yeast)
        # - "hygromycin" for hygromycin B resistance
        # - "leu2" for leucine biosynthesis marker (yeast)
        # - "neomycin" for neomycin/G418 resistance
        # - "puromycin" for puromycin resistance
        # - "trp1" for tryptophan biosynthesis marker (yeast)
        # - "ura3" for uracil biosynthesis marker (yeast)
        # - "zeocin" for zeocin resistance
        #
        # USAGE EXAMPLES:
        # - For mammalian cell selection: resistance_marker="puromycin" or resistance_marker="neomycin"
        # - For yeast selection: resistance_marker="his3" or resistance_marker="leu2" or resistance_marker="ura3"
        # - For plant selection: resistance_marker="hygromycin" or resistance_marker="basta"
        # - For general eukaryotic selection: resistance_marker="zeocin"
        #
        # IMPORTANT: These are the ONLY valid values. Common incorrect values to avoid:
        # - DON'T use "g418" (use "neomycin")
        # - DON'T use "puro" (use "puromycin")
        # - DON'T use "hygro" (use "hygromycin")
        # - DON'T confuse with bacterial_resistance (this is for eukaryotic cells)
        resistance_marker: Optional[ResistanceMarker] = None,
        
        # BACTERIAL RESISTANCE FILTERS - Controls bacterial selection markers
        # Use these EXACT string values for the bacterial_resistance parameter:
        # - "ampicillin" for ampicillin resistance only
        # - "ampicillin_kanamycin" for dual ampicillin and kanamycin resistance
        # - "zeocin" for zeocin/bleocin resistance
        # - "chloramphenicol" for chloramphenicol resistance only
        # - "chloramphenicol_ampicillin" for dual chloramphenicol and ampicillin
        # - "chloramphenicol_spectinomycin" for dual chloramphenicol and spectinomycin
        # - "gentamicin" for gentamicin resistance
        # - "kanamycin" for kanamycin resistance only
        # - "spectinomycin" for spectinomycin resistance
        # - "tetracycline" for tetracycline resistance
        #
        # USAGE EXAMPLES:
        # - For standard cloning: bacterial_resistance="ampicillin"
        # - For dual selection: bacterial_resistance="ampicillin_kanamycin"
        # - For chloramphenicol-resistant vectors: bacterial_resistance="chloramphenicol"
        # - For high-copy plasmids: bacterial_resistance="kanamycin"
        #
        # IMPORTANT: These are the ONLY valid values. Common incorrect values to avoid:
        # - DON'T use "amp" (use "ampicillin")
        # - DON'T use "kan" (use "kanamycin")
        # - DON'T use "cm" or "cam" (use "chloramphenicol")
        # - DON'T use "tet" (use "tetracycline")
        # - DON'T confuse with resistance_marker (this is for bacterial selection)
        bacterial_resistance: Optional[BacterialResistance] = None,
        
        # POPULARITY FILTERS - Controls popularity level based on request count
        # Use these EXACT string values for the popularity parameter:
        # - "low" for plasmids with 20+ requests (moderately popular)
        # - "medium" for plasmids with 50+ requests (highly popular)
        # - "high" for plasmids with 100+ requests (extremely popular)
        #
        # USAGE EXAMPLES:
        # - For well-established plasmids: popularity="high"
        # - For commonly used plasmids: popularity="medium"
        # - For recently published plasmids: popularity="low"
        # - For finding the most trusted plasmids: popularity="high"
        #
        # IMPORTANT: These are the ONLY valid values. Common incorrect values to avoid:
        # - DON'T use "popular" (use "high")
        # - DON'T use "unpopular" (omit parameter or use "low")
        # - DON'T use numbers like "100" (use "high")
        popularity: Optional[Popularity] = None
    ) -> SearchResult:
        """Search for plasmids on Addgene using Scrapy."""
        with start_action(action_type="mcp_search_plasmids", query=query, page_size=page_size, page_number=page_number) as action:
            scrapy_results = await self.scraper.search_plasmids(
                query=query,
                page_size=page_size,
                page_number=page_number,
                expression=expression,
                vector_types=vector_types,
                species=species,
                plasmid_type=plasmid_type,
                resistance_marker=resistance_marker,
                bacterial_resistance=bacterial_resistance,
                popularity=popularity
            )
            
            # Convert results to PlasmidOverview objects
            plasmids = []
            for result in scrapy_results:
                try:
                    plasmid = PlasmidOverview(**result)
                    plasmids.append(plasmid)
                except Exception as e:
                    action.log(message_type="plasmid_conversion_error", error=str(e), result=result)
                    continue
            
            result = SearchResult(
                plasmids=plasmids,
                count=len(plasmids),
                query=query or "",
                page=page_number,
                page_size=page_size
            )
            
            action.add_success_fields(results_count=len(plasmids))
            return result
    
    async def get_sequence_info(self, plasmid_id: int, format: SequenceFormat = "snapgene") -> SequenceDownloadInfo:
        """Get information about downloading a plasmid sequence.
        
        Args:
            plasmid_id: The Addgene plasmid ID number (e.g., 12345)
            format: Sequence file format - use these EXACT string values:
                   - "snapgene" for SnapGene .dna files (default, recommended)
                   - "genbank" for GenBank .gb files
                   
        USAGE EXAMPLES:
        - For SnapGene format: format="snapgene" 
        - For GenBank format: format="genbank"
        
        IMPORTANT: These are the ONLY valid values. Common incorrect values to avoid:
        - DON'T use "dna" (use "snapgene")
        - DON'T use "gb" or "gbk" (use "genbank")
        - DON'T use "fasta" (not available, use "genbank")
        """
        with start_action(action_type="mcp_get_sequence_info", plasmid_id=plasmid_id, format=format) as action:
            # Use Scrapy to get sequence info
            scrapy_result = await self.scraper.get_sequence_info(plasmid_id, format)
            
            if scrapy_result:
                result = SequenceDownloadInfo(**scrapy_result)
            else:
                result = SequenceDownloadInfo(
                    plasmid_id=plasmid_id,
                    download_url=None,
                    format=format,
                    available=False
                )
            
            action.add_success_fields(sequence_available=result.available)
            return result
    
    async def get_popular_plasmids(self, page_size: int = 50) -> SearchResult:
        """Get popular plasmids from Addgene (100+ requests each).
        
        This is a convenience method that searches for plasmids with high popularity
        (100+ requests). It's equivalent to calling search_plasmids with popularity="high".
        
        Args:
            page_size: Number of results to return (max 50)
            
        EXAMPLES:
        - For top 20 most popular plasmids: page_size=20
        - For top 50 most popular plasmids: page_size=50 (default)
        
        COMMON MISTAKES TO AVOID:
        - DON'T use page_size > 50 (will be capped at 50)
        """
        with start_action(action_type="mcp_get_popular_plasmids", page_size=page_size) as action:
            result = await self.search_plasmids(
                page_size=page_size,
                page_number=1,
                popularity="high"
            )
            action.add_success_fields(results_count=result.count)
            return result

    async def download_sequence(
        self, 
        plasmid_id: int, 
        format: SequenceFormat = "genbank",
        download_directory: Optional[str] = None
    ) -> SequenceDownloadResult:
        """Download a plasmid sequence file to the local filesystem.
        
        Args:
            plasmid_id: The Addgene plasmid ID number (e.g., 12345)
            format: Sequence file format - use these EXACT string values:
                   - "genbank" for GenBank .gb files (default)
                   - "snapgene" for SnapGene .dna files
            download_directory: Optional directory to save the file. If None, resolves to the current 
                   working directory (recommended unless you need a specific location).
                   
        USAGE EXAMPLES:
        - Download SnapGene format: format="snapgene" 
        - Download GenBank format: format="genbank"
        - Save to specific directory: download_directory="/path/to/sequences"
        
        IMPORTANT: These are the ONLY valid values. Common incorrect values to avoid:
        - DON'T use "dna" (use "snapgene")
        - DON'T use "gb" or "gbk" (use "genbank")
        - DON'T use "fasta" (not available, use "genbank")
        
        Returns:
            SequenceDownloadResult with download status and local file path
        """
        with start_action(action_type="mcp_download_sequence", plasmid_id=plasmid_id, format=format) as action:
            try:
                # First get the sequence info to get the download URL
                sequence_info = await self.get_sequence_info(plasmid_id, format)
                
                if not sequence_info.available or not sequence_info.download_url:
                    return SequenceDownloadResult(
                        plasmid_id=plasmid_id,
                        format=format,
                        download_success=False,
                        error_message=f"Sequence not available for plasmid {plasmid_id} in {format} format"
                    )
                
                # Set up download directory
                # It's recommended to resolve to the current working directory by default
                # unless the user specifically wants a different location
                import os
                if download_directory is None:
                    download_directory = os.getcwd()  # Use current working directory
                else:
                    download_directory = os.path.abspath(download_directory)  # Make absolute
                
                # Create directory if it doesn't exist
                os.makedirs(download_directory, exist_ok=True)
                
                # Determine file extension based on format
                extension = ".dna" if format == "snapgene" else ".gb"
                filename = f"plasmid_{plasmid_id}_{format}{extension}"
                file_path = os.path.join(download_directory, filename)
                
                # Download the file
                async with httpx.AsyncClient(
                    timeout=30.0,
                    follow_redirects=True,
                    headers={'User-Agent': 'addgene-mcp/1.0.0 (+https://github.com/your-repo/addgene-mcp)'}
                ) as client:
                    response = await client.get(str(sequence_info.download_url))
                    response.raise_for_status()
                    
                    # Write file to disk
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    
                    file_size = len(response.content)
                    
                    action.add_success_fields(
                        file_path=file_path,
                        file_size=file_size,
                        download_url=str(sequence_info.download_url)
                    )
                    
                    return SequenceDownloadResult(
                        plasmid_id=plasmid_id,
                        format=format,
                        file_path=file_path,
                        file_size=file_size,
                        download_success=True
                    )
                    
            except Exception as e:
                error_message = f"Failed to download sequence: {str(e)}"
                action.log(message_type="download_error", error=error_message)
                
                return SequenceDownloadResult(
                    plasmid_id=plasmid_id,
                    format=format,
                    download_success=False,
                    error_message=error_message
                )

# Create Typer app
app = typer.Typer(
    name="addgene-mcp",
    help="Addgene MCP Server - API interface for Addgene plasmid repository",
    add_completion=False
)

def version_callback(value: bool):
    """Show version information."""
    if value:
        typer.echo(f"addgene-mcp version {__version__}")
        raise typer.Exit()

@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(
        None, 
        "--version", 
        "-V", 
        callback=version_callback, 
        is_eager=True,
        help="Show version and exit"
    )
):
    """Addgene MCP Server - API interface for Addgene plasmid repository."""
    if ctx.invoked_subcommand is None:
        # Default to stdio if no command is specified
        cli_app_stdio()

@app.command("server")
def cli_app(
    host: str = typer.Option(DEFAULT_HOST, "--host", help="Host to bind to"),
    port: int = typer.Option(DEFAULT_PORT, "--port", help="Port to bind to")
):
    """Run the Addgene MCP server with HTTP transport."""
    mcp = AddgeneMCP()
    mcp.run(transport=DEFAULT_TRANSPORT, host=host, port=port)

@app.command("stdio")
def cli_app_stdio():
    """Run the Addgene MCP server with STDIO transport."""
    mcp = AddgeneMCP()
    mcp.run(transport="stdio")

@app.command("sse")
def cli_app_sse(
    host: str = typer.Option(DEFAULT_HOST, "--host", help="Host to bind to"),
    port: int = typer.Option(DEFAULT_PORT, "--port", help="Port to bind to")
):
    """Run the Addgene MCP server with SSE transport."""
    mcp = AddgeneMCP()
    mcp.run(transport="sse", host=host, port=port)

# For backward compatibility - default command
@app.command(hidden=True)
def default():
    """Default command - runs STDIO transport."""
    cli_app_stdio()

# Individual Typer apps for script entry points
stdio_app = typer.Typer(name="stdio", help="Run the Addgene MCP server with STDIO transport")

@stdio_app.callback(invoke_without_command=True)
def cli_app_stdio_entry(ctx: typer.Context):
    """Run the Addgene MCP server with STDIO transport."""
    cli_app_stdio()

server_app = typer.Typer(name="server", help="Run the Addgene MCP server with HTTP transport")

@server_app.callback(invoke_without_command=True)
def cli_app_entry(
    ctx: typer.Context,
    host: str = typer.Option(DEFAULT_HOST, "--host", help="Host to bind to"),
    port: int = typer.Option(DEFAULT_PORT, "--port", help="Port to bind to")
):
    """Run the Addgene MCP server with HTTP transport."""
    mcp = AddgeneMCP()
    mcp.run(transport=DEFAULT_TRANSPORT, host=host, port=port)

sse_app = typer.Typer(name="sse", help="Run the Addgene MCP server with SSE transport")

@sse_app.callback(invoke_without_command=True)
def cli_app_sse_entry(
    ctx: typer.Context,
    host: str = typer.Option(DEFAULT_HOST, "--host", help="Host to bind to"),
    port: int = typer.Option(DEFAULT_PORT, "--port", help="Port to bind to")
):
    """Run the Addgene MCP server with SSE transport."""
    mcp = AddgeneMCP()
    mcp.run(transport="sse", host=host, port=port)

if __name__ == "__main__":
    app() 