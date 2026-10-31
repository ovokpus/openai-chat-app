# Business case: OpenAI Chat with RAG

**Chat with a model, or upload your own documents and get answers grounded in them.**

## Who buys this

The buyer is an operations or knowledge-management lead at a small professional-services firm or internal team with documents people keep asking about. The users are staff who need answers from policies, reports and spreadsheets.

## The problem and what it costs

People spend time searching through documents for an answer that is in there somewhere. Retrieval-augmented generation (RAG) lets a model answer from those documents. Many such projects stall at the demo stage: Gartner predicted that at least 30% of generative AI projects would be abandoned after proof of concept by the end of 2025 ([Gartner, 2024](https://www.gartner.com/en/newsroom/press-releases/2024-07-29-gartner-predicts-30-percent-of-generative-ai-projects-will-be-abandoned-after-proof-of-concept-by-end-of-2025)). A small, readable RAG stack is a cheap way to test whether it works on your documents before buying or building more.

## How the repo solves it

| Need | What in the repo does it |
|---|---|
| Read many formats | PDF, Word, Excel, PowerPoint, CSV, Markdown, HTML, SQL and text |
| Retrieve | Chunking, embeddings, an in-memory vector store and BM25 from the small `aimakerspace` library in the repo |
| Answer | A FastAPI backend that calls OpenAI with the retrieved chunks |
| Keep keys out of the server | The user's key is sent with each request and never stored |
| Example domain | A `regulatory_reporting/` folder with sample documents |

## Use-case scenarios

All of these organisations are fictional.

1. **A small accounting firm** uploads its internal procedures and asks how to handle a specific filing.
2. **A compliance analyst** uploads a regulatory guidance document and asks which sections apply to a product.
3. **A project team** uploads meeting reports and asks what was decided about a supplier.

## ROI: a worked model (illustrative)

These figures are **illustrative assumptions** unless a source is linked.

| Input | Value | Basis |
|---|---|---|
| Staff using it | 10 | Assumption |
| Minutes a day saved searching documents | 15 | Assumption |
| Working days a year | 220 | Assumption |
| Staff loaded cost an hour | US$49 | BLS May 2024 median for compliance officers, $37.70 an hour ([BLS OEWS](https://www.bls.gov/news.release/archives/ocwage_04022025.pdf)), multiplied by an assumed 1.3 |

Saving: 10 × 0.25 h × 220 × $49 ≈ **US$27,000 a year**, minus API costs. The 15-minute figure must be measured in a pilot.

## Path to production

1. Replace the in-memory store with a persistent vector database.
2. Add authentication and per-user document access.
3. Evaluate answer accuracy with a test set from your own documents (see EvolSynth-API for one way to build it).

## Risks and limits

- Answers can be wrong or cite the wrong chunk, so people should check the source.
- Uploaded documents go to OpenAI for embeddings and answers, so check data-handling terms.
- Sessions are lost on restart.

**Case strength:** **Moderate.** A common, real need, but many products offer the same thing. Its value is as a readable prototype.

## Sources

- Gartner (2024), 30% of GenAI projects abandoned after proof of concept: https://www.gartner.com/en/newsroom/press-releases/2024-07-29-gartner-predicts-30-percent-of-generative-ai-projects-will-be-abandoned-after-proof-of-concept-by-end-of-2025
- U.S. Bureau of Labor Statistics, OEWS May 2024: https://www.bls.gov/news.release/archives/ocwage_04022025.pdf
