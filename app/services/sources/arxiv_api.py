import requests
import urllib.parse
import xml.etree.ElementTree as ET

def query_arxiv(query, max_results=5):
    title_query = query.strip()
    for suffix in (' paper', ' article', ' publication'):
        if title_query.lower().endswith(suffix):
            title_query = title_query[:-len(suffix)].strip()
            break
    if title_query:
        search_query = f'ti:"{title_query}" OR all:"{query}"'
    else:
        search_query = f'all:"{query}"'
    encoded_query = urllib.parse.quote(search_query)
    url = f'https://export.arxiv.org/api/query?search_query={encoded_query}&start=0&max_results={max_results}&sortBy=relevance'
    
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    
    root = ET.fromstring(response.content)
    entries = root.findall('{http://www.w3.org/2005/Atom}entry')
    
    results = []
    for entry in entries:
        title_node = entry.find('{http://www.w3.org/2005/Atom}title')
        summary_node = entry.find('{http://www.w3.org/2005/Atom}summary')
        published_node = entry.find('{http://www.w3.org/2005/Atom}published')
        id_node = entry.find('{http://www.w3.org/2005/Atom}id')
        title = ' '.join((title_node.text or '').split()) if title_node is not None else "Unknown Title"
        summary = ' '.join((summary_node.text or '').split()) if summary_node is not None else ""
        published = (published_node.text or '')[:10] if published_node is not None else "Unknown Date"
        url_link = id_node.text.strip() if id_node is not None and id_node.text else ""
        
        authors = []
        for author in entry.findall('{http://www.w3.org/2005/Atom}author'):
            name = author.find('{http://www.w3.org/2005/Atom}name')
            if name is not None and name.text:
                authors.append(name.text.strip())
            
        # Find PDF link
        pdf_url = ""
        for link in entry.findall('{http://www.w3.org/2005/Atom}link'):
            if link.get('title') == 'pdf':
                pdf_url = link.get('href', '')
                
        results.append({
            "title": title,
            "authors": ", ".join(authors),
            "abstract": summary,
            "publication_date": published,
            "source": "arXiv",
            "url": url_link,
            "pdf_url": pdf_url,
            "doi": None
        })
        
    return results