"""
DOM-level change highlighting
Compares HTML structure and highlights changed elements
"""

from bs4 import BeautifulSoup
import difflib
from collections import defaultdict


def extract_dom_structure(html_content):
    """
    Extract DOM structure with text content
    Returns list of elements with their paths and content
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove script and style tags
    for tag in soup(['script', 'style', 'noscript']):
        tag.decompose()
    
    elements = []
    
    def get_element_path(element):
        """Get CSS-like path for element"""
        path = []
        current = element
        
        while current and current.name:
            selector = current.name
            
            # Add ID if present
            if current.get('id'):
                selector += f"#{current['id']}"
            
            # Add first class if present
            if current.get('class'):
                selector += f".{current['class'][0]}"
            
            path.insert(0, selector)
            current = current.parent
        
        return ' > '.join(path)
    
    def extract_elements(element, depth=0):
        """Recursively extract elements"""
        if depth > 10:  # Limit depth
            return
        
        if element.name:
            # Get text content (direct children only)
            text = element.get_text(separator=' ', strip=True)
            
            if text and len(text) > 10:  # Only meaningful text
                elements.append({
                    'path': get_element_path(element),
                    'tag': element.name,
                    'text': text[:200],  # Limit text length
                    'attributes': dict(element.attrs) if element.attrs else {}
                })
        
        # Process children
        if hasattr(element, 'children'):
            for child in element.children:
                if hasattr(child, 'name'):
                    extract_elements(child, depth + 1)
    
    extract_elements(soup.body if soup.body else soup)
    
    return elements


def compare_dom_structures(old_html, new_html):
    """
    Compare two HTML documents at DOM level
    Returns dict with added, removed, and modified elements
    """
    old_elements = extract_dom_structure(old_html)
    new_elements = extract_dom_structure(new_html)
    
    # Create path-based lookup
    old_dict = {elem['path']: elem for elem in old_elements}
    new_dict = {elem['path']: elem for elem in new_elements}
    
    old_paths = set(old_dict.keys())
    new_paths = set(new_dict.keys())
    
    changes = {
        'added': [],
        'removed': [],
        'modified': []
    }
    
    # Find added elements
    for path in new_paths - old_paths:
        changes['added'].append({
            'path': path,
            'tag': new_dict[path]['tag'],
            'text': new_dict[path]['text']
        })
    
    # Find removed elements
    for path in old_paths - new_paths:
        changes['removed'].append({
            'path': path,
            'tag': old_dict[path]['tag'],
            'text': old_dict[path]['text']
        })
    
    # Find modified elements
    for path in old_paths & new_paths:
        old_elem = old_dict[path]
        new_elem = new_dict[path]
        
        # Compare text content
        if old_elem['text'] != new_elem['text']:
            similarity = difflib.SequenceMatcher(
                None, 
                old_elem['text'], 
                new_elem['text']
            ).ratio()
            
            changes['modified'].append({
                'path': path,
                'tag': new_elem['tag'],
                'old_text': old_elem['text'],
                'new_text': new_elem['text'],
                'similarity': similarity
            })
    
    return changes


def generate_dom_diff_html(changes):
    """
    Generate HTML visualization of DOM changes
    """
    html = """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; }
            h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
            h2 { color: #3498db; margin-top: 30px; }
            .change-item { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid; }
            .change-item.added { border-left-color: #27ae60; }
            .change-item.removed { border-left-color: #e74c3c; }
            .change-item.modified { border-left-color: #f39c12; }
            .path { font-family: monospace; color: #7f8c8d; font-size: 12px; }
            .tag { background: #ecf0f1; padding: 2px 6px; border-radius: 3px; font-family: monospace; }
            .text { margin-top: 8px; color: #2c3e50; }
            .old-text { background: #ffebee; padding: 5px; border-radius: 3px; }
            .new-text { background: #e8f5e9; padding: 5px; border-radius: 3px; }
            .badge { display: inline-block; padding: 4px 10px; border-radius: 3px; font-size: 11px; font-weight: bold; }
            .badge.added { background: #d4edda; color: #155724; }
            .badge.removed { background: #f8d7da; color: #721c24; }
            .badge.modified { background: #fff3cd; color: #856404; }
            .stats { display: flex; gap: 20px; margin: 20px 0; }
            .stat { background: #ecf0f1; padding: 15px; border-radius: 5px; text-align: center; }
            .stat-number { font-size: 32px; font-weight: bold; color: #3498db; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔍 DOM-Level Change Analysis</h1>
            
            <div class="stats">
                <div class="stat">
                    <div class="stat-number">{added_count}</div>
                    <div>Added Elements</div>
                </div>
                <div class="stat">
                    <div class="stat-number">{removed_count}</div>
                    <div>Removed Elements</div>
                </div>
                <div class="stat">
                    <div class="stat-number">{modified_count}</div>
                    <div>Modified Elements</div>
                </div>
            </div>
    """.format(
        added_count=len(changes['added']),
        removed_count=len(changes['removed']),
        modified_count=len(changes['modified'])
    )
    
    # Added elements
    if changes['added']:
        html += "<h2>✅ Added Elements</h2>"
        for item in changes['added'][:20]:  # Limit to 20
            html += f"""
            <div class="change-item added">
                <span class="badge added">ADDED</span>
                <span class="tag">&lt;{item['tag']}&gt;</span>
                <div class="path">{item['path']}</div>
                <div class="text">{item['text']}</div>
            </div>
            """
    
    # Removed elements
    if changes['removed']:
        html += "<h2>❌ Removed Elements</h2>"
        for item in changes['removed'][:20]:
            html += f"""
            <div class="change-item removed">
                <span class="badge removed">REMOVED</span>
                <span class="tag">&lt;{item['tag']}&gt;</span>
                <div class="path">{item['path']}</div>
                <div class="text">{item['text']}</div>
            </div>
            """
    
    # Modified elements
    if changes['modified']:
        html += "<h2>🔄 Modified Elements</h2>"
        for item in changes['modified'][:20]:
            html += f"""
            <div class="change-item modified">
                <span class="badge modified">MODIFIED</span>
                <span class="tag">&lt;{item['tag']}&gt;</span>
                <small>(Similarity: {item['similarity']*100:.1f}%)</small>
                <div class="path">{item['path']}</div>
                <div class="text">
                    <strong>Before:</strong>
                    <div class="old-text">{item['old_text']}</div>
                    <strong>After:</strong>
                    <div class="new-text">{item['new_text']}</div>
                </div>
            </div>
            """
    
    html += """
        </div>
    </body>
    </html>
    """
    
    return html
