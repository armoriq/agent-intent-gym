# Shared brief for reference-verification agents

Paper: "intent drift" in AI coding agents. Agents pass visible tests (the metric) while violating the
developer's actual intent. Measured with (a) a visible/hidden test split (drift gap = visible pass rate
minus intent pass rate), (b) three prompt phrasings of the same bug (scoped / loose / vague), and
(c) out-of-scope edits against planted "rabbit holes" (tempting adjacent code the agent should not touch).
Tasks carry contamination tags (fresh / post-cutoff / classic). Context: /Users/psudokit/benchmark/docs/research-design.md

## Hard rules
- Every entry must be confirmed on a PRIMARY source you actually fetched this session: arXiv abs page
  (https://arxiv.org/abs/ID), arXiv's own BibTeX export (https://arxiv.org/bibtex/ID), ACL Anthology,
  ACM DL, OpenReview, proceedings.neurips.cc / proceedings.mlr.press, or the official blog/report page.
  Use WebFetch or `curl -sL` (arXiv export API also fine: http://export.arxiv.org/api/query?id_list=ID).
- Do NOT invent or guess any author, year, title, venue, page or number. Copy authors and titles exactly.
  If you cannot confirm a paper exists, DROP it and say so.
- Venue: only claim a conference/journal venue if you confirmed it on OpenReview, the proceedings page,
  ACL Anthology, or the arXiv "Comments"/"Journal ref" field. Otherwise use @misc with arXiv eprint.
- Every entry needs eprint+archivePrefix (if arXiv) AND url, plus doi if one exists and you saw it.
- Keys: firstauthorlastnameYEARfirstword, lowercase, e.g. jimenez2024swebench.
- For very long author lists (> 25) you may list the first ~10 exactly as on the source, then "and others".
- No em dashes anywhere. Plain academic English.

## Notes
For each entry write 2-4 sentences in your own words: what it does; the specific finding or number we
might cite WITH its location (section / table / figure / page; read the paper body, e.g. the arXiv HTML
version https://arxiv.org/html/ID or the PDF, not just the abstract); and exactly how it relates to our
paper, starting with one of: Supports / Contrasts / Gap we fill / Method precedent / Background.
Any number you could not locate in the source body: append "[number not confirmed in source body]".

## Output
Write two files in /Users/psudokit/benchmark/paper2/refs/_work/ named <cluster>.bib and <cluster>_notes.md.
Notes format per entry:

### <key>: <Title>
Source checked: <URL(s) you fetched>
<2-4 sentences>

At the end of the notes file add "## Dropped / unverifiable" and "## Claim checks" (for any claims you
were asked to verify: state CONFIRMED / WRONG (with correction) / NOT FOUND, with the URL).
Your final message: list keys written, anything dropped, and claim-check results. Keep it short.
