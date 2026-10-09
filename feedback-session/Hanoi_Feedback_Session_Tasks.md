# EcoFoodSystems Dashboard — Guided Feedback Session

**City:** Hà Nội &nbsp;|&nbsp; **Format:** 5 exploration tasks &nbsp;|&nbsp; **Suggested time:** ~45 minutes

**Instructions for participants:**
Work through the tasks below in any order. There are no step-by-step instructions — finding *where* the answer lives is part of the task. Talk aloud as you explore, and note anything confusing, broken, or surprising. Every answer can be found inside the dashboard.

---

## Participant Tasks

### Task 1 — Market access on foot
> **Which commune in Hanoi has the highest share of women living within a 15-minute walk of a market?**
> **If those same women only had 5 minutes, roughly what share would be covered in that commune?**
> **Does the picture change if they drive instead?**

*Hint: think about where "accessibility" and "population" meet.*

---

### Task 2 — Policy detective
> **Vietnam's food safety policy landscape: how many policies in the database relate to food safety, and which is the most recent one? Follow its link to the original source document.**
> **Which "primary subject" covers the most policies overall?**

---

### Task 3 — Who's who in the food system
> **How many organizations in Hanoi's food system work on service provision?**
> **Which stakeholder category (public sector, private sector, civil society, …) dominates that group? Does that surprise you?**

---

### Task 4 — Follow the food
> **Pick a commodity (e.g., rice or vegetables). Where does most of Hanoi's supply of it come from, and what is the total volume flowing into the city?**
> **Trace one full chain from origin to consumer and describe each stage.**

---

### Task 5 — Self-sufficiency check-up
> **Out of fish, meat and rice, which product is Hanoi most self-sufficient in?**
> **Has that changed over the last 10 years (2014–2024)?**

---

---

# Facilitator Guide & Answer Key

*(Print separately — do not distribute to participants.)*

## Task 1 — Market access on foot
**Verified answers (from underlying accessibility statistics):**
- **15-min walk, women, marketplace:** **Hoàn Kiếm — 94.0%** (top 3: Hoàn Kiếm 94.0%, Đống Đa 86.3%, Láng 82.5%)
- **5-min walk, same commune:** Hoàn Kiếm drops to **12.0%** — a dramatic contrast that shows the slider's impact.
- **15-min drive:** several central communes hit **100%** (Ngọc Hà, Giảng Võ, Kim Liên).

**Path:** Food Environments → vendor properties view → transport-mode buttons (walk/bus/car icons) → travel-time slider (5/10/15 min) → outlet layer dropdown (select marketplaces) → "Population in Accessibility Zones" dropdown (Women) → ranked bar chart + map.
**Components exercised:** transport-mode toggle, travel-time slider, outlet multi-select, population dropdown, bar chart, choropleth map.
**Watch for:** Do participants find the transport-mode icon buttons? Do they understand the values are *% of the commune's women population within the zone*? Note: the bar chart is scrollable (126 communes).

## Task 2 — Policy detective
**Verified answers:**
- Database holds **149 policies** in total.
- Filtering **Keywords** by "food safety" yields **121 policies**.
- Largest **Primary subjects** category: **Food & nutrition (100 policies)**.
- "Most recent" is found by sorting **Year Enacted** descending — note some recent entries carry the year of the latest plan period; treat exact "newest" answers flexibly.

**Path:** Policies & Regulation tab → Food System Policies Database table → type in the Keywords filter box → sort Year Enacted → click the markdown link in Document Link / Available website → ⓘ tooltip shows the FAO FAOLEX source.
**Components exercised:** DataTable native filters, multi-column sort, pagination, info tooltip, external links.
**Watch for:** Do participants discover the per-column filter row unprompted? Do they use the row count to answer "how many"?

## Task 3 — Who's who
**Verified answers:**
- **115 stakeholders** in the database.
- **Service provision: 57 organizations** — the largest activity area.
- Dominated by the **International community (21 of 57)**, then Academia/knowledge organizations (14) and Public sector (11). Overall category counts: International community 35, Public sector 21, Civil society 21, Private sector 15, Academia 14, Media 5, Other 3.

**Path:** Food Systems Stakeholders tab → stakeholder database → filter "Area of Activity in the food system" = Service provision → read the category column / sort it to count.
**Components exercised:** stakeholder table filtering + sorting, interpreting categories.
**Watch for:** The category column header contains a typo ("catagorization") — worth noting if participants comment.

## Task 4 — Follow the food
**Verification path (no fixed answer — depends on commodity chosen):**
Food Flows & Supply Chains tab → Storage & Distribution section → use the dropdowns to select a commodity/stage → hover the **Sankey diagram** links for flow volumes → cross-check the headline figure in the **total-flow KPI card**.
**Components exercised:** Sankey hover interaction, supply-chain dropdowns, KPI card.
**Watch for:** Do participants realize Sankey links are hoverable? Do they connect the KPI card total to the diagram? Record the commodity they pick and the volumes they report for spot-checking later.

## Task 5 — Self-sufficiency check-up
**Verified answers (from the Globalisation & Trade temporal indicators, 2014–2024):**
- **In 2014: rice** was most self-sufficient (0.73), ahead of meat (0.56) and fish (0.16).
- **In 2024: meat has overtaken rice** — meat 0.71 vs rice 0.54; fish remains lowest (0.39).
- **The trend is the story:** rice self-sufficiency has *fallen* steadily (0.73 → 0.54), while meat (0.56 → 0.71) and fish (0.16 → 0.39) have *risen*. Either "rice" or "meat" is acceptable for part one depending on the year — the key insight is the crossover.

**Path:** sidebar pillar navigation → **Drivers** → **Globalisation & Trade** sub-domain → KPI indicator cards (Rice / Meat / Fish self-sufficiency rate), each with a sparkline; hover the sparkline for yearly values and read the latest value shown prominently on the card.
**Components exercised:** pillar/sidebar navigation, sub-domain switcher, KPI cards with sparklines, sparkline hover, interpreting trend + latest value together.
**Watch for:** Values are ratios (0–1); do participants read 0.54 as 54%? Do they notice the sparkline year axis, or only read the headline number? Bonus discussion: companion cards show *import rates* and *supplier concentration (HHI)* — a good prompt for advanced participants.

---

## Session coverage summary

| Dashboard area | Covered by |
|---|---|
| Vendor accessibility (transport modes, travel-time slider, population groups) | Task 1 |
| Policies database (filter/sort/links) | Task 2 |
| Stakeholder database | Task 3 |
| Food-flow Sankey + total-flow KPI | Task 4 |
| KPI indicator cards with sparklines (Drivers → Globalisation & Trade) | Task 5 |
| Nutrition/expenditure KPI cards | Task 1 (context) |
| AI chatbot | Not tasked — optional free exploration at the end |
| City selector | Not tasked (Hanoi-only session) |

*All numerical answers verified against the dashboard's underlying CSVs on 2026-10-08. Re-verify if data files are updated before the session.*
