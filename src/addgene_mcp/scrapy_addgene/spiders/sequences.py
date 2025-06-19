"""Scrapy spider for scraping plasmid sequence download information."""

import scrapy
from urllib.parse import urljoin
from typing import Optional
from eliot import start_action

from addgene_mcp.scrapy_addgene.items import SequenceItem


class SequenceSpider(scrapy.Spider):
    """Spider for scraping plasmid sequence download information."""
    
    name = 'sequences'
    allowed_domains = ['addgene.org']
    
    custom_settings = {
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 1,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS': 4,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
        'USER_AGENT': 'addgene-mcp/0.1.0 (+https://github.com/your-repo/addgene-mcp)',
    }
    
    def __init__(self, plasmid_id: int, format: str = "snapgene", **kwargs):
        """Initialize spider with plasmid ID and format."""
        super().__init__(**kwargs)
        self.plasmid_id = int(plasmid_id)
        self.format = format
        self.start_urls = [f'https://www.addgene.org/{self.plasmid_id}/sequences/']
    
    def parse(self, response):
        """Parse the sequences page and extract download URLs."""
        with start_action(action_type="parse_sequences", plasmid_id=self.plasmid_id, format=self.format) as action:
            # Find full plasmid sequence section
            full_sequences_section = response.css('section#depositor-full')
            
            download_url = None
            available = False
            
            if full_sequences_section:
                # Look for the specific format download link
                download_link = full_sequences_section.css(f'a.{self.format}-file-download::attr(href)').get()
                if download_link:
                    download_url = urljoin(response.url, download_link)
                    available = True
                    action.log(message_type="download_url_found", url=download_url)
                else:
                    action.log(message_type="download_url_not_found", format=self.format)
            else:
                action.log(message_type="sequences_section_not_found")
            
            yield SequenceItem(
                plasmid_id=self.plasmid_id,
                format=self.format,
                download_url=download_url,
                available=available,
            ) 