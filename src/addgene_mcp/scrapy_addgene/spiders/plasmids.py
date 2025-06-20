"""Scrapy spider for scraping Addgene plasmid search results."""

import scrapy
from urllib.parse import urljoin, urlparse, parse_qs
from typing import Optional, Dict, Any, List
from eliot import start_action

from addgene_mcp.scrapy_addgene.items import PlasmidItem


class PlasmidsSpider(scrapy.Spider):
    """Spider for scraping Addgene plasmid search results and details."""
    
    name = 'plasmids'
    allowed_domains = ['addgene.org']
    start_urls = ['https://www.addgene.org/search/catalog/plasmids/']
    
    # Default settings
    custom_settings = {
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 1,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS': 8,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
        'USER_AGENT': 'addgene-mcp/0.1.0 (+https://github.com/your-repo/addgene-mcp)',
    }
    
    def __init__(self, query: Optional[str] = None, page_size: int = 50, 
                 page_number: int = 1, 
                 # Expression System Filters - "bacterial", "mammalian", "insect", "plant", "worm", "yeast"
                 expression: Optional[str] = None,
                 # Vector Type Filters - "aav", "cre_lox", "crispr", "lentiviral", "luciferase", "retroviral", "rnai", "synthetic_biology", "talen", "unspecified"
                 vector_types: Optional[str] = None,
                 # Species Filters - "arabidopsis_thaliana", "danio_rerio", "drosophila_melanogaster", "escherichia_coli", "homo_sapiens", "mus_musculus", "rattus_norvegicus", "saccharomyces_cerevisiae", "sars_cov_2", "synthetic"
                 species: Optional[str] = None,
                 # Plasmid Type Filters - "empty_backbone", "grna_shrna", "multiple_inserts", "single_insert"
                 plasmid_type: Optional[str] = None,
                 # Eukaryotic Resistance Marker Filters - "basta", "blasticidin", "his3", "hygromycin", "leu2", "neomycin", "puromycin", "trp1", "ura3", "zeocin"
                 resistance_marker: Optional[str] = None,
                 # Bacterial Resistance Filters - "ampicillin", "ampicillin_kanamycin", "zeocin", "chloramphenicol", "chloramphenicol_ampicillin", "chloramphenicol_spectinomycin", "gentamicin", "kanamycin", "spectinomycin", "tetracycline"
                 bacterial_resistance: Optional[str] = None,
                 # Popularity Filters - "low", "medium", "high"
                 popularity: Optional[str] = None,
                 results_list: Optional[List] = None,
                 **kwargs):
        """Initialize spider with search parameters."""
        super().__init__(**kwargs)
        self.query = query
        self.page_size = page_size
        self.page_number = page_number
        self.results_list = results_list
        
        # Store all filter parameters
        self.search_params = {
            'expression': expression,
            'vector_types': vector_types,
            'species': species,
            'plasmid_type': plasmid_type,
            'resistance_marker': resistance_marker,
            'bacterial_resistance': bacterial_resistance,
            'popularity': popularity,
            **kwargs
        }
        
        # Build search URL with parameters
        self.start_urls = [self.build_search_url()]
    
    def build_search_url(self) -> str:
        """Build the search URL with parameters."""
        base_url = "https://www.addgene.org/search/catalog/plasmids/"
        params = {
            'page_size': self.page_size,
            'page_number': self.page_number,
        }
        
        if self.query:
            params['q'] = self.query
        
        # Import mapping dictionaries from datatypes
        from addgene_mcp.datatypes.expression import EXPRESSION_MAP
        from addgene_mcp.datatypes.vector_type import VECTOR_TYPE_MAP
        from addgene_mcp.datatypes.species import SPECIES_MAP
        from addgene_mcp.datatypes.plasmid_type import PLASMID_TYPE_MAP
        from addgene_mcp.datatypes.resistance_marker import RESISTANCE_MARKER_MAP
        from addgene_mcp.datatypes.bacterial_resistance import BACTERIAL_RESISTANCE_MAP
        from addgene_mcp.datatypes.popularity import POPULARITY_MAP
        
        # Map filter parameters to their expected values
        filter_mappings = {
            'expression': EXPRESSION_MAP,
            'vector_types': VECTOR_TYPE_MAP,
            'species': SPECIES_MAP,
            'plasmid_type': PLASMID_TYPE_MAP,
            'resistance_marker': RESISTANCE_MARKER_MAP,
            'bacterial_resistance': BACTERIAL_RESISTANCE_MAP,
            'popularity': POPULARITY_MAP,
        }
        
        # Add additional filter parameters with proper mapping
        for key, value in self.search_params.items():
            if value is not None and key not in ['query', 'page_size', 'page_number']:
                if key in filter_mappings:
                    # Use the mapped value that Addgene expects
                    mapped_value = filter_mappings[key].get(value, value)
                    params[key] = mapped_value
                    self.logger.info(f"Mapped {key}: '{value}' -> '{mapped_value}'")
                else:
                    params[key] = value
        
        # Build URL with parameters
        from urllib.parse import urlencode
        url = f"{base_url}?{urlencode(params)}"
        self.logger.info(f"Built search URL: {url}")
        return url
    
    def parse(self, response):
        """Parse the search results page."""
        # Find all plasmid entries
        plasmid_entries = response.css('div.search-result-item')
        self.logger.info(f"Found {len(plasmid_entries)} plasmid entries")
        
        for entry in plasmid_entries:
            plasmid_item = self.parse_plasmid_entry(entry, response)
            if plasmid_item:
                if self.results_list is not None:
                    self.results_list.append(dict(plasmid_item))
                yield plasmid_item
        
        # Handle pagination
        next_page = response.css('a.next-page::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)
    
    def parse_plasmid_entry(self, entry, response) -> Optional[PlasmidItem]:
        """Parse a single plasmid entry from search results."""
        # Extract plasmid ID from div id attribute (most reliable)
        entry_id = entry.css('::attr(id)').get()
        plasmid_id = None
        if entry_id and entry_id.startswith('Plasmids-'):
            try:
                plasmid_id = int(entry_id.split('-')[1])
            except (ValueError, IndexError):
                self.logger.warning(f"Failed to extract ID from entry_id: {entry_id}")
        
        # Extract plasmid name and URL - the structure is h3 > span > a
        title_link = entry.css('h3.search-result-title span a')
        
        if not title_link:
            self.logger.warning("Missing title link in entry")
            return None
        
        plasmid_name = title_link.css('::text').get()
        plasmid_url = title_link.css('::attr(href)').get()
        
        if not plasmid_name or not plasmid_url:
            self.logger.warning(f"Missing basic info - name: {plasmid_name}, url: {plasmid_url}")
            return None
        
        from urllib.parse import urljoin
        plasmid_name = plasmid_name.strip()
        plasmid_url = urljoin(response.url, plasmid_url)
        
        # Extract plasmid popularity from flame icon
        popularity = self.extract_popularity(entry)
        
        # Extract plasmid details from rows - the structure is different
        plasmid_info = {
            "name": plasmid_name,
            "plasmid_url": plasmid_url,
            "popularity": popularity,
            "plasmid": f"#{plasmid_id}" if plasmid_id else None,
        }
        
        # Parse detail rows - updated structure based on actual HTML
        details = entry.css('div.search-result-details')
        if details:
            # Look for field-label elements and their corresponding values
            field_labels = details.css('span.field-label')
            
            for label_elem in field_labels:
                label_text = label_elem.css('::text').get()
                if label_text:
                    original_field_name = label_text.strip()
                    field_name = original_field_name.lower()
                    
                    # Find the value in the next column
                    parent_row = label_elem.xpath('../..')  # Go up to the row
                    value_column = parent_row.css('.col-xs-10, .col-md-10, .col-lg-10')
                    
                    if value_column:
                        field_value = value_column.css('::text').get()
                        if field_value:
                            field_value = field_value.strip()
                            
                            # Special handling for article links
                            if field_name == "article":
                                article_link = value_column.css('a::attr(href)').get()
                                if article_link:
                                    field_value = urljoin(response.url, article_link)
                            
                            plasmid_info[field_name] = field_value
            
            # Additional attempt to find depositor info in all text
            all_text = details.xpath('.//text()').getall()
            for i, text in enumerate(all_text):
                text = text.strip()
                if text == "Depositing Lab" and i + 1 < len(all_text):
                    depositor_name = all_text[i + 1].strip()
                    if depositor_name and depositor_name != "Depositing Lab":
                        plasmid_info["depositing lab"] = depositor_name
                        self.logger.info(f"Found depositing lab: {depositor_name}")
                        break
        
        # Extract plasmid map
        map_column = entry.css('div.map-column')
        if map_column:
            map_img = map_column.css('img::attr(src)').get()
            if map_img:
                plasmid_info["map_url"] = urljoin(response.url, map_img)
        
        # Create plasmid item
        item = self.create_plasmid_item(plasmid_info)
        return item
    
    def extract_popularity(self, entry) -> Optional[str]:
        """Extract popularity from flame icon."""
        flame_icon = entry.css('span.addgene-flame')
        if flame_icon:
            flame_classes = flame_icon.css('::attr(class)').get()
            if flame_classes:
                classes = flame_classes.split()
                for cls in classes:
                    if cls == "addgene-flame-high":
                        return "high"
                    elif cls == "addgene-flame-medium":
                        return "medium"
                    elif cls == "addgene-flame-low":
                        return "low"
        
        # If no flame icon is found, assume low popularity
        # Many plasmids don't show the icon at all, which typically means low popularity
        return "low"
    
    def create_plasmid_item(self, plasmid_info: Dict[str, Any]) -> PlasmidItem:
        """Create a PlasmidItem from extracted information."""
        # Extract plasmid ID from plasmid field
        plasmid_id_str = plasmid_info.get("plasmid", "0")
        if plasmid_id_str.startswith("#"):
            plasmid_id_str = plasmid_id_str[1:]
        
        try:
            plasmid_id = int(plasmid_id_str)
        except (ValueError, TypeError):
            plasmid_id = 0
        
        # Process expression field
        expression = plasmid_info.get("expression")
        if expression:
            expression = [e.strip().lower() for e in expression.replace(" and ", ", ").split(", ")]
        
        # Determine industry availability
        availability = plasmid_info.get("availability", "")
        is_industry = availability != "Academic Institutions and Nonprofits only"
        
        return PlasmidItem(
            id=plasmid_id,
            name=plasmid_info.get("name", ""),
            depositor=plasmid_info.get("depositing lab", plasmid_info.get("depositor", "")),
            purpose=plasmid_info.get("purpose"),
            article_url=plasmid_info.get("article"),
            insert=plasmid_info.get("insert"),
            tags=plasmid_info.get("tags"),
            mutation=plasmid_info.get("mutation"),
            plasmid_type=plasmid_info.get("type"),
            vector_type=plasmid_info.get("use"),
            popularity=plasmid_info.get("popularity"),
            expression=expression,
            promoter=plasmid_info.get("promoter"),
            map_url=plasmid_info.get("map_url"),
            services=plasmid_info.get("has service"),
            is_industry=is_industry,
            availability=availability,
            plasmid_url=plasmid_info.get("plasmid_url"),
        )

 