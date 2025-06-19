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
from bs4 import BeautifulSoup
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

class SearchResult(BaseModel):
    """Result from a plasmid search."""
    plasmids: List[PlasmidOverview] = Field(description="List of plasmids found")
    count: int = Field(description="Number of plasmids returned")
    query: str = Field(description="The search query that was executed")
    page: int = Field(description="Page number")
    page_size: int = Field(description="Number of results per page")

class SequenceDownloadInfo(BaseModel):
    """Information about downloading a plasmid sequence."""
    plasmid_id: int
    download_url: Optional[HttpUrl] = None
    format: str
    available: bool

class AddgeneScrapyManager:
    """Manages Scrapy-based scraping for Addgene."""
    
    def __init__(self):
        self.scrapy_manager = get_scrapy_manager()
    
    async def search_plasmids(
        self,
        query: Optional[str] = None,
        page_size: int = 50,
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
        with start_action(action_type="scrapy_search_plasmids", query=query, page_size=page_size, page_number=page_number) as action:
            # Use Scrapy to get results
            scrapy_results = await self.scrapy_manager.search_plasmids(
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
                    plasmid = PlasmidOverview(
                        id=result.get('id', 0),
                        name=result.get('name', ''),
                        depositor=result.get('depositor', ''),
                        purpose=result.get('purpose'),
                        article_url=result.get('article_url'),
                        insert=result.get('insert'),
                        tags=result.get('tags'),
                        mutation=result.get('mutation'),
                        plasmid_type=result.get('plasmid_type'),
                        vector_type=result.get('vector_type'),
                        popularity=result.get('popularity'),
                        expression=result.get('expression'),
                        promoter=result.get('promoter'),
                        map_url=result.get('map_url'),
                        services=result.get('services'),
                        is_industry=result.get('is_industry', False),
                    )
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
    
    async def get_plasmid_sequence_info(self, plasmid_id: int, format: str = "snapgene") -> SequenceDownloadInfo:
        """Get information about downloading a plasmid sequence using Scrapy."""
        with start_action(action_type="scrapy_get_sequence_info", plasmid_id=plasmid_id, format=format) as action:
            # Use Scrapy to get sequence info
            scrapy_result = await self.scrapy_manager.get_sequence_info(plasmid_id, format)
            
            if scrapy_result:
                result = SequenceDownloadInfo(
                    plasmid_id=scrapy_result.get('plasmid_id', plasmid_id),
                    download_url=scrapy_result.get('download_url'),
                    format=scrapy_result.get('format', format),
                    available=scrapy_result.get('available', False)
                )
            else:
                result = SequenceDownloadInfo(
                    plasmid_id=plasmid_id,
                    download_url=None,
                    format=format,
                    available=False
                )
            
            action.add_success_fields(sequence_available=result.available)
            return result

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
    
    def _register_addgene_tools(self):
        """Register Addgene-specific tools."""
        self.tool(name=f"{self.prefix}search_plasmids", description="Search for plasmids in the Addgene repository")(self.search_plasmids)
        self.tool(name=f"{self.prefix}get_sequence_info", description="Get information about downloading a plasmid sequence")(self.get_sequence_info)
        self.tool(name=f"{self.prefix}get_popular_plasmids", description="Get popular plasmids from Addgene")(self.get_popular_plasmids)
    
    def _register_addgene_resources(self):
        """Register Addgene-specific resources."""
        
        @self.resource(f"resource://{self.prefix}api-info")
        def get_api_info() -> str:
            """
            Get information about the Addgene API capabilities.
            
            This resource contains information about:
            - Available search parameters
            - Supported sequence formats
            - Filter options
            - Usage guidelines
            
            Returns:
                API information and usage guidelines
            """
            return """
            Addgene MCP Server API Information
            
            This server provides access to the Addgene plasmid repository through web scraping.
            
            Available Tools:
            1. search_plasmids - Search for plasmids by query and filters
            2. get_sequence_info - Get download information for plasmid sequences
            3. get_popular_plasmids - Get popular plasmids
            
            Search Parameters:
            - query: Free text search across plasmid names, depositors, etc.
            - page_size: Number of results per page (default: 50)
            - page_number: Page number for pagination (default: 1)
            
            Filter Options (LLMs should use the short form values in parentheses):
            
            Expression Systems (expression):
            - "bacterial" (Bacterial Expression)
            - "mammalian" (Mammalian Expression) 
            - "insect" (Insect Expression)
            - "plant" (Plant Expression)
            - "worm" (Worm Expression)
            - "yeast" (Yeast Expression)
            
            Vector Types (vector_types):
            - "aav" (AAV), "cre_lox" (Cre/Lox), "crispr" (CRISPR)
            - "lentiviral" (Lentiviral), "luciferase" (Luciferase)
            - "retroviral" (Retroviral), "rnai" (RNAi)
            - "synthetic_biology" (Synthetic Biology), "talen" (TALEN)
            - "unspecified" (Unspecified)
            
            Species (species):
            - "homo_sapiens" (Homo sapiens), "mus_musculus" (Mus musculus)
            - "rattus_norvegicus" (Rattus norvegicus), "escherichia_coli" (Escherichia coli)
            - "arabidopsis_thaliana" (Arabidopsis thaliana), "danio_rerio" (Danio rerio)
            - "drosophila_melanogaster" (Drosophila melanogaster)
            - "saccharomyces_cerevisiae" (Saccharomyces cerevisiae)
            - "sars_cov_2" (SARS-CoV-2), "synthetic" (Synthetic)
            
            Plasmid Types (plasmid_type):
            - "single_insert" (Encodes one insert), "multiple_inserts" (Encodes multiple inserts)
            - "grna_shrna" (Encodes gRNA/shRNA), "empty_backbone" (Empty backbone)
            
            Eukaryotic Resistance Markers (resistance_marker):
            - "neomycin" (Neomycin/G418), "puromycin" (Puromycin), "hygromycin" (Hygromycin)
            - "blasticidin" (Blasticidin), "zeocin" (Zeocin), "basta" (Basta)
            - "his3" (HIS3), "leu2" (LEU2), "trp1" (TRP1), "ura3" (URA3)
            
            Bacterial Resistance Markers (bacterial_resistance):
            - "ampicillin" (Ampicillin), "kanamycin" (Kanamycin), "chloramphenicol" (Chloramphenicol)
            - "ampicillin_kanamycin" (Ampicillin and kanamycin), "gentamicin" (Gentamicin)
            - "chloramphenicol_ampicillin" (Chloramphenicol and ampicillin)
            - "chloramphenicol_spectinomycin" (Chloramphenicol and spectinomycin)
            - "spectinomycin" (Spectinomycin), "tetracycline" (Tetracycline)
            - "zeocin" (Bleocin/zeocin)
            
            Popularity Levels (popularity):
            - "low" (20+ requests), "medium" (50+ requests), "high" (100+ requests)
            
            Sequence Formats:
            - snapgene: SnapGene format (default)
            - genbank: GenBank format
            - fasta: FASTA format
            
            Note: This is an unofficial API that scrapes the Addgene website.
            Please be respectful of their servers and use reasonable request rates.
            """
    
    async def search_plasmids(
        self,
        query: Optional[str] = None,
        page_size: int = 50,
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
        """Search for plasmids in the Addgene repository."""
        filters = {
            "expression": expression,
            "vector_types": vector_types,
            "species": species,
            "plasmid_type": plasmid_type,
            "resistance_marker": resistance_marker,
            "bacterial_resistance": bacterial_resistance,
            "popularity": popularity
        }
        
        api = AddgeneScrapyManager()
        return await api.search_plasmids(
            query=query,
            page_size=page_size,
            page_number=page_number,
            **filters
        )
    
    async def get_sequence_info(self, plasmid_id: int, format: str = "snapgene") -> SequenceDownloadInfo:
        """Get information about downloading a plasmid sequence."""
        api = AddgeneScrapyManager()
        return await api.get_plasmid_sequence_info(plasmid_id, format)
    
    async def get_popular_plasmids(self, page_size: int = 20) -> SearchResult:
        """Get popular plasmids from Addgene."""
        api = AddgeneScrapyManager()
        return await api.search_plasmids(
            page_size=page_size,
            page_number=1,
            popularity="high"
        )

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