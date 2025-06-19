"""Scrapy pipelines for Addgene."""

from addgene_mcp.scrapy_addgene.pipelines.validation import ValidationPipeline
from addgene_mcp.scrapy_addgene.pipelines.duplicates import DuplicatesPipeline

__all__ = ['ValidationPipeline', 'DuplicatesPipeline'] 