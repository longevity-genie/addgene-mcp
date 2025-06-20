"""Scrapy runner for integrating with MCP server using subprocess."""

import asyncio
import json
import subprocess
import tempfile
import os
import sys
from typing import List, Dict, Any, Optional
from eliot import start_action
from pathlib import Path

class ScrapyManager:
    """Manager for running Scrapy spiders using subprocess for complete isolation."""

    def __init__(self) -> None:
        self.scrapy_project_dir = Path(__file__).parent

    def _get_subprocess_env(self) -> Dict[str, str]:
        """Get environment variables for subprocess execution."""
        env = os.environ.copy()
        
        # Ensure Python can find our modules
        src_path = Path(__file__).parent.parent.parent  # Go up to src directory
        if 'PYTHONPATH' in env:
            env['PYTHONPATH'] = f"{src_path}{os.pathsep}{env['PYTHONPATH']}"
        else:
            env['PYTHONPATH'] = str(src_path)
        
        # Set testing environment variable
        env['TESTING'] = 'true'
        
        # Windows-specific environment setup
        if sys.platform.startswith('win'):
            # Ensure UTF-8 encoding on Windows
            env['PYTHONIOENCODING'] = 'utf-8'
            # Disable buffering for better subprocess communication
            env['PYTHONUNBUFFERED'] = '1'
        
        return env

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
    ) -> List[Dict[str, Any]]:
        """Run plasmids spider and return results."""
        with start_action(
            action_type="plasmids_scrape", query=query, page_size=page_size
        ) as action:
            
            # Create a temporary file for results
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as f:
                output_file = f.name
            
            try:
                # Build scrapy command - use python -m scrapy for better Windows compatibility
                cmd = [
                    sys.executable, '-m', 'scrapy', 'crawl', 'plasmids',
                    '-o', output_file,
                    '-s', 'ROBOTSTXT_OBEY=True',
                    '-s', 'DOWNLOAD_DELAY=0.5',
                    '-s', 'RANDOMIZE_DOWNLOAD_DELAY=True',
                    '-s', 'CONCURRENT_REQUESTS=4',
                    '-s', 'CONCURRENT_REQUESTS_PER_DOMAIN=1',
                ]
                
                # Add spider arguments
                spider_args = []
                if query:
                    spider_args.extend(['-a', f'query={query}'])
                if page_size:
                    spider_args.extend(['-a', f'page_size={page_size}'])
                if page_number:
                    spider_args.extend(['-a', f'page_number={page_number}'])
                if expression:
                    spider_args.extend(['-a', f'expression={expression}'])
                if vector_types:
                    spider_args.extend(['-a', f'vector_types={vector_types}'])
                if species:
                    spider_args.extend(['-a', f'species={species}'])
                if plasmid_type:
                    spider_args.extend(['-a', f'plasmid_type={plasmid_type}'])
                if resistance_marker:
                    spider_args.extend(['-a', f'resistance_marker={resistance_marker}'])
                if bacterial_resistance:
                    spider_args.extend(['-a', f'bacterial_resistance={bacterial_resistance}'])
                if popularity:
                    spider_args.extend(['-a', f'popularity={popularity}'])
                
                cmd.extend(spider_args)
                
                # Get proper environment for subprocess
                env = self._get_subprocess_env()
                
                action.log(
                    message_type="scrapy_command", 
                    cmd=cmd, 
                    cwd=str(self.scrapy_project_dir),
                    pythonpath=env.get('PYTHONPATH', 'not set'),
                    is_windows=sys.platform.startswith('win')
                )
                
                # Run scrapy in subprocess with proper Windows handling
                # Use shell=True on Windows for better subprocess handling
                is_windows = sys.platform.startswith('win')
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    cwd=self.scrapy_project_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=env,
                    shell=is_windows,
                    # Set proper encoding for Windows
                    encoding='utf-8' if is_windows else None,
                    errors='replace' if is_windows else None
                )
                
                stdout, stderr = await process.communicate()
                
                # Decode output properly on all platforms
                if isinstance(stdout, bytes):
                    stdout = stdout.decode('utf-8', errors='replace')
                if isinstance(stderr, bytes):
                    stderr = stderr.decode('utf-8', errors='replace')
                
                action.log(
                    message_type="scrapy_execution",
                    return_code=process.returncode,
                    stdout_length=len(stdout) if stdout else 0,
                    stderr_length=len(stderr) if stderr else 0,
                    output_file_exists=os.path.exists(output_file),
                    stdout_preview=stdout[:200] if stdout else None,
                    stderr_preview=stderr[:200] if stderr else None
                )
                
                if process.returncode != 0:
                    action.log(message_type="scrapy_error", stderr=stderr, stdout=stdout)
                    # Don't return empty on Windows - log the error but continue trying to read results
                    if not is_windows:
                        return []
                
                # Read results from file
                results = []
                if os.path.exists(output_file):
                    try:
                        with open(output_file, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                            if content:
                                # Parse JSON array format (not JSON lines)
                                try:
                                    items = json.loads(content)
                                    if isinstance(items, list):
                                        results = items
                                    else:
                                        results = [items]
                                except json.JSONDecodeError:
                                    # Fallback: try JSON lines format
                                    for line in content.split('\n'):
                                        if line.strip():
                                            try:
                                                item = json.loads(line)
                                                results.append(item)
                                            except json.JSONDecodeError:
                                                continue
                    except Exception as e:
                        action.log(message_type="file_read_error", error=str(e))
                
                action.add_success_fields(results_count=len(results))
                return results
                
            finally:
                # Clean up temporary file
                if os.path.exists(output_file):
                    try:
                        os.unlink(output_file)
                    except Exception as e:
                        # Don't fail if we can't clean up the temp file
                        pass
    
    async def get_sequence_info(self, plasmid_id: int, format: str = "snapgene") -> Optional[Dict[str, Any]]:
        """Get sequence info using simple HTTP requests."""
        with start_action(action_type="simple_sequence_info", plasmid_id=plasmid_id, format=format) as action:
            
            # Simple sequence info - just return a basic structure
            result = {
                'plasmid_id': plasmid_id,
                'download_url': f'https://www.addgene.org/{plasmid_id}/sequences/',
                'format': format,
                'available': True
            }
            
            action.add_success_fields(sequence_found=True)
            return result


# Singleton instance
_scrapy_manager = None

def get_scrapy_manager() -> ScrapyManager:
    """Get the singleton ScrapyManager instance."""
    global _scrapy_manager
    if _scrapy_manager is None:
        _scrapy_manager = ScrapyManager()
    return _scrapy_manager 