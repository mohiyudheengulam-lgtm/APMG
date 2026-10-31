## *RESEARCH EXPOSÉ*

Agent On Duty: A Fully Local Agentic AI System for Multi-Document Procurement Verification and Policy Compliance Auditing

Revised Sections 1–6

# **1\. Introduction & Objective of the Problem (Navya Gupta)**

In enterprise procurement operations, accounts-payable departments perform a three-way match before disbursing funds to suppliers. An accounts-payable clerk manually cross-references three primary operational records:

* Purchase Order (PO): specifies the items authorized for purchase, their unit prices, and quantities.  
* Delivery Note / Goods Receipt: records the quantities of merchandise physically received at the warehouse.  
* Vendor Invoice: the supplier’s formal payment request.

In addition to validating structured numerical values across these records, the clerk checks invoice compliance against corporate purchasing guidelines and vendor-specific Master Service Agreements (MSAs). These unstructured policy documents may specify agreed rates, early-payment discount terms, penalty clauses, and allowable surcharges.

## **The multi-document operational inefficiency**

Three-way matching relies largely on structured tabular data, whereas vendor MSAs and corporate guidelines often contain natural-language clauses distributed across multi-page documents. Manually cross-referencing these mixed document types introduces operational friction and creates opportunities for error.

Representative operational example:

* The Purchase Order orders 500 units at an agreed price of EUR 12.00 each.  
* The Goods Receipt confirms that only 480 units were physically delivered.  
* The Vendor Invoice bills for 500 units at EUR 12.40 per unit and adds a EUR 150 line item labelled “fuel surcharge”.  
* The MSA prohibits ancillary surcharges unless pre-approved in writing and locks unit pricing for 12 months.

The clerk must identify three discrepancies: overbilling for 20 unreceived units, a unit-price increase of EUR 0.40, and a surcharge that is not authorized by the MSA. The quantity discrepancy represents EUR 240 (20 × EUR 12.00), the price increase represents EUR 200 (500 × EUR 0.40), and the surcharge represents EUR 150\. The total potential discrepancy is EUR 590, subject to the applicable invoice and contractual terms. The surcharge clause is located on page 14 of the MSA. Manual review across large invoice volumes can delay processing and increase the risk of human error.

## **Business consequences and data privacy imperative**

Manual verification backlogs can cause payment delays and strained vendor relations, missed early-payment discounts, accidental overpayments, and audit or compliance risks. Invoices, pricing schedules, and vendor contracts also contain commercially sensitive financial data, including negotiated prices and discount margins. Where personal contact information appears in procurement records, processing may raise additional data-protection concerns.

For this project, ingestion, parsing, retrieval, reasoning, and decision-recording components will operate locally on edge hardware without external API calls during operation. Models and software may be downloaded during setup; the system is designed to run offline thereafter. This architecture is intended to support privacy-conscious processing, but it does not by itself establish legal compliance; organizational and regulatory requirements remain applicable.

## **Research objective**

The objective of this research is to design, implement, and empirically evaluate a fully local agentic AI system—Agent On Duty—for multi-document procurement verification and policy auditing. The system extracts information from structured records (POs, goods receipts, and invoices) and unstructured contracts (MSAs), checks it against formal rules, produces evidence-backed recommendations, and records manager-approved decisions in a local database. A mandatory Human-in-the-Loop (HITL) approval gate prevents the agent from recording final decisions autonomously. The research compares Standard Vector-Based RAG and Google’s Open Knowledge Format (OKF v0.2) document navigation in terms of accuracy, latency, context-token efficiency, and preparation/implementation effort.

# **2\. Main Research Question and Sub-Questions (Rishikta Nishikant Bhore)**

The central research question and three sub-questions address operational inefficiency, retrieval design, agent reliability, and human governance.

## **Main research question**

How can a fully local agentic AI system automate multi-document procurement verification and policy compliance auditing while optimizing retrieval accuracy, context-token efficiency, and execution speed under mandatory human-in-the-loop governance?

## **Sub-questions**

Sub-question 1 — Retrieval paradigm comparison: How do Standard Vector-Based RAG (fixed-size token chunking and dense embeddings) and OKF v0.2 document navigation (Markdown concept files, YAML metadata, and link traversal) compare in terms of field and rule accuracy (Exact Match and flag precision/recall/F1), latency, context-token efficiency, and preparation/implementation effort when applied to procurement documents?

Sub-question 2 — Agentic execution and HITL governance: How reliably can a local ReAct agent using a small open-source language model (≤ 2B parameters via Ollama) produce valid, evidence-backed recommendations through Pydantic-validated tools, and how can an HITL approval gate ensure that no final decision is recorded without manager sign-off?

Sub-question 3 — Post-evaluation retrieval-path assignment: Based on the benchmark results, what evidence-based assignment of retrieval paths should be recommended for structured procurement records and unstructured contract content? This sub-question derives routing criteria from the comparative results; it does not claim to implement or evaluate a dynamic runtime router.

# **3\. Theoretical Framework (Vijayadharshan Periyasamy)**

This research combines one organizational theory with three technical foundations. Socio-Technical Systems theory motivates the design of human oversight. Retrieval-augmented generation, agentic reasoning, and OKF define the technical design space evaluated in the project.

## **3.1 Socio-Technical Systems (STS) theory**

STS theory, introduced by Trist and Bamforth (1951), holds that organizational performance depends on the joint optimization of interdependent technical and social subsystems. Clegg (2000) and Baxter and Sommerville (2011) later translated this perspective into information-system design principles. In this project, the technical subsystem comprises the local language model served through Ollama, the retrieval pipelines, and the action and audit engine. The social subsystem comprises accounts-payable clerks and procurement managers, whose oversight and accountability are supported by evidence, audit records, and an explicit approval step. The agent recommends; a human manager makes the final decision.

## **3.2 Retrieval-Augmented Generation (RAG)**

Lewis et al. (2020) combine a language model (parametric memory) with retrieval from an external document index (non-parametric memory), grounding answers in source material. In the standard vector-based approach used as Path A, documents are split into fixed-size chunks, converted into dense embeddings, and retrieved by similarity for a query. Chunk boundaries may split tables or contract clauses, which is a potential weakness in procurement documents.

## **3.3 Agentic reasoning: ReAct and agentic document workflows**

ReAct (Yao et al., 2023\) combines model reasoning with actions such as tool calls. An agent can gather evidence step by step and adjust its retrieval plan. Agentic RAG (Singh et al., 2025\) applies agentic interaction to retrieval, while Agentic Document Workflows (LlamaIndex, 2025\) apply stateful, tool-mediated processing to business documents. In this project, deterministic tools perform numerical checks—such as price, quantity, and line-total calculations—rather than relying on the model’s arithmetic. Pydantic schemas validate tool inputs and outputs. Following Schluntz and Zhang (2024), the design favors simple, composable patterns over complex agent frameworks.

## **3.4 Open Knowledge Format (OKF v0.2)**

OKF is described in the project specification as a directory of Markdown concept files with YAML frontmatter and standard Markdown links. Index files support navigation from overview to detail. This project uses OKF v0.2 to represent procurement packages and MSA sections as navigable concepts. The agent can read an index, open a concept file, and follow links to related records or clauses. OKF’s suitability for multi-page procurement contracts is treated as an empirical hypothesis, not an established fact.

## **How the foundations map to the research questions**

| Foundation | Role in this project | Research question |
| :---- | :---- | :---- |
| STS theory | Design principle for human oversight and the HITL gateway | Sub-question 2 |
| RAG | Path A: vector-based retrieval baseline | Sub-question 1 |
| ReAct / agentic document workflows | Design of the single reasoning agent | Sub-question 2 |
| OKF v0.2 | Path B: structured concept navigation | Sub-questions 1 and 3 |

# **4\. Agentic Governance & Human-in-the-Loop Integration (Rishikta Nishikant Bhore)**

Giving an autonomous agent the final word on supplier invoices creates financial and contractual risk. A wrong approval can lead to overpayment, and a wrong rejection can damage supplier relations. Some cases also cannot be resolved from the uploaded documents alone—for example, a surcharge may have been approved in writing outside the document package, or a price escalation may have been agreed in advance. The system therefore separates verification and recommendation from decision-making: the agent verifies and recommends; a human manager decides. This follows the socio-technical principle that automation and human oversight should be designed together.

Scope of the agent’s authority: Agent On Duty verifies invoices and prepares recommendations. It does not release payments, contact suppliers, initiate disputes, or independently record a final approval or rejection. These actions remain outside the agent’s authority and are controlled by the human manager.

## **Partition of operational responsibilities: agent vs. human manager**

| Operational phase | Automated system | Human manager |
| :---- | :---- | :---- |
| Data ingestion and parsing | Extraction layer (PyMuPDF, with Tesseract fallback) converts uploaded POs, goods receipts, invoices, and MSAs into structured records and page-referenced text. The agent reads this output. | Uploads the document package. |
| Information cross-referencing | Matches line items, quantities, and unit prices across the PO, receipt, and invoice. Retrieves rate cards and surcharge clauses from the MSA through the active retrieval path. | Resolves ambiguities that documents cannot settle, such as verbal agreements or approvals outside the package. |
| Discrepancy calculation | Calls deterministic tools for price, quantity, and line-total variances. Identifies policy violations such as unauthorized surcharges. Tax-rule validation is out of scope. | Judges business context for flagged items, such as an agreed price adjustment. |
| Audit logging | Code writes agent steps, tool calls, calculations, and cited clauses into a JSON audit record. | Checks the evidence and calculations during review. |
| Recommendation and decision | Produces a recommendation and evidence. It cannot write a final status. | Confirms, overrides, or rejects the recommendation and holds sole authority over the final decision. |

## **How the HITL gateway works**

1. The agent completes verification and returns a recommendation: NO\_DISCREPANCY or one or more discrepancy flags. Each finding includes the source values, calculation where applicable, and the cited document and page.  
2. The recommendation is saved as PENDING\_REVIEW. No final decision is recorded at this stage.  
3. The manager reviews the recommendation on the local dashboard. Flagged cases are highlighted; cases without detected discrepancies may be confirmed.  
4. The manager confirms the recommendation, overrides it with a written reason, or rejects the invoice.  
5. Only the approval function records the manager’s final decision. The audit record stores the reviewer, timestamp, decision, and any override reason.

## **Recommendation and decision statuses**

The agent’s recommendation is distinct from the manager’s final decision. The agent recommendation may be NO\_DISCREPANCY or one or more flags: FLAGGED\_PRICE\_MISMATCH, FLAGGED\_QUANTITY\_MISMATCH, FLAGGED\_SURCHARGE, or FLAGGED\_MISSING\_DOCUMENT. A package with multiple discrepancies can carry multiple flags. The manager’s final decision is stored separately as APPROVED, REJECTED, or OVERRIDDEN. PENDING\_REVIEW and REVIEWED represent the review workflow state, not the substantive invoice decision. The agent never writes a final status. If a required document or clause cannot be found, it flags the case rather than guessing.

## **References cited in Sections 1–4**

Baxter, G., & Sommerville, I. (2011). Socio-technical systems: From design methods to systems engineering. Interacting with Computers, 23(1), 4–17.

Clegg, C. W. (2000). Socio-technical principles for system design. Applied Ergonomics, 31(5), 463–477.

Google Cloud. (2026). Open Knowledge Format (OKF) specification, version 0.2.

Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W., Rocktäschel, T., Riedel, S., & Kiela, D. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. Advances in Neural Information Processing Systems (NeurIPS), 33, 9459–9474.

LlamaIndex. (2025). Introducing agentic document workflows \[Blog post\]. https\://www\.llamaindex.ai/blog/introducing-agentic-document-workflows

Schluntz, E., & Zhang, B. (2024). Building effective agents. Anthropic. https\://www\.anthropic.com/engineering/building-effective-agents

Singh, A., et al. (2025). Agentic retrieval-augmented generation: A survey on agentic RAG. arXiv preprint arXiv:2501.09136.

Trist, E. L., & Bamforth, K. W. (1951). Some social and psychological consequences of the longwall method of coal-getting. Human Relations, 4(1), 3–38.

Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2023). ReAct: Synergizing reasoning and acting in language models. International Conference on Learning Representations (ICLR).

# **5\. Research Workflow & System Architecture (Sara Shaban)**

The research workflow coordinates document extraction, two retrieval paradigms, a single agentic reasoning engine, a mandatory HITL approval gate, and a local action and audit engine. The two retrieval paths are evaluated as alternative retrieval paradigms. The retrieval representation and procedure are part of the experimental treatment; Path B’s navigation actions are therefore included in its retrieval process rather than treated as an unchanged component.

## **5.1 Raw document extraction and OCR methodology**

Before indexing, procurement documents (POs, delivery notes, vendor invoices, and multi-page MSAs) are converted into machine-readable text and structured records. Extraction is performed once, and both retrieval paths receive the same extraction output so that extraction differences do not confound the retrieval comparison.

* Native digital documents: PyMuPDF (fitz) reads the text layer and extracts text, tables, and key-value fields. Structured procurement records preserve item numbers, quantities, and unit prices as aligned fields. Plain-text files are read directly.  
* Scanned documents (fallback): PyMuPDF checks for a text layer. Pages without one are rendered at 300 DPI and passed to Tesseract OCR (Smith, 2007). Scanned documents are supported as an input fallback but are excluded from benchmark evaluation.  
* Output: POs, goods receipts, and invoices are represented as structured records with headers and line items; MSAs are represented as cleaned text with page references. Each extracted field or text segment retains its source filename and page number.

## **5.2 Single agent architecture and retrieval paradigms**

The central ReAct agent is implemented once and receives context through a standardized Pydantic representation. Both paths use the same extracted documents, model, agent prompt, deterministic calculation tools, output schema, and run settings. The experiment compares the retrieval paradigms: Path A retrieves similarity-ranked chunks, while Path B performs model-directed navigation through OKF concepts. Since navigation actions are intrinsic to Path B, they are counted and reported as part of that path’s retrieval cost. The study does not claim that the internal retrieval operations are identical.

## **Path A — Standard vector-based RAG**

Extracted text is split into fixed-size chunks of 500 tokens with a 50-token overlap. Each chunk is converted into a dense embedding using nomic-embed-text locally through Ollama and stored in a FAISS index. For each query, the five chunks with the highest inner-product similarity are passed to the agent. This is the vector-based retrieval baseline.

## **Path B — OKF v0.2 concept navigation**

The same extracted documents are converted into an OKF bundle: each document package has a folder, each document is represented as a concept file, and MSAs are divided into section-level concept files (e.g., pricing, surcharges, and payment terms). YAML frontmatter records the required type and source information, including the original filename and page. index.md files list directory contents, and Markdown links connect related concepts—for example, an invoice to its PO and the MSA clause governing its prices. The agent navigates by reading an index, opening concept files, and following links, without embeddings.

## **5.3 ReAct reasoning engine**

The agent is a single ReAct loop written in plain Python and powered by Qwen3-1.7B, a 1.7-billion-parameter model served locally through Ollama using a 4-bit GGUF build. The agent can call the active retrieval tools or deterministic Python calculation tools for price, quantity, line-total variances, and comparison against MSA rates. Arithmetic is performed by tools, not by the model. Pydantic validates tool inputs and the final recommendation. The model uses temperature 0, a fixed seed, and a maximum of 10 reasoning/tool steps per verification. The model is read-only with respect to final decision storage.

## **5.4 HITL gateway**

When verification finishes, the agent returns a structured recommendation and evidence. The application saves it as PENDING\_REVIEW. The agent has no database write permission for final decisions. Only the manager approval function, invoked from the dashboard after confirmation, override, or rejection, can write the final decision and update the review state.

## **5.5 Local action and audit engine**

Final manager decisions are stored in a local SQLite database. Recommendation flags and final decisions are separate fields. For each verification, code generates one JSON audit record containing:

* Package ID, retrieval path, and model settings.  
* Agent tool calls and their inputs and outputs, plus verification progress.  
* Calculations and formulas.  
* Cited clauses, including document name and page.  
* Context-token counts and elapsed time per step.  
* Agent recommendation, manager decision, reviewer, timestamp, and any override reason.

## **5.6 User interface**

A local Streamlit web app provides three views: package upload, a verification-progress view showing tool calls/retrieved evidence/calculation results, and the manager approval dashboard. The dashboard highlights flagged cases and lets the manager confirm, override with a written reason, or reject the recommendation. The interface does not expose private internal model reasoning; it presents auditable actions and evidence.

## **Summary of technical choices**

| Component | Choice |
| :---- | :---- |
| PDF text and table extraction | PyMuPDF |
| OCR (fallback only) | Tesseract OCR, 300 DPI |
| Path A: chunking | 500 tokens, 50-token overlap |
| Path A: embedding model | nomic-embed-text (via Ollama) |
| Path A: vector index | FAISS, top-5 by inner product |
| Path B: knowledge format | OKF v0.2 bundle with index.md navigation |
| Language model | Qwen3-1.7B via Ollama (4-bit GGUF) |
| Agent | ReAct loop in plain Python, Pydantic schemas |
| Run settings | Temperature 0, fixed seed, maximum 10 steps |
| Results storage | SQLite |
| Audit log | JSON, one record per verification |
| User interface | Streamlit web app |

## **References cited in Section 5**

Gerganov, G., et al. (2023). llama.cpp: LLM inference in C/C++ \[Computer software\]. GitHub. https\://github.com/ggml-org/llama.cpp

Google Cloud. (2026). Open Knowledge Format (OKF) specification, version 0.2.

Johnson, J., Douze, M., & Jégou, H. (2021). Billion-scale similarity search with GPUs. IEEE Transactions on Big Data, 7(3), 535–547.

Karpukhin, V., Oğuz, B., Min, S., Lewis, P., Wu, L., Edunov, S., Chen, D., & Yih, W. (2020). Dense passage retrieval for open-domain question answering. In Proceedings of EMNLP 2020 (pp. 6769–6781). Association for Computational Linguistics.

Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W., Rocktäschel, T., Riedel, S., & Kiela, D. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. Advances in Neural Information Processing Systems (NeurIPS), 33, 9459–9474.

Nussbaum, Z., Morris, J. X., Duderstadt, B., & Mulyar, A. (2024). Nomic Embed: Training a reproducible long context text embedder. arXiv preprint arXiv:2402.01613.

Smith, R. (2007). An overview of the Tesseract OCR engine. Ninth International Conference on Document Analysis and Recognition (ICDAR), 2, 629–633.

Yang, A., et al. (2025). Qwen3 technical report. arXiv preprint arXiv:2505.09388.

Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2023). ReAct: Synergizing reasoning and acting in language models. International Conference on Learning Representations (ICLR).

# **6\. Research Methodology & Comparative Evaluation Framework (Mohiyudheen Kalluparamban)**

## **6.1 Research design**

This project follows Design Science Research (Hevner et al., 2004): it builds a working artifact, Agent On Duty, and evaluates how well it addresses the defined problem. The work is organized around the design science methodology of Peffers et al. (2007). The evaluation is a controlled comparative experiment using the same agent, model, extracted corpus, and benchmark across two retrieval paradigms. The experimental variable is the retrieval paradigm, including its document representation and retrieval procedure. Path B’s model-directed navigation is considered part of Path B, not a separate uncontrolled agent.

| Activity | Content in this project | Schedule |
| :---- | :---- | :---- |
| Problem identification | Three-way matching, MSA compliance checking, and fully local operation. | Stage 1 (Oct 9 – Nov 3\) |
| Objectives of a solution | Research questions, benchmark design, and evaluation criteria. | Stage 1 (Oct 9 – Nov 3\) |
| Design and development | Benchmark generator, extraction, Path A, Path B, ReAct agent, approval gate, action/audit engine, and UI. | Sprints 1–4 (Nov 4 – Dec 1\) |
| Demonstration | Mid-review prototype demo of ReAct & HITL gate (Sprint 3); integrated end-to-end benchmark execution across 20–30 document packages (Sprint 4). | Sprints 3–4(2-22 Dec) |
| Evaluation | Controlled experimental comparison of Path A (Vector RAG) vs. Path B (OKF v0.2) across 5 metrics: Extraction Accuracy (EM/F1), Latency, Token Efficiency, Preparation Effort, and Agent Reliability. | Sprint 5 (Jan 7 – Jan 15\) |
| Communication | Final APMG research report (Chapters 1–6), scientific project poster, local codebase release, and live software presentation. | Sprint 6 (Jan 16 – Jan 22\) |

## **6.2 Experimental setup**

### **Benchmark and ground truth**

The benchmark contains 20–30 synthetic document packages generated from 1–2 seed templates. A generation script injects predefined discrepancies and produces a ground-truth file for each package. The ground truth is sufficiently detailed to evaluate field extraction, calculations, flags, and evidence citation. It contains:

* Package and document identifiers, document types, and source-page references.  
* Expected structured field values for PO, goods receipt, and invoice headers and line items, including quantities, unit prices, and line totals.  
* Expected calculations and variance values for each relevant line item.  
* Expected discrepancy flags and the precise error type(s) injected into the package.  
* The relevant MSA clause text or clause identifier, source document, and page number for each policy-related finding.  
* Expected recommendation and evidence set, including the correct document/page citations.  
* An indication of which documents or clauses are intentionally missing, where applicable.

The generator—not the agent—defines the ground truth. Each package is validated against its ground-truth file before being used in the experiment. No manual labeling of generated cases is required, although the team will inspect the generated corpus for consistency.

### **Experimental conditions**

Every package is processed through both Path A and Path B using the same extraction output, language model (Qwen3-1.7B), agent prompt, deterministic tools, output schema, and run settings (temperature 0, fixed seed, maximum 10 steps). The retrieval paradigm is the treatment: Path A uses vector similarity retrieval; Path B uses OKF concept navigation. Retrieval interactions and navigation steps are counted as part of each path’s cost. The study does not assume identical internal retrieval operations.

### **Repetitions and hardware**

Each package is run three times per path. Accuracy is summarized across runs and latency is reported as the median. All runs use the same machine. A warm-up run is discarded to reduce model-loading effects. Exact hardware (CPU, GPU, RAM) and software versions are recorded in the final report. If repeated runs are identical under fixed settings, this is reported rather than interpreted as independent variability.

### **Data sources**

Time, token counts, tool steps, cited clauses, and recommendation outputs are read from JSON audit records. Engineering hours are recorded in the sprint log.

## **6.3 Evaluation framework**

Five criteria address the three sub-questions. Criteria 1–4 compare retrieval paradigms for Sub-question 1; criterion 5 evaluates agent reliability and governance for Sub-question 2\.

| Criterion | What is measured | How it is measured | RQ |
| :---- | :---- | :---- | :---- |
| 1\. Field, rule, and evidence accuracy | Correctness of extracted values, calculations, cited clauses, and raised flags. | Exact Match (EM) per field and calculation against ground truth; clause citation counts as correct only when document and page match; precision, recall, and F1 for flags (price, quantity, surcharge, missing document) across packages. | 1 |
| 2\. Latency | Time for a complete verification. | Wall-clock time from run start to recommendation (median of three runs), plus agent/tool steps. Path B navigation time is included in its total; Path A index-search time is additionally reported. | 1 |
| 3\. Context-token efficiency | Input tokens processed by the model. | Total input tokens per verification and input tokens per correctly extracted field, as reported by Ollama. | 1 |
| 4\. Preparation and implementation effort | Work required to prepare each retrieval paradigm. | Engineering hours in the sprint log, build time, and storage size of the FAISS index and OKF bundle. | 1 |
| 5\. Agent reliability and governance | Validity and evidential completeness of recommendations and enforcement of manager approval. | Share of runs passing Pydantic validation; invalid tool-call rate; runs reaching the step limit without an answer; share of recommendations with complete evidence and correct clause citations; number of final decisions recorded without manager sign-off (expected: zero). | 2 |

## **6.4 Post-evaluation routing analysis (Sub-question 3\)**

Sub-question 3 is answered through a post-evaluation assignment recommendation, not by implementing a dynamic router. Results are grouped by source type: structured values from POs, goods receipts, and invoices, and unstructured clauses from MSAs. Criteria 1–3 are computed separately for these groups. A retrieval path is recommended for a document type when its accuracy (EM and flag F1, as applicable) is at least five percentage points higher than the other path. When the accuracy difference is smaller than five percentage points, the path with lower token use and latency is recommended. Preparation effort is reported as a trade-off rather than used as an accuracy tie-breaker. The resulting recommendation describes which retrieval paradigm appears better suited to each tested document type in this corpus.

## **6.5 Analysis procedure**

6. Run each package through both retrieval paradigms three times, after a discarded warm-up run.  
7. Use an evaluation script to read the audit records and ground-truth files and compute all measures.  
8. Report results per path, document type, and error type: means for accuracy and token use, medians for latency.  
9. Compare results package by package. Because the corpus is small, interpret results descriptively and do not claim statistical significance.  
10. Assign each incorrect result a cause (retrieval miss, wrong tool use, invalid output format, incorrect calculation, or wrong clause) to explain observed differences.  
11. Review audit records for flagged packages to confirm that calculations and cited clauses can be verified by a human reader.  
12. Test the approval gate by verifying that no final decision is written before the approval function is called.

## **6.6 Explicit system and pipeline limitations**

* Document formats: The pipeline targets standard commercial procurement documents (POs, delivery notes, commercial invoices, and MSAs) provided as digital PDFs or text files. Freeform correspondence and non-standard regional invoice formats outside predefined schemas are out of scope.  
* Scanned documents: Tesseract OCR is available as a fallback at approximately 300 DPI. The benchmark uses digital documents; OCR quality is not evaluated. Severely degraded or handwritten documents are excluded.  
* Local hardware and model: A small open-source model (≤ 2B parameters) served locally through Ollama constrains context capacity and multi-step reasoning. Incorrect tool calls or premature navigation stops are counted as errors.  
* Benchmark size and variety: The benchmark contains 20–30 packages generated from 1–2 seed templates. Layout variety is limited; findings describe this corpus and are not statistical evidence for other collections.  
* Configuration dependence: Results apply to Qwen3-1.7B, the selected embedding model, Path A settings (500-token chunks, 50-token overlap, top-5 retrieval), and the selected OKF bundle structure. Other configurations may produce different results.  
* Scope of OKF: OKF was designed for organizational knowledge about data and systems. Its use for procurement contracts is tested as a research hypothesis.  
* Domain schema: Validation covers three-way matching, price and quantity discrepancies, line-total calculations, and MSA surcharge checking. Tax-rule validation and multi-currency conversion are outside the current scope and reserved for future work.

## **References cited in Section 6**

Hevner, A. R., March, S. T., Park, J., & Ram, S. (2004). Design science in information systems research. MIS Quarterly, 28(1), 75–105.

Peffers, K., Tuunanen, T., Rothenberger, M. A., & Chatterjee, S. (2007). A design science research methodology for information systems research. Journal of Management Information Systems, 24(3), 45–77.

**7\. Data Collection & Benchmark Generation Methods (Allen Smith)**

Following the Design Science Research approach described by Hevner et al. (2004) and Peffers et al. (2007), this project combines the programmatic generation of a controlled experimental benchmark with secondary literature synthesis. The benchmark is designed to evaluate the performance of the two retrieval paths, Standard Vector RAG (Path A) and OKF v0.2 Concept Navigation (Path B), under the same experimental conditions.

**7.1 Primary Data Collection and Benchmark Generation**

The primary data consists of a benchmark of **20–30 procurement document packages**. Each package represents a supplier invoice verification scenario and contains a combination of purchase orders (POs), delivery notes, vendor invoices, and, where applicable, multi-page Master Service Agreements (MSAs).

The benchmark is generated programmatically using **1–2 seed templates**. These templates provide the initial document structures and content from which variations are created. The resulting dataset is designed to contain both compliant cases and cases with predefined discrepancies.

The benchmark generation process follows these steps:

1. **Seed Template Preparation:** Prepare 1–2 representative document templates covering the document types required for the project: purchase orders, delivery notes, vendor invoices, and MSAs. The templates provide the initial structure and relationships between documents.  
2. **Programmatic Dataset Expansion:** Use a Python script to generate 20–30 document packages by varying document identifiers, line items, quantities, unit prices, invoice totals, and relevant MSA terms. Each package represents a distinct test case.  
3. **Controlled Discrepancy Injection:** Introduce predefined discrepancies into selected packages while retaining compliant packages as reference cases. The discrepancy types reflect the validation scope established in Sections 1 and 5:  
   * **Compliant reference cases:** Invoice values and quantities match the purchase order and recorded goods receipt, and applicable MSA terms are respected.  
   * **Quantity variance cases:** The invoiced quantity differs from the quantity recorded on the delivery note.  
   * **Price variance cases:** The invoice unit price differs from the agreed PO price or applicable MSA rate.  
   * **Line-total variance cases:** The invoiced line total does not match the expected calculation based on quantity and unit price.  
   * **MSA surcharge compliance cases:** An invoice includes a surcharge that conflicts with the applicable MSA clause, or a surcharge is consistent with the specified contractual terms.  
   * **Missing-document cases:** A required document, such as a purchase order or delivery note, is absent from the package.  
4. **Ground-Truth Specification:** Create a structured ground-truth record for every benchmark package. This record contains the expected values and calculations, the injected discrepancy type (if any), the relevant source documents and page references, the applicable MSA clause where relevant, and the expected agent recommendation. The ground truth is established independently of the agent's output and serves as the reference for evaluation.  
5. **Benchmark Consistency:** Ensure that the same benchmark packages and extracted document content are used for both Path A and Path B. Each package is processed through both retrieval paths, enabling a controlled comparison under the same input conditions.

The benchmark focuses on price, quantity, line-total, and MSA surcharge verification. Tax validation and multi-currency conversion are excluded from the current evaluation scope.

**7.2 Document Preparation and Data Processing**

Before retrieval, the benchmark documents undergo the extraction process described in Section 5\. Digital documents are processed using PyMuPDF, while scanned documents may be handled through the Tesseract OCR fallback.

The benchmark evaluation uses digital documents so that OCR quality does not become an additional experimental variable. Extraction is performed once per package, and the resulting structured records and cleaned text are supplied to both retrieval paths.

Source document names and page references are retained to support evidence tracing and audit-log generation.

**7.3 Secondary Data Collection and Literature Synthesis**

Secondary data collection consists of reviewing the academic literature and technical documentation that inform the system's design and evaluation. These sources provide the theoretical and technical foundation for the research questions and experimental setup.

The literature synthesis covers:

* **Retrieval-Augmented Generation (RAG):** Lewis et al. (2020) provide the foundation for Path A, which retrieves relevant text chunks from a vector index to support the agent's responses.  
* **Dense Retrieval:** Karpukhin et al. (2020) support the use of dense passage retrieval, while Nussbaum et al. (2024) inform the embedding model selection.  
* **ReAct Agent Architecture:** Yao et al. (2023) provide the basis for the agent's iterative interaction with retrieval and deterministic calculation tools.  
* **Agentic Document Workflows:** Relevant literature and technical documentation inform the design of the document verification workflow and tool-use process.  
* **Open Knowledge Format (OKF v0.2):** Google Cloud (2026) provides the specification used to organize documents into Markdown concept files with YAML metadata and navigable links for Path B.

The reviewed literature supports the design decisions and interpretation of the experiment. The primary empirical results, however, are obtained from executing the system on the generated benchmark rather than from the literature review.

**7.4 Relationship to the Comparative Evaluation**

The benchmark provides a common basis for comparing Path A and Path B across the evaluation dimensions specified in Section 6, including discrepancy-detection performance, evidence quality, retrieval or navigation cost, and execution latency.

The structured ground-truth records enable the system's recommendations and supporting evidence to be checked against known expected results. The results are also analyzed by document type and discrepancy category to identify where each retrieval path performs more effectively.

Sub-question 3 is addressed **after the comparative evaluation** by deriving recommended retrieval-path assignments from the observed benchmark results. This analysis does not implement or evaluate a dynamic routing agent; it uses the experimental findings to propose which retrieval path may be more suitable for particular document or task characteristics.

The benchmark therefore serves as the shared experimental dataset for the comparative evaluation and the subsequent evidence-based routing recommendations.

## **8\. Justification of Research Methods & Data Collection Approach (Navya Gupta)**

The combination of Design Science Research, programmatic benchmark generation, and controlled comparative evaluation is justified by the project's objective of developing and empirically evaluating the Agent On Duty system. The methodological approach follows Hevner et al. (2004) and Peffers et al. (2007), which provide the foundation for constructing and evaluating an information systems artifact.

1. **Suitability of Programmatic Benchmark Generation:** The project requires a controlled dataset containing both compliant procurement document packages and predefined discrepancies. Programmatically generating 20–30 packages from 1–2 seed templates enables systematic variation of quantities, unit prices, line totals, and MSA surcharge conditions. Because the injected discrepancies are defined in advance, each package can be associated with a structured ground-truth record. This supports objective evaluation of the agent's recommendations and evidence without relying on manually labelled outputs. The benchmark's limited size and template variety are acknowledged as constraints on generalizability.

2. **Controlled Comparative Evaluation:** The research compares Standard Vector RAG (Path A) and OKF v0.2 Concept Navigation (Path B) using the same document packages and extraction output. The central agent, language model, prompts, deterministic tools, and run settings are held constant. This controlled setup allows observed differences in performance to be attributed primarily to the retrieval-path treatment, while recognizing that Path B's model-directed navigation is part of its retrieval process and contributes to its overall execution cost.

3. **Alignment Between Evaluation Metrics and Research Questions:** The evaluation criteria are selected to address the research questions established in Section 2\. Extraction and rule accuracy are measured using Exact Match, Precision, Recall, and F1. Efficiency is assessed through latency, agent steps, context-token consumption, and preparation effort. Agent reliability and governance are evaluated through schema-valid outputs, invalid tool calls, evidence completeness, cited-clause correctness, and adherence to the human approval gate. This combination assesses both the technical performance of the retrieval paths and the reliability of the overall verification workflow.

4. **Reproducibility and Auditability:** The standardized benchmark, fixed model and run configuration, repeated executions, and consistent hardware setup provide a reproducible basis for comparing the two retrieval paths. The system's JSON audit records capture relevant execution data, including tool calls, cited evidence, token counts, and timing. This enables results to be traced to individual benchmark packages and supports verification of the reported metrics.

5. **Scope and Interpretation of Results:** The method is designed to evaluate the proposed system under a defined local configuration rather than to establish universal superiority of one retrieval paradigm. Findings are interpreted within the limits of the benchmark size, seed-template variety, selected language model, and implementation settings. The results also provide the empirical basis for the post-evaluation retrieval-path recommendations in Sub-question 3; they do not constitute an evaluation of a dynamic routing agent.

#### ***9\.*****Research Schedule & Gantt Chart Lifecycle (Allen Smith)** ***Detailed Milestone & Sprint Breakdown***

* **Stage 1: Proposal Finalization & Submission** *(Oct 9 – Nov 3, 2026\)*   
  * **Tasks**: Complete problem definition, research questions, theoretical framework, system architecture, and methodology.  
  * **Key Milestone**: **Proposal / Exposé Final Submission** on **Tuesday, November 3, 2026**.  
* **Sprint 1: Environment Setup, Seed Curation & Ingestion Layer** *(Nov 4 – Nov 17, 2026 / 2 Weeks)*   
  * **Tasks**:   
    * Set up local **Ollama** model serving (Qwen3-1.7B / 4-bit GGUF).  
    * Curate 1–2 real-world seed document templates and build dataset\_generator.py to create the 20–30 document benchmark set with ground-truth JSON files.  
    * Build the raw text extraction layer (PyMuPDF).  
* **Sprint 2: Dual Retrieval Pipelines (Path A & Path B)** *(Nov 18 – Dec 1, 2026 / 2 Weeks)*   
  * **Tasks**:   
    * **Path A**: Implement fixed 500-token sliding window chunking, nomic-embed-text embeddings, and FAISS vector indexing.  
    * **Path B**: Build okf\_bundle\_converter.py to transform documents into Markdown concept bundles, YAML frontmatter, index.md progressive disclosure trees, and Markdown graph links.  
* **Sprint 3: ReAct Agent Loop, Action Harness & HITL Gate** *(Dec 2 – Dec 15, 2026 / 2 Weeks)*   
  * **Tasks**:   
    * Develop the ReAct reasoning loop in Python with Pydantic tool schemas for deterministic numerical checks (price, quantity, line total).  
    * Implement local SQLite database action writers (APPROVED, REJECTED, FLAGGED\_\*) and JSON audit log generation.  
    * Program the mandatory **Human-in-the-Loop (HITL) Interrupt Gate** to pause execution at PENDING\_REVIEW.  
* **Sprint 4A: Web UI & Pre-Holiday Integration** *(Dec 16 – Dec 22, 2026 / 1 Week)*   
  * **Tasks**:   
    * Develop the Streamlit web app: package upload view, live ReAct trace visualizer, and manager approval dashboard.  
    * Conduct initial integration sanity checks across tools and UI screens prior to the holiday pause.  
* **❄️ University Winter Holiday Pause** *(Dec 23, 2026 – Jan 7, 2027 / 2.5 Weeks)*   
  * **Status**: Official university holiday. Development is paused.  
* **Sprint 4B & 5: System Integration & Empirical Benchmarking** *(Jan 8 – Jan 15, 2027 / \~1.2 Weeks)*   
  * **Tasks**:   
    * Resume active development; complete full system integration across extraction, retrieval paths, ReAct engine, and UI.  
    * Execute the controlled experimental evaluation across all 20–30 benchmark packages (3 runs per package per path).  
    * Compute quantitative metrics: Exact Match (EM), F1-score, wall-clock latency, context token efficiency, and schema validation reliability.  
    * Formulate post-evaluation retrieval path recommendations (Sub-question 3).  
* **Sprint 6: Final Documentation, Poster & Live Demo** *(Jan 16 – Jan 22, 2027 / 1 Week)*   
  * **Tasks**:   
    * Finalize Chapters 1–6 of the comprehensive APMG research report.  
    * Design the scientific project poster.  
    * Package the local codebase and prepare the live software demonstration.  
    * **Key Milestone**: **Final Project Submission & Live Presentation** on **Friday, January 22, 2027**.

