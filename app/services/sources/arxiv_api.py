import requests
from bs4 import BeautifulSoup
import urllib.parse

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
    
    soup = BeautifulSoup(response.content, 'xml')
    entries = soup.find_all('entry')
    
    results = []
    for entry in entries:
        title = entry.title.text.replace('\n', ' ').strip() if entry.title else "Unknown Title"
        summary = entry.summary.text.replace('\n', ' ').strip() if entry.summary else ""
        published = entry.published.text[:10] if entry.published else "Unknown Date"
        url_link = entry.id.text if entry.id else ""
        
        authors = []
        for author in entry.find_all('author'):
            name = author.find('name')
            if name is not None and name.text:
                authors.append(name.text.strip())
            
        # Find PDF link
        pdf_url = ""
        for link in entry.find_all('link'):
            if link.get('title') == 'pdf':
                pdf_url = link.get('href')
                
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