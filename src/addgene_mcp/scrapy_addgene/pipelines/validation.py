"""Validation pipeline for Scrapy items."""

from scrapy.exceptions import DropItem
from eliot import start_action
from addgene_mcp.scrapy_addgene.items import PlasmidItem, SequenceItem


class ValidationPipeline:
    """Pipeline to validate scraped items."""
    
    def process_item(self, item, spider):
        """Validate item data."""
        with start_action(action_type="validate_item", item_type=type(item).__name__) as action:
            if isinstance(item, PlasmidItem):
                return self.validate_plasmid_item(item, action)
            elif isinstance(item, SequenceItem):
                return self.validate_sequence_item(item, action)
            else:
                action.log(message_type="unknown_item_type")
                raise DropItem(f"Unknown item type: {type(item)}")
    
    def validate_plasmid_item(self, item, action):
        """Validate plasmid item."""
        # Check required fields
        if not item.get('id') or item['id'] <= 0:
            action.log(message_type="invalid_plasmid_id", id=item.get('id'))
            raise DropItem("Invalid plasmid ID")
        
        if not item.get('name'):
            action.log(message_type="missing_plasmid_name", id=item.get('id'))
            raise DropItem("Missing plasmid name")
        
        if not item.get('depositor'):
            action.log(message_type="missing_depositor", id=item.get('id'))
            # Don't drop for missing depositor, just log
        
        # Validate URLs if present
        for url_field in ['article_url', 'map_url', 'plasmid_url']:
            url = item.get(url_field)
            if url and not self.is_valid_url(url):
                action.log(message_type="invalid_url", field=url_field, url=url)
                item[url_field] = None
        
        action.add_success_fields(plasmid_id=item['id'])
        return item
    
    def validate_sequence_item(self, item, action):
        """Validate sequence item."""
        # Check required fields
        if not item.get('plasmid_id') or item['plasmid_id'] <= 0:
            action.log(message_type="invalid_plasmid_id", id=item.get('plasmid_id'))
            raise DropItem("Invalid plasmid ID")
        
        if not item.get('format'):
            action.log(message_type="missing_format", id=item.get('plasmid_id'))
            raise DropItem("Missing sequence format")
        
        # Validate download URL if present
        download_url = item.get('download_url')
        if download_url and not self.is_valid_url(download_url):
            action.log(message_type="invalid_download_url", url=download_url)
            item['download_url'] = None
            item['available'] = False
        
        action.add_success_fields(plasmid_id=item['plasmid_id'])
        return item
    
    def is_valid_url(self, url: str) -> bool:
        """Check if URL is valid."""
        try:
            from urllib.parse import urlparse
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False 