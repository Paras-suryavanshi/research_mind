import os
import urllib.parse

import requests


def query_core(query, max_results=5):
    api_key = os.environ.get('CORE_API_KEY')
    if not api_key:
        return []

    encoded_query = urllib.parse.quote(query)
    url = f"https://api.core.ac.uk/v3/search/works?q={encoded_query}&limit={max_results}"
    headers = {
        'Authorization': 'Bearer ' + api_key,
        'Accept': 'application/json',
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        items = response.json().get('results', [])
        results = []
        for item in items:
            authors = ", ".join(
                author.get('name', '') for author in item.get('authors', [])
            )
            publication_date = item.get('publishedDate', 'Unknown Date')
            if publication_date:
                publication_date = publication_date[:10]
            source_urls = item.get('sourceFulltextUrls') or ['']
            results.append({
                'title': item.get('title', 'Unknown Title'),
                'authors': authors or 'Unknown Authors',
                'abstract': item.get('abstract', 'Abstract not available.'),
                'publication_date': publication_date,
                'source': 'CORE',
                'url': source_urls[0],
                'pdf_url': item.get('downloadUrl', ''),
                'doi': item.get('doi', ''),
            })
        return results
    except requests.RequestException:
        return []
