# Market research and product decision

Research cutoff and source access date: **2026-11-09**. The preferred recent-evidence window is May–November 2026. This is a small qualitative desk-research sample, not a market-size estimate, customer interview study or willingness-to-pay validation.

## Decision

Build a personal, persistent archive for people who already have extracted MBOX/EML exports and want to find old messages later without connecting an account or operating Docker services. The core journey is import → inspect receipt → search/read → recover an attachment → back up → restore and search again.

Confidence that this underlying task exists is **moderate**. Confidence in an underserved, commercially viable segment is **low and unvalidated**. Established products already solve much of this task. MailCairn's proposed advantage is a focused combination of low setup overhead, explicit import outcomes, exact-byte deduplication and portable recovery. This is a product hypothesis, not a claim of unique features or superiority.

## Evidence ledger

Dates below are the dates recorded during initial research. Some currently rendered Reddit pages expose only relative timestamps; the uncertain deployment-thread date is deliberately not normalized to an invented day. All URLs were accessed or reviewed for this project on 2026-11-09.

| Source and publication date | Observed evidence | Weight and counterevidence |
| --- | --- | --- |
| [Gmail user seeking an independent local archive](https://www.reddit.com/r/GMail/comments/1vzwbqc/looking_for_a_way_to_automatically_archive_all_my/), 2026-08-27 | The user wants locally retained mail after Gmail deletion, with search across old messages. Their follow-up connects this to storage pressure and later retrieval of financial correspondence. | Useful original user report. **On 2026-09-20 the original poster reported that OpenArchiver solved their purpose.** The request also includes automatic ingestion, which MailCairn does not implement. This validates a task, not an unmet market or a switch to MailCairn. |
| [Opening and searching large MBOX files](https://www.reddit.com/r/Thunderbird/comments/1x5gcxd/how_do_you_usually_open_and_search_large_mbox/), 2026-10-14 | Discussion addresses opening and searching exported mail. | Low weight: Readmbox is mentioned and promotional intent is possible. Do not count this as independent buying intent or proof that existing viewers fail. |
| [Gmail nearly full of old mail](https://www.reddit.com/r/GMail/comments/1xl6zwm/gmail_nearly_full_of_old_mail_what_do_you/), 2026-11-01 | Connects storage pressure to keeping access to historical messages. | Low weight: developer disclosure makes this partially promotional. It is not a clean independent demand observation. |
| [Mozilla support: importing Gmail MBOX](https://support.mozilla.org/en-US/questions/1572448), 2026-03-24 | A user describes spending about four hours on an import workflow and ultimately resolving it. | Independent historical usability evidence, **outside the preferred six-month window**. The successful resolution matters; this is not evidence that Thunderbird cannot perform the task. |
| [OpenArchiver deployment discussion](https://www.reddit.com/r/selfhosted/comments/1wjouzn/openarchiver_env_and_dockercompose_file_are_wrong/), uncertain 2026-09/11 | A discussion reports environment/Docker Compose setup friction. | Index/rendered date evidence conflicts; exact day unconfirmed. A single deployment report is weak evidence and does not establish a current general defect. Official installation requirements below are a firmer basis for comparing setup. |

These signals recur around retrieval, independence from a provider and import/setup effort. They do not establish how many users reject current tools. No interviews, presales, paid pilots or retention measurements were conducted.

## Existing solutions are credible alternatives

| Alternative | What the evidence supports | Implication for MailCairn |
| --- | --- | --- |
| [OpenArchiver installation guide](https://github.com/LogicLabs-OU/OpenArchiver/blob/main/docs/user-guides/installation.md) | Official documentation recommends Docker Compose, lists at least 4 GB RAM for the default deployment, and includes PostgreSQL, Valkey and Meilisearch; external services change the requirement. The original Gmail requester reports success. | Stronger fit for ongoing provider-connected archiving. MailCairn offers a narrower manual-export workflow with Python/SQLite and no service stack. Fewer dependencies do not prove better reliability or performance. |
| [MailStore Home](https://www.mailstore.com/en/products/mailstore-home/) | The vendor offers a dedicated free home/private email archiving product. | A direct and effective alternative must be acknowledged. Users should not adopt MailCairn merely because they were told local archiving did not exist. |
| Thunderbird with import tooling | The Mozilla support case demonstrates both initial effort and a successful outcome. | Existing users may prefer their familiar client. MailCairn reduces the scope to archive retrieval, but has fewer mail-client capabilities. |
| [Windows MBox Viewer reviews](https://sourceforge.net/projects/mbox-viewer/reviews/) | The reviewed material includes positive feedback dated 2026-01-20; older large-file complaints had subsequent fixes. | Do not reuse historical complaints as current performance failures. Review scores are not a controlled benchmark. |
| [Browser MBOX tools, including DevToolLab](https://devtoollab.com/tools/mbox-viewer) | Browser competitors advertise local processing and multi-GB streaming. Those are vendor claims, not independently reproduced benchmarks here. | “Browser tools cannot open large files” would be false positioning. MailCairn emphasizes persistent indexed storage, receipt visibility and recovery instead. |

No controlled competitor speed, memory, import-fidelity or accessibility comparison was performed. Configuration limits in MailCairn are not evidence of large-archive performance; see [executed test results](test-results.md).

## Why this scope

The selected user is comfortable obtaining an export but does not want to configure an always-running archiving server. The initial source version required Python; the current Windows64 review candidate bundles its runtime and adds a desktop control window. This reduces setup steps but is still unsigned and has not been validated on a second clean machine. Manual export and later re-import are deliberate limits, and users who need automatic capture should evaluate connected archivers instead. See the current [product-form decision](product-form.md).

Implemented differentiation maps to specific checks:

- Import receipts identify recognized record outcomes, offsets and hashes; skipped spans remain the user's responsibility to preserve in the original source.
- SHA-256 deduplication prevents storing identical message bytes twice while retaining different content with the same Message-ID. It is not semantic deduplication.
- The archive contains raw mail and a persistent search index; restarting does not require importing the source again.
- SQLite snapshot backup and restore support a recoverable archive. Hash checks concern stored bytes, not export completeness or message authenticity.
- Mail HTML becomes inert text. The application does not need an AI service or access to an email account to fulfill this workflow.

Other directions were screened but not selected. Calendar migration comparison already has a close functional alternative: [ICS Compare](https://grichard.eu/en/tools/ics-compare/) handles missing, modified and duplicate events. Google Takeout photo repair and local PDF redaction also had substantial existing competition in the initial screen; no sufficiently differentiated workflow was established. Those screens were not exhaustive market audits, and this decision does not imply email archiving is an empty market.

## Acquisition, repeated use and revenue: hypotheses only

Potential discovery channels are searchable guides about reopening Gmail exports, recovering attachments and restoring a local archive, plus a clearly documented GitHub release. Useful comparisons should recommend existing alternatives when they fit better. Community participation must follow each community's rules and disclose authorship; no promotional posts or outreach were sent for this research.

Expected use is episodic: periodic export imports, occasional historical searches and backup/restore checks. Daily engagement is not an appropriate success metric. A useful validation study would observe whether first-time users can import their own permitted data, explain a partial receipt, locate a known message and restore a backup without help. Next, measure voluntary repeat imports and successful later retrieval; gather consent without collecting message contents.

A plausible revenue experiment is a separately licensed, packaged edition or paid support for permitted commercial use. A one-time desktop purchase may fit episodic use better than a subscription, but this has not been tested. **There is no validated price, forecast or commitment to offer these services.** Free capable alternatives may make willingness to pay low. The current [commercial licensing policy](../COMMERCIAL.md) preserves the rights holder's options without claiming revenue or granting commercial rights.

Continue only if real users show that receipt clarity, recovery and setup simplicity materially improve their task. Narrow or stop expansion if users are satisfied with existing products, cannot tolerate manual exports, or need provider synchronization more than the chosen workflow.
