# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

<!-- What topic or category of knowledge does your system cover?
     Why is this knowledge valuable, and why is it hard to find through official channels?
     Example: "Student reviews of CS professors at [university] — useful because official
     course descriptions don't reflect teaching style, exam difficulty, or workload." -->
The domain that I chose is off-campus housing near Santa Clara University (SCU). This knowledge is valuable for students who are unfamiliar with finding rental apartments and local leases. It is hard to find because the information is highly scattered and not available on a single centralized platform. It takes a significant amount of research to know where to find potential subleasing locations, avoid bad landlords, and understand rental agreements. A centralized guide will drastically reduce the research burden for students navigating the local housing market.

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | SCU Off-Campus Housing Information | Official website containing information and resources on finding apartments for SCU students from the Off-Campus living office. | https://www.scu.edu/ocl/off-campus-housing/ |
| 2 | Off-Campus Landlord Contacts | A PDF containing contact information for landlords and property managers associated with SCU off-campus housing. | https://www.scu.edu/media/offices/dean-of-students-office/off-campus-living/Off-Campus-Landlord-Contacts-4.pdf |
| 3 | Local Apartment Listings | A spreadsheet containing a list of apartments, distance to campus, and rent information for students. | ai201-project1-unofficial-guide-starter/data/Local-Apartment-Listings---Santa-Clara-County.xlsx |
| 4 | Rental Listings Portal | A website where students can find places to rent or look for subleasers. | data/scu_portal_listings.txt |
| 5 | Roommate Finder Responses | A spreadsheet of responses from the roommate finder Google form where students share their contact and budget info. | data/2026-2027 Roommate Finder Results (Responses).xlsx |
| 6 | Sublease Listing Responses | A spreadsheet of responses from the Google form where students submit the spaces they are subleasing. | ai201-project1-unofficial-guide-starter/data/Sublease Listing & Connection Form (Responses).xlsx |
| 7 | Student Sublet | A website dedicated to helping students find places to rent or sublease near their selected university. | https://www.studentsublet.app/ |
| 8 | Apartments.com | A third-party real estate website showing a list of commercial apartments currently available for rent in Santa Clara. | ai201-project1-unofficial-guide-starter/data/apartments_com_listings.txt |
| 9 | Reddit Off-Campus Housing | A Reddit discussion thread meant for students to share off-campus apartment recommendations and landlord warnings. | https://www.reddit.com/r/SCU/comments/ca39x3/offcampus_apartment_recommendation/ |
| 10 | SCU Facebook Housing Group | A private Facebook group where students post spaces they are subleasing and find potential roommates. | ai201-project1-unofficial-guide-starter/data/facebook_housing_posts.txt |
---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:** 230 tokens

**Overlap:** 20 tokens

**Why these choices fit your documents:**

The all-MiniLM-L6-v2 embedding model has a hard maximum sequence length of 256 tokens. A chunk size of 230 tokens with a 20-token overlap means the maximum possible chunk (230 + 20 = 250 tokens) stays safely under that limit, preventing any content from being silently truncated during embedding. A hybrid chunking approach was used based on document format. For unstructured text (HTML, PDF, Reddit threads, Facebook posts, and portal listings), a token-aware RecursiveCharacterTextSplitter was used — it tries to preserve paragraph and sentence boundaries before falling back to word-level splits. For structured spreadsheets (.xlsx), each non-empty row is serialized as a single chunk in `Col: value | ...` format, keeping all details for a single apartment or roommate in one unit. Oversized rows are recursively split using the same splitter. Additionally, for the SCU portal listings, fields are reordered before chunking so short, high-signal fields (Address, Rules, Lease Term) appear before the long Description, ensuring those key fields always fall within the model's context window.

**Final chunk count:** 119

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers`

**Production tradeoff reflection:**
While `all-MiniLM-L6-v2` might have slightly lower accuracy on complex semantic nuances compared to massive, paid API models like OpenAI's `text-embedding-3-large`, it is the best choice for this project. It runs locally, has zero API costs, and offers extremely low latency. If cost were not a constraint, I might switch to a larger model with a longer context window to better understand complex Reddit threads, but for a localized guide, the speed and cost-effectiveness of MiniLM are ideal.

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**

The following system prompt is passed to the Groq LLM (`llama-3.3-70b-versatile`) on every request in `generator.py`:

> "You are a helpful assistant for Santa Clara University students. Answer the user's question using ONLY the provided context. If the context does not contain the answer, reply exactly with: 'I do not have enough information to answer that based on the provided documents.' Do not use outside knowledge."

The retrieved chunks are formatted as a numbered list (`[1] ...`, `[2] ...`, etc.) and prepended to the user's question as a `Context:` block. The model is never given any instruction to name or cite sources — it is only asked to produce a prose answer from the numbered context. Temperature is set to 0.2 to reduce hallucinations and keep responses factual.

**How source attribution is surfaced in the response:**

Source attribution is handled entirely in Python by `format_sources()` in `generator.py`, which reads the `source` field directly from the ChromaDB metadata dicts returned by the retrieval step. The LLM never touches this data. Because the source list is assembled from database records written during `embed_and_store.py`'s upsert, it is structurally impossible for the model to introduce a fabricated citation. Sources are deduplicated, sorted by retrieval rank, and displayed in the Gradio UI as a `### Sources Retrieved` markdown block with each source's cosine similarity score so the user can judge relevance at a glance.

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | Who can I contact at SCU to seek advice on off-campus housing? | offcampusliving@scu.edu | offcampusliving@scu.edu or by calling 408-551-3665. | Relevant | Accurate |
| 2 | What are some local apartments that are closest to SCU? | Domicilio Apts, The Benton, Park Central Apts, Normandy Park Apts, Timberleaf Apts | 1. 655 Washington St, Santa Clara 95050 - 0.069 miles from SCU, $1500/mo for a 1-bedroom (single) available.
2. 860 Washington St, Santa Clara 95050 - 0.077 miles from SCU, $2000/mo for a large single in a house.
3. Domicilio - exact distance not specified, but mentioned as a convenient location, with a price over $2.5k/mo.
4. The Villas - exact distance not specified, but mentioned as a decent option for juniors and seniors, with a single room available for a comparable price to on-campus housing.
5. The Grad San Jose - 4.0 miles from SCU, contact for pricing.
 | Relevant | Partially accurate |
| 3 | What apartment complex on El Camino Real is closest to SCU? | Domicilio Apts (0.2 miles) | Domicilio Apts, with an address of 431 El Camino Real, Santa Clara, CA 95050, and a distance of 0.2 miles (or 0.057 miles as mentioned in another source) from SCU, and also Villas on the Blvd is 3.2 miles from SCU, and The Deck is not specified but the address is 3406 El Camino Real. However, Domicilio Apts is the closest. | Relevant | Partially Accurate 
| 4 | How far in advance does SCU recommend starting your housing search? | 9-14 months| 9-14 months | Relevant | Accurate |
| 5 | What summer subleases are listed near SCU campus? | 655 Washington St, 820 Panelli Pl, 1153 Lafayette St | 1. A fully furnished single bedroom, 2 blocks from campus, available from September 1, 2026, to December 31, 2026.
2. A large single bedroom in a 2-story house, 1 block from SCU campus, available from July 1, 2026, to June 30, 2027.
3. A summer sublease at 1153 Lafayette St, 0.12 miles from SCU, available from July 13, 2026, to September 13, 2026, for $1300/mo.
4. Additional options are listed on the Student Sublet platform, including:
   - A private room near University Ave, 0.4 mi from SCU, for $1,150/mo.
   - A studio in Midtown, near campus, for $1,400/mo.
   - A shared room near Campus Edge, 0.1 mi from SJSU (not SCU, but nearby), for $950/mo. | Partially relevant | Partially accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:** What is the email address at HOB Management?

**What the system returned:** I do not have enough information to answer that based on the provided documents.

**Root cause (tied to a specific pipeline stage):** The root cause is in the retrieval stage where `TOP_K` is set to 5 in `generator.py`. After investigating, the PDF chunk containing HOB Management's contact information ranks 13th by cosine similarity for this query — it is diluted by other landlord entries and apartment listings that score higher. With only 5 chunks retrieved, the relevant chunk never enters the context window passed to the LLM, so the model correctly reports it cannot answer.

**What you would change to fix it:**
To fix it, I would increase `TOP_K` to around 15 so that the HOB Management chunk falls within the retrieval window and is included in the context passed to the LLM.

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**
The spec helped me gain a bigger picture of the overall RAG pipeline and clarified exactly which requirements each stage needed to satisfy. Having the chunking strategy, retrieval approach, and evaluation plan written out in advance gave me concrete targets to verify against at each milestone — for example, I could directly compare the actual chunk count and retrieval results against the expected answers in the Evaluation Plan table.

**One way your implementation diverged from the spec, and why:**
The planning.md specified a chunk size of 500 tokens with 50 tokens of overlap, but the implementation uses 230 tokens with 20 tokens of overlap. This change was necessary because the all-MiniLM-L6-v2 embedding model has a hard 256-token maximum sequence length. Using 500-token chunks would silently truncate every chunk during encoding, destroying retrieval quality. Reducing to 230 tokens (with a maximum of 250 when overlap is added) keeps every chunk safely within the model's context window.
---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:* I gave Claude my Chunking Strategy section from planning.md, which specified a chunk size of 500 tokens and 50-token overlap using a RecursiveCharacterTextSplitter for unstructured text and a row-by-row parser for spreadsheets.
- *What it produced:* It produced `ingest.py`, implementing `_recursive_split()` for text sources and `_chunk_excel()` for Excel files, matching the hybrid strategy from the spec.
- *What I changed or overrode:* I reduced the chunk size from 500 to 230 tokens and the overlap from 50 to 20 tokens, because the all-MiniLM-L6-v2 model has a 256-token maximum sequence length. At 500 tokens, every chunk would have been silently truncated during embedding. I also added field reordering logic for the SCU portal listings so that short, high-signal fields (Address, Rules, Lease Term) are embedded before the longer Description field.

**Instance 2**

- *What I gave the AI:* I gave Claude the Retrieval Approach section from planning.md and the pipeline architecture diagram, asking it to implement the embedding and vector store stage using sentence-transformers and ChromaDB.
- *What it produced:* It produced `embed_and_store.py`, which loads all-MiniLM-L6-v2, upserts embeddings into a persistent ChromaDB collection using cosine similarity, and runs the 5 evaluation queries from planning.md to verify retrieval quality.
- *What I changed or overrode:* I updated the 5 evaluation queries in the `EVAL_QUERIES` list to exactly match the wording in planning.md's Evaluation Plan table, since the AI had paraphrased them slightly differently from what I had written.
