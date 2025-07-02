# Regulatory Reporting Copilot - RAG Application

### 💡 Chosen use-case: **"Reg-Reporting Copilot"**

*A Retrieval-Augmented Generation (RAG) assistant that helps banks prepare COREP / FINREP / Basel III reports, answer ad-hoc regulator questions, and track delivery status—while quoting the exact paragraph, slide or spreadsheet cell it pulled from.*

---

## 1 — Why this matters

| Pain today                                                                                  | How the RAG Copilot helps                                                                    | Primary user                 |
| ------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- | ---------------------------- |
| Thousands of pages of Basel III, CRR3 and EBA ITS updates every year                        | Ask "What changed in IRRBB templates v3.3 vs v3.2?" → instant diff with citations            | Regulatory-reporting analyst |
| Data lineage & transformation logic scattered across run-books, SQL, Excel "mapping sheets" | "Which source table drives FINREP F 18.00 row 120?" → shows the exact ETL spec & SQL snippet | Data engineer                |
| Programme managers need weekly status across dozens of Jira epics                           | "Summarise open CRR3 items still **amber**" → returns a table grouped by owner & due date    | Project manager              |

Banks already experiment with RAG for compliance workloads because it provides traceable answers without putting sensitive data into model weights. ([lumenova.ai][1], [revvence.com][2])

---

## 2 — What to ingest (beyond PDFs)

| Format                       | Typical content                                 | Parser / notes                                                             |
| ---------------------------- | ----------------------------------------------- | -------------------------------------------------------------------------- |
| **PDF** (existing)           | Basel III, EBA ITS, national guidance notes     | Keep page numbers for trust                                                |
| **DOCX**                     | Previous regulator Q\&A letters, policy memos   | `python-docx` preserves comments                                           |
| **Excel / CSV**              | COREP / FINREP templates; data-mapping sheets   | Load with `pandas`, convert each sheet or row to Markdown before embedding |
| **SQL / YAML / Terraform**   | ETL logic and infra-as-code for reporting stack | Chunk by statement; tag `lang=sql`                                         |
| **PowerPoint**               | Steering-committee decks with timelines         | `python-pptx`; each slide a chunk with speaker notes                       |
| **Jira / Azure Boards JSON** | Epics, stories, risk logs                       | Nightly export → embed each ticket with `status`, `owner` metadata         |

Add a metadata flag `audience: analyst | engineer | pm` at ingest time to let retrieval prioritise the right chunks.

---

## 3 — Retrieval & generation tweaks

1. **Hybrid search**

   * BM25 boost on cell/row IDs (`F18.00_120`) and issue keys (`RPT-123`) so precise queries hit first.
   * Embedding search for natural-language questions ("interest-rate risk buffer floor").

2. **Persona routing**
   If the user toggles **Analyst / Engineer / PM**:
   *Analyst* → prefer regulation PDFs & policy memos.
   *Engineer* → prefer SQL / mapping sheets.
   *PM* → prefer Jira tickets & PPT timelines.

3. **Answer formats**
   *Analyst*: numbered bullet answer + direct quotes.
   *Engineer*: code fences + table lineage diagram.
   *PM*: Markdown table *(issue • owner • status • target date)* plus a "Copy to PowerPoint" button.

---

## 4 — UI sketch (Slack/Teams)

| Area               | Analyst view                                          | PM view                                          |
| ------------------ | ----------------------------------------------------- | ------------------------------------------------ |
| **Prompt hints**   | "Explain CRR3 output-floor calculation."              | "Give me % complete by workstream."              |
| **Answer pane**    | Rich quotes + page links                              | Progress bar + risk table                        |
| **Source sidebar** | Collapsible tree: *Basel III (pdf)* / *ITS (2023-03)* | Collapsible tree: *Jira* / *Decks* / *Templates* |
| **Export buttons** | "Generate formal response letter (DOCX)"              | "Export status slide (PPTX)"                     |

A top-right persona toggle switches layouts without re-querying.

---

## 5 — Implementation checklist

| Step                    | Key action                                                                                                                                               |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Ingestion pipeline**  | Extend current PDF loader with plug-in classes for DOCX, XLSX, SQL, PPTX, Jira JSON. Each writes `{chunk_text, metadata}` to the same vector store.      |
| **Vector store schema** | Add `audience`, `doc_type`, `template_cell`, `jira_status` fields for filtering.                                                                         |
| **Retrieval wrapper**   | `python\nresults = vs.search(q, filter={\"audience\": persona})\n`                                                                                       |
| **Formatter**           | Detect if ≥ 3 Jira chunks → aggregate to table; detect code chunks → render fenced.                                                                      |
| **CI tests**            | 20 historical regulator questions (expect cited paragraph); 10 lineage questions (expect correct table) ; 5 status queries (expect correct Jira counts). |

---

## 6 — Roll-out plan

1. **Week 1** – Load latest Basel III PDFs + one quarter of Jira export; deploy Slack bot to the reg-reporting channel.
2. **Week 3** – Add XLSX template ingestion; start nightly Jira/Confluence sync.
3. **Week 6** – Enable persona-aware UI + "export to PPTX/DOCX".
4. **Quarter 2** – Integrate with workflow APIs (create Jira sub-task, trigger ETL re-run) for closed-loop fixes.

---

## 7 — Test Documents for PoC

Here's a starter set of **public, downloadable examples** for every document type your Reg-Reporting RAG will ingest. Each one is a genuine artefact that teams in risk- and regulatory-reporting use day-to-day, so they're perfect for testing your pipeline.

| Doc type                                      | Example you can download & test with                                                                                             | Why it's useful in your PoC                                                                   |
| --------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| **Basel III primary text (PDF)**              | *"Basel III: Finalising post-crisis reforms"* – 118-page PDF from the Basel Committee. ([bis.org][3])                            | Rich headings & tables let you verify heading-aware chunking and page-number citations.       |
| **EBA ITS / Reporting Framework (PDF/HTML)**  | EBA's *Reporting Framework 3.3* release notes and taxonomy package. ([eba.europa.eu][4])                                         | Contains change-logs you can query ("What's new in v3.3?").                                   |
| **FINREP templates (XLS/XLSX)**               | *Annex I / Annex III – FINREP IFRS templates* spreadsheets. ([eba.europa.eu][5], [eba.europa.eu][6])                             | Each sheet is a table-heavy form—great for testing table-to-Markdown extraction.              |
| **COREP templates (XLSX)**                    | *Annex I – Own Funds templates* (COREP capital adequacy). ([eba.europa.eu][7])                                                   | Lets you ask cell-level questions ("What goes in C 01.00, row 040?").                         |
| **Mapping / lineage spreadsheet (XLS)**       | SIFMA's *Third-Party Regulation Mapping Matrix* sample. ([sifma.org][8])                                                         | Mimics the data-lineage worksheets banks keep between source tables and report rows.          |
| **SQL lineage or ETL spec (code / Markdown)** | Blog demo: *Automate SQL Data Lineage Mapping using Azure Data Factory* – includes full SQL snippets. ([shivp436.medium.com][9]) | Perfect for code-block chunking and `lang=sql` metadata tagging.                              |
| **Jira (CSV)**                                | Atlassian support page with step-by-step export instructions and a sample CSV. ([support.atlassian.com][10])                      | After export you'll have real issue keys, statuses, and owners to test PM queries.            |
| **Steering-committee deck (PPTX)**            | Princeton PATCO's *Steering Committee Presentation Template* (PowerPoint). ([patco.princeton.edu][11])                            | Slide titles + speaker notes let you trial slide-level chunking and "Export to PPTX" answers. |

---

## 8 — Technical Implementation: From PDF-Only to Regulatory Copilot

### 8.1 Architecture Evolution

**Original State:**
- Basic PDF-only RAG application
- Single document upload
- Simple chat interface
- Limited to PDF text extraction

**Current State:**
- Multi-document RAG with regulatory specialization
- Global knowledge base with pre-loaded documents
- Role-based responses (Analyst/Engineer/PM)
- Enhanced citations with precise source locations
- Performance-optimized async processing

### 8.2 Backend Enhancements

#### **Multi-Document Processing (`aimakerspace/multi_document_processor.py`)**
```python
class MultiDocumentProcessor:
    """
    Processes multiple document types for regulatory reporting:
    - PDF, DOCX, XLSX, XLS, PPTX, PPT, CSV, SQL, PY, JS, TS, MD, TXT
    - Preserves metadata and source locations
    - Handles document type detection
    """
```

**Key Features:**
- **13 file types supported** with automatic format detection
- **Enhanced metadata** with document type classification
- **COREP/FINREP template detection** for Excel files
- **Precise source citations** (Page X, Sheet Y, Slide Z, Line N)
- **Error handling** for corrupt or encrypted files

#### **Regulatory RAG Enhancement (`aimakerspace/regulatory_rag_enhancer.py`)**
```python
class RegulatoryRAGEnhancer:
    """
    Wraps existing RAG pipeline with regulatory-specific features:
    - Role-based prompts (Analyst/Data Engineer/Programme Manager)
    - Document type filtering and prioritization
    - Enhanced search scoring with regulatory relevance
    - Regulatory query detection and routing
    """
```

**Key Features:**
- **Role-based responses** tailored to banking professionals
- **Document type filtering** (prefer SQL for engineers, PDFs for analysts)
- **Enhanced search scoring** with regulatory relevance calculation
- **Fallback protection** to original RAG if enhancement fails
- **Priority source support** for specific document prioritization

#### **Global Knowledge Base Implementation**
```python
# Auto-loads all documents from ./documents directory at startup
async def initialize_global_knowledge_base():
    """
    Processes all documents in ./documents directory:
    - Basel III PDF (3.1MB) - regulatory text
    - FINREP/COREP templates (1.2MB) - Excel reporting forms
    - SQL lineage samples (8KB) - ETL calculation scripts
    - Jira exports (8KB) - project tracking data
    - Policy documents (12KB) - comprehensive guidelines
    """
```

**Key Features:**
- **Automatic startup processing** of regulatory documents (5.1MB total)
- **Session-independent access** - users get immediate document access
- **Performance optimization** with async batch embeddings (1375+ chunks in seconds)
- **Comprehensive test data** covering all major regulatory document types

### 8.3 API Enhancements

#### **New Endpoints Added:**
1. **`/api/upload-document`** - Multi-document upload (preserves original PDF endpoint)
2. **`/api/regulatory-rag-chat`** - Enhanced RAG with regulatory features
3. **`/api/global-knowledge-base`** - Global knowledge base status and info

#### **Enhanced Session Management:**
- **Dual RAG support** - works with user documents AND global knowledge base
- **Automatic session creation** with global KB access for immediate usage
- **Async session handling** for better performance
- **Proper session ID management** to prevent KeyError issues

### 8.4 Frontend Enhancements

#### **Document Upload Component (`frontend/src/components/PDFUpload/PDFUpload.tsx`)**
**Before:** PDF-only with MIME type validation
**After:** 
- **Multi-format support** with file extension validation
- **13 file types** with detailed format descriptions
- **Enhanced error handling** and user feedback
- **Backward compatibility** maintained for existing PDF functionality

#### **Global Knowledge Base Integration**
- **`useGlobalKnowledgeBase.ts`** hook for managing global KB state
- **Enhanced WelcomeSection** showing pre-loaded documents
- **Document count displays** (user + global documents)
- **"Try Global KB" functionality** with sample queries

#### **Enhanced RAG Integration**
- **Dual RAG mode support** (user documents + global KB)
- **Automatic session management** with temporary session IDs
- **Improved error handling** and loading states
- **Better user experience** with immediate document access

### 8.5 Performance Optimizations

#### **Async Batch Embedding Generation**
**Before:** 1375+ sequential API calls taking minutes
**After:** 2-3 concurrent batch requests taking seconds

```python
async def async_get_embeddings(self, texts: List[str], batch_size: int = 1024):
    """
    Generate embeddings in batches with async processing:
    - 99% reduction in API calls (1375 → 2-3 requests)
    - ~90% reduction in initialization time (minutes → seconds)
    - Concurrent processing instead of sequential
    """
```

**Performance Improvements:**
- **Initialization Time:** ~90% reduction (minutes → seconds)
- **API Efficiency:** ~99% fewer API calls (1375 → 2-3 requests)
- **Concurrency:** Parallel processing instead of sequential
- **User Experience:** Immediate access to regulatory documents

### 8.6 Dependency Management

#### **Added Dependencies:**
```txt
# Multi-document processing
openpyxl>=3.1.2          # Excel (.xlsx) file processing
xlrd>=2.0.1              # Legacy Excel (.xls) file support
python-docx>=0.8.11      # Word document processing
python-pptx>=0.6.21      # PowerPoint presentation processing
pandas>=2.0.0            # CSV and data processing
cryptography>=3.1        # PDF encryption support
```

#### **Removed Dependencies:**
- **beautifulsoup4** - HTML processing removed for simplification
- **lxml** - No longer needed without HTML processing

### 8.7 Bug Fixes and Stability Improvements

#### **Major Issues Resolved:**
1. **API Key Management** - Deferred embedding creation until user provides API key
2. **Method Name Consistency** - Fixed `process_document()` vs `load_documents()` discrepancies
3. **Document Format Handling** - Proper document object creation with metadata
4. **Text Splitting Methods** - Corrected `split_texts` vs `split_documents` usage
5. **Excel File Processing** - Added support for both .xlsx and .xls formats
6. **Vector Database Integration** - Fixed `add_documents` vs `insert` method calls
7. **Session Management** - Resolved session ID mismatch issues
8. **Async Event Loop Conflicts** - Fixed `asyncio.run()` conflicts in FastAPI

#### **Error Handling Improvements:**
- **Malformed CSV parsing** with better error recovery
- **Excel format detection** with fallback for misnamed extensions
- **Document chunk creation** with proper metadata handling
- **Vector database operations** with individual document insertion
- **Frontend session validation** with proper error states

### 8.8 Testing and Quality Assurance

#### **Test Document Collection (5.1MB):**
- **Basel III PDF** (3.1MB) - Primary regulatory text
- **FINREP IFRS templates** (852KB) - Excel reporting forms
- **COREP Own Funds templates** (312KB) - Capital adequacy spreadsheets
- **SIFMA regulation mapping** (796KB) - Data lineage matrices
- **Basel III policy document** (12KB) - Comprehensive guidelines
- **SQL data lineage sample** (8KB) - ETL calculation scripts
- **Jira regulatory issues** (8KB) - Project tracking exports
- **Regulatory committee presentation** (12KB) - Slide content samples

#### **Validation Scenarios:**
- **Analyst Queries:** Basel III regulation explanations with precise citations
- **Engineer Queries:** SQL lineage tracking and ETL specifications
- **PM Queries:** Project status aggregation and timeline tracking
- **Document Format Testing:** All 13 file types with real regulatory content
- **Performance Testing:** 1375+ chunk processing in seconds vs minutes

---

### Bottom line

Regulatory reporting is a perfect fit for RAG: it's document-dense, compliance-critical, and demands *traceable* answers. By expanding the PDF-only application into a **Reg-Reporting Copilot**—with XLSX templates, SQL lineage files and Jira status feeds—we deliver daily wins to analysts, data engineers **and** programme managers, all without rewriting the core retrieval loop.

The application now provides:
- **Immediate access** to comprehensive regulatory document collection
- **Role-based assistance** for different banking professionals
- **Multi-format document processing** beyond just PDFs
- **Performance-optimized** initialization and retrieval
- **Production-ready** error handling and stability
- **Extensible architecture** for future regulatory document types

Happy shipping! 🚀

[1]: https://www.lumenova.ai/blog/ai-finance-retrieval-augmented-generation/ "AI in Finance: The Promise and Risks of RAG - Lumenova AI"
[2]: https://revvence.com/blog/rag-in-banking "Leveraging Retrieval-Augmented Generation (RAG) in Banking"
[3]: https://www.bis.org/bcbs/publ/d424.pdf "[PDF] Basel III: Finalising post-crisis reforms"
[4]: https://www.eba.europa.eu/risk-and-data-analysis/reporting/reporting-frameworks/reporting-framework-33 "Reporting framework 3.3 | European Banking Authority"
[5]: https://www.eba.europa.eu/documents/10180/1679431/145eff2a-0fd4-4348-b82b-25a91b0ec8a8/Annex%20I%20%28FINREP%20Annex%20III%20-%20IFRS%20templates%29.xls "[XLS] Annex 1 (FINREP IFRS templates)"
[6]: https://www.eba.europa.eu/documents/10180/359626/049e48a4-e7c2-44c6-89b1-4086447bced9/Annex%20III%20-%20FINREP%20templates%20IFRS.xlsx "[XLS] Annex III - FINREP templates IFRS.xlsx"
[7]: https://www.eba.europa.eu/sites/default/files/documents/10180/359626/b11ab86f-63e3-4219-9add-6a74b4922654/Annex%20I%20-%20Own%20funds%20templates.xlsx "[XLS] Annex I - Own funds templates.xlsx"
[8]: https://www.sifma.org/wp-content/uploads/2017/08/third-party-regulation-mapping-matrix.xls "[XLS] Third Party Regulation Mapping Matrix"
[9]: https://shivp436.medium.com/automate-your-sql-data-lineage-mapping-using-azure-data-factory-8485830d9c3a "Automate your SQL Data Lineage Mapping using Azure Data Factory"
[10]: https://support.atlassian.com/automation/kb/how-to-export-issues-from-jira-cloud-in-csv-format/ "Export issues from Jira cloud in CSV format - Atlassian Support"
[11]: https://patco.princeton.edu/templates/all/steering-committee-presentation-template "Steering Committee Presentation Template - PATCO" 