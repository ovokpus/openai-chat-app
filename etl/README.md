# ETL Directory

This directory contains the original knowledge base documents and ETL (Extract, Transform, Load) scripts for processing them.

## Purpose

The ETL directory serves as:
- **Archive** of original regulatory documents
- **Processing scripts** for converting documents to deployment-ready format
- **Source of truth** for knowledge base content

## Structure

```
etl/
├── README.md                           # This file
├── preprocess_knowledge_base.py        # Script to convert docs to JSON
├── knowledge_base/
│   ├── regulatory_docs/                # Original source documents
│   │   ├── basel_iii/                  # Basel III regulatory documents
│   │   ├── corep_templates/            # COREP reporting templates
│   │   ├── finrep_templates/           # FINREP reporting templates
│   │   └── other_regulatory/           # Other regulatory documents
│   └── uploaded_docs/                  # Runtime user uploads
```

## Usage

### Regenerate Preprocessed Knowledge Base

To update the deployed knowledge base after adding/modifying documents:

```bash
# From project root
python etl/preprocess_knowledge_base.py

# This will create: api/services/preprocessed_knowledge_base.json
```

### Deploy Changes

After preprocessing:

```bash
git add api/services/preprocessed_knowledge_base.json
git commit -m "Update knowledge base content"
vercel --prod
```

## Benefits of This Approach

- **Lightweight Deployment**: Only 1.7MB JSON instead of 25MB+ binary files
- **Fast Initialization**: No document processing at runtime
- **Consistent Chunking**: Same text chunks across all deployments
- **Version Control**: Track changes to processed knowledge base
- **Vercel Compatible**: Stays well under 250MB function size limit

## Document Categories

1. **Basel III** (927 chunks)
   - Implementation policies
   - Post-crisis reforms documentation

2. **FINREP Templates** (337 chunks)
   - IFRS reporting templates
   - Financial reporting standards

3. **COREP Templates** (135 chunks)
   - Capital adequacy reporting
   - Own funds templates

4. **Other Regulatory** (284 chunks)
   - JIRA regulatory issues
   - Data lineage samples
   - Third-party regulation mapping
   - Steering committee presentations

**Total: 1,683 text chunks across 9 regulatory documents** 