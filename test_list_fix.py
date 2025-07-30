#!/usr/bin/env python3
"""
Simple test to demonstrate the list formatting fix.
"""

import re

from src.ui.markdown_formatter import get_markdown_formatter


def extract_html_content(styled_html):
    """Extract just the HTML content without CSS styling."""
    match = re.search(r'<div>(.*?)</div>', styled_html, re.DOTALL)
    return match.group(1) if match else styled_html

def test_list_formatting():
    """Test that nested lists are formatted correctly."""

    # Original problem case
    test_markdown = '''### Random Dinner Shopping List

1. **Proteins**
   - Chicken breasts
   - Salmon fillets
   - Tofu (for a vegetarian option)

2. **Vegetables**
   - Bell peppers
   - Onions
'''

    formatter = get_markdown_formatter()
    result = formatter.format_message(test_markdown)
    html_content = extract_html_content(result)
    
    print("=== FORMATTED HTML ===")
    print(html_content)
    print("\n=== ANALYSIS ===")
    
    # Check for proper nesting
    if '<ol>' in html_content and '<ul>' in html_content:
        print("✅ Contains both ordered and unordered lists")
    else:
        print("❌ Missing proper list types")
    
    if '<li><strong>Proteins</strong></li>' not in html_content:
        print("✅ Proteins is NOT a separate list item (good!)")
    else:
        print("❌ Proteins is still showing as a separate list item")
    
    if 'Chicken breasts</li>' in html_content and 'Salmon fillets</li>' in html_content:
        print("✅ Sub-items are properly nested as list items")
    else:
        print("❌ Sub-items are not properly nested")
    
    # Test deep nesting
    deep_test = '''1. **Main**
   - Sub 1
     - Deep 1
     - Deep 2
   - Sub 2
'''
    
    deep_result = formatter.format_message(deep_test)
    deep_html = extract_html_content(deep_result)
    
    print("\n=== DEEP NESTING TEST ===")
    print(deep_html)
    
    if deep_html.count('<ul>') >= 2:
        print("✅ Deep nesting creates multiple nested <ul> elements")
    else:
        print("❌ Deep nesting not working properly")

if __name__ == "__main__":
    test_list_formatting()
