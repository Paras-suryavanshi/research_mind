import logging
from flask import current_app
from app.services.groq_service import GroqService
from app.services.sources.arxiv_api import query_arxiv
from app.services.sources.pubmed_api import query_pubmed
from app.services.sources.crossref_api import query_crossref
from app.services.sources.core_api import query_core

logger = logging.getLogger(__name__)

class ResearchSelector:
    
    @classmethod
    def determine_source(cls, query):
        """
        Uses heuristic keyword matching to route to the fastest, most relevant source.
        Falls back to Groq for classification if ambiguous.
        """
        query_lower = query.lower()
        
        # Medical / Biomedical -> PubMed
        medical_keywords = ['health', 'medicine', 'clinical', 'disease', 'patient', 'therapy', 'virus', 'biology', 'cancer', 'syndrome', 'drug']
        if any(kw in query_lower for kw in medical_keywords):
            return 'pubmed'
            
        # Physics / Math / CS / AI -> arXiv
        arxiv_keywords = ['quantum', 'machine learning', 'artificial intelligence', 'algorithm', 'physics', 'mathematics', 'neural network', 'deep learning', 'transformer', 'llm', 'computer vision', 'attention is all you need', 'attention layer']
        if any(kw in query_lower for kw in arxiv_keywords):
            return 'arxiv'
            
        # Broad / General Metadata -> Crossref
        crossref_keywords = ['history', 'sociology', 'economics', 'literature', 'business', 'management', 'review of', 'journal of']
        if any(kw in query_lower for kw in crossref_keywords):
            return 'crossref'
            
        # Default to CORE for broad open-access repository search
        return 'core'

    @classmethod
    def execute_search(cls, query, max_results=5):
        source = cls.determine_source(query)
        results = []
        current_app.logger.info(
            "Fetching up to %s papers from %s for query: %s",
            max_results,
            source,
            query,
        )
        
        try:
            if source == 'arxiv':
                results = query_arxiv(query, max_results)
            elif source == 'pubmed':
                results = query_pubmed(query, max_results)
            elif source == 'crossref':
                results = query_crossref(query, max_results)
            elif source == 'core':
                results = query_core(query, max_results)
                # Fallback if CORE fails (e.g., missing API key)
                if not results:
                    current_app.logger.info("No papers returned by CORE; falling back to Crossref")
                    results = query_crossref(query, max_results)
                    source = 'crossref'
        except Exception as e:
            logger.error(f"Error querying {source}: {str(e)}")
            # Ultimate fallback to Crossref which is highly stable and requires no API key
            try:
                results = query_crossref(query, max_results)
                source = 'crossref'
            except Exception as fallback_error:
                logger.error("Crossref fallback failed: %s", fallback_error)
                results = []

        results = cls._rank_results(query, results)
        current_app.logger.info("Fetched %s papers from %s", len(results), source)
            
        return {
            "source": source,
            "papers": results
        }

    @staticmethod
    def _rank_results(query, results):
        """Keep exact-title and topic matches ahead of broad provider ranking."""
        query_terms = {
            term for term in query.lower().replace('"', '').split()
            if len(term) > 2 and term not in {'paper', 'article', 'about', 'what', 'latest'}
        }
        if not query_terms:
            return results

        def score(paper):
            title = str(paper.get('title', '')).lower()
            abstract = str(paper.get('abstract', '')).lower()
            title_score = sum(term in title for term in query_terms) * 5
            abstract_score = sum(term in abstract for term in query_terms)
            exact_title = query.lower().replace(' paper', '').strip() in title
            return title_score + abstract_score + (100 if exact_title else 0)

        return sorted(results, key=score, reverse=True)