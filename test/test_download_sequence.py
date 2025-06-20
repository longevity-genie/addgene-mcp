#!/usr/bin/env python3
"""
Test sequence download functionality for Addgene MCP.
Tests downloading plasmid sequence files to local filesystem.
"""

import pytest
import asyncio
import os
import tempfile
import shutil
from pathlib import Path
from typing import Optional
from unittest.mock import patch, AsyncMock, MagicMock

from addgene_mcp.server import AddgeneMCP, SequenceDownloadResult, SequenceDownloadInfo
from addgene_mcp.datatypes import SequenceFormat
from eliot import start_action
import httpx

# Set testing flag to use optimized scrapy settings
os.environ['TESTING'] = 'true'


class TestSequenceDownload:
    """Test sequence download functionality."""
    
    @pytest.fixture(scope="class")
    def mcp_server(self):
        """Set up the MCP server for testing."""
        return AddgeneMCP()
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for downloads."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup after test
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def mock_sequence_content(self):
        """Mock sequence file content."""
        return b"LOCUS       pUC19                   2686 bp    DNA     circular SYN 01-JAN-1980\nDEFINITION  pUC19 cloning vector.\n//\n"
    
    def test_server_has_download_method(self, mcp_server):
        """Test that the server has the download method."""
        assert hasattr(mcp_server, 'download_sequence')
        assert callable(mcp_server.download_sequence)
    
    @pytest.mark.asyncio
    async def test_download_sequence_success_snapgene(self, mcp_server, temp_dir, mock_sequence_content):
        """Test successful sequence download in SnapGene format."""
        with start_action(action_type="test_download_sequence_success_snapgene") as action:
            plasmid_id = 12345
            
            # Mock the get_sequence_info method to return a valid download URL
            mock_sequence_info = SequenceDownloadInfo(
                plasmid_id=plasmid_id,
                download_url="https://www.addgene.org/sequences/12345.dna",
                format="snapgene",
                available=True
            )
            
            # Mock the HTTP response
            mock_response = MagicMock()
            mock_response.content = mock_sequence_content
            mock_response.raise_for_status = MagicMock()
            
            with patch.object(mcp_server, 'get_sequence_info', return_value=mock_sequence_info):
                with patch('httpx.AsyncClient') as mock_client:
                    mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
                    
                    result = await mcp_server.download_sequence(
                        plasmid_id=plasmid_id,
                        format="snapgene",
                        download_directory=temp_dir
                    )
            
            action.log(
                message_type="download_result",
                success=result.download_success,
                file_path=result.file_path,
                file_size=result.file_size
            )
            
            # Verify download result
            assert isinstance(result, SequenceDownloadResult)
            assert result.download_success is True
            assert result.plasmid_id == plasmid_id
            assert result.format == "snapgene"
            assert result.error_message is None
            assert result.file_path is not None
            assert result.file_size == len(mock_sequence_content)
            
            # Verify file was created
            assert os.path.exists(result.file_path)
            assert result.file_path.endswith("plasmid_12345_snapgene.dna")
            
            # Verify file content
            with open(result.file_path, 'rb') as f:
                content = f.read()
                assert content == mock_sequence_content
    
    @pytest.mark.asyncio
    async def test_download_sequence_success_genbank(self, mcp_server, temp_dir, mock_sequence_content):
        """Test successful sequence download in GenBank format."""
        with start_action(action_type="test_download_sequence_success_genbank") as action:
            plasmid_id = 67890
            
            # Mock the get_sequence_info method to return a valid download URL
            mock_sequence_info = SequenceDownloadInfo(
                plasmid_id=plasmid_id,
                download_url="https://www.addgene.org/sequences/67890.gb",
                format="genbank",
                available=True
            )
            
            # Mock the HTTP response
            mock_response = MagicMock()
            mock_response.content = mock_sequence_content
            mock_response.raise_for_status = MagicMock()
            
            with patch.object(mcp_server, 'get_sequence_info', return_value=mock_sequence_info):
                with patch('httpx.AsyncClient') as mock_client:
                    mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
                    
                    result = await mcp_server.download_sequence(
                        plasmid_id=plasmid_id,
                        format="genbank",
                        download_directory=temp_dir
                    )
            
            action.log(
                message_type="download_result_genbank",
                success=result.download_success,
                file_path=result.file_path,
                file_size=result.file_size
            )
            
            # Verify download result
            assert result.download_success is True
            assert result.format == "genbank"
            assert result.file_path.endswith("plasmid_67890_genbank.gb")
            
            # Verify file was created with correct extension
            assert os.path.exists(result.file_path)
    
    @pytest.mark.asyncio
    async def test_download_sequence_not_available(self, mcp_server, temp_dir):
        """Test download when sequence is not available."""
        with start_action(action_type="test_download_sequence_not_available") as action:
            plasmid_id = 99999
            
            # Mock the get_sequence_info method to return unavailable sequence
            mock_sequence_info = SequenceDownloadInfo(
                plasmid_id=plasmid_id,
                download_url=None,
                format="snapgene",
                available=False
            )
            
            with patch.object(mcp_server, 'get_sequence_info', return_value=mock_sequence_info):
                result = await mcp_server.download_sequence(
                    plasmid_id=plasmid_id,
                    format="snapgene",
                    download_directory=temp_dir
                )
            
            action.log(
                message_type="unavailable_sequence_result",
                success=result.download_success,
                error=result.error_message
            )
            
            # Verify failure result
            assert result.download_success is False
            assert result.plasmid_id == plasmid_id
            assert result.file_path is None
            assert result.file_size is None
            assert "not available" in result.error_message.lower()
    
    @pytest.mark.asyncio
    async def test_download_sequence_http_error(self, mcp_server, temp_dir):
        """Test download when HTTP request fails."""
        with start_action(action_type="test_download_sequence_http_error") as action:
            plasmid_id = 12345
            
            # Mock the get_sequence_info method to return a valid download URL
            mock_sequence_info = SequenceDownloadInfo(
                plasmid_id=plasmid_id,
                download_url="https://www.addgene.org/sequences/12345.dna",
                format="snapgene",
                available=True
            )
            
            # Mock HTTP client to raise an exception
            with patch.object(mcp_server, 'get_sequence_info', return_value=mock_sequence_info):
                with patch('httpx.AsyncClient') as mock_client:
                    mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                        side_effect=httpx.HTTPStatusError("404 Not Found", request=None, response=None)
                    )
                    
                    result = await mcp_server.download_sequence(
                        plasmid_id=plasmid_id,
                        format="snapgene",
                        download_directory=temp_dir
                    )
            
            action.log(
                message_type="http_error_result",
                success=result.download_success,
                error=result.error_message
            )
            
            # Verify failure result
            assert result.download_success is False
            assert result.plasmid_id == plasmid_id
            assert result.file_path is None
            assert result.error_message is not None
            assert "failed to download" in result.error_message.lower()
    
    @pytest.mark.asyncio
    async def test_download_sequence_default_directory(self, mcp_server, mock_sequence_content):
        """Test download to default directory (current directory)."""
        with start_action(action_type="test_download_sequence_default_directory") as action:
            plasmid_id = 54321
            
            # Mock the get_sequence_info method
            mock_sequence_info = SequenceDownloadInfo(
                plasmid_id=plasmid_id,
                download_url="https://www.addgene.org/sequences/54321.dna",
                format="snapgene",
                available=True
            )
            
            # Mock the HTTP response
            mock_response = MagicMock()
            mock_response.content = mock_sequence_content
            mock_response.raise_for_status = MagicMock()
            
            with patch.object(mcp_server, 'get_sequence_info', return_value=mock_sequence_info):
                with patch('httpx.AsyncClient') as mock_client:
                    mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
                    
                    result = await mcp_server.download_sequence(
                        plasmid_id=plasmid_id,
                        format="snapgene"
                        # No download_directory specified - should use current directory
                    )
            
            action.log(
                message_type="default_directory_result",
                success=result.download_success,
                file_path=result.file_path
            )
            
            # Verify download result
            assert result.download_success is True
            assert result.file_path is not None
            
            # Clean up file created in current directory
            if result.file_path and os.path.exists(result.file_path):
                os.remove(result.file_path)
    
    @pytest.mark.asyncio
    async def test_download_sequence_creates_directory(self, mcp_server, mock_sequence_content):
        """Test that download creates directory if it doesn't exist."""
        with start_action(action_type="test_download_sequence_creates_directory") as action:
            plasmid_id = 11111
            
            # Use a non-existent directory path
            with tempfile.TemporaryDirectory() as temp_parent:
                non_existent_dir = os.path.join(temp_parent, "sequences", "downloads")
                assert not os.path.exists(non_existent_dir)
                
                # Mock the get_sequence_info method
                mock_sequence_info = SequenceDownloadInfo(
                    plasmid_id=plasmid_id,
                    download_url="https://www.addgene.org/sequences/11111.dna",
                    format="snapgene",
                    available=True
                )
                
                # Mock the HTTP response
                mock_response = MagicMock()
                mock_response.content = mock_sequence_content
                mock_response.raise_for_status = MagicMock()
                
                with patch.object(mcp_server, 'get_sequence_info', return_value=mock_sequence_info):
                    with patch('httpx.AsyncClient') as mock_client:
                        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
                        
                        result = await mcp_server.download_sequence(
                            plasmid_id=plasmid_id,
                            format="snapgene",
                            download_directory=non_existent_dir
                        )
                
                action.log(
                    message_type="directory_creation_result",
                    success=result.download_success,
                    directory_exists=os.path.exists(non_existent_dir)
                )
                
                # Verify directory was created
                assert os.path.exists(non_existent_dir)
                assert result.download_success is True
                assert os.path.exists(result.file_path)
    
    @pytest.mark.asyncio
    async def test_download_sequence_file_naming(self, mcp_server, temp_dir, mock_sequence_content):
        """Test correct file naming for different formats and plasmid IDs."""
        with start_action(action_type="test_download_sequence_file_naming") as action:
            test_cases = [
                (12345, "snapgene", "plasmid_12345_snapgene.dna"),
                (67890, "genbank", "plasmid_67890_genbank.gb"),
                (999, "snapgene", "plasmid_999_snapgene.dna"),
                (1, "genbank", "plasmid_1_genbank.gb"),
            ]
            
            for plasmid_id, format_type, expected_filename in test_cases:
                # Mock the get_sequence_info method
                mock_sequence_info = SequenceDownloadInfo(
                    plasmid_id=plasmid_id,
                    download_url=f"https://www.addgene.org/sequences/{plasmid_id}.{format_type}",
                    format=format_type,
                    available=True
                )
                
                # Mock the HTTP response
                mock_response = MagicMock()
                mock_response.content = mock_sequence_content
                mock_response.raise_for_status = MagicMock()
                
                with patch.object(mcp_server, 'get_sequence_info', return_value=mock_sequence_info):
                    with patch('httpx.AsyncClient') as mock_client:
                        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
                        
                        result = await mcp_server.download_sequence(
                            plasmid_id=plasmid_id,
                            format=format_type,
                            download_directory=temp_dir
                        )
                
                action.log(
                    message_type="file_naming_test",
                    plasmid_id=plasmid_id,
                    format=format_type,
                    expected=expected_filename,
                    actual=os.path.basename(result.file_path) if result.file_path else None
                )
                
                # Verify correct filename
                assert result.download_success is True
                assert result.file_path.endswith(expected_filename)
                assert os.path.exists(result.file_path)
    
    @pytest.mark.asyncio
    async def test_download_sequence_data_types(self, mcp_server, temp_dir, mock_sequence_content):
        """Test that download returns correct data types."""
        with start_action(action_type="test_download_sequence_data_types") as action:
            plasmid_id = 12345
            
            # Mock successful download
            mock_sequence_info = SequenceDownloadInfo(
                plasmid_id=plasmid_id,
                download_url="https://www.addgene.org/sequences/12345.dna",
                format="snapgene",
                available=True
            )
            
            mock_response = MagicMock()
            mock_response.content = mock_sequence_content
            mock_response.raise_for_status = MagicMock()
            
            with patch.object(mcp_server, 'get_sequence_info', return_value=mock_sequence_info):
                with patch('httpx.AsyncClient') as mock_client:
                    mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
                    
                    result = await mcp_server.download_sequence(
                        plasmid_id=plasmid_id,
                        format="snapgene",
                        download_directory=temp_dir
                    )
            
            action.log(
                message_type="data_types_validation",
                result_type=type(result).__name__
            )
            
            # Verify data types
            assert isinstance(result, SequenceDownloadResult)
            assert isinstance(result.plasmid_id, int)
            assert isinstance(result.format, str)
            assert isinstance(result.download_success, bool)
            
            if result.file_path:
                assert isinstance(result.file_path, str)
            
            if result.file_size:
                assert isinstance(result.file_size, int)
                assert result.file_size > 0
            
            if result.error_message:
                assert isinstance(result.error_message, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 