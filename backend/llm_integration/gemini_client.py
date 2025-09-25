"""
Gemini LLM client for generating trend summaries and claims
"""

import google.generativeai as genai
import logging
from typing import List, Dict, Any, Optional
import json
import re
from datetime import datetime
from config import settings

logger = logging.getLogger(__name__)

class GeminiClient:
    """Client for interacting with Google's Gemini LLM"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.mock_mode = not bool(self.api_key)
        
        if not self.mock_mode:
            # Configure Gemini
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            logger.warning("Gemini API key not provided, running in mock mode")
            self.model = None
        
        # Initialize prompt templates
        self._init_prompt_templates()
    
    def _init_prompt_templates(self):
        """Initialize prompt templates for different tasks"""
        
        self.trend_summary_template = """
You are a research assistant specializing in Brain-Computer Interface (BCI) literature. 
Analyze the provided documents and extract specific, factual claims with evidence.

Topic: {query}

Retrieved documents:
{documents}

IMPORTANT: You MUST generate at least 2-3 claims from the documents. Each claim must be:
1. A specific, factual statement about BCI research
2. Supported by direct evidence from the documents
3. Formatted exactly as shown below

Format your response EXACTLY as follows:

TREND SUMMARY:
[4-6 sentence summary of the overall trends and findings]

KEY CLAIMS:
1) [Specific claim about BCI research] [DOC#] Evidence: "[exact supporting sentence from document]" (confidence: HIGH)
2) [Another specific claim] [DOC#] Evidence: "[exact supporting sentence from document]" (confidence: HIGH)
3) [Third specific claim] [DOC#] Evidence: "[exact supporting sentence from document]" (confidence: MEDIUM)

REPRODUCIBILITY SNAPSHOT:
{{
    "query": "{query}",
    "timestamp": "{timestamp}",
    "doc_ids": {doc_ids},
    "retrieval_seed": {retrieval_seed}
}}

Remember: You MUST include the KEY CLAIMS section with at least 2-3 numbered claims, each with proper [DOC#] citations and evidence quotes.
"""
    
    def generate_trend_summary(
        self, 
        query: str, 
        documents: List[Dict[str, Any]],
        retrieval_seed: int = None
    ) -> Dict[str, Any]:
        """
        Generate trend summary and claims from retrieved documents
        
        Args:
            query: Original search query
            documents: List of retrieved documents
            retrieval_seed: Seed used for retrieval (for reproducibility)
        
        Returns:
            Dictionary with summary, claims, and metadata
        """
        try:
            if not documents:
                return self._empty_response(query)
            
            # Format documents for prompt
            formatted_docs = self._format_documents_for_prompt(documents)
            doc_ids = [doc.get('id', f"doc_{i}") for i, doc in enumerate(documents)]
            
            # Generate timestamp
            timestamp = datetime.now().isoformat()
            
            # Create prompt
            prompt = self.trend_summary_template.format(
                query=query,
                documents=formatted_docs,
                timestamp=timestamp,
                doc_ids=json.dumps(doc_ids),
                retrieval_seed=retrieval_seed or hash(query) % 10000
            )
            
            # Generate response
            logger.info(f"Generating trend summary for query: {query}")
            
            if self.mock_mode:
                response_text = self._generate_mock_response(query, documents)
            else:
                response = self.model.generate_content(prompt)
                response_text = response.text
                
                if not response_text:
                    logger.error("Empty response from Gemini")
                    return self._empty_response(query)
            
            # Parse response
            parsed_response = self._parse_trend_summary_response(response_text, query, doc_ids)
            
            # Debug logging
            logger.info(f"Raw LLM response length: {len(response_text)}")
            logger.info(f"Parsed claims count: {len(parsed_response.get('claims', []))}")
            if parsed_response.get('claims'):
                for i, claim in enumerate(parsed_response['claims']):
                    logger.info(f"Claim {i+1}: confidence_score={claim.get('confidence_score', 'N/A')}, text={claim.get('text', 'N/A')[:100]}...")
            
            logger.info(f"Generated trend summary with {len(parsed_response.get('claims', []))} claims")
            return parsed_response
            
        except Exception as e:
            logger.error(f"Error generating trend summary: {e}")
            return self._empty_response(query)
    
    def _format_documents_for_prompt(self, documents: List[Dict[str, Any]]) -> str:
        """Format documents for inclusion in prompt"""
        formatted_docs = []
        
        for i, doc in enumerate(documents, 1):
            doc_text = f"[DOC{i}] {doc.get('title', 'No title')}\n"
            doc_text += f"Authors: {', '.join(doc.get('authors', []))}\n"
            doc_text += f"Year: {doc.get('year', 'Unknown')}\n"
            doc_text += f"Abstract: {doc.get('abstract', 'No abstract')}\n"
            doc_text += f"URL: {doc.get('url', 'No URL')}\n"
            
            if doc.get('doi'):
                doc_text += f"DOI: {doc['doi']}\n"
            
            formatted_docs.append(doc_text)
        
        return "\n\n".join(formatted_docs)
    
    def _parse_trend_summary_response(
        self, 
        response_text: str, 
        query: str, 
        doc_ids: List[str]
    ) -> Dict[str, Any]:
        """Parse Gemini response into structured format"""
        try:
            # Extract trend summary
            trend_summary = self._extract_section(response_text, "TREND SUMMARY:")
            
            # Extract claims
            claims = self._extract_claims(response_text)
            
            # Extract reproducibility snapshot
            snapshot = self._extract_snapshot(response_text)
            
            return {
                'query': query,
                'trend_summary': trend_summary,
                'claims': claims,
                'reproducibility_snapshot': snapshot,
                'doc_ids': doc_ids,
                'generated_at': datetime.now().isoformat(),
                'model': 'gemini-1.5-flash'
            }
            
        except Exception as e:
            logger.error(f"Error parsing trend summary response: {e}")
            return self._empty_response(query)
    
    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract a specific section from response text"""
        try:
            # Find section start
            start_pattern = f"{section_name}\\s*"
            start_match = re.search(start_pattern, text, re.IGNORECASE)
            
            if not start_match:
                return ""
            
            start_pos = start_match.end()
            
            # Find next section or end of text
            next_section_pattern = r"\n[A-Z\s]+:"
            next_match = re.search(next_section_pattern, text[start_pos:])
            
            if next_match:
                end_pos = start_pos + next_match.start()
            else:
                end_pos = len(text)
            
            section_text = text[start_pos:end_pos].strip()
            return section_text
            
        except Exception as e:
            logger.error(f"Error extracting section {section_name}: {e}")
            return ""
    
    def _extract_claims(self, text: str) -> List[Dict[str, Any]]:
        """Extract claims from response text"""
        try:
            claims_section = self._extract_section(text, "KEY CLAIMS:")
            logger.info(f"Claims section found: {len(claims_section)} characters")
            logger.info(f"Claims section preview: {claims_section[:200]}...")
            
            if not claims_section:
                logger.warning("No KEY CLAIMS section found in response")
                return []
            
            claims = []
            claim_pattern = r"(\d+)\)\s*(.+?)\s*\[DOC(\d+)\]\s*Evidence:\s*\"([^\"]+)\"\s*\(confidence:\s*(HIGH|MEDIUM|LOW_CONFIDENCE)\)"
            
            matches = re.findall(claim_pattern, claims_section, re.DOTALL)
            logger.info(f"Found {len(matches)} claim matches")
            
            for match in matches:
                claim_num, claim_text, doc_num, evidence, confidence = match
                
                claim = {
                    'id': f"claim_{claim_num}",
                    'text': claim_text.strip(),
                    'evidence': evidence.strip(),
                    'supporting_doc': f"DOC{doc_num}",
                    'confidence': confidence.lower(),
                    'confidence_score': self._confidence_to_score(confidence)
                }
                claims.append(claim)
                logger.info(f"Extracted claim {claim_num}: confidence={confidence}, score={claim['confidence_score']}")
            
            return claims
            
        except Exception as e:
            logger.error(f"Error extracting claims: {e}")
            return []
    
    def _extract_snapshot(self, text: str) -> Dict[str, Any]:
        """Extract reproducibility snapshot from response text"""
        try:
            snapshot_section = self._extract_section(text, "REPRODUCIBILITY SNAPSHOT:")
            if not snapshot_section:
                return {}
            
            # Try to parse as JSON
            try:
                snapshot = json.loads(snapshot_section)
                return snapshot
            except json.JSONDecodeError:
                # Fallback: extract key-value pairs
                snapshot = {}
                lines = snapshot_section.split('\n')
                for line in lines:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip().strip('"')
                        value = value.strip().strip('",')
                        try:
                            snapshot[key] = json.loads(value)
                        except:
                            snapshot[key] = value
                
                return snapshot
                
        except Exception as e:
            logger.error(f"Error extracting snapshot: {e}")
            return {}
    
    def _confidence_to_score(self, confidence: str) -> float:
        """Convert confidence string to numeric score"""
        confidence_lower = confidence.lower()
        if confidence_lower == 'high':
            return 0.9
        elif confidence_lower == 'medium':
            return 0.6
        elif confidence_lower == 'low_confidence':
            return 0.3
        else:
            return 0.5
    
    def _generate_mock_response(self, query: str, documents: List[Dict[str, Any]]) -> str:
        """Generate mock response for testing"""
        return f"""
TREND SUMMARY:
Recent research in {query} shows significant advances in signal processing and classification accuracy. Multiple studies demonstrate improved performance through novel feature extraction methods and machine learning approaches.

KEY CLAIMS:
1) Advanced signal processing techniques improve classification accuracy [DOC1] Evidence: "novel feature extraction methods achieved 95% accuracy" (confidence: HIGH)
2) Machine learning approaches show promising results [DOC2] Evidence: "deep learning models outperformed traditional methods" (confidence: MEDIUM)

REPRODUCIBILITY SNAPSHOT:
{{
    "query": "{query}",
    "timestamp": "{datetime.now().isoformat()}",
    "doc_ids": {[doc.get('id', f'doc_{i}') for i, doc in enumerate(documents)]},
    "retrieval_seed": {hash(query) % 10000}
}}
"""
    
    def _empty_response(self, query: str) -> Dict[str, Any]:
        """Return empty response structure"""
        return {
            'query': query,
            'trend_summary': "No relevant documents found for this query.",
            'claims': [],
            'reproducibility_snapshot': {
                'query': query,
                'timestamp': datetime.now().isoformat(),
                'doc_ids': [],
                'retrieval_seed': hash(query) % 10000
            },
            'doc_ids': [],
            'generated_at': datetime.now().isoformat(),
            'model': 'gemini-1.5-flash'
        }
    
    def test_connection(self) -> bool:
        """Test connection to Gemini API"""
        try:
            if self.mock_mode:
                logger.info("Mock mode: Connection test successful")
                return True
                
            test_prompt = "Hello, this is a test. Please respond with 'Connection successful.'"
            response = self.model.generate_content(test_prompt)
            
            if response.text and "successful" in response.text.lower():
                logger.info("Gemini API connection test successful")
                return True
            else:
                logger.warning("Gemini API connection test failed")
                return False
                
        except Exception as e:
            logger.error(f"Gemini API connection test failed: {e}")
            return False
