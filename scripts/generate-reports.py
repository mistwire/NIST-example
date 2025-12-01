#!/usr/bin/env python3
"""
Generate HTML compliance report from compliance-mapping.yml
Usage: python generate-reports.py
"""

import yaml
from datetime import datetime
from pathlib import Path

def load_mapping():
    """Load the YAML mapping file"""
    with open('compliance-mapping.yml', 'r') as f:
        return yaml.safe_load(f)

def calculate_coverage(controls):
    """Calculate coverage statistics"""
    total = len(controls)
    implemented = sum(1 for c in controls if c['status'] == 'implemented')
    in_progress = sum(1 for c in controls if c['status'] == 'in_progress')
    not_implemented = sum(1 for c in controls if c['status'] == 'not_implemented')
    
    return {
        'total': total,
        'implemented': implemented,
        'in_progress': in_progress,
        'not_implemented': not_implemented,
        'percentage': round((implemented / total) * 100, 1) if total > 0 else 0
    }

def generate_html(mapping):
    """Generate HTML report"""
    coverage = calculate_coverage(mapping['controls'])
    
    # Build HTML (using the template shown earlier)
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>MUFG NIST Compliance Report</title>
        <!-- Include the CSS from earlier -->
    </head>
    <body>
        <div class="header">
            <h1>NIST 800-53 Compliance Report</h1>
            <p>Generated: {datetime.now().strftime('%B %d, %Y')}</p>
        </div>
        
        <div class="coverage-summary">
            <div class="coverage-card">
                <h3>Total Controls</h3>
                <div class="number">{coverage['total']}</div>
            </div>
            <!-- More cards -->
        </div>
        
        <!-- Generate control sections -->
        {generate_control_sections(mapping['controls'])}
    </body>
    </html>
    """
    
    # Write to file
    output_path = Path('reports/compliance-report.html')
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(html)
    
    print(f"✓ Report generated: {output_path}")
    print(f"  Coverage: {coverage['percentage']}% ({coverage['implemented']}/{coverage['total']})")

if __name__ == '__main__':
    mapping = load_mapping()
    generate_html(mapping)