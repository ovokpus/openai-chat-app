# Regulatory Reporting Test Documents

This directory contains sample documents for testing the RAG (Retrieval-Augmented Generation) system's ability to handle various regulatory reporting document types.

## Document Types

### 1. Jira Export (`sample_jira_export.csv`)

- Sample project management data for Basel III implementation
- Contains epics, stories, and tasks with status tracking
- Useful for testing PM-focused queries about project status

### 2. SQL Lineage (`sql_lineage.md`)

- Documentation of SQL transformations for regulatory calculations
- Includes FINREP F 18.00 and COREP C 01.00 examples
- Perfect for testing code-block chunking and technical queries

### 3. Steering Committee Template (`steering_committee_template.md`)

- Example of a regulatory program status update
- Contains progress tracking, risks, and timelines
- Tests the system's ability to handle structured presentation content

### 4. Data Lineage Sample (`data_lineage_sample.xlsx`)

- Mapping between source systems and regulatory templates
- Shows transformation logic and validation rules
- Tests Excel processing and table format handling

## Testing Scenarios

### Analyst Queries

- "What are the calculation rules for FINREP F 18.00 row 120?"
- "Show me the validation rules for COREP capital ratios"
- "What's the status of the Basel III implementation program?"

### Engineer Queries

- "How is the performing debt securities amount calculated?"
- "What source systems feed into FINREP F 01.01?"
- "Show me the SQL for capital ratio calculations"

### PM Queries

- "List all red status workstreams in the Basel III program"
- "What's the progress on credit risk RWA implementation?"
- "Show open tasks for FRTB implementation"

## Usage

1. Upload these documents to test multi-format support
2. Try queries from different personas (Analyst, Engineer, PM)
3. Verify citation accuracy and context relevance
4. Test table extraction and code block handling

## Document Sources

These test files are based on public regulatory documentation and common industry practices. They contain no confidential information and are suitable for testing purposes.
