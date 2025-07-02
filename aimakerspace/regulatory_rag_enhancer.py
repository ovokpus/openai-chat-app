"""
Regulatory RAG Enhancer

This module extends the existing RAG pipeline with regulatory reporting capabilities
while preserving all original functionality. It provides:
- Role-based guidance for banking professionals
- Regulatory domain expertise for Basel III, COREP, FINREP
- Enhanced citation with precise source locations
- Regulatory-specific prompts and formatting

The original RAG pipeline remains completely unchanged.
"""

import logging
from typing import List, Dict, Any, Optional
from .rag_pipeline import RAGPipeline
from .openai_utils.prompts import SystemRolePrompt, UserRolePrompt


class RegulatoryRAGEnhancer:
    """
    Enhancer for the RAG pipeline that adds regulatory reporting capabilities.
    
    This class wraps the existing RAG pipeline and adds regulatory-specific
    features without modifying the original implementation.
    """
    
    def __init__(self, base_rag_pipeline: RAGPipeline):
        """
        Initialize the regulatory enhancer.
        
        Args:
            base_rag_pipeline: The existing RAG pipeline to enhance
        """
        self.base_rag = base_rag_pipeline
        self.regulatory_roles = {
            "analyst": "Regulatory Analyst",
            "data_engineer": "Data Engineer", 
            "programme_manager": "Programme Manager",
            "general": "General User"
        }
        
        # Regulatory domain expertise
        self.regulatory_frameworks = {
            "basel_iii": "Basel III Capital Requirements",
            "corep": "Common Reporting (COREP)",
            "finrep": "Financial Reporting (FINREP)",
            "ifrs": "International Financial Reporting Standards",
            "crd_iv": "Capital Requirements Directive IV",
            "crr": "Capital Requirements Regulation"
        }
    
    def get_regulatory_system_prompt(self, user_role: str = "general") -> SystemRolePrompt:
        """
        Create a regulatory-specific system prompt based on user role.
        
        Args:
            user_role: The role of the user (analyst, data_engineer, programme_manager, general)
            
        Returns:
            Enhanced system prompt with regulatory context
        """
        role_guidance = self._get_role_specific_guidance(user_role)
        
        regulatory_prompt = f"""You are a specialized Regulatory Reporting Copilot for banking institutions, designed to create beautifully formatted, professional regulatory guidance.

            🏦 **REGULATORY DOMAIN EXPERTISE:**
            You have deep knowledge of:
            • **Basel III** Capital Requirements and liquidity frameworks
            • **COREP** (Common Reporting) templates and calculations  
            • **FINREP** (Financial Reporting) under IFRS/national GAAP
            • **EBA Guidelines** and technical standards
            • **CRD IV/CRR** regulatory frameworks
            • **Data lineage** and regulatory calculations

            👤 **USER ROLE GUIDANCE:**
            {role_guidance}

            📋 **PROFESSIONAL FORMATTING REQUIREMENTS:**

            **STRUCTURE & HIERARCHY:**
            - Start with # main title for the regulatory topic
            - Use ## for major regulatory sections (e.g., ## Capital Requirements)
            - Use ### for specific subsections (e.g., ### CET1 Calculation)
            - Create logical regulatory information flow

            **REGULATORY TEXT FORMATTING:**
            - **Bold** for regulatory terms, framework names, and key requirements
            - *Italics* for definitions, regulatory guidance, or interpretations  
            - `Code formatting` for specific calculations, cell references, or data fields
            - > Use blockquotes for regulatory warnings or critical compliance notes

            **REGULATORY LISTS & ORGANIZATION:**
            - Use numbered lists for sequential regulatory processes or calculation steps
            - Use bullet points (•) for regulatory requirements or framework components
            - Create sub-bullets for detailed regulatory guidance
            - Add spacing between regulatory sections for clarity

                         **MATHEMATICAL & CALCULATION FORMATTING:**
             - Display regulatory formulas prominently using LaTeX math notation
             - Use inline math for simple ratios and calculations
             - Format regulatory thresholds clearly: **Minimum CET1 Ratio: 4.5%**

            **VISUAL REGULATORY ENHANCEMENTS:**
            - Use regulatory emojis effectively: 📊 (data/reporting), ⚖️ (compliance), 📈 (capital), 💧 (liquidity), ⚠️ (warnings)
            - Create tables for regulatory requirements, thresholds, or comparisons
            - Use horizontal rules (---) to separate major regulatory sections
            - Add proper spacing for professional presentation

            **PRECISE CITATION REQUIREMENTS:**
            Always include specific source references:
            - **PDF Documents**: `📄 Source: [filename], Page X`
            - **Excel Templates**: `📊 Source: [filename], Sheet '[sheet_name]', Cell/Range`  
            - **PowerPoint**: `📋 Source: [filename], Slide X`
            - **Code Files**: `💻 Source: [filename], Lines X-Y`

            **🎯 REGULATORY FOCUS AREAS:**
            
            ## 📈 **Capital Adequacy**
            - Common Equity Tier 1 (CET1), Tier 1, Total Capital ratios
            - Capital conservation and countercyclical buffers
            - Systemically important institution surcharges

            ## 💧 **Liquidity Management**  
            - Liquidity Coverage Ratio (LCR)
            - Net Stable Funding Ratio (NSFR)
            - Liquidity risk monitoring tools

            ## ⚖️ **Risk Calculations**
            - Credit risk (Standardised and IRB approaches)
            - Market risk (Standardised and internal models)
            - Operational risk calculations
            - Counterparty credit risk

            ## 📊 **Data & Reporting**
            - Data quality and lineage validation
            - Regulatory change impact assessment
            - Template completion guidance

            **⚠️ COMPLIANCE NOTE:** If the provided context doesn't contain sufficient regulatory information, clearly state this and suggest specific additional documentation needed.

            Context will be provided below marked with [Source: filename] followed by the content."""

        return SystemRolePrompt(regulatory_prompt)
    
    def _get_role_specific_guidance(self, user_role: str) -> str:
        """Get role-specific guidance for different banking professionals"""
        guidance_map = {
            "analyst": """
            **As a Regulatory Analyst, you need:**
            - Detailed explanations of regulatory calculations and methodologies
            - Step-by-step breakdowns of complex reporting requirements
            - Identification of data sources and dependencies
            - Impact analysis for regulatory changes
            - Validation of regulatory interpretations
            Focus on accuracy, compliance implications, and detailed technical guidance.
                        """.strip(),
                        
                        "data_engineer": """
            **As a Data Engineer, you need:**
            - Technical implementation details and data lineage
            - Database schema and data transformation requirements
            - Calculation logic and business rules
            - Data quality checks and validation procedures
            - ETL process design for regulatory reporting
            Focus on technical implementation, data architecture, and system integration.
                        """.strip(),
                        
                        "programme_manager": """
            **As a Programme Manager, you need:**
            - High-level project impact and scope assessment
            - Resource requirements and timeline considerations
            - Cross-functional dependencies and coordination points
            - Risk assessment and mitigation strategies
            - Business case justification and benefits
            Focus on project delivery, stakeholder management, and strategic alignment.
                        """.strip(),
                        
                        "general": """
            **As a General User, you need:**
            - Clear, accessible explanations of regulatory concepts
            - Practical guidance for day-to-day regulatory tasks
            - Understanding of compliance requirements and deadlines
            - Overview of regulatory frameworks and their relationships
            Focus on clarity, practical application, and comprehensive understanding.
                        """.strip()
                    }
        
        return guidance_map.get(user_role, guidance_map["general"])
    
    def enhanced_search(
        self, 
        query: str, 
        k: int = 4,
        doc_types: Optional[List[str]] = None,
        priority_sources: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Enhanced search with regulatory-specific filtering and prioritization.
        
        Args:
            query: The search query
            k: Number of results to return
            doc_types: Filter by document types (pdf, excel, powerpoint, etc.)
            priority_sources: Prioritize specific source files
            
        Returns:
            Enhanced search results with regulatory context
        """
        # Use the base RAG pipeline's search functionality
        base_results = self.base_rag.search_documents(query, k=k * 2)  # Get more results for filtering
        
        # Apply regulatory enhancements
        enhanced_results = []
        for result in base_results:
            enhanced_result = result.copy()
            
            # Add regulatory context scoring
            reg_score = self._calculate_regulatory_relevance(result, query)
            enhanced_result["regulatory_score"] = reg_score
            
            # Apply document type filtering
            if doc_types:
                doc_type = result.get("metadata", {}).get("doc_type", "unknown")
                if doc_type not in doc_types:
                    continue
            
            # Apply priority source boost
            if priority_sources:
                filename = result.get("metadata", {}).get("filename", "")
                if any(priority in filename.lower() for priority in priority_sources):
                    enhanced_result["score"] = enhanced_result.get("score", 0) * 1.5
            
            enhanced_results.append(enhanced_result)
        
        # Sort by combined relevance and regulatory score
        enhanced_results.sort(
            key=lambda x: (x.get("score", 0) * 0.7 + x.get("regulatory_score", 0) * 0.3),
            reverse=True
        )
        
        return enhanced_results[:k]
    
    def _calculate_regulatory_relevance(self, result: Dict[str, Any], query: str) -> float:
        """Calculate regulatory relevance score for search results"""
        score = 0.0
        
        content = result.get("text", "").lower()
        metadata = result.get("metadata", {})
        query_lower = query.lower()
        
        # Boost for regulatory keywords in content
        regulatory_keywords = [
            "basel", "corep", "finrep", "capital", "liquidity", "lcr", "nsfr",
            "cet1", "tier 1", "total capital", "risk weight", "exposure",
            "regulatory", "compliance", "reporting", "calculation", "template"
        ]
        
        for keyword in regulatory_keywords:
            if keyword in content:
                score += 0.1
            if keyword in query_lower:
                score += 0.2
        
        # Boost for specific regulatory document types
        doc_type = metadata.get("doc_type", "")
        regulatory_type = metadata.get("regulatory_type", "")
        
        if regulatory_type in ["corep_template", "finrep_template", "basel_document"]:
            score += 0.3
        elif regulatory_type in ["regulatory_calculation", "data_lineage"]:
            score += 0.2
        
        # Boost for Excel sheets with regulatory naming
        if doc_type == "excel":
            sheet_name = metadata.get("sheet_name", "").lower()
            if any(term in sheet_name for term in ["corep", "finrep", "capital", "liquidity"]):
                score += 0.2
        
        return min(score, 1.0)  # Cap at 1.0
    
    def enhanced_format_context(
        self, 
        search_results: List[Dict[str, Any]],
        user_role: str = "general"
    ) -> tuple[str, str]:
        """
        Enhanced context formatting with regulatory-specific structure.
        
        Args:
            search_results: Search results to format
            user_role: User role for context customization
            
        Returns:
            Tuple of (formatted_context, metadata_info)
        """
        if not search_results:
            return "", ""
        
        context_parts = []
        metadata_parts = []
        
        # Group results by document type for better organization
        grouped_results = self._group_by_document_type(search_results)
        
        for doc_type, results in grouped_results.items():
            if not results:
                continue
                
            context_parts.append(f"## {doc_type.upper()} DOCUMENTS")
            
            for i, result in enumerate(results):
                content = result.get("text", "").strip()
                metadata = result.get("metadata", {})
                score = result.get("score", 0.0)
                reg_score = result.get("regulatory_score", 0.0)
                
                if content:
                    # Enhanced source citation with precise location
                    citation = self._create_enhanced_citation(metadata)
                    context_parts.append(f"[{citation}]\n{content}")
                    
                    # Collect enhanced metadata
                    metadata_info = f"{citation}, Relevance: {score:.3f}, Regulatory: {reg_score:.3f}"
                    metadata_parts.append(metadata_info)
            
            context_parts.append("")  # Add spacing between document types
        
        formatted_context = "\n\n---\n\n".join(context_parts)
        metadata_info = " | ".join(metadata_parts)
        
        return formatted_context, metadata_info
    
    def _group_by_document_type(self, results: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group search results by document type"""
        grouped = {}
        
        for result in results:
            doc_type = result.get("metadata", {}).get("doc_type", "unknown")
            if doc_type not in grouped:
                grouped[doc_type] = []
            grouped[doc_type].append(result)
        
        return grouped
    
    def _create_enhanced_citation(self, metadata: Dict[str, Any]) -> str:
        """Create enhanced citation with precise source location"""
        filename = metadata.get("filename", "Unknown")
        doc_type = metadata.get("doc_type", "")
        
        if doc_type == "pdf":
            page_num = metadata.get("page_number", 1)
            return f"Source: {filename}, Page {page_num}"
        elif doc_type == "excel":
            sheet_name = metadata.get("sheet_name", "Unknown")
            max_row = metadata.get("max_row", "")
            max_col = metadata.get("max_column", "")
            # Avoid template syntax issues by only including range info if both values are valid
            if max_row and max_col and max_row != "0" and max_col != "0":
                range_info = f" (Rows: 1-{max_row}, Cols: A-{max_col})"
            else:
                range_info = ""
            return f"Source: {filename}, Sheet '{sheet_name}'{range_info}"
        elif doc_type == "powerpoint":
            slide_num = metadata.get("slide_number", 1)
            return f"Source: {filename}, Slide {slide_num}"
        elif doc_type == "code":
            language = metadata.get("language", "")
            line_count = metadata.get("line_count", "")
            lang_info = f" ({language})" if language else ""
            line_info = f", {line_count} lines" if line_count else ""
            return f"Source: {filename}{lang_info}{line_info}"
        else:
            return f"Source: {filename}"
    
    def run_enhanced_rag(
        self,
        query: str,
        user_role: str = "general",
        k: int = 4,
        doc_types: Optional[List[str]] = None,
        priority_sources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Run the enhanced RAG pipeline with regulatory features.
        
        Args:
            query: User's question
            user_role: User's role for customized responses
            k: Number of documents to retrieve
            doc_types: Filter by document types
            priority_sources: Prioritize specific sources
            
        Returns:
            Enhanced RAG response with regulatory context
        """
        try:
            # Enhanced search with regulatory filtering
            search_results = self.enhanced_search(
                query=query,
                k=k,
                doc_types=doc_types,
                priority_sources=priority_sources
            )
            
            if not search_results:
                return {
                    "response": "I couldn't find relevant regulatory documents to answer your question. Please ensure you have uploaded the appropriate regulatory templates, frameworks, or documentation.",
                    "sources": [],
                    "metadata": "No relevant documents found"
                }
            
            # Enhanced context formatting
            context, metadata_info = self.enhanced_format_context(search_results, user_role)
            
            # Generate response with regulatory system prompt
            regulatory_system_prompt = self.get_regulatory_system_prompt(user_role)
            
            user_prompt_text = f"""Question: {query}

Regulatory Context:
{context}

Please provide a comprehensive answer based on the regulatory documentation provided above. Focus on accuracy, compliance implications, and precise citations."""

            user_prompt = UserRolePrompt(user_prompt_text)
            
            # Use the base RAG's LLM with enhanced prompts
            messages = [regulatory_system_prompt, user_prompt]
            response = self.base_rag.llm.run(messages)
            
            # Extract source information for tracking
            sources = []
            for result in search_results:
                metadata = result.get("metadata", {})
                sources.append({
                    "filename": metadata.get("filename", "Unknown"),
                    "doc_type": metadata.get("doc_type", "unknown"),
                    "regulatory_type": metadata.get("regulatory_type", ""),
                    "source_location": self._create_enhanced_citation(metadata),
                    "relevance_score": result.get("score", 0.0),
                    "regulatory_score": result.get("regulatory_score", 0.0)
                })
            
            return {
                "response": response,
                "sources": sources,
                "metadata": metadata_info,
                "user_role": user_role,
                "regulatory_context": True
            }
            
        except Exception as e:
            logging.error(f"Error in enhanced RAG pipeline: {e}")
            # Fallback to base RAG functionality
            try:
                base_result = self.base_rag.run(query, k)
                base_result["regulatory_context"] = False
                base_result["fallback"] = True
                return base_result
            except Exception as fallback_error:
                logging.error(f"Fallback to base RAG also failed: {fallback_error}")
                return {
                    "response": f"I encountered an error while processing your regulatory query: {str(e)}",
                    "sources": [],
                    "metadata": "Error occurred",
                    "error": True
                }
    
    def get_supported_roles(self) -> List[str]:
        """Get list of supported user roles"""
        return list(self.regulatory_roles.keys())
    
    def get_regulatory_frameworks(self) -> Dict[str, str]:
        """Get supported regulatory frameworks"""
        return self.regulatory_frameworks.copy()
    
    def is_regulatory_query(self, query: str) -> bool:
        """Determine if a query is regulatory-focused"""
        regulatory_indicators = [
            "basel", "corep", "finrep", "capital", "liquidity", "regulatory",
            "compliance", "reporting", "template", "calculation", "requirement",
            "framework", "guidance", "directive", "regulation", "eba", "crd", "crr"
        ]
        
        query_lower = query.lower()
        return any(indicator in query_lower for indicator in regulatory_indicators) 