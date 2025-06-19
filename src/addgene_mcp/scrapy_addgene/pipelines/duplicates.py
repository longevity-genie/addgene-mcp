"""Duplicates filter pipeline for Scrapy items."""

from scrapy.exceptions import DropItem
from eliot import start_action
from addgene_mcp.scrapy_addgene.items import PlasmidItem, SequenceItem


class DuplicatesPipeline:
    """Pipeline to filter duplicate items."""
    
    def __init__(self):
        self.ids_seen = set()
        self.sequence_keys_seen = set()
    
    def process_item(self, item, spider):
        """Filter duplicate items."""
        with start_action(action_type="check_duplicates", item_type=type(item).__name__) as action:
            if isinstance(item, PlasmidItem):
                return self.check_plasmid_duplicate(item, action)
            elif isinstance(item, SequenceItem):
                return self.check_sequence_duplicate(item, action)
            else:
                action.log(message_type="unknown_item_type")
                return item
    
    def check_plasmid_duplicate(self, item, action):
        """Check for duplicate plasmid items."""
        plasmid_id = item.get('id')
        
        if plasmid_id in self.ids_seen:
            action.log(message_type="duplicate_plasmid", id=plasmid_id)
            raise DropItem(f"Duplicate plasmid: {plasmid_id}")
        else:
            self.ids_seen.add(plasmid_id)
            action.add_success_fields(plasmid_id=plasmid_id, unique=True)
            return item
    
    def check_sequence_duplicate(self, item, action):
        """Check for duplicate sequence items."""
        plasmid_id = item.get('plasmid_id')
        format_type = item.get('format')
        sequence_key = (plasmid_id, format_type)
        
        if sequence_key in self.sequence_keys_seen:
            action.log(message_type="duplicate_sequence", plasmid_id=plasmid_id, format=format_type)
            raise DropItem(f"Duplicate sequence: {plasmid_id}/{format_type}")
        else:
            self.sequence_keys_seen.add(sequence_key)
            action.add_success_fields(plasmid_id=plasmid_id, format=format_type, unique=True)
            return item 