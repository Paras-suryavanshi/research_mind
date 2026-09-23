import requests
import urllib.parse

def query_crossref(query, max_results=5):
    encoded_query = urllib.parse.quote(query)
    url = f"https://api.crossref.org/works?query={encoded_query}&select=title,author,abstract,URL,DOI,issued,link&rows={max_results}"
    
    headers = {
        'User-Agent': 'ResearchMind/1.0 (mailto:admin@researchmind.com)'
    }
    
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    items = data.get('message', {}).get('items', [])
    results = []
    
    for item in items:
        title = item.get('title', ['Unknown Title'])[0]
        
        authors_list = item.get('author', [])
        authors = ", ".join([f"{a.get('given', '')} {a.get('family', '')}".strip() for a in authors_list])
        
        abstract = item.get('abstract', 'Abstract not available.')
        if abstract:
            abstract = abstract.replace('<jats:p>', '').replace('</jats:p>', '')
        
        date_parts = item.get('issued', {}).get('date-parts', [[None]])[0]
        pub_date = str(date_parts[0]) if date_parts[0] else "Unknown Date"
        
        doi = item.get('DOI', '')
        url_link = item.get('URL', '')
        
        # Crossref links array sometimes contains text-mining PDF links
        pdf_url = ""
        for link in item.get('link', []):
            if link.get('content-type') == 'application/pdf':
                pdf_url = link.get('URL')
                break
                
        results.append({
            "title": title,
            "authors": authors if authors else "Unknown Authors",
            "abstract": abstract,
            "publication_date": pub_date,
            "source": "Crossref",
            "url": url_link,
            "pdf_url": pdf_url,
            "doi": doi
        })
        
    return results