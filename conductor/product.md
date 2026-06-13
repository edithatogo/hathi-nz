# Initial Concept

Within the this folder- "C:/Users/60217257/OneDrive - Flinders/repos/legal-nz"- is a series of related projects to parliament and legal documents and nlp for nz. Hathi contains a lot of NZ-related documents. I want to create corpus from them, to upload to hugging face, github and zenodo, similar to what has been done for: "C:\Users\60217257\OneDrive - Flinders\repos\legal-nz\corpus-law-nz" and "C:\Users\60217257\OneDrive - Flinders\repos\legal-nz\corpus-cases-medilegal-nz". Initially we don't need to extract anything from them. Start by just transferring the raw files, then we will progressively manage them, for instance, with OCR. I'm trying to build a shared library in "C:\Users\60217257\OneDrive - Flinders\repos\legal-nz\nlp-policy-nz" for all processing scripts, with the data kept separately. This is the hugging face site: https://huggingface.co/edithatogo. You may need to consider how we organise Hugging Face, as the number of datasets expands. I think if you look within the other repo's, you'll find I've already started to do some work on hathi, so you could leverage that work. Those repos are also on github already: https://github.com/edithatogo/corpus-legislation-nz, https://github.com/edithatogo/nlp-policy-nz, https://github.com/edithatogo/corpus-nz-hansard. Try to systematise all of this work. I do also want it to be bleeding edge though.

# Product Guide: Hathi NZ Corpus

## 1. Product Vision & Goals
The goal of `hathi-nz` is to build a systematic, bleeding-edge corpus of New Zealand parliamentary and legal documents sourced from the HathiTrust Digital Library. The project aims to:
- **Systematize NZ Legal NLP:** Align with and connect existing repositories like `corpus-law-nz`, `corpus-cases-medilegal-nz`, `corpus-legislation-nz`, and `corpus-nz-hansard`.
- **Multi-Platform Hosting:** Host data securely and accessibly on Hugging Face (under the `edithatogo` organization), GitHub (for code and metadata), and Zenodo (for long-term archival with DOIs).
- **Decoupled Architecture:** Build and maintain processing scripts inside a shared library in `nlp-policy-nz`, keeping the raw and processed data separate in `hathi-nz`.
- **Progressive Processing:** Start with raw file transfers, followed by progressive management steps, including optical character recognition (OCR) and text extraction.

## 2. Target Audience
The primary consumers of this corpus include:
- **NLP Researchers & AI Developers:** Training or fine-tuning language models on specialized NZ legal, political, and historical texts.
- **Legal Scholars, Historians & Policy Analysts:** Investigating parliamentary debates, hansard transcripts, and legislative histories.
- **Open Science & Data Preservationists:** Seeking structured, versioned, and easily citeable NZ legal datasets.
- **General Public & Interested Stakeholders:** Anyone else interested in open-access NZ parliamentary and legal history.

## 3. Scope & Key Features
- **Raw File Staging:** Identify and transfer NZ-related documents from HathiTrust as raw data files.
- **Shared NLP Utility Integration:** Consume and extend the shared processing library located in `nlp-policy-nz`.
- **Progressive OCR & Cleaning:** Apply modern OCR techniques to extract machine-readable text.
- **Hugging Face Organization Structure:** Standardize dataset naming conventions and repository structures under `edithatogo` to scale to dozens of datasets seamlessly.
- **Archival Pipeline:** Automatically package versioned releases and deposit them to Zenodo to obtain persistent DOIs.

## 4. Future Roadmap & Bleeding-Edge Extensions
- **Layout-Aware Parsing:** Implement vision-based layout detection (e.g., layout-parser or Nougat) for complex historical columns.
- **Semantic Search Indexing:** Create dense vector embeddings for the corpus to support semantic queries.
