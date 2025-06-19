"""Scrapy items for Addgene data structures."""

import scrapy
from typing import Optional, List


class PlasmidItem(scrapy.Item):
    """Scrapy item for plasmid data."""
    
    # Basic information
    id = scrapy.Field()
    name = scrapy.Field()
    depositor = scrapy.Field()
    purpose = scrapy.Field()
    
    # URLs and links
    article_url = scrapy.Field()
    map_url = scrapy.Field()
    plasmid_url = scrapy.Field()
    
    # Plasmid details
    insert = scrapy.Field()
    tags = scrapy.Field()
    mutation = scrapy.Field()
    plasmid_type = scrapy.Field()
    vector_type = scrapy.Field()
    popularity = scrapy.Field()
    expression = scrapy.Field()
    promoter = scrapy.Field()
    services = scrapy.Field()
    is_industry = scrapy.Field()
    
    # Additional metadata
    availability = scrapy.Field()
    species = scrapy.Field()
    resistance_marker = scrapy.Field()


class SequenceItem(scrapy.Item):
    """Scrapy item for sequence download information."""
    
    plasmid_id = scrapy.Field()
    format = scrapy.Field()
    download_url = scrapy.Field()
    available = scrapy.Field()
    file_size = scrapy.Field()
    last_updated = scrapy.Field() 