# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->
The domain that I chose is off-campus housing near Santa Clara University (SCU). This knowledge is valuable for students who are unfamiliar with finding rental apartments and local leases. It is hard to find because the information is highly scattered and not available on a single centralized platform. It takes a significant amount of research to know where to find potential subleasing locations, avoid bad landlords, and understand rental agreements. A centralized guide will drastically reduce the research burden for students navigating the local housing market.
---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | SCU Off-Campus Housing Information | Official website containing information and resources on finding apartments for SCU students from the Off-Campus living office. | https://www.scu.edu/ocl/off-campus-housing/ |
| 2 | Off-Campus Landlord Contacts | A PDF containing contact information for landlords and property managers associated with SCU off-campus housing. | https://www.scu.edu/media/offices/dean-of-students-office/off-campus-living/Off-Campus-Landlord-Contacts-4.pdf |
| 3 | Local Apartment Listings | A spreadsheet containing a list of apartments, distance to campus, and rent information for students. | `Local File: Local-Apartment-Listings.xlsx` [Requires SCU Login] |
| 4 | Rental Listings Portal | A website where students can find places to rent or look for subleasers. | https://www.scu.edu/apps/org/osl/housing/?&rent_max=3000&dt_avail=2026-6-30 |
| 5 | Roommate Finder Responses | A spreadsheet of responses from the roommate finder Google form where students share their contact and budget info. |https://docs.google.com/spreadsheets/d/18ePZsGSRrtJFdiauEeciIowmljPT7i0VEtk6Mzqpfqk/edit?usp=sharing |
| 6 | Sublease Listing Responses | A spreadsheet of responses from the Google form where students submit the spaces they are subleasing. | https://docs.google.com/spreadsheets/d/1ZfW5om36RmOGwKv63ySEm-hbeEzTMKJuZkmlNeuNGdg/edit?gid=1417528019#gid=1417528019 |
| 7 | Student Sublet | A website dedicated to helping students find places to rent or sublease near their selected university. | https://www.studentsublet.app/ |
| 8 | Apartments.com | A third-party real estate website showing a list of commercial apartments currently available for rent in Santa Clara. | https://www.apartments.com/santa-clara-ca/ |
| 9 | Reddit Off-Campus Housing | A Reddit discussion thread meant for students to share off-campus apartment recommendations and landlord warnings. | https://www.reddit.com/r/SCU/comments/ca39x3/offcampus_apartment_recommendation/ |
| 10 | SCU Facebook Housing Group | A private Facebook group where students post spaces they are subleasing and find potential roommates. | https://www.facebook.com/groups/308542176473013/ |
---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:** 500 tokens

**Overlap:** 50 tokens

**Reasoning:**

I will use a hybrid approach based on the document format. For unstructured text like the PDFs and Reddit/Facebook discussion forums, I will use a Recursive Character Text Splitter to ensure that paragraphs and conversational contexts stay together. For the structured data (like the Local Apartment Listing spreadsheets), I will chunk row-by-row so that all the details (price, distance, amenities) for a single apartment are kept in one single chunk.
---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:** `all-MiniLM-L6-v2` via `sentence-transformers`

**Top-k:** 5

**Production tradeoff reflection:**
While `all-MiniLM-L6-v2` might have slightly lower accuracy on complex semantic nuances compared to massive, paid API models like OpenAI's `text-embedding-3-large`, it is the best choice for this project. It runs locally, has zero API costs, and offers extremely low latency. If cost were not a constraint, I might switch to a larger model with a longer context window to better understand complex Reddit threads, but for a localized guide, the speed and cost-effectiveness of MiniLM are ideal.
---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | Who can I contact at SCU to seek advice on off-campus housing| offcampusliving@scu.edu |
| 2 | What are some local apartments that are closest to SCU? | Domicilio Apts, The Benton, Park Central Apts, Normandy Park Apts, Timberleaf Apts |
| 3 | What is the email address at HOB Management | Houseonbellomy@gmail.com |
| 4 | When should I start searching for a house or apartment? | 9-14 months |
| 5 | Where can I find the official SCU Facebook group to look for a sublease? | Santa Clara University (SCU) Housing, Sublets & Roommates (Link: https://www.facebook.com/groups/308542176473013/) |
---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1. **Dynamic and Outdated Data:** Information like sublease availability or rent prices on Apartments.com and Facebook changes constantly. The AI might retrieve a chunk stating an apartment is $1,200/month, but that data could already be months old.

2. **Inconsistent Formatting in Forums:** The discussion forums (Reddit/Facebook) often feature slang, abbreviations (like "lf roommate"), or unstructured venting, which might be retrieved out of context or confuse the generation model.
---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->
[Documents (PDFs/URLs)] 
       ↓ 
[Chunking (RecursiveTextSplitter)] 
       ↓ 
[Embedding (all-MiniLM-L6-v2) -> Vector Store] 
       ↓ 
[Retrieval (Top-K=5)] 
       ↓ 
[Generation (LLM Context Prompt)] -> User Answer


---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->
* **Document Ingestion & Chunking:** I will use **Claude Code** (Anthropic's agentic CLI tool). I will initialize it in my project repository and provide it with my *Chunking Strategy* section. I will instruct it to write a Python script using LangChain's `RecursiveCharacterTextSplitter` (size=500, overlap=50) for the text files and a custom CSV row parser for the spreadsheets. Because Claude Code can run commands autonomously, I will ask it to execute the script and verify the output by checking the first 3 chunks.
* **Embedding & Vector Store:** I will prompt Claude Code with my *Retrieval Approach* section. I will instruct it to initialize the `sentence-transformers/all-MiniLM-L6-v2` model, generate embeddings for the chunks, and store them in a local ChromaDB instance. I will verify success by having Claude Code run a test retrieval script to ensure it returns exactly 5 chunks.
* **Generation & Evaluation:** I will use Claude Code to build the final RAG chain that passes the retrieved context to an LLM. I will provide Claude Code with my *Evaluation Plan* table and instruct it to write an automated test script (`test_rag.py`). I will verify the pipeline works by having Claude Code run the tests and confirm the generated answers match my expected answers.

**Milestone 3 — Ingestion and chunking:**

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
