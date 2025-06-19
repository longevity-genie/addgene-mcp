#!/usr/bin/env python3
"""Addgene MCP Server - API interface for Addgene plasmid repository."""

import asyncio
import os
from typing import List, Dict, Any, Optional, Union
from contextlib import asynccontextmanager
import sys
import argparse

from fastmcp import FastMCP
from pydantic import BaseModel, Field, HttpUrl
from eliot import start_action
import httpx
from tenacity import retry, stop_after_attempt, retry_if_exception_type

from addgene_mcp.scrapy_addgene.runner import get_scrapy_manager

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
        @self.tool(name=f"{self.prefix}search_plasmids", description="Search for plasmids in the Addgene repository")
        async def search_plasmids_tool(
            query: Optional[str] = None,
            page_size: int = 50,  # NOTE: Maximum page_size is 50. Values > 50 are not processed properly by Addgene's website
            page_number: int = 1,
            expression: Optional[str] = None,
            vector_types: Optional[str] = None,
            species: Optional[str] = None,
            plasmid_type: Optional[str] = None,
            resistance_marker: Optional[str] = None,
            bacterial_resistance: Optional[str] = None,
            popularity: Optional[str] = None
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
        
        @self.tool(name=f"{self.prefix}get_sequence_info", description="Get information about downloading a plasmid sequence")
        async def get_sequence_info_tool(plasmid_id: int, format: str = "snapgene") -> SequenceDownloadInfo:
            """Get information about downloading a plasmid sequence."""
            return await self.get_sequence_info(plasmid_id, format)
        
        @self.tool(name=f"{self.prefix}get_popular_plasmids", description="Get popular plasmids from Addgene")
        async def get_popular_plasmids_tool(page_size: int = 20) -> SearchResult:
            """Get popular plasmids from Addgene."""
            return await self.get_popular_plasmids(page_size=page_size)
    
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
        # Expression System Filters - Controls where/how the plasmid is expressed
        # Available options: "bacterial", "mammalian", "insect", "plant", "worm", "yeast"
        # Maps to: "Bacterial Expression", "Mammalian Expression", "Insect Expression", 
        #          "Plant Expression", "Worm Expression", "Yeast Expression"
        expression: Optional[str] = None,
        
        # Vector Type Filters - Controls the type of vector/delivery system
        # Available options: "aav", "cre_lox", "crispr", "lentiviral", "luciferase", 
        #                   "retroviral", "rnai", "synthetic_biology", "talen", "unspecified"
        # Maps to: "AAV", "Cre/Lox", "CRISPR", "Lentiviral", "Luciferase", 
        #          "Retroviral", "RNAi", "Synthetic Biology", "TALEN", "Unspecified"
        vector_types: Optional[str] = None,
        
        # Species Filters - Controls the species/organism the plasmid is designed for
        # Available options: "arabidopsis_thaliana", "danio_rerio", "drosophila_melanogaster", 
        #                   "escherichia_coli", "homo_sapiens", "mus_musculus", "rattus_norvegicus", 
        #                   "saccharomyces_cerevisiae", "sars_cov_2", "synthetic"
        # Maps to: "Arabidopsis thaliana", "Danio rerio", "Drosophila melanogaster", 
        #          "Escherichia coli", "Homo sapiens", "Mus musculus", "Rattus norvegicus", 
        #          "Saccharomyces cerevisiae", "Severe acute respiratory syndrome coronavirus 2", "Synthetic"
        species: Optional[str] = None,
        
        # Plasmid Type Filters - Controls the type/structure of the plasmid
        # Available options: "empty_backbone", "grna_shrna", "multiple_inserts", "single_insert"
        # Maps to: "Empty backbone", "Encodes gRNA/shRNA", "Encodes multiple inserts", "Encodes one insert"
        plasmid_type: Optional[str] = None,
        
        # Eukaryotic Resistance Marker Filters - Controls eukaryotic selection markers
        # Available options: "basta", "blasticidin", "his3", "hygromycin", "leu2", 
        #                   "neomycin", "puromycin", "trp1", "ura3", "zeocin"
        # Maps to: "Basta", "Blasticidin", "HIS3", "Hygromycin", "LEU2", 
        #          "Neomycin (select with G418)", "Puromycin", "TRP1", "URA3", "Zeocin"
        resistance_marker: Optional[str] = None,
        
        # Bacterial Resistance Filters - Controls bacterial selection markers
        # Available options: "ampicillin", "ampicillin_kanamycin", "zeocin", "chloramphenicol", 
        #                   "chloramphenicol_ampicillin", "chloramphenicol_spectinomycin", 
        #                   "gentamicin", "kanamycin", "spectinomycin", "tetracycline"
        # Maps to: "Ampicillin", "Ampicillin and kanamycin", "Bleocin (zeocin)", "Chloramphenicol", 
        #          "Chloramphenicol and ampicillin", "Chloramphenicol and spectinomycin", 
        #          "Gentamicin", "Kanamycin", "Spectinomycin", "Tetracycline"
        bacterial_resistance: Optional[str] = None,
        
        # Popularity Filters - Controls popularity level based on request count
        # Available options: "low", "medium", "high"
        # Maps to: "20+ requests", "50+ requests", "100+ requests"
        popularity: Optional[str] = None
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
    
    async def get_sequence_info(self, plasmid_id: int, format: str = "snapgene") -> SequenceDownloadInfo:
        """Get information about downloading a plasmid sequence."""
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
    
    async def get_popular_plasmids(self, page_size: int = 20) -> SearchResult:
        """Get popular plasmids from Addgene."""
        with start_action(action_type="mcp_get_popular_plasmids", page_size=page_size) as action:
            result = await self.search_plasmids(
                page_size=page_size,
                page_number=1,
                popularity="high"
            )
            action.add_success_fields(results_count=result.count)
            return result

def cli_app():
    """Run the Addgene MCP server with HTTP transport."""
    parser = argparse.ArgumentParser(description="Addgene MCP Server")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Host to bind to")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to bind to")
    args = parser.parse_args()
    
    mcp = AddgeneMCP()
    mcp.run(transport=DEFAULT_TRANSPORT, host=args.host, port=args.port)

def cli_app_stdio():
    """Run the Addgene MCP server with STDIO transport."""
    mcp = AddgeneMCP()
    mcp.run(transport="stdio")

def cli_app_sse():
    """Run the Addgene MCP server with SSE transport."""
    parser = argparse.ArgumentParser(description="Addgene MCP Server")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Host to bind to")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to bind to")
    args = parser.parse_args()
    
    mcp = AddgeneMCP()
    mcp.run(transport="sse", host=args.host, port=args.port)

if __name__ == "__main__":
    cli_app_stdio() 