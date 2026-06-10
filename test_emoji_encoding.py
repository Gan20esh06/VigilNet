#!/usr/bin/env python3
"""Test UTF-8 encoding with emoji characters for report generation."""

import tempfile
import json

# Simple test of UTF-8 file writing with emoji
test_data = {
    'title': 'VigilNet Report 📋',
    'events': ['📱 Phone detected 🔴', '👀 Looking away ⚠️'],
    'status': '✅ Complete'
}

try:
    with tempfile.TemporaryDirectory() as tmpdir:
        # Test JSON
        json_file = f'{tmpdir}/test.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2)
        print(f"✅ JSON with emoji: {test_data['title']} - SUCCESS")
        
        # Test HTML
        html_file = f'{tmpdir}/test.html'
        html = f"""<html><body>
        <h1>{test_data['title']}</h1>
        <p>Status: {test_data['status']}</p>
        </body></html>"""
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html)
        print("✅ HTML with emoji: SUCCESS")
        
        # Test CSV
        csv_file = f'{tmpdir}/test.csv'
        csv_content = 'event,description\n'
        for event in test_data['events']:
            csv_content += f'violation,{event}\n'
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        print("✅ CSV with emoji: SUCCESS")
        
        print('\n✅ All report formats support emoji characters!')
except UnicodeEncodeError as e:
    print(f'❌ UnicodeEncodeError: {e}')
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
