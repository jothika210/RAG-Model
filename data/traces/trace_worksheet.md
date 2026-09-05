# Trace Worksheet — Week 5 Error Analysis (HR Policy)

20 traces, randomly sampled with seed `42` from a pool of diverse real queries run through the live pipeline. Read every trace in order below and write one honest note per trace about what, if anything, went wrong — **before** grouping or ranking anything. Full raw data (including which trace_ids were drawn) is in `data/traces/traces_raw.json` and `data/traces/sampled_trace_ids.json`.

---

### t000

**Question asked:** What is the carry-over cap for a probationary employee under HR-207 section 4.2?

_region filter: `APAC` · strategy: `naive` · retrieval_mode: `hybrid`_

**Fetched:**

1. `HR-207_carryover_apac.md::naive::2` — policy=HR-207 section=4.2 region=APAC score=0.8365
2. `HR-207_carryover_apac.md::naive::0` — policy=HR-207 section=01 region=APAC score=0.7943
3. `HR-201_annual_leave_apac.md::naive::3` — policy=HR-201 section=4.1 region=APAC score=0.7647
4. `HR-207_carryover_apac.md::naive::1` — policy=HR-207 section=4.2 region=APAC score=0.7635
5. `HR-201_annual_leave_apac.md::naive::2` — policy=HR-201 section=3.1 region=APAC score=0.7276

**Answer:**

The carry-over cap for a probationary employee under HR-207 section 4.2 is 2 days for the transition year only, regardless of sub-region [HR-207_carryover_apac.md::naive::2].

**Citations:** `HR-207_carryover_apac.md::naive::2`

**Note:** Correct — answer and citation match the known HR-207 §4.2 fact (2 days).

---

### t001

**Question asked:** Under HR-207, what is the carry-over cap for a full-time confirmed employee in India?

_region filter: `APAC` · strategy: `structure_aware` · retrieval_mode: `semantic`_

**Fetched:**

1. `HR-207_carryover_apac.md::structure_aware::3` — policy=HR-207 section=3 region=APAC score=0.7899
2. `HR-207_carryover_apac.md::structure_aware::5` — policy=HR-207 section=4.2 region=APAC score=0.7797
3. `HR-207_carryover_apac.md::structure_aware::4` — policy=HR-207 section=4 region=APAC score=0.7465
4. `HR-201_annual_leave_apac.md::structure_aware::6` — policy=HR-201 section=3 region=APAC score=0.734
5. `HR-201_annual_leave_apac.md::structure_aware::10` — policy=HR-201 section=4.2 region=APAC score=0.7329

**Answer:**

The carry-over cap for a full-time confirmed employee in India is 10 days [HR-207_carryover_apac.md::structure_aware::3].

**Citations:** `HR-207_carryover_apac.md::structure_aware::3`

**Note:** Correct — 10 days for India matches HR-207 §3, citation resolves to the right chunk.

---

### t002

**Question asked:** How many days of company-paid sick leave is an EMEA employee entitled to per calendar year under HR-203?

_region filter: `EMEA` · strategy: `structure_aware` · retrieval_mode: `hybrid`_

**Fetched:**

1. `HR-209_remote_work_emea.md::structure_aware::0` — policy=HR-209 section=1 region=EMEA score=0.7885
2. `HR-203_sick_leave_emea.md::structure_aware::3` — policy=HR-203 section=2.1 region=EMEA score=0.7882
3. `HR-203_sick_leave_emea.md::structure_aware::0` — policy=HR-203 section=1 region=EMEA score=0.7604
4. `HR-203_sick_leave_emea.md::structure_aware::5` — policy=HR-203 section=2.3 region=EMEA score=0.7072
5. `HR-203_sick_leave_emea.md::structure_aware::8` — policy=HR-203 section=4.1 region=EMEA score=0.7157

**Answer:**

Employees in the EMEA region are entitled to 10 days of company-paid sick leave per calendar year at full salary [HR-203_sick_leave_emea.md::structure_aware::3].

**Citations:** `HR-203_sick_leave_emea.md::structure_aware::3`

**Note:** Correct — 10 days matches HR-203 §2.1, though it's worth noting the top-ranked fetch was actually an unrelated HR-209 chunk; the model still picked the right source from lower in the list.

---

### t005

**Question asked:** Under HR-211, what is the carry-over cap for a full-time confirmed employee in Brazil, and why can't it be reduced?

_region filter: `AMER` · strategy: `structure_aware` · retrieval_mode: `semantic`_

**Fetched:**

1. `HR-211_carryover_amer.md::structure_aware::3` — policy=HR-211 section=2.1 region=AMER score=0.8346
2. `HR-211_carryover_amer.md::structure_aware::2` — policy=HR-211 section=2 region=AMER score=0.7753
3. `HR-211_carryover_amer.md::structure_aware::5` — policy=HR-211 section=4.2 region=AMER score=0.7631
4. `HR-211_carryover_amer.md::structure_aware::4` — policy=HR-211 section=3 region=AMER score=0.728
5. `HR-211_carryover_amer.md::structure_aware::0` — policy=HR-211 section=1 region=AMER score=0.7196

**Answer:**

The carry-over cap for a full-time confirmed employee in Brazil is 30 days, which reflects statutory annual leave (férias) requirements. It cannot be reduced by future addenda without legal review because it is not a company discretionary policy [HR-211_carryover_amer.md::structure_aware::3].

**Citations:** `HR-211_carryover_amer.md::structure_aware::3`

**Note:** Correct — 30 days, statutory reasoning included, matches HR-211 and the citation resolves correctly.

---

### t006

**Question asked:** Under HR-209, if a remote employee's scheduled annual leave day coincides with a public holiday in their home country, what happens to that leave day?

_region filter: `EMEA` · strategy: `naive` · retrieval_mode: `hybrid`_

**Fetched:**

1. `HR-209_remote_work_emea.md::naive::1` — policy=HR-209 section=2.2 region=EMEA score=0.8136
2. `HR-209_remote_work_emea.md::naive::0` — policy=HR-209 section=15 region=EMEA score=0.7936
3. `HR-203_sick_leave_emea.md::naive::0` — policy=HR-203 section=01 region=EMEA score=0.6495
4. `HR-203_sick_leave_emea.md::naive::1` — policy=HR-203 section=2.2 region=EMEA score=0.6084
5. `HR-203_sick_leave_emea.md::naive::2` — policy=HR-203 section=4.1 region=EMEA score=0.6248

**Answer:**

If a scheduled annual leave day coincides with a public holiday in the employee's registered home country, the day is credited back to the employee's leave balance and does not count against their annual entitlement [HR-209_remote_work_emea.md::naive::1].

**Citations:** `HR-209_remote_work_emea.md::naive::1`

**Note:** Correct — credited-back-to-balance answer matches HR-209 §2.2, citation resolves correctly.

---

### t007

**Question asked:** Under HR-201, what is the special carry-over exception for full-time confirmed employees based in Singapore, and how many days can they carry over?

_region filter: `APAC` · strategy: `structure_aware` · retrieval_mode: `semantic`_

**Fetched:**

1. `HR-201_annual_leave_apac.md::structure_aware::10` — policy=HR-201 section=4.2 region=APAC score=0.822
2. `HR-207_carryover_apac.md::structure_aware::3` — policy=HR-207 section=3 region=APAC score=0.7959
3. `HR-207_carryover_apac.md::structure_aware::5` — policy=HR-207 section=4.2 region=APAC score=0.7456
4. `HR-201_annual_leave_apac.md::structure_aware::6` — policy=HR-201 section=3 region=APAC score=0.7146
5. `HR-207_carryover_apac.md::structure_aware::2` — policy=HR-207 section=2 region=APAC score=0.6969

**Answer:**

Full-time confirmed employees based in Singapore may carry over up to 7 days due to statutory minimum requirements under the Singapore Employment Act [HR-201_annual_leave_apac.md::structure_aware::10].

**Citations:** `HR-201_annual_leave_apac.md::structure_aware::10`

**Note:** Correct — 7 days for Singapore matches; cites the older HR-201 §4.2 rather than the newer, more specific HR-207 §3, but both documents agree on the figure so no factual error.

---

### t008

**Question asked:** What is the company's sabbatical leave policy after 5 years of continuous service?

_strategy: `structure_aware` · retrieval_mode: `hybrid`_

**Fetched:**

1. `HR-211_carryover_amer.md::structure_aware::1` — policy=HR-211 section=1.1 region=AMER score=0.674
2. `HR-201_annual_leave_apac.md::structure_aware::2` — policy=HR-201 section=1.2 region=APAC score=0.6949
3. `HR-205_parental_leave_amer.md::structure_aware::1` — policy=HR-205 section=1.1 region=AMER score=0.7075
4. `HR-201_annual_leave_apac.md::structure_aware::4` — policy=HR-201 section=2.1 region=APAC score=0.6956
5. `HR-207_carryover_apac.md::structure_aware::1` — policy=HR-207 section=1.1 region=APAC score=0.6717

**Result:** REFUSED (reason: `low_retrieval_confidence`, top_score=0.6740)

**Note:** Good — correctly refused; no addendum defines a sabbatical policy, so refusal is the right outcome, not a failure.

---

### t014

**Question asked:** I'm based in India and I'm full-time and confirmed -- what's my leave carry-over limit per HR-207?

_region filter: `APAC` · strategy: `structure_aware` · retrieval_mode: `hybrid`_

**Fetched:**

1. `HR-207_carryover_apac.md::structure_aware::3` — policy=HR-207 section=3 region=APAC score=0.7591
2. `HR-207_carryover_apac.md::structure_aware::0` — policy=HR-207 section=1 region=APAC score=0.7034
3. `HR-201_annual_leave_apac.md::structure_aware::10` — policy=HR-201 section=4.2 region=APAC score=0.6981
4. `HR-201_annual_leave_apac.md::structure_aware::6` — policy=HR-201 section=3 region=APAC score=0.7052
5. `HR-201_annual_leave_apac.md::structure_aware::4` — policy=HR-201 section=2.1 region=APAC score=0.6754

**Answer:**

Your leave carry-over limit as a full-time confirmed employee based in India is 10 days [HR-207_carryover_apac.md::structure_aware::3].

**Citations:** `HR-207_carryover_apac.md::structure_aware::3`

**Note:** Good — 10 days for India matches even with informal first-person phrasing; retrieval and citation held up under rephrasing.

---

### t015

**Question asked:** How much sick pay from the company do EMEA staff get each year, per HR-203?

_region filter: `EMEA` · strategy: `structure_aware` · retrieval_mode: `hybrid`_

**Fetched:**

1. `HR-203_sick_leave_emea.md::structure_aware::5` — policy=HR-203 section=2.3 region=EMEA score=0.7376
2. `HR-203_sick_leave_emea.md::structure_aware::3` — policy=HR-203 section=2.1 region=EMEA score=0.7314
3. `HR-209_remote_work_emea.md::structure_aware::0` — policy=HR-209 section=1 region=EMEA score=0.7076
4. `HR-203_sick_leave_emea.md::structure_aware::0` — policy=HR-203 section=1 region=EMEA score=0.7101
5. `HR-203_sick_leave_emea.md::structure_aware::4` — policy=HR-203 section=2.2 region=EMEA score=0.6672

**Answer:**

EMEA staff are entitled to 10 days of company-paid sick leave per calendar year at full salary, in addition to any statutory sick pay they may separately be entitled to under local law [HR-203_sick_leave_emea.md::structure_aware::3].

**Citations:** `HR-203_sick_leave_emea.md::structure_aware::3`

**Note:** Good — 10 days matches HR-203 §2.1 even with casual rephrasing ("sick pay").

---

### t016

**Question asked:** What paperwork do I need for a sick day that's 5 days long under HR-203?

_region filter: `EMEA` · strategy: `structure_aware` · retrieval_mode: `hybrid`_

**Fetched:**

1. `HR-203_sick_leave_emea.md::structure_aware::3` — policy=HR-203 section=2.1 region=EMEA score=0.716
2. `HR-203_sick_leave_emea.md::structure_aware::6` — policy=HR-203 section=3 region=EMEA score=0.6818
3. `HR-209_remote_work_emea.md::structure_aware::0` — policy=HR-209 section=1 region=EMEA score=0.6574
4. `HR-203_sick_leave_emea.md::structure_aware::4` — policy=HR-203 section=2.2 region=EMEA score=0.6875
5. `HR-203_sick_leave_emea.md::structure_aware::5` — policy=HR-203 section=2.3 region=EMEA score=0.6615

**Result:** REFUSED (reason: `low_retrieval_confidence`, top_score=0.7160)

**Note:** False refusal — HR-203 §3 (the certification table, "4-7 days -> doctor's note") was actually retrieved at rank 2 and directly answers this, but the top-1 score (0.716) narrowly missed the 0.72 threshold, so the app refused a question the corpus could answer.

---

### t017

**Question asked:** As the non-primary parent, how much paid leave do I get for parental leave under HR-205?

_region filter: `AMER` · strategy: `structure_aware` · retrieval_mode: `hybrid`_

**Fetched:**

1. `HR-211_carryover_amer.md::structure_aware::6` — policy=HR-211 section=4 region=AMER score=0.7673
2. `HR-205_parental_leave_amer.md::structure_aware::3` — policy=HR-205 section=2.1 region=AMER score=0.7415
3. `HR-205_parental_leave_amer.md::structure_aware::4` — policy=HR-205 section=2.2 region=AMER score=0.7384
4. `HR-205_parental_leave_amer.md::structure_aware::8` — policy=HR-205 section=3.3 region=AMER score=0.7121
5. `HR-205_parental_leave_amer.md::structure_aware::6` — policy=HR-205 section=3.1 region=AMER score=0.685

**Answer:**

As the non-primary parent, you are entitled to 6 weeks of paid parental leave at full salary under HR-205 [HR-205_parental_leave_amer.md::structure_aware::4].

**Citations:** `HR-205_parental_leave_amer.md::structure_aware::4`

**Note:** Correct — "non-primary parent" was correctly interpreted as secondary caregiver, 6 weeks matches HR-205.

---

### t019

**Question asked:** If my scheduled leave lands on a public holiday back home while I'm working remotely, do I lose that day under HR-209?

_region filter: `EMEA` · strategy: `structure_aware` · retrieval_mode: `hybrid`_

**Fetched:**

1. `HR-209_remote_work_emea.md::structure_aware::4` — policy=HR-209 section=2.2 region=EMEA score=0.8238
2. `HR-209_remote_work_emea.md::structure_aware::5` — policy=HR-209 section=3 region=EMEA score=0.7497
3. `HR-209_remote_work_emea.md::structure_aware::3` — policy=HR-209 section=2.1 region=EMEA score=0.7363
4. `HR-209_remote_work_emea.md::structure_aware::0` — policy=HR-209 section=1 region=EMEA score=0.7132
5. `HR-209_remote_work_emea.md::structure_aware::2` — policy=HR-209 section=2 region=EMEA score=0.6379

**Answer:**

No, if your scheduled leave coincides with a public holiday in your registered home country, the day is credited back to your leave balance and does not count against your annual entitlement [HR-209_remote_work_emea.md::structure_aware::4].

**Citations:** `HR-209_remote_work_emea.md::structure_aware::4`

**Note:** Correct — rephrased public holiday question still resolves to HR-209 §2.2 correctly.

---

### t027

**Question asked:** What is 'continuous service' and how does it affect all my leave entitlements?

_strategy: `structure_aware` · retrieval_mode: `hybrid`_

**Fetched:**

1. `HR-211_carryover_amer.md::structure_aware::1` — policy=HR-211 section=1.1 region=AMER score=0.8037
2. `HR-207_carryover_apac.md::structure_aware::1` — policy=HR-207 section=1.1 region=APAC score=0.7863
3. `HR-205_parental_leave_amer.md::structure_aware::1` — policy=HR-205 section=1.1 region=AMER score=0.7237
4. `HR-201_annual_leave_apac.md::structure_aware::2` — policy=HR-201 section=1.2 region=APAC score=0.7698
5. `HR-201_annual_leave_apac.md::structure_aware::7` — policy=HR-201 section=3.1 region=APAC score=0.6965

**Answer:**

"Continuous service" means unbroken employment with the company from the employee's confirmed start date, excluding any period of unpaid leave exceeding 30 consecutive days. A break in continuous service resets accrual eligibility to zero [HR-201_annual_leave_apac.md::structure_aware::2]. 

For leave entitlements, employees must complete at least 6 months of continuous service to be eligible for certain types of leave, such as parental leave [HR-205_parental_leave_amer.md::structure_aware::1]. Additionally, probationary employees accrue leave from day one but cannot take it until their probationary period ends and continuous service is confirmed in writing [HR-201_annual_leave_apac.md::structure_aware::7].

**Citations:** `HR-201_annual_leave_apac.md::structure_aware::2`, `HR-205_parental_leave_amer.md::structure_aware::1`, `HR-201_annual_leave_apac.md::structure_aware::7`

**Note:** Correct — broad multi-part question handled well, pulled the definition plus two relevant eligibility rules from separate documents with accurate citations.

---

### t030

**Question asked:** secondary caregiver parental leave weeks HR205???

_strategy: `structure_aware` · retrieval_mode: `semantic`_

**Fetched:**

1. `HR-205_parental_leave_amer.md::structure_aware::4` — policy=HR-205 section=2.2 region=AMER score=0.8415
2. `HR-205_parental_leave_amer.md::structure_aware::3` — policy=HR-205 section=2.1 region=AMER score=0.7991
3. `HR-205_parental_leave_amer.md::structure_aware::5` — policy=HR-205 section=3 region=AMER score=0.7792
4. `HR-205_parental_leave_amer.md::structure_aware::6` — policy=HR-205 section=3.1 region=AMER score=0.7721
5. `HR-205_parental_leave_amer.md::structure_aware::8` — policy=HR-205 section=3.3 region=AMER score=0.753

**Answer:**

Secondary caregivers are entitled to 6 weeks of paid parental leave at full salary [HR-205_parental_leave_amer.md::structure_aware::4].

**Citations:** `HR-205_parental_leave_amer.md::structure_aware::4`

**Note:** Correct — shorthand/typo-laden phrasing ("HR205???") still resolved to the right chunk and answer.

---

### t031

**Question asked:** carryover cap brasil hr 211 full time

_strategy: `structure_aware` · retrieval_mode: `semantic`_

**Fetched:**

1. `HR-211_carryover_amer.md::structure_aware::3` — policy=HR-211 section=2.1 region=AMER score=0.7979
2. `HR-211_carryover_amer.md::structure_aware::2` — policy=HR-211 section=2 region=AMER score=0.7702
3. `HR-211_carryover_amer.md::structure_aware::5` — policy=HR-211 section=4.2 region=AMER score=0.7604
4. `HR-207_carryover_apac.md::structure_aware::5` — policy=HR-207 section=4.2 region=APAC score=0.7462
5. `HR-201_annual_leave_apac.md::structure_aware::6` — policy=HR-201 section=3 region=APAC score=0.7372

**Answer:**

The carry-over cap for full-time confirmed employees in Brazil is 30 days, which reflects statutory annual leave requirements and is not a company discretionary policy [HR-211_carryover_amer.md::structure_aware::3].

**Citations:** `HR-211_carryover_amer.md::structure_aware::3`

**Note:** Correct — abbreviated, no-punctuation phrasing ("carryover cap brasil hr 211 full time") still resolved to the right chunk and answer.

---

### t034

**Question asked:** What is the carry-over cap for a full-time confirmed employee in India under HR-207?

_region filter: `AMER` · strategy: `structure_aware` · retrieval_mode: `semantic`_

**Fetched:**

1. `HR-211_carryover_amer.md::structure_aware::5` — policy=HR-211 section=4.2 region=AMER score=0.7572
2. `HR-211_carryover_amer.md::structure_aware::4` — policy=HR-211 section=3 region=AMER score=0.7559
3. `HR-211_carryover_amer.md::structure_aware::2` — policy=HR-211 section=2 region=AMER score=0.7437
4. `HR-211_carryover_amer.md::structure_aware::3` — policy=HR-211 section=2.1 region=AMER score=0.7222
5. `HR-211_carryover_amer.md::structure_aware::0` — policy=HR-211 section=1 region=AMER score=0.717

**Result:** REFUSED (reason: `model_declined`, top_score=0.7572)

**Model output:** REFUSE: insufficient grounding.

**Note:** Correct — India is APAC but the region filter was set to AMER (deliberate mismatch); only unrelated HR-211 chunks were fetched, and the model correctly refused rather than answering an India question from AMER-only context.

---

### t035

**Question asked:** How many weeks of parental leave does a secondary caregiver get under HR-205?

_region filter: `EMEA` · strategy: `structure_aware` · retrieval_mode: `semantic`_

**Fetched:**

1. `HR-203_sick_leave_emea.md::structure_aware::3` — policy=HR-203 section=2.1 region=EMEA score=0.6659
2. `HR-209_remote_work_emea.md::structure_aware::0` — policy=HR-209 section=1 region=EMEA score=0.6512
3. `HR-203_sick_leave_emea.md::structure_aware::4` — policy=HR-203 section=2.2 region=EMEA score=0.6335
4. `HR-203_sick_leave_emea.md::structure_aware::0` — policy=HR-203 section=1 region=EMEA score=0.6261
5. `HR-203_sick_leave_emea.md::structure_aware::1` — policy=HR-203 section=1.1 region=EMEA score=0.6128

**Result:** REFUSED (reason: `low_retrieval_confidence`, top_score=0.6659)

**Note:** Correct — HR-205 is AMER but the region filter was set to EMEA (deliberate mismatch); only unrelated HR-203/HR-209 chunks were fetched, so refusing is right.

---

### t039

**Question asked:** hr policy question please help

_strategy: `structure_aware` · retrieval_mode: `semantic`_

**Fetched:**

1. `HR-205_parental_leave_amer.md::structure_aware::5` — policy=HR-205 section=3 region=AMER score=0.7021
2. `HR-205_parental_leave_amer.md::structure_aware::8` — policy=HR-205 section=3.3 region=AMER score=0.6842
3. `HR-205_parental_leave_amer.md::structure_aware::2` — policy=HR-205 section=2 region=AMER score=0.6775
4. `HR-203_sick_leave_emea.md::structure_aware::2` — policy=HR-203 section=2 region=EMEA score=0.6775
5. `HR-209_remote_work_emea.md::structure_aware::4` — policy=HR-209 section=2.2 region=EMEA score=0.6726

**Result:** REFUSED (reason: `low_retrieval_confidence`, top_score=0.7021)

**Note:** Correct — question is too vague to answer any specific policy fact; refusal is reasonable, though a clarifying question would arguably be more helpful than a flat refusal (out of scope for this app's design).

---

### t040

**Question asked:** what about the thing with the days

_strategy: `structure_aware` · retrieval_mode: `semantic`_

**Fetched:**

1. `HR-209_remote_work_emea.md::structure_aware::2` — policy=HR-209 section=2 region=EMEA score=0.6498
2. `HR-209_remote_work_emea.md::structure_aware::4` — policy=HR-209 section=2.2 region=EMEA score=0.5814
3. `HR-203_sick_leave_emea.md::structure_aware::8` — policy=HR-203 section=4.1 region=EMEA score=0.5805
4. `HR-205_parental_leave_amer.md::structure_aware::2` — policy=HR-205 section=2 region=AMER score=0.5784
5. `HR-203_sick_leave_emea.md::structure_aware::2` — policy=HR-203 section=2 region=EMEA score=0.5784

**Result:** REFUSED (reason: `low_retrieval_confidence`, top_score=0.6498)

**Note:** Correct — "what about the thing with the days" gives no identifiable policy fact to look up; refusal is clearly right here.

---

### t041

**Question asked:** policy

_strategy: `structure_aware` · retrieval_mode: `semantic`_

**Fetched:**

1. `HR-205_parental_leave_amer.md::structure_aware::2` — policy=HR-205 section=2 region=AMER score=0.6551
2. `HR-203_sick_leave_emea.md::structure_aware::2` — policy=HR-203 section=2 region=EMEA score=0.6551
3. `HR-201_annual_leave_apac.md::structure_aware::3` — policy=HR-201 section=2 region=APAC score=0.6196
4. `HR-207_carryover_apac.md::structure_aware::4` — policy=HR-207 section=4 region=APAC score=0.5927
5. `HR-211_carryover_amer.md::structure_aware::4` — policy=HR-211 section=3 region=AMER score=0.587

**Result:** REFUSED (reason: `low_retrieval_confidence`, top_score=0.6551)

**Note:** Correct — a single word ("policy") gives nothing specific to answer; refusal is clearly right here.

---
