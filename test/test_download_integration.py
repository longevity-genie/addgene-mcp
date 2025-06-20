#!/usr/bin/env python3
"""
Integration test for sequence download functionality.
This demonstrates real-world usage of the download tool.
"""

import pytest
import asyncio
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock

from addgene_mcp.server import AddgeneMCP
from eliot import start_action
import httpx

# Set testing flag
os.environ['TESTING'] = 'true'


class TestDownloadIntegration:
    """Integration tests for the download functionality."""
    
    @pytest.fixture(scope="class")
    def mcp_server(self):
        """Set up the MCP server for testing."""
        return AddgeneMCP()
    
    @pytest.fixture
    def temp_download_dir(self):
        """Create a temporary downloads directory."""
        temp_dir = tempfile.mkdtemp(prefix="addgene_downloads_")
        yield temp_dir
        # Cleanup after test
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_download_workflow_snapgene(self, mcp_server, temp_download_dir):
        """Test complete workflow: search -> get info -> download for SnapGene format."""
        with start_action(action_type="test_download_workflow_snapgene") as action:
            plasmid_id = 12345
            
            # Mock sequence content
            mock_sequence_content = b"""LOCUS       pExample                2000 bp    DNA     circular SYN 01-JAN-2024
DEFINITION  Example plasmid for testing.
ACCESSION   pExample
VERSION     pExample
KEYWORDS    .
SOURCE      synthetic DNA construct
  ORGANISM  synthetic DNA construct
COMMENT     Test plasmid sequence for download functionality.
FEATURES             Location/Qualifiers
     source          1..2000
                     /organism="synthetic DNA construct"
                     /mol_type="other DNA"
ORIGIN      
        1 atgaaataca tgaatcatgc aagaagctta taaagaactt cagaagaaac ggagcgaagg
       61 aagaagaaga agaagaagaa gaagaagaag aagaagaaga agaagaagaa gaagaagaag
      121 aagaagaaga agaagaagaa gaagaagaag aagaagaaga agaagaagaa gaagaagaag
      181 aagaagaaga agaagaagaa gaagaagaag aagaagaaga agaagaagaa gaagaagaag
      241 aagaagaaga agaagaagaa gaagaagaag aagaagaaga agaagaagaa gaagaagaag
      301 aagaagaaga agaagaagaa gaagaagaag aagaagaaga agaagaagaa gaagaagaag
//"""
            
            # Step 1: Mock getting sequence info
            from addgene_mcp.server import SequenceDownloadInfo
            mock_sequence_info = SequenceDownloadInfo(
                plasmid_id=plasmid_id,
                download_url="https://www.addgene.org/sequences/12345.dna",
                format="snapgene",
                available=True
            )
            
            # Step 2: Mock HTTP response for download
            mock_response = MagicMock()
            mock_response.content = mock_sequence_content
            mock_response.raise_for_status = MagicMock()
            
            # Step 3: Execute the download workflow
            with patch.object(mcp_server, 'get_sequence_info', return_value=mock_sequence_info):
                with patch('httpx.AsyncClient') as mock_client:
                    mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
                    
                    # First get sequence info
                    info_result = await mcp_server.get_sequence_info(plasmid_id, "snapgene")
                    
                    # Then download the sequence
                    download_result = await mcp_server.download_sequence(
                        plasmid_id=plasmid_id,
                        format="snapgene",
                        download_directory=temp_download_dir
                    )
            
            action.log(
                message_type="workflow_complete",
                info_available=info_result.available,
                download_success=download_result.download_success,
                file_path=download_result.file_path,
                file_size=download_result.file_size
            )
            
            # Verify sequence info step
            assert info_result.available is True
            assert info_result.download_url is not None
            
            # Verify download step
            assert download_result.download_success is True
            assert download_result.file_path is not None
            assert download_result.file_size == len(mock_sequence_content)
            
            # Verify file exists and has correct content
            assert os.path.exists(download_result.file_path)
            assert download_result.file_path.endswith("plasmid_12345_snapgene.dna")
            
            with open(download_result.file_path, 'rb') as f:
                downloaded_content = f.read()
                assert downloaded_content == mock_sequence_content
                assert b"LOCUS" in downloaded_content
                assert b"pExample" in downloaded_content
    
    @pytest.mark.asyncio
    async def test_download_workflow_genbank(self, mcp_server, temp_download_dir):
        """Test complete workflow for GenBank format."""
        with start_action(action_type="test_download_workflow_genbank") as action:
            plasmid_id = 67890
            
            # Mock GenBank sequence content
            mock_genbank_content = b"""LOCUS       pGFP_Test               3000 bp    DNA     circular SYN 01-JAN-2024
DEFINITION  GFP expression vector for testing.
ACCESSION   pGFP_Test
VERSION     pGFP_Test
KEYWORDS    .
SOURCE      synthetic DNA construct
  ORGANISM  synthetic DNA construct
COMMENT     Test GFP expression plasmid.
FEATURES             Location/Qualifiers
     source          1..3000
                     /organism="synthetic DNA construct"
                     /mol_type="other DNA"
     gene            100..800
                     /gene="gfp"
                     /label="GFP"
     CDS             100..800
                     /gene="gfp"
                     /product="green fluorescent protein"
                     /translation="MSKGEELFTGVVPILVELDGDVNGHKFSVSGEGEG..."
ORIGIN      
        1 atgaaataca tgaatcatgc aagaagctta taaagaactt cagaagaaac ggagcgaagg
       61 aagaagaaga agaagaagaa gaagaagaag aagaagaaga agaagaagaa gaagaagaag
      121 aagaagaaga agaagaagaa gaagaagaag aagaagaaga agaagaagaa gaagaagaag
//"""
            
            from addgene_mcp.server import SequenceDownloadInfo
            mock_sequence_info = SequenceDownloadInfo(
                plasmid_id=plasmid_id,
                download_url="https://www.addgene.org/sequences/67890.gb",
                format="genbank",
                available=True
            )
            
            mock_response = MagicMock()
            mock_response.content = mock_genbank_content
            mock_response.raise_for_status = MagicMock()
            
            with patch.object(mcp_server, 'get_sequence_info', return_value=mock_sequence_info):
                with patch('httpx.AsyncClient') as mock_client:
                    mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
                    
                    download_result = await mcp_server.download_sequence(
                        plasmid_id=plasmid_id,
                        format="genbank",
                        download_directory=temp_download_dir
                    )
            
            action.log(
                message_type="genbank_workflow_complete",
                download_success=download_result.download_success,
                file_path=download_result.file_path
            )
            
            # Verify GenBank download
            assert download_result.download_success is True
            assert download_result.file_path.endswith("plasmid_67890_genbank.gb")
            assert os.path.exists(download_result.file_path)
            
            # Verify GenBank content
            with open(download_result.file_path, 'rb') as f:
                content = f.read()
                assert b"LOCUS" in content
                assert b"pGFP_Test" in content
                assert b"GFP" in content
    
    @pytest.mark.asyncio
    async def test_multiple_downloads_same_directory(self, mcp_server, temp_download_dir):
        """Test downloading multiple sequences to the same directory."""
        with start_action(action_type="test_multiple_downloads") as action:
            plasmids = [
                (11111, "snapgene", b"Mock SnapGene content for plasmid 11111"),
                (22222, "genbank", b"Mock GenBank content for plasmid 22222"),
                (33333, "snapgene", b"Mock SnapGene content for plasmid 33333"),
            ]
            
            downloaded_files = []
            
            for plasmid_id, format_type, mock_content in plasmids:
                from addgene_mcp.server import SequenceDownloadInfo
                mock_sequence_info = SequenceDownloadInfo(
                    plasmid_id=plasmid_id,
                    download_url=f"https://www.addgene.org/sequences/{plasmid_id}.{format_type}",
                    format=format_type,
                    available=True
                )
                
                mock_response = MagicMock()
                mock_response.content = mock_content
                mock_response.raise_for_status = MagicMock()
                
                with patch.object(mcp_server, 'get_sequence_info', return_value=mock_sequence_info):
                    with patch('httpx.AsyncClient') as mock_client:
                        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
                        
                        result = await mcp_server.download_sequence(
                            plasmid_id=plasmid_id,
                            format=format_type,
                            download_directory=temp_download_dir
                        )
                
                downloaded_files.append(result.file_path)
                
                # Verify each download
                assert result.download_success is True
                assert os.path.exists(result.file_path)
                
                # Verify content
                with open(result.file_path, 'rb') as f:
                    content = f.read()
                    assert content == mock_content
            
            action.log(
                message_type="multiple_downloads_complete",
                files_downloaded=len(downloaded_files),
                directory=temp_download_dir
            )
            
            # Verify all files exist in the same directory
            assert len(downloaded_files) == 3
            all_files = os.listdir(temp_download_dir)
            assert len(all_files) == 3
            
            # Verify correct file names
            expected_files = [
                "plasmid_11111_snapgene.dna",
                "plasmid_22222_genbank.gb", 
                "plasmid_33333_snapgene.dna"
            ]
            for expected_file in expected_files:
                assert any(f.endswith(expected_file) for f in downloaded_files)
    
    @pytest.mark.asyncio
    async def test_download_error_handling_workflow(self, mcp_server, temp_download_dir):
        """Test error handling in download workflow."""
        with start_action(action_type="test_download_error_handling") as action:
            plasmid_id = 99999
            
            # Test case 1: Sequence not available
            from addgene_mcp.server import SequenceDownloadInfo
            unavailable_info = SequenceDownloadInfo(
                plasmid_id=plasmid_id,
                download_url=None,
                format="snapgene",
                available=False
            )
            
            with patch.object(mcp_server, 'get_sequence_info', return_value=unavailable_info):
                result = await mcp_server.download_sequence(
                    plasmid_id=plasmid_id,
                    format="snapgene",
                    download_directory=temp_download_dir
                )
            
            action.log(
                message_type="unavailable_sequence_test",
                success=result.download_success,
                error=result.error_message
            )
            
            # Verify graceful failure
            assert result.download_success is False
            assert result.error_message is not None
            assert "not available" in result.error_message.lower()
            
            # Test case 2: Network error during download
            available_info = SequenceDownloadInfo(
                plasmid_id=plasmid_id,
                download_url="https://www.addgene.org/sequences/99999.dna",
                format="snapgene",
                available=True
            )
            
            with patch.object(mcp_server, 'get_sequence_info', return_value=available_info):
                with patch('httpx.AsyncClient') as mock_client:
                    mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                        side_effect=httpx.ConnectError("Connection failed")
                    )
                    
                    result = await mcp_server.download_sequence(
                        plasmid_id=plasmid_id,
                        format="snapgene",
                        download_directory=temp_download_dir
                    )
            
            action.log(
                message_type="network_error_test",
                success=result.download_success,
                error=result.error_message
            )
            
            # Verify graceful failure for network error
            assert result.download_success is False
            assert result.error_message is not None
            assert "failed to download" in result.error_message.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 