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
| 1 | Who can I contact at SCU to seek advice on off-campus housing? | offcampusliving@scu.edu |
| 2 | What are some local apartments that are closest to SCU? | Domicilio Apts, The Benton, Park Central Apts, Normandy Park Apts, Timberleaf Apts |
| 3 | What apartment complex on El Camino Real is closest to SCU? | Domicilio Apts (0.2 miles) |
| 4 | How far in advance does SCU recommend starting your housing search? | 9-14 months |
| 5 | What summer subleases are listed near SCU campus? | 655 Washington St, 820 Panelli Pl, 1153 Lafayette St |
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

After generating the ingestion and chunking code, it created a total of 93 chunks.

[OK]      Source 1: SCU Off-Campus Housing Information -> 1 text chunks
[OK]      Source 2: Off-Campus Landlord Contacts (PDF) -> 1 text chunks
[OK]      Source 3: Local Apartment Listings (local file) -> 34 row chunks
[OK]      Source 4: Rental Listings Portal -> 10 text chunks
[OK]      Source 5: Roommate Finder Responses -> 7 row chunks
[OK]      Source 6: Sublease Listing Responses -> 13 row chunks
[OK]      Source 7: Student Sublet -> 1 text chunks
[OK]      Source 8: Apartments.com – Santa Clara -> 18 text chunks
[OK]      Source 9: Reddit – SCU Off-Campus Apartment Recommendation -> 2 text chunks
[OK]      Source 10: SCU Facebook Housing Group -> 6 text chunks

Total chunks: 93

Source                                         Chunks  Type
--------------------------------------------------------------
SCU Off-Campus Housing Information                  1  text
Off-Campus Landlord Contacts (PDF)                  1  text
Local Apartment Listings (local file)              34  spreadsheet
Rental Listings Portal                             10  text
Roommate Finder Responses                           7  spreadsheet
Sublease Listing Responses                         13  spreadsheet
Student Sublet                                      1  text
Apartments.com – Santa Clara                       18  text
Reddit – SCU Off-Campus Apartment Recommendation       2  text
SCU Facebook Housing Group                          6  text

-- 5 Random Chunks (quality check) -----------------------------------

[chunk_id=17 | tokens=134 | type=spreadsheet | OK]
source: Local Apartment Listings (local file)
Apartment Name: Old Orchard Apts | Address: 2200 Monroe St., Santa Clara, CA 95050 | Distance from SCU: 2.4 miles | Website: https://www.theoldorchardapts.com/ | Monthly Rent: Contact for pricing | Security Deposit: Contact for details | Application Fee: Not listed | Move-In Fees: Not listed | Background Check Fee: Not listed | Parking: Not listed | Pet Policy: Pets allowed (deposit required) | Cosigner / Guarantor: Not listed | Lease Length Options: Contact for lease terms | Utilities Included: ELECTRIC VEHICLE STATIONS Charge your EV while you sleep
----------------------------------------------------------------------

[chunk_id=81 | tokens=70 | type=text | OK]
source: Apartments.com – Santa Clara
Summerwood Apartments
Address: 444 Saratoga Ave, Santa Clara, CA 95050
Pricing: 1 Bed: $3,200+ | 2 Beds: $3,615+
Amenities: Pets Allowed, Fitness Center, Pool, Dishwasher, Kitchen, In Unit Washer & Dryer
Contact: (669) 201-8578
----------------------------------------------------------------------

[chunk_id=42 | tokens=254 | type=text | OK]
source: Rental Listings Portal
Title: $1300/mo - SUMMER SUBLEASE - 1153 Lafayette St.
Type: House - Share (renting a room or part of a unit)
Address: 1153 Lafayette Street, Santa Clara 95053
Configuration: 1 bedroom | 1.5 bath | Up to 1 person
Description: Looking for a summer subletter to share a double bedroom in 1153 Lafayette Street from July to September. About the House: - 3 bed / 1.5 bath home - Bright living spaces + full kitchen - Large backyard and patio - In-unit laundry and street parking available The Room: - Shared bedroom with one other female - Fully furnished Housemates: - 3 other females (college students / young professionals) - Friendly, clean, and social but respectful of space Location Perks: - Walking distance to Santa Clara University - Easy access to Caltrain, grocery stores, and restaurants
Availability: July 13, 2026 until September 13, 2026
Distance from SCU: 0.12 miles
Lease Term: Summer Quarter
Rules: Utilities Included: No | Smoking Allowed: No | Pets Allowed: No | Accessible: No
Parking: Street Parking
Contact: Jane Doe | Phone: 555-010-0001 | Email: user1@example.com
----------------------------------------------------------------------

[chunk_id=49 | tokens=226 | type=spreadsheet | OK]
source: Roommate Finder Responses
Timestamp: 2026-06-01 10:56:11.160000 | Email Address: user1@example.com | Name:: Jane Doe | SCU Email:: user1@example.com | Phone Number (Optional):: 5550100001.0 | Preferred Contact:: Text | Academic Standing for 2026-2027:: Junior | Please indicate if any apply to you:: Transfer Student | Roommate Gender Preference:: Gender-Inclusive | What best describes your current housing situation?: I need both housing and roommates | Please provide a description of what you are looking for (i.e. Lease start/end dates, preferred monthly rent, single or shared room request, any other details).: Hello, my name is Matilde and I am transferring to Santa Clara for the fall term 2026. I am moving in late August and I am looking for a private room or roommates  to share a place with. My budget is approximately $1000. (I don’t have a scu email yet!)
----------------------------------------------------------------------

[chunk_id=86 | tokens=291 | type=text | OK]
source: Reddit – SCU Off-Campus Apartment Recommendation
[COMMENT] There are a few places on homestead before San Tomas. I’m my time living in SC and moving to keep with the cheaper side of renting (because a shared room is something I would never do) Zillow has always had good leads, however on a day off, I would suggest driving around time (or walking close to the university) and calling the numbers posted with an apartment for rent. However, rent is outrageous now. Average studio is about $1,600/$1,800 but you can find something not too super fancy for mayyyyyyyyybe $1,200. But even shared rooms are going for about $1,000. I live next to the Pruneyard in Campbell and I’m paying $2,500 just for rent.
[COMMENT] Insanely expensive around campus. Watch out for scammers. New housing options are around the corner in about 6 months. Late winter 2020/spring 2020. I know, doesn't help for incoming new students. There will be tons of housing in San Jose proper on Coleman Ave. There is a tunnel that runs under the tracks. You'll be in a little competition with the new Google employees coming to town but these will loosen the availability of units in the surrounding area. Hopefully a price drop. Sub $2000 for a 1br. Sub $2500 for 2br. Gets worse form there.
----------------------------------------------------------------------

**Milestone 4 — Embedding and retrieval:**
── Step 1: Load and chunk all sources ───────────────────────────────────

[OK]      Source 1: SCU Off-Campus Housing Information -> 2 text chunks
[OK]      Source 2: Off-Campus Landlord Contacts (PDF) -> 2 text chunks
[OK]      Source 3: Local Apartment Listings (local file) -> 34 row chunks
[OK]      Source 4: Rental Listings Portal -> 13 text chunks
[OK]      Source 5: Roommate Finder Responses -> 9 row chunks
[OK]      Source 6: Sublease Listing Responses -> 26 row chunks
[OK]      Source 7: Student Sublet -> 2 text chunks
[OK]      Source 8: Apartments.com – Santa Clara -> 18 text chunks
[OK]      Source 9: Reddit – SCU Off-Campus Apartment Recommendation -> 4 text chunks
[OK]      Source 10: SCU Facebook Housing Group -> 9 text chunks

Total chunks loaded: 119

── Step 2: Initialise ChromaDB and embedding model ──────────────────────

Loading embedding model: sentence-transformers/all-MiniLM-L6-v2

ChromaDB path : C:\Users\School\Projects\CodePath\AI201\ai201-project1-unofficial-guide-starter\chroma_db
Collection    : scu_housing
Chunks on disk: 119

── Step 3: Embed and ingest into ChromaDB ───────────────────────────────

Collection already contains 119 chunks — skipping ingestion.
── Step 4: Retrieval quality test — 5 evaluation queries ────────────────

These queries come from the planning.md Evaluation Plan table.
Inspect each result set: do the top chunks contain the expected answer?
Scoring: similarity (higher=better) | distance=1-similarity (lower=better, <0.50 passes checkpoint)

========================================================================
QUERY: Who can I contact at SCU to seek advice on off-campus housing?
========================================================================
  Rank 1  |  similarity=0.8071  distance=0.1929  ✓  |  chunk_id=0  |  type=text
  Source: SCU Off-Campus Housing Information
  ────────────────────────────────────────────────────────────────────
  Student demand for housing within 5 miles of campus is continually
  increasing
  We highly recommend starting your housing search 9-14 months in
  advance of your desired move-in date, BUT if you start later than
  that, we can help Get Support & Resources: We offer compiled
  resources for undergraduate and graduate students seeking
  off-campus housing
  For more assistance, you can reach out to our office: Email:
  offcampusliving@scu.edu Call: 408-551-3665 Undergraduate options
  Graduate/Law Options Non-affiliated Off Campus Housing Resources
  References to any person, organization, or services related to
  such person or organization, or any linkages from this web site to
  the web site of another party, do not constitute or imply the
  endorsement, recommendation, or favoring of such
  SCU does not manage, oversee, or vet any postings on the
  non-affiliated Facebook page nor do they oversee any local
  landlords or property management companies
  We recommend individuals look through our "Resources" page as they
  are exploring any housing options found in rental listings

  Rank 2  |  similarity=0.6487  distance=0.3513  ✓  |  chunk_id=1  |  type=text
  Source: SCU Off-Campus Housing Information
  ────────────────────────────────────────────────────────────────────
  Rental Listings Local Apartment Listings Off Campus
  Landlord/Property Management List SCU Owned Off Campus Housing
  Non-affiliated Off Campus Housing Resources Subleasing and
  Roommate Resources Sublease Finder & Connection Form Sublease
  Finder & Connection Results Roommate Finder Form Roommate Finder
  Results

  Rank 3  |  similarity=0.6254  distance=0.3746  ✓  |  chunk_id=56  |  type=spreadsheet
  Source: Roommate Finder Responses
  ────────────────────────────────────────────────────────────────────
  Timestamp: 2026-06-01 11:35:15.260000 | Email Address:
  [REDACTED] | Name:: [REDACTED] | SCU Email:: [REDACTED] |
  Phone Number (Optional):: [REDACTED] | Preferred Contact:: Text
  | Academic Standing for 2026-2027:: Junior | Please indicate if
  any apply to you:: Transfer Student | Roommate Gender Preference::
  Female | What best describes your current housing situation?: I
  need both housing and roommates | Please provide a description of
  what you are looking for (i.e. Lease start/end dates, preferred
  monthly rent, single or shared room request, any other details).:
  Single, starting in September until July or even just looking for
  roommates

  Rank 4  |  similarity=0.6158  distance=0.3842  ✓  |  chunk_id=57  |  type=spreadsheet
  Source: Roommate Finder Responses
  ────────────────────────────────────────────────────────────────────
  Timestamp: 2026-06-04 00:02:43.207000 | Email Address:
  [REDACTED] | Name:: [REDACTED] | SCU Email::
  [REDACTED] | Phone Number (Optional):: [REDACTED] |
  Preferred Contact:: Email, Text, Call | Academic Standing for
  2026-2027:: Junior | Please indicate if any apply to you::
  Transfer Student | Roommate Gender Preference:: Male | What best
  describes your current housing situation?: I need both housing and
  roommates | Please provide a description of what you are looking
  for (i.e
  Lease start/end dates, preferred monthly rent, single or shared
  room request, any other details).: Looking for one roommate for a
  2 bed / 2 bath apartment, preferably at The Benton or a similar
  apartment complex within walking distance to campus
  I would prefer a private bedroom and private bathroom setup

  Rank 5  |  similarity=0.5938  distance=0.4062  ✓  |  chunk_id=51  |  type=spreadsheet
  Source: Roommate Finder Responses
  ────────────────────────────────────────────────────────────────────
  Timestamp: 2026-04-21 22:10:28.298000 | Email Address:
  [REDACTED] | Name:: [REDACTED] | SCU Email:: [REDACTED] |
  Phone Number (Optional):: [REDACTED] | Preferred Contact:: Text
  | Academic Standing for 2026-2027:: Senior | Roommate Gender
  Preference:: Male | What best describes your current housing
  situation?: I already have housing and am looking for roommates |
  Please provide a description of what you are looking for (i.e.
  Lease start/end dates, preferred monthly rent, single or shared
  room request, any other details).: I have signed a lease for a
  great house 3 blocks away from the business school with 3 other
  guys (excluding myself), and am looking for a roommate. Full
  bathroom connected directly to our room. The cost is $1149 per
  month. If you would like more info, including pics, address, or
  more specifics, message me


========================================================================
QUERY: What are some local apartments that are closest to SCU?
========================================================================
  Rank 1  |  similarity=0.6211  distance=0.3789  ✓  |  chunk_id=106  |  type=text
  Source: Reddit – SCU Off-Campus Apartment Recommendation
  ────────────────────────────────────────────────────────────────────
  [POST] Off-campus apartment recommendation?
  For students, faculty, alumni, or members associated with the
  Santa Clara University.
  [COMMENT] For students, faculty, alumni, or members associated
  with the Santa Clara University.
  [COMMENT] I'm transferring to SCU this fall and want to live
  off-campus so I don't have to share a room with some other person
  (I'm a sophomore transfer). What're some apartments with
  convenient location that you guys recommend?
  [COMMENT] Domicilio is expensive but fancy if you can swing >
  2.5k/mo.
  [COMMENT] If you're a sophomore > to junior transfer, Villas
  aren't a bad spot. You can get a single (Where you room the place
  with someone else, but have your own room) for a decent price that
  is comparable to more expensive on campus housing. But that's only
  for juniors/seniors. Single spots around the area are hard to come
  by though. Even in houses off campus, people are usually sharing
  rooms.
  [COMMENT] I’d second this. The villas are pretty good as housing
  goes.

  Rank 2  |  similarity=0.6003  distance=0.3997  ✓  |  chunk_id=0  |  type=text
  Source: SCU Off-Campus Housing Information
  ────────────────────────────────────────────────────────────────────
  Student demand for housing within 5 miles of campus is continually
  increasing
  We highly recommend starting your housing search 9-14 months in
  advance of your desired move-in date, BUT if you start later than
  that, we can help Get Support & Resources: We offer compiled
  resources for undergraduate and graduate students seeking
  off-campus housing
  For more assistance, you can reach out to our office: Email:
  offcampusliving@scu.edu Call: 408-551-3665 Undergraduate options
  Graduate/Law Options Non-affiliated Off Campus Housing Resources
  References to any person, organization, or services related to
  such person or organization, or any linkages from this web site to
  the web site of another party, do not constitute or imply the
  endorsement, recommendation, or favoring of such
  SCU does not manage, oversee, or vet any postings on the
  non-affiliated Facebook page nor do they oversee any local
  landlords or property management companies
  We recommend individuals look through our "Resources" page as they
  are exploring any housing options found in rental listings

  Rank 3  |  similarity=0.5833  distance=0.4167  ✓  |  chunk_id=41  |  type=text
  Source: Rental Listings Portal
  ────────────────────────────────────────────────────────────────────
  Title: $1500/mo - 1 Bedroom (Single) available (Summer and Fall
  2026)
  Address: 655 Washington St, Santa Clara 95050
  Distance from SCU: 0.069 miles
  Lease Term: Summer and Fall Quarter
  Rules: Utilities Included: No | Smoking Allowed: No | Pets
  Allowed: No | Accessible: No
  Contact: Maria Zeiter | Phone: 2099810917 | Email: mzeiter@scu.edu
  Type: House - Share (renting a room or part of a unit)
  Configuration: 1 bed available / 4 total | 3 bath | Up to 1 person
  Availability: July 01, 2026 until January 01, 2027
  Description: I am looking for a subleaser for my room in spacious
  4-bedroom, 3 bath house just 1 block from Santa Clara University
  from July 1, 2026 through January 1, 2027. Rent is $1,500/month.
  The house is shared with other students and is in a convenient
  location near SCU. Please message me if you are interested or
  would like more details/photos!

  Rank 4  |  similarity=0.5741  distance=0.4259  ✓  |  chunk_id=28  |  type=spreadsheet
  Source: Local Apartment Listings (local file)
  ────────────────────────────────────────────────────────────────────
  Apartment Name: The Grad San Jose | Address: 88 E. San Carlos St.,
  San Jose, CA 95128 | Distance from SCU: 4.0 miles | Website:
  https://www.thegradsanjose.com/ | Monthly Rent: Contact for
  pricing | Security Deposit: Contact for details | Application Fee:
  Not listed | Move-In Fees: Not listed | Background Check Fee: Not
  listed | Parking: Not listed | Pet Policy: Pets allowed (contact
  for details) | Cosigner / Guarantor: Not listed | Lease Length
  Options: Contact for lease terms | Utilities Included: electric
  kitchen, central air and heating, and an in-home washer and dryer,
  which is excellent for a student on the go

  Rank 5  |  similarity=0.5737  distance=0.4263  ✓  |  chunk_id=44  |  type=text
  Source: Rental Listings Portal
  ────────────────────────────────────────────────────────────────────
  Title: $2000/mo - Large single in house - only 1 block from campus
  Address: 860 Washington St, Santa Clara 95050
  Distance from SCU: 0.077 miles
  Lease Term: 1 year
  Rules: Utilities Included: No | Smoking Allowed: No | Pets
  Allowed: No | Accessible: No
  Parking: Large driveway and paved backyard space
  Contact: [REDACTED] | Phone: [REDACTED] | Email: [REDACTED]
  Type: House - Share (renting a room or part of a unit)
  Configuration: 1 bed available / 5 total | 2 bath | Up to 1 person
  Availability: July 01, 2026 until June 30, 2027


========================================================================
QUERY: What apartment complex on El Camino Real is closest to SCU?
========================================================================
  Rank 1  |  similarity=0.6927  distance=0.3073  ✓  |  chunk_id=23  |  type=spreadsheet
  Source: Local Apartment Listings (local file)
  ────────────────────────────────────────────────────────────────────
  Apartment Name: Villas on the Blvd | Address: 2615 El Camino Real,
  Santa Clara, CA 95051 | Distance from SCU: 3.2 miles | Website:
  http://villasontheboulevard.com/ | Monthly Rent: Contact for
  pricing | Security Deposit: Contact for details | Application Fee:
  Not listed | Move-In Fees: Not listed | Background Check Fee: Not
  listed | Parking: Not listed | Pet Policy: Not listed | Cosigner /
  Guarantor: Not listed | Lease Length Options: Contact:
  408-389-7860 | Utilities Included: Tenant pays all utilities

  Rank 2  |  similarity=0.6052  distance=0.3948  ✓  |  chunk_id=39  |  type=text
  Source: Rental Listings Portal
  ────────────────────────────────────────────────────────────────────
  Title: $2200/mo - Domicilio 2 Bedroom Apartment
  Address: 431 El Camino Real, Santa Clara 95050
  Distance from SCU: 0.057 miles
  Lease Term: 9 months - 1 year
  Rules: Utilities Included: No | Smoking Allowed: No | Pets
  Allowed: No | Accessible: No
  Parking: 1 free parking spot. An additional $50-200/month for
  extra parking spot
  Contact: [REDACTED] | Phone: [REDACTED] | Email: [REDACTED]
  Type: Apartment - Share (renting a room or part of a unit)
  Configuration: 1 bed available / 2 total | 2 bath | Up to 1 person
  Availability: Available starting September 12, 2026
  Description: Hi I am looking for 1 roommate (preferably female)
  that is willing to live in Domicilio which is right off of campus.
  I already have living room furniture and some furniture for the
  kitchen. You would have your own bedroom and bathroom. The room is
  also on the 4th floor so there won’t be anyone above.

  Rank 3  |  similarity=0.5936  distance=0.4064  ✓  |  chunk_id=97  |  type=text
  Source: Apartments.com – Santa Clara
  ────────────────────────────────────────────────────────────────────
  The Deck
  Address: 3406 El Camino Real, Santa Clara, CA 95051
  Pricing: 1 Bed: $3,600+
  Amenities: Fitness Center, Pool, In Unit Washer & Dryer, Heat,
  High-Speed Internet, Controlled Access, Elevator
  Contact: (650) 668-3073

  Rank 4  |  similarity=0.5701  distance=0.4299  ✓  |  chunk_id=92  |  type=text
  Source: Apartments.com – Santa Clara
  ────────────────────────────────────────────────────────────────────
  The Murphy Station
  Address: 1008 E El Camino Real, Sunnyvale, CA 94087
  Pricing: Studio: $3,040+ | 1 Bed: $3,550
  Amenities: Pets Allowed, Fitness Center, Pool, Kitchen, In Unit
  Washer & Dryer, Clubhouse
  Contact: (650) 374-5379

  Rank 5  |  similarity=0.5684  distance=0.4316  ✓  |  chunk_id=4  |  type=spreadsheet
  Source: Local Apartment Listings (local file)
  ────────────────────────────────────────────────────────────────────
  Apartment Name: Domicilio Apts | Address: 431 El Camino Real,
  Santa Clara, CA 95050 | Distance from SCU: 0.2 miles | Website:
  https://www.domicilioapts.com/ | Monthly Rent: $2,994 – $3,212/mo
  | Security Deposit: Contact for details | Application Fee: Not
  listed | Move-In Fees: Move-In Cost (including General and Special
  Fees) and the Total Monthly Leasing Price going forward of a lease
  | Background Check Fee: Not listed | Parking: parking Available
  More info on Underground parking Available | Pet Policy: Pets
  allowed | Cats ✓ | Dogs ✓ | Deposit: $500 | Monthly pet rent: $65
  | Cosigner / Guarantor: Not listed | Lease Length Options: lease
  terms | Utilities Included: water


========================================================================
QUERY: How far in advance does SCU recommend starting your housing search?
========================================================================
  Rank 1  |  similarity=0.6273  distance=0.3727  ✓  |  chunk_id=0  |  type=text
  Source: SCU Off-Campus Housing Information
  ────────────────────────────────────────────────────────────────────
  Student demand for housing within 5 miles of campus is continually
  increasing
  We highly recommend starting your housing search 9-14 months in
  advance of your desired move-in date, BUT if you start later than
  that, we can help Get Support & Resources: We offer compiled
  resources for undergraduate and graduate students seeking
  off-campus housing
  For more assistance, you can reach out to our office: Email:
  offcampusliving@scu.edu Call: 408-551-3665 Undergraduate options
  Graduate/Law Options Non-affiliated Off Campus Housing Resources
  References to any person, organization, or services related to
  such person or organization, or any linkages from this web site to
  the web site of another party, do not constitute or imply the
  endorsement, recommendation, or favoring of such
  SCU does not manage, oversee, or vet any postings on the
  non-affiliated Facebook page nor do they oversee any local
  landlords or property management companies
  We recommend individuals look through our "Resources" page as they
  are exploring any housing options found in rental listings

  Rank 2  |  similarity=0.5561  distance=0.4439  ✓  |  chunk_id=70  |  type=spreadsheet
  Source: Sublease Listing Responses
  ────────────────────────────────────────────────────────────────────
  Timestamp: 2026-05-19 14:01:26.019000 | Email Address:
  [REDACTED] | Name:: [REDACTED] | SCU Email::
  [REDACTED] | Phone Number (Optional):: [REDACTED] |
  Preferred Contact:: Text | Academic Standing for 2026-2027::
  Graduating Senior | Please select one of the following:: I am
  looking for a room to sublease
  | Sublease End Date:: NaT | Please provide a description of what
  you are looking for (i.e
  Lease start/end dates, preferred monthly rent, single or shared
  room request, any other details).: I need a lease ASAP if
  possible, before graduation at the least with a hard deadline of
  5/15 to move in
  Length isn't too important, but the longer, the better, to find
  more permanent housing
  Room type doesn't matter too much but I would definitely prefer a
  private space

  Rank 3  |  similarity=0.5330  distance=0.4670  ✓  |  chunk_id=56  |  type=spreadsheet
  Source: Roommate Finder Responses
  ────────────────────────────────────────────────────────────────────
  Timestamp: 2026-06-01 11:35:15.260000 | Email Address:
  [REDACTED] | Name:: [REDACTED] | SCU Email:: [REDACTED] |
  Phone Number (Optional):: [REDACTED] | Preferred Contact:: Text
  | Academic Standing for 2026-2027:: Junior | Please indicate if
  any apply to you:: Transfer Student | Roommate Gender Preference::
  Female | What best describes your current housing situation?: I
  need both housing and roommates | Please provide a description of
  what you are looking for (i.e. Lease start/end dates, preferred
  monthly rent, single or shared room request, any other details).:
  Single, starting in September until July or even just looking for
  roommates

  Rank 4  |  similarity=0.5275  distance=0.4725  ✓  |  chunk_id=50  |  type=text
  Source: Rental Listings Portal
  ────────────────────────────────────────────────────────────────────
  Availability: September 01, 2026 until December 31, 2026
  Description: Looking for a subleaser from September 1 2026 through
  December 31 2026 for a fully furnished single bedroom only 2
  blocks from campus! The room features a closet, large windows, and
  a keypad lock on the door for privacy. The room is 143 sq ft,
  offering a very spacious personal living space which will be
  furnished with a full sized bed, desk, and dresser. The house has
  a fully furnished living room, kitchen, and backyard, as well as
  in-unit laundry. The main house has 4 female SCU students, as well
  as 1 female SCU student in an ADU separate from the main house.
  Three bedrooms in the main house as well as the ADU will be
  subleased during fall quarter.

  Rank 5  |  similarity=0.5154  distance=0.4846  ✓  |  chunk_id=1  |  type=text
  Source: SCU Off-Campus Housing Information
  ────────────────────────────────────────────────────────────────────
  Rental Listings Local Apartment Listings Off Campus
  Landlord/Property Management List SCU Owned Off Campus Housing
  Non-affiliated Off Campus Housing Resources Subleasing and
  Roommate Resources Sublease Finder & Connection Form Sublease
  Finder & Connection Results Roommate Finder Form Roommate Finder
  Results


========================================================================
QUERY: What summer subleases are listed near SCU campus?
========================================================================
  Rank 1  |  similarity=0.6523  distance=0.3477  ✓  |  chunk_id=50  |  type=text
  Source: Rental Listings Portal
  ────────────────────────────────────────────────────────────────────
  Availability: September 01, 2026 until December 31, 2026
  Description: Looking for a subleaser from September 1 2026 through
  December 31 2026 for a fully furnished single bedroom only 2
  blocks from campus! The room features a closet, large windows, and
  a keypad lock on the door for privacy. The room is 143 sq ft,
  offering a very spacious personal living space which will be
  furnished with a full sized bed, desk, and dresser. The house has
  a fully furnished living room, kitchen, and backyard, as well as
  in-unit laundry. The main house has 4 female SCU students, as well
  as 1 female SCU student in an ADU separate from the main house.
  Three bedrooms in the main house as well as the ADU will be
  subleased during fall quarter.

  Rank 2  |  similarity=0.5745  distance=0.4255  ✓  |  chunk_id=45  |  type=text
  Source: Rental Listings Portal
  ────────────────────────────────────────────────────────────────────
  Availability: July 01, 2026 until June 30, 2027
  Description: We are looking for a female student to live in a
  large single (with closet) in our 2-story house with lease
  starting July 2026. Included in house is an in-unit washer and
  dryer, large kitchen, living room, AC/heat, big backyard &
  driveway, and it is only one block from SCU campus. Lots of
  parking space available. Email or text me if you would like to see
  it!

  Rank 3  |  similarity=0.5366  distance=0.4634  ✓  |  chunk_id=1  |  type=text
  Source: SCU Off-Campus Housing Information
  ────────────────────────────────────────────────────────────────────
  Rental Listings Local Apartment Listings Off Campus
  Landlord/Property Management List SCU Owned Off Campus Housing
  Non-affiliated Off Campus Housing Resources Subleasing and
  Roommate Resources Sublease Finder & Connection Form Sublease
  Finder & Connection Results Roommate Finder Form Roommate Finder
  Results

  Rank 4  |  similarity=0.5338  distance=0.4662  ✓  |  chunk_id=86  |  type=text
  Source: Student Sublet
  ────────────────────────────────────────────────────────────────────
  Student Sublet — Find your summer sublet Trusted by students The
  trusted way for students to find and list sublets
  Verified students and young professionals listing rooms near
  universities across the country
  No sketchy listings
  No strangers
  Find a room List your room 🏠 Private room · University Ave 0.4 mi
  from SCU · $1,150/mo Student verified 🏢 Studio · Midtown Near
  campus · $1,400/mo ID verified 🏡 Shared room · Campus Edge 0.1 mi
  from SJSU · $950/mo Student verified How it works Find or fill a
  room in minutes
  1 Create your verified profile Sign up with your .edu email for
  instant student verification, or upload a government ID if you're
  a young professional
  2 Browse or post a listing Search by university, city, or
  neighborhood
  Filter by price, dates, and gender preference
  Or post your own room in under 5 minutes
  3 Connect safely Send an inquiry and message directly in the app
  Your contact info stays private until you're ready to share it
  Why Student Sublet Built for trust, not just convenience

  Rank 5  |  similarity=0.5302  distance=0.4698  ✓  |  chunk_id=46  |  type=text
  Source: Rental Listings Portal
  ────────────────────────────────────────────────────────────────────
  Title: $1300/mo - SUMMER SUBLEASE - 1153 Lafayette St.
  Address: 1153 Lafayette Street, Santa Clara 95053
  Distance from SCU: 0.12 miles
  Lease Term: Summer Quarter
  Rules: Utilities Included: No | Smoking Allowed: No | Pets
  Allowed: No | Accessible: No
  Parking: Street Parking
  Contact: [REDACTED] | Phone: [REDACTED] | Email:
  [REDACTED]
  Type: House - Share (renting a room or part of a unit)
  Configuration: 1 bedroom | 1.5 bath | Up to 1 person
  Availability: July 13, 2026 until September 13, 2026

**Milestone 5 — Generation and interface:**
