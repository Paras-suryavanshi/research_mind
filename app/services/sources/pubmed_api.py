import requests
import xml.etree.ElementTree as ET
import urllib.parse

def query_pubmed(query, max_results=5):
    encoded_query = urllib.parse.quote(query)
    
    # Step 1: ESearch to get PMIDs
    search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pmc&term={encoded_query}&retmode=json&retmax={max_results}"
    search_res = requests.get(search_url, timeout=10)
    search_res.raise_for_status()
    search_data = search_res.json()
    
    id_list = search_data.get("esearchresult", {}).get("idlist", [])
    if not id_list:
        return []
        
    ids_str = ",".join(id_list)
    fetch_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id={ids_str}&retmode=xml"
    
    fetch_res = requests.get(fetch_url, timeout=10)
    fetch_res.raise_for_status()
    
    root = ET.fromstring(fetch_res.content)
    results = []
    
    for article in root.findall('.//article'):
        title_elem = article.find('.//article-title')
        title = "".join(title_elem.itertext()).strip() if title_elem is not None else "Unknown Title"
        
        abstract_elem = article.find('.//abstract/p')
        abstract = " ".join(abstract_elem.itertext()).strip() if abstract_elem is not None else "Abstract not available."
        
        authors = []
        for contrib in article.findall('.//contrib[@contrib-type="author"]'):
            surname = contrib.find('.//surname')
            given_names = contrib.find('.//given-names')
            if surname is not None and given_names is not None:
                given = given_names.text or ""
                family = surname.text or ""
                authors.append(f"{given} {family}".strip())
                
        pmc_id_elem = article.find('.//article-id[@pub-id-type="pmc"]')
        pmc_id = pmc_id_elem.text if pmc_id_elem is not None else ""
        year = article.findtext('.//pub-date/year')
        month = article.findtext('.//pub-date/month')
        day = article.findtext('.//pub-date/day')
        publication_date = "-".join(part for part in (year, month, day) if part) or "Unknown Date"
        
        url_link = f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/" if pmc_id else ""
        pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/pdf/" if pmc_id else ""
        
        results.append({
            "title": title,
            "authors": ", ".join(authors) if authors else "Unknown Authors",
            "abstract": abstract,
            "publication_date": publication_date,
            "source": "PubMed Central",
            "url": url_link,
            "pdf_url": pdf_url,
            "doi": None
        })
        
    return results