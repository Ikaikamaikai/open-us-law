# Storage and database options: price check

Checked 2026-10-18 against official vendor pages. Each section lists what was found and the source links.

Job A = storing the original PDFs (about 13-16 GB). Job B = the searchable records database (a few hundred MB now).

## Cloudflare R2 object storage (Standard storage class), for job A: storing the roughly 2,970 original government PDFs and letting the public download them

Confidence: high

**Free:** Free every month, on Standard storage only: 10 GB-month of storage, 1 million Class A operations (writes and uploads, such as PutObject and CreateMultipartUpload), 10 million Class B operations (reads, such as GetObject and HeadObject), and unlimited egress (data downloaded to the internet). Deletes are always free. The free tier does not cover the Infrequent Access storage class. Unauthorized requests (HTTP 401) are not charged. Source: https://developers.cloudflare.com/r2/pricing/ (last updated Oct 1, 2026).

**Paid:** Standard storage: $0.015 per GB-month. Class A: $4.50 per million requests. Class B: $0.36 per million requests. No retrieval fee. Infrequent Access storage: $0.01 per GB-month, Class A $9.00 per million, Class B $0.90 per million, $0.01 per GB retrieved, and a 30-day minimum storage charge. Usage is rounded up to the next whole unit, so 1.1 GB-month is billed as 2 GB-month and 1,000,001 operations as 2 million. Storage is measured as the average of each day's peak storage over a 30-day period. Applied to this project (my arithmetic from the published rates): 13 to 16 GB stored means 3 to 6 GB above the free 10 GB, about $0.05 to $0.09 per month ($0.54 to $1.08 per year). At 50 GB: 40 x $0.015 = $0.60 per month. At 100 GB: $1.35 per month. Uploading about 3,000 files uses about 3,000 Class A operations, well under the 1 million free. Not confirmed: whether Cloudflare actually charges a card for amounts this small or has a minimum invoice. Source: https://developers.cloudflare.com/r2/pricing/

**When the public downloads or searches:** Bandwidth (egress) is $0 for every storage class. The pricing page says egress straight from R2 through the Workers API, the S3 API or r2.dev domains is free, but other metered services connected to a bucket may charge. The cost of a public download is the read operation: each download that reaches the bucket is one Class B GetObject. The first 10 million per month are free, then $0.36 per million. Cloudflare's own billing example of 10 million reads per day for a month (about 300 million) totals $104.40. When files are served through a custom domain with Cloudflare's cache, cache misses route through one upper-tier data center before they reach R2, and Cloudflare says this means "fewer requests to R2". So repeat downloads of the same PDF from cache should not count as R2 reads. That last point is my inference from the docs, not a stated billing rule. PDF is on Cloudflare's default list of cached file types. On Free, Pro and Business plans the cache holds files up to 512 MB, so the largest PDF here (~40 MB) can be cached. Not confirmed: a browser's built-in PDF viewer sometimes fetches a file in pieces (range requests), and I found no official statement on how those count when the file is not cached. Sources: https://developers.cloudflare.com/r2/pricing/ , https://developers.cloudflare.com/changelog/post/2024-11-20-smart-tiered-cache-for-r2/ , https://developers.cloudflare.com/cache/concepts/default-cache-behavior/

**Size limits:** Max object size: about 4.995 TiB (multipart upload). Max single-request upload: about 4.995 GiB. Multipart parts: 5 MiB to 5 GiB each, up to 10,000 parts. Storage per bucket: unlimited. Buckets per account: 1,000,000. Object name (key) length: 1,024 bytes. Object metadata: 8,192 bytes. Writes to the same key: 1 per second (faster returns HTTP 429). Custom domains: 100 per bucket. r2.dev public URL: a "variable rate limit" with HTTP 429 and possible bandwidth throttling, and "not intended for production usage". Cloudflare REST API (management calls): 1,200 requests per 5 minutes per account. Wrangler (Cloudflare's command-line tool) uploads files up to 315 MB, one at a time. For bulk uploads Cloudflare points to rclone or other S3-compatible tools. CDN cache maximum per file: 512 MB on Free, Pro and Business plans. Sources: https://developers.cloudflare.com/r2/platform/limits/ (last updated Jun 8, 2026), https://developers.cloudflare.com/r2/objects/upload-objects/ (last updated Jul 29, 2026), https://developers.cloudflare.com/cache/concepts/default-cache-behavior/ (last updated Sep 14, 2026)

**Fit for this project:** R2 is a place to keep files and hand them to anyone who clicks a link. It only stores the PDFs. It does not search inside them, so the search bar (job B) would need something else. For the original PDFs (job A), here is how the published numbers apply. Your 13 to 16 GB is a bit over the 10 GB free allowance, so storage would cost about 5 to 9 cents a month. That grows by about 1.5 cents for each extra GB (roughly $0.60 a month at 50 GB, $1.35 at 100 GB). Downloads have no bandwidth charge, however many gigabytes people pull. Cloudflare counts "reads" instead: 10 million free per month, then 36 cents per million. A small public-records site would have to get very popular to pass 10 million PDF opens a month, and cached repeat downloads should not count against R2 at all. Uploading all ~2,970 files once uses a tiny share of the free write allowance. File size is not a problem: your largest PDF (~40 MB) is far below every limit, and Cloudflare's cache will hold PDFs that size. Your domain is already registered at Cloudflare. R2 wants the domain set up in the same Cloudflare account to serve files from your own address (for example a files.hawaiipublicinfo.com style address). That custom-domain route is the one Cloudflare supports for real public traffic; the free r2.dev address is rate-limited and meant only for testing. Possible problems: (1) You must turn on an R2 subscription through a checkout flow even to use the free tier, and outside guides say this asks for a card or PayPal. (2) There is no hard spending cap. Budget alerts only email you, they do not stop charges. (3) If a scraper or bot hammered uncached files, read charges could appear. (4) Cloudflare's general CDN terms restrict serving "large files" without one of its paid services. The terms name the "Developer Platform" as such a service and do not mention R2 by name, so whether R2 fully covers this is my inference. Your files are not locked in: R2 works with the standard S3 protocol, and leaving has no bandwidth fee.

**Catches:**
- You must add an R2 subscription through a checkout flow before using R2, even on the free tier (official get-started page). Cloudflare's docs do not say a credit card is required, but third-party 2025-2026 guides say a card or PayPal must be on file as verification, and one forum report says the payment method had to be added to the account first. The card requirement is not confirmed by an official source.
- No hard spending cap. Budget alerts exist, and since June 2026 Cloudflare has been creating a default $10 alert on Pay-as-you-go accounts. Cloudflare says the alert is informational only and does not cap usage. Usage is processed once a day, so an alert fires the day after the threshold is crossed.
- The free tier applies only to Standard storage. Putting files in Infrequent Access removes the free allowance and adds a $0.01/GB retrieval fee and a 30-day minimum charge.
- Billing rounds up to the next whole unit: 10.1 GB is billed as 11 GB-month, and 10,000,001 reads as 11 million.
- The free r2.dev public address is rate-limited, may throttle bandwidth, and Cloudflare says it is for development only. Pointing a CNAME at r2.dev is an unsupported setup. Production public access is meant to use a custom domain that is a zone in the same Cloudflare account. Caching, WAF and bot protection only work with a custom domain.
- With caching on, a deleted or replaced file can keep being served until the cache expires or is purged. A 404 for a file you upload later can also stay cached for a while.
- Cloudflare's CDN service terms (updated Sep 28, 2026) say non-Enterprise customers must use specific paid services, such as 'the Developer Platform, Images, and Stream', to serve video and other large files through the CDN, and Cloudflare may limit CDN use for a 'disproportionate percentage' of large files served without them. R2 is not named in that clause. Whether R2 counts as the qualifying service is an inference, not confirmed.
- R2 stores and serves files only. It does not make PDF contents searchable.
- A bucket's location can only be set at creation, through a best-effort location hint (options include Western North America and Oceania) or a fixed jurisdiction (us, eu, fedramp). It cannot be changed later, and Hawaii is not a listed region.
- Wrangler, Cloudflare's command-line tool, uploads only one file at a time and only files up to 315 MB. For bulk uploads Cloudflare points to rclone or another S3-compatible tool.

**Sources:**
- https://developers.cloudflare.com/r2/pricing/ (Free tier (10 GB-month, 1M Class A, 10M Class B, free egress); Standard $0.015/GB-month, Class A $4.50/M, Class B $0.36/M; Infrequent Access prices, retrieval fee and 30-day minimum; free tier is Standard-only; rounding up to the next unit; 30-day average of daily peak storage; billing examples ($14.85, $104.40); free deletes; 401s not charged; which operations are Class A or B. Last updated Oct 1, 2026.)
- https://developers.cloudflare.com/r2/platform/limits/ (Max object size ~4.995 TiB; single upload ~4.995 GiB; 10,000 parts; unlimited storage per bucket; 1,000,000 buckets; 1,024-byte keys; 8,192-byte metadata; 1 write per second per key; 100 custom domains per bucket; r2.dev variable rate limit and not for production; REST API 1,200 requests per 5 minutes. Last updated Jun 8, 2026.)
- https://developers.cloudflare.com/r2/buckets/public-buckets/ (Public access by custom domain or r2.dev; r2.dev rate-limited and for development only; custom domain must be a zone in the same account; caching, WAF and bot management need a custom domain; default caching covers only certain file types; CNAME to r2.dev unsupported. Last updated Sep 25, 2026.)
- https://developers.cloudflare.com/r2/get-started/ (An R2 subscription is required and is added through a checkout flow; 'R2 is free to get started with included free monthly usage.' No mention of a card. Last updated Apr 21, 2026.)
- https://developers.cloudflare.com/cache/concepts/default-cache-behavior/ (PDF is on the default cached extensions list; max cacheable file is 512 MB on Free, Pro and Business (5 GB default on Enterprise). Last updated Sep 14, 2026.)
- https://developers.cloudflare.com/changelog/post/2024-11-20-smart-tiered-cache-for-r2/ (With Smart Tiered Cache, cache misses route through an upper tier before reaching R2, meaning 'fewer requests to R2'. This supports the inference that cached downloads do not create R2 reads. Dated Nov 20, 2024.)
- https://developers.cloudflare.com/r2/reference/consistency/ (Cached deleted or overwritten objects can still be served until TTL expiry or purge; 404s are cached by default.)
- https://developers.cloudflare.com/r2/objects/upload-objects/ (Wrangler uploads up to 315 MB, one object at a time; rclone or S3 tools recommended for bulk; multipart part sizes 5 MiB to 5 GiB. Last updated Jul 29, 2026.)
- https://developers.cloudflare.com/changelog/post/2026-06-15-budget-alerts-default-on/ (Default $10 budget alert on Pay-as-you-go accounts; informational only, does not cap usage; processed daily.)
- https://developers.cloudflare.com/changelog/post/2026-04-13-billable-usage-dashboard-and-budget-alerts/ (Budget alerts are dollar thresholds that send email when projected spend crosses them; available to Pay-as-you-go accounts using R2.)
- https://developers.cloudflare.com/r2/reference/data-location/ (Location hints (wnam, enam, weur, eeur, apac, oc) are best effort; jurisdictions us, eu, fedramp; jurisdiction cannot be changed after creation. Last updated Aug 19, 2026.)
- https://www.cloudflare.com/service-specific-terms-application-services/ (CDN terms: non-Enterprise customers must use specific paid services (e.g., the Developer Platform, Images, and Stream) to serve video and other large files; Cloudflare may limit CDN use otherwise. R2 not named. Last updated Sep 28, 2026.)
- https://tech-insider.org/au/how-to-set-up-cloudflare-r2-2026/ (Third-party (not official): says Cloudflare asks for a payment method before the first bucket can be created, as verification. Used only for the unconfirmed card-requirement point.)
- https://dev.to/leonwong282/the-complete-beginners-guide-to-cloudflare-r2-image-hosting-2025-2g4k (Third-party (not official): says activating R2 requires binding a credit card or PayPal for verification. Used only for the unconfirmed card-requirement point.)

## Backblaze B2 Cloud Storage (pay-as-you-go), served through Cloudflare's free egress partnership. Covers job A (original PDFs) only.

Confidence: high

**Free:** Taken from Backblaze's live pricing page (https://www.backblaze.com/cloud-storage/pricing, fetched 2026-10-18; the page itself shows no date):
- Storage: "First 10GB storage is always free."
- Egress (downloads): free up to 3x your average monthly storage, averaged by byte-hours over the billing cycle. Downloads through partner CDNs are unlimited and free. The page names Cloudflare as a partner: "unlimited free egress when downloading to or through partner content delivery networks (CDNs) and compute services, including Fastly, Cloudflare, bunny.net, ...".
- API transactions: Class A (uploads), Class B (downloads/reads, including b2_download_file_by_name and S3 GetObject) and Class C (listing/bucket management) are all free. Only Class D (Event Notification outbound calls) is billed, and the first 2,500 per day are free (https://www.backblaze.com/cloud-storage/transaction-pricing).
- No minimum file-size fees and no minimum storage-duration fees (pricing page).
- Backblaze's blog post of March 17, 2026 confirms that API calls became free for all B2 customers starting May 1, 2026, and that 3x free egress and unlimited free egress to CDN partners did not change (https://www.backblaze.com/blog/?p=112830).
- Cloudflare side: the Free plan is "$0" per month and "CDN" is listed as "Included" (https://www.cloudflare.com/plans/network-cdn/).

**Paid:** - Storage beyond 10 GB costs $6.95 per TB per month ($0.00695 per GB per month). It is billed per byte-hour ("$6.95/TB/30 days") (https://www.backblaze.com/cloud-storage/pricing). The price went from $6 to $6.95/TB effective May 1, 2026 (https://www.backblaze.com/blog/?p=112830). Before that it went from $5 to $6/TB effective October 3, 2023 (https://backblaze.com/blog/2023-product-announcement; seen in a search-result snippet, the page itself was not opened).
- Egress beyond 3x average stored data, when not going through a partner such as Cloudflare: $0.01 per GB (pricing page).
- Class D calls: $0.004 per 10,000 after the first 2,500 per day (transaction-pricing page).
- Optional annual or multi-year commitments (1 to 5 years, paid up front) give discounts (pricing page). These are not needed at this size.
- Worked numbers for this project, using the $6.95/TB rate: 15 GB stored means 5 GB is billable, about $0.035 per month (about $0.42 per year). 50 GB is about $0.28 per month. 100 GB is about $0.63 per month. 1 TB is about $6.88 per month.
- Billing: charges are calculated daily and charged monthly on the anniversary of the account's creation date (https://help.backblaze.com/hc/en-us/articles/218514337-Understanding-the-B2-Billing-Page; seen in a search-result snippet). I could not confirm from an official source whether Backblaze actually charges a card for tiny amounts like $0.03, or whether there is a minimum invoice.

**When the public downloads or searches:** - Through Cloudflare on the site's own domain (for example files.hawaiipublicinfo.com): Backblaze charges $0 for the download, with no volume limit. Sources: the pricing page FAQ lists Cloudflare under "unlimited free egress"; the Backblaze guide says "no download fees from Backblaze" (https://www.backblaze.com/docs/cloud-storage-deliver-public-backblaze-b2-content-through-cloudflare-cdn, updated June 26, 2026); the 2018 announcement says it applies to "all Cloudflare customers using any plan" (https://www.backblaze.com/blog/backblaze-and-cloudflare-partner-to-provide-free-data-transfer/). The Backblaze guide says nothing about Cloudflare's own charges. Cloudflare's Free plan is $0/month with CDN "Included", but its pricing page gives no per-GB bandwidth terms (https://www.cloudflare.com/plans/network-cdn/).
- Straight from Backblaze, without Cloudflare: free up to 3x average stored data per month (about 45 GB/month at 15 GB stored), then $0.01 per GB (pricing page).
- Download API calls (Class B) are free (transaction-pricing page).
- Cloudflare caches PDF files by default, so repeat downloads are served from Cloudflare's cache. The Free plan caches files up to 512 MB each (https://developers.cloudflare.com/cache/concepts/default-cache-behavior/, updated Sept 14, 2026).

**Size limits:** - Maximum file size: 10 TB using the "large file" multi-part upload (parts of 5 MB to 5 GB) (https://www.backblaze.com/docs/cloud-storage-large-files, dated Aug 29, 2023).
- Maximum single upload with the CLI or Native API: 5 GB (https://www.backblaze.com/docs/cloud-storage-files, updated May 7, 2026).
- Web-console uploads: the Cloudflare guide says 500 MB per file, while the Files page says 0 bytes to 5 GiB. The two official pages conflict. Either limit is far above the largest PDF here (about 40 MB).
- File names: up to 1,024 bytes UTF-8 (Files page).
- Total account storage: no limit stated in the docs I checked.
- Cloudflare Free plan: caches files up to 512 MB each (Cloudflare cache docs).
- B2 is file storage only. It has no database or search features.

**Fit for this project:** In plain terms, Backblaze B2 is a large online folder. You upload the roughly 2,970 PDFs once, and each file gets a permanent web link the public can click to open or download it. Because hawaiipublicinfo.com is already managed at Cloudflare, those links can be routed through Cloudflare so they look like files.hawaiipublicinfo.com/some-record.pdf. Backblaze's own pages say downloads routed through Cloudflare cost nothing, however many people download.

What it costs: the first 10 GB of storage is free. The current 13-16 GB collection would cost about 3 to 4 cents a month (well under $1 a year). 50 GB would be about 28 cents a month and 100 GB about 63 cents a month. There are no per-click or per-download fees. If someone downloads straight from Backblaze and skips Cloudflare, those downloads are free up to about 3 times what you store each month, then 1 cent per GB.

What setup involves: create a "public" bucket, which is Backblaze's word for a folder anyone can read. Upload the files with a command-line tool, since the website uploader is clumsy for thousands of files. Then add a few Cloudflare settings: a DNS record pointing at Backblaze, a URL rewrite rule, and an SSL setting. Backblaze publishes a step-by-step guide for this. The rewrite rule matters. Without it, your domain could be used to fetch other Backblaze customers' public files.

What could be a problem:
(1) It is not strictly $0. Once you pass 10 GB there is a small monthly charge.
(2) Before you can make any folder public, Backblaze requires a verified email plus either a payment history or a small card payment, which is credited back to your balance.
(3) This only covers storing and serving the PDFs. It does nothing for the searchable database or the search bar (job B).
(4) Cloudflare's own rules for its free and lower paid plans say "video and other large files" need specific paid Cloudflare services. Cloudflare may limit accounts that serve "a disproportionate percentage of pictures, audio files, or other large files." The rules do not define "large," so it is unclear whether a site that mostly serves 1-40 MB PDFs would fall under that. Backblaze's 2018 announcement itself told users to check Cloudflare's terms.
(5) Backblaze has raised storage prices twice since 2023 (from $5 to $6, then to $6.95 per TB).
(6) Anyone who has a file's link can download it. That fits public records, but nothing in a public bucket can stay private.

**Catches:**
- A credit card is effectively needed: making a bucket public the first time requires a verified email AND either a payment history on file or a small card payment credited to the account (https://www.backblaze.com/docs/cloud-storage-create-and-manage-buckets, updated May 22, 2026). The fee amount is not stated.
- Only 10 GB is free. The current 13-16 GB collection already exceeds it, so there is a small monthly bill (about $0.035/month at 15 GB). I could not confirm whether Backblaze charges or rolls over tiny amounts, or has a minimum invoice.
- Free unlimited egress applies only when downloads go through Cloudflare (or another named partner) on your own domain, set up as Backblaze's guide describes: public bucket, proxied CNAME, URL-rewrite Transform Rule, SSL Full (Strict). Backblaze's guide page carries a 'stale: true' metadata flag even though it is dated June 26, 2026.
- Cloudflare's Service-Specific Terms (updated Sept 28, 2026) say non-Enterprise customers 'must use' certain Paid Services 'to serve video and other large files via the CDN', and Cloudflare may limit or disable CDN use for serving 'a disproportionate percentage of pictures, audio files, or other large files'. 'Large files' is not defined, so how this applies to a site serving mostly multi-MB PDFs is unclear (https://www.cloudflare.com/service-specific-terms-application-services/).
- The Backblaze-Cloudflare free-transfer announcement dates from 2018. Backblaze's current pricing page and its March 2026 blog post still list Cloudflare as an unlimited-free-egress partner. Cloudflare's own Bandwidth Alliance page, as fetched, did not name Backblaze among the partners it linked. Cloudflare's undated Backblaze partner page still describes Backblaze as a founding Bandwidth Alliance member.
- Prices change. Storage went from $5 to $6/TB (Oct 3, 2023) and from $6 to $6.95/TB (May 1, 2026). The Terms say usage fees accrue at 'then-current rates' (https://www.backblaze.com/company/policy/terms-of-service, effective April 16, 2026).
- Spending caps are optional and are off by default. With no caps set, 'usage is unlimited' and charges can accrue without limit. Caps are set in dollars per day for storage and for Class A/B/C transactions; Class D cannot be capped. Alerts fire at 75% and 100% of a cap. The docs do not say what happens when a cap is hit, and do not clearly describe a separate cap on download bandwidth (https://www.backblaze.com/docs/cloud-storage-data-caps-and-alerts).
- Unpaid or rule-violating accounts can be suspended or terminated, and Backblaze 'may delete your data'. No grace period is stated in the Terms. The Terms do not describe the B2 free 10 GB as a formal free tier; that only appears on the pricing page.
- A public bucket means anyone with a file's URL can download it. Private files would need a different, more complex setup (Backblaze has a separate guide for private buckets).
- Storage only: B2 gives no database, full-text search or PDF text extraction, so job B needs something else.
- The web-console upload limit is stated inconsistently (500 MB in the Cloudflare guide, 5 GiB on the Files page). Bulk-uploading about 2,970 files is easier with the B2 CLI or an S3-compatible tool.

**Sources:**
- https://www.backblaze.com/cloud-storage/pricing ($6.95/TB/month; first 10 GB always free; free egress up to 3x average monthly storage, then $0.01/GB; unlimited free egress through partners including Cloudflare; free transactions; no minimum file-size or storage-duration fees; commitment discounts (fetched 2026-10-18, page undated))
- https://www.backblaze.com/cloud-storage/transaction-pricing (Class A/B/C API calls free (downloads are Class B); Class D $0.004 per 10,000 after 2,500/day free)
- https://www.backblaze.com/blog/?p=112830 (Blog post of March 17, 2026: price $6 to $6.95/TB effective May 1; API calls free from May 1; 3x free egress and unlimited partner egress unchanged)
- https://backblaze.com/blog/2023-product-announcement (Price $5 to $6/TB and 3x free egress, effective Oct 3, 2023 (seen in a search-result snippet; page not opened))
- https://www.backblaze.com/docs/cloud-storage-deliver-public-backblaze-b2-content-through-cloudflare-cdn (Setup steps for B2 behind Cloudflare; bucket must be public; Cloudflare Free plan usable; 'no download fees from Backblaze'; Transform Rule needed; updated June 26, 2026, with a stale flag)
- https://www.backblaze.com/blog/backblaze-and-cloudflare-partner-to-provide-free-data-transfer/ (2018 announcement: zero B2 transfer fees to Cloudflare on any Cloudflare plan; advises checking Cloudflare's terms on non-HTML content)
- https://www.cloudflare.com/partners/technology-partners/backblaze/ (Cloudflare says Backblaze offers free data transfer to shared customers and is a founding Bandwidth Alliance member (undated))
- https://www.cloudflare.com/bandwidth-alliance/ (Bandwidth Alliance described as discounting or waiving egress; Backblaze not named among the partners linked on the page as fetched)
- https://www.cloudflare.com/service-specific-terms-application-services/ (CDN terms (updated Sept 28, 2026): paid services required for video and other large files; possible limits for a disproportionate share of large files)
- https://developers.cloudflare.com/cache/concepts/default-cache-behavior/ (PDF cached by default; Free plan max cacheable file size 512 MB (updated Sept 14, 2026))
- https://www.cloudflare.com/plans/network-cdn/ (Cloudflare Free plan $0/month, CDN included)
- https://www.backblaze.com/docs/cloud-storage-create-and-manage-buckets (First public bucket requires a verified email plus a payment history or a small credited card fee (updated May 22, 2026))
- https://www.backblaze.com/docs/cloud-storage-data-caps-and-alerts (Caps in dollars per day; storage and Class A/B/C cappable, Class D not; unlimited charges without caps; alerts at 75%/100% (updated May 22, 2026))
- https://www.backblaze.com/docs/cloud-storage-create-and-manage-caps-and-alerts (Caps cover 'storage, downloads, or transaction usage'; does not say what happens at the cap (updated April 23, 2026))
- https://www.backblaze.com/docs/cloud-storage-files (5 GB max single upload via CLI/Native API; 1,024-byte file names (updated May 7, 2026))
- https://www.backblaze.com/docs/cloud-storage-large-files (Large files up to 10 TB; parts 5 MB to 5 GB (dated Aug 29, 2023))
- https://www.backblaze.com/company/policy/terms-of-service (Usage fees at then-current rates; accounts may be suspended or terminated and data deleted for non-payment or violations; effective April 16, 2026)
- https://help.backblaze.com/hc/en-us/articles/218514337-Understanding-the-B2-Billing-Page (Charges calculated daily, billed on the monthly anniversary of account creation (seen in a search-result snippet))

## Hugging Face Hub dataset repositories (public or private "datasets" on huggingface.co), used for job A (original PDFs) and job B (searchable records)

Confidence: medium

**Free:** Free user or org account: public storage is "Best-effort" with no number given; private storage is 100GB (https://huggingface.co/docs/hub/storage-limits). The footnote says HF aims to keep public storage generous, but "Beyond the first few gigabytes, please use this resource responsibly by uploading content that offers genuine value to other users. If you need substantial storage space, you will need to upgrade" (same page). Downloads cost nothing extra: the pricing page says "Egress and CDN included at no extra cost" (https://huggingface.co/pricing). The free search API (dataset viewer /search) needs no account for public datasets (https://huggingface.co/docs/dataset-viewer/quick_start). Free rate limits, counted per 5-minute window: anonymous users get 3,000 file downloads ("resolvers") per IP address, 500 API calls and 100 page views; logged-in free users get 5,000 resolvers, 1,000 API calls and 200 pages. HF marks the anonymous and free numbers "subject to change over time depending on platform health". The table is labeled "in September '25" (https://huggingface.co/docs/hub/rate-limits). A live check on 2026-10-18 showed the response header ratelimit-policy "resolvers";q=3000;w=300 on an anonymous request, so the anonymous resolver limit still stood.

**Paid:** PRO is $9/month (https://huggingface.co/pricing). PRO includes "Up to 10TB" of public storage, plus add-ons and grants for impactful work, and 1TB of private storage plus pay-as-you-go (https://huggingface.co/docs/hub/storage-limits). Team is $20/user/month and Enterprise $50/user/month (https://huggingface.co/pricing). Team includes 12TB public base plus 1TB per seat, and 1TB private per seat (https://huggingface.co/docs/hub/storage-limits). Public storage add-on, paid plans only: $12/TB/month for 1, 5, 10 or 20 TB, and $10/TB/month for 50TB (https://huggingface.co/docs/hub/storage-limits). The pricing page also lists lower volume tiers: $9/TB/mo at 200TB+ and $8/TB/mo at 500TB+ (https://huggingface.co/pricing). Extra private storage costs $18/TB/month at base, $16 at 50TB+, $14 at 200TB+ and $12 at 500TB+ (https://huggingface.co/docs/hub/storage-limits). PRO rate limits: 12,000 resolvers, 2,500 API calls and 400 pages per 5 minutes (https://huggingface.co/docs/hub/rate-limits).

**When the public downloads or searches:** HF does not charge for downloads. The pricing page says "Egress and CDN included at no extra cost" (https://huggingface.co/pricing). Downloads are limited by request counts instead of money: 3,000 file downloads per 5 minutes per IP address for anonymous visitors, 5,000 for a logged-in free account, with HTTP error 429 when exceeded (https://huggingface.co/docs/hub/rate-limits). If visitors' browsers open the HF links directly, each visitor's own IP is counted. If the founder's server fetches files for visitors, all that traffic counts against the server's single IP or token. The second point is my reading of the per-IP / per-account rule, not a statement from HF. HF publishes no rate-limit numbers for the dataset viewer /search API, and my test responses from it carried no rate-limit headers.

**Size limits:** No single file may exceed 500GB (hard limit). HF recommends files under 200GB, fewer than 100k files per repo, fewer than 10k entries per folder ("cannot exceed 10k files per folder") and fewer than 100 files per commit. There is no per-repo size limit, but everything counts against the account's storage quota (https://huggingface.co/docs/hub/storage-limits). The project's largest PDF (~40MB) and 2,970 files are well inside these limits, though the PDFs would need to be split across subfolders if any one folder would hold more than 10k files. The Hub accepts PDF as a native format, along with Parquet, CSV, JSON/JSONL and text (https://huggingface.co/docs/hub/datasets-adding). Search API limits: at most 100 results per request (paged with offset/length). It only works on datasets with a Parquet export, and "the indexing for /search can be partial if the dataset is bigger than 5GB. In that case, it only uses the first 5GB" (https://huggingface.co/docs/dataset-viewer/search). The automatic Parquet conversion is likewise capped at 5GB, and private datasets get it only if owned by PRO/Enterprise (https://huggingface.co/docs/dataset-viewer/parquet). Git history: deleting or replacing files does not free storage unless history is "super-squashed", which cannot be undone (https://huggingface.co/docs/hub/storage-limits).

**Fit for this project:** Job A (the PDFs). Hugging Face can technically hold 13-16 GB of PDFs in a public dataset and hand them out to the public. In a live test on 2026-10-18, a PDF link in someone else's public dataset (huggingface.co/datasets/<owner>/<name>/resolve/main/<file>.pdf) redirected to HF's content delivery network. The file came back labeled as a PDF, marked to open in the browser ("inline"), and readable from any website (access-control-allow-origin: *). HF charges nothing for downloads. Three things could be a problem. (1) "Free" public storage has no fixed allowance. It is "best-effort", and HF asks anyone going past "the first few gigabytes" to upload content of genuine value to the community, or else upgrade. 13-16 GB is past that line, so the free space is a courtesy, not a promise. (2) HF says large datasets should be shared "to enable community reuse" for AI/data work. It says that if you don't expect reuse, "other platforms are likely more suitable", and its content policy lists "Hosting excessive or irrelevant data in repositories" as abuse. A public-records collection might count as useful data, but HF decides, and its terms let it remove content "at any time, at our sole discretion". (3) The links point to huggingface.co, not hawaiipublicinfo.com, and I found nothing in the docs I read about using your own domain. Rate limits are per visitor IP (3,000 file downloads per 5 minutes for anonymous visitors), which is plenty for one person reading documents.

Job B (the search bar). HF stores files, not a live database. The only search built into HF is the free "dataset viewer" search API. It runs keyword search (BM25, with an English word-stemmer) over the text columns of a public dataset and returns up to 100 matching rows per request. Only the first 5 GB of a dataset is searched, which covers the current few hundred MB but could matter at "a few GB later". In my test on a small public dataset, 4 of 6 search requests failed with "the dataset index is loading" after waiting 20-80 seconds. The 2 that worked took 2.3 and 5.3 seconds, which is slow for a public search bar. The other route is to keep the records as a file on HF (for example Parquet, which supports partial downloads) and have the website search that file itself. That still requires the founder to build the search part elsewhere; HF only stores the file.

Private datasets get 100 GB free, but then the public website cannot reach the files without a secret key, and the built-in search works on private datasets only for paying (PRO) users.

**Catches:**
- Free public storage is 'Best-effort' with no stated number. Past 'the first few gigabytes', HF asks for content of genuine community value or an upgrade to PRO ($9/mo) (https://huggingface.co/docs/hub/storage-limits).
- HF's stated purpose for large datasets is community reuse (AI/data). It says: 'If you plan to upload a dataset you anticipate won't have any further reuse, other platforms are likely more suitable.' A dataset card (README) is required for large datasets (https://huggingface.co/docs/hub/storage-limits).
- The content policy (effective April 10, 2025) lists 'Hosting excessive or irrelevant data in repositories' as platform abuse (https://huggingface.co/content-policy).
- The content policy restricts 'publishing others' private information, such as a physical or email address, without their explicit permission'. Hearing decisions that name individuals or include addresses could fall under this (https://huggingface.co/content-policy).
- The terms of service (effective Sept 15, 2022) say: 'We may remove your Content at any time, at our sole discretion', 'we reserve the right to suspend or terminate your access to the Services anytime with or without cause', and the service comes with no guarantee it will be 'uninterrupted or available at any time' (https://huggingface.co/terms-of-service).
- Public repositories grant every user 'a perpetual, irrevocable, worldwide, royalty-free, non-exclusive license' to the content (https://huggingface.co/terms-of-service).
- Anonymous and free rate limits are 'subject to change over time depending on platform health'. The rate-limit table is labeled September 2025 (https://huggingface.co/docs/hub/rate-limits).
- Built-in search: only the first 5GB is indexed; results are listed in row order with no highlighting of matches; at most 100 rows per request (https://huggingface.co/docs/dataset-viewer/search). In my own test on 2026-10-18, 4 of 6 calls returned HTTP 500 'the dataset index is loading' after 20-80 seconds. That is one test of one small dataset, not an official figure.
- The redirect address each PDF link sends you to is a signed CDN URL that expired about 1 hour later in my test. The website must link to the stable huggingface.co/.../resolve/... address, not the CDN one (observed live, 2026-10-18).
- The PDF responses carry a security header 'content-security-policy: default-src 'none'; media-src 'self'; sandbox allow-same-origin' (observed live). I could not check whether every browser's built-in PDF viewer shows such files in the page or downloads them instead. This needs a test in real browsers.
- Files are served from huggingface.co and us.aws.cdn.hf.co addresses. The docs I read mention no custom-domain option for dataset files.
- Dataset repos are Git-based. Every batch update of the records file keeps old versions in history, and that history counts toward storage until it is 'super-squashed', which is irreversible (https://huggingface.co/docs/hub/storage-limits). HF also offers non-versioned 'Storage Buckets' under the same storage policies (https://huggingface.co/docs/hub/storage-buckets). I did not research them further, since they are outside this option's scope.
- Private datasets: 100GB free, but files then require a secret token, and the built-in viewer/search/Parquet conversion works for private datasets only if owned by a PRO user or an Enterprise org (https://huggingface.co/docs/dataset-viewer/quick_start).

**Sources:**
- https://huggingface.co/docs/hub/storage-limits (Free: public 'Best-effort', private 100GB; PRO up to 10TB public + 1TB private; Team/Enterprise amounts; add-on $12/TB/mo (1-20TB), $10/TB/mo (50TB); private pay-as-you-go $18/$16/$14/$12 per TB/mo; 500GB hard file limit, <200GB recommended; <100k files/repo; 10k files/folder; 'first few gigabytes' guidance; community-reuse requirement; history/super-squash storage rules)
- https://huggingface.co/pricing (PRO $9/mo, Team $20/user/mo, Enterprise $50/user/mo; storage tiers $12/$10/$9/$8 public and $18/$16/$14/$12 private per TB/mo; 'Egress and CDN included at no extra cost')
- https://huggingface.co/docs/hub/rate-limits (Per-5-minute limits: anonymous per IP 500 API / 3,000 resolvers / 100 pages; free user 1,000 / 5,000 / 200; PRO 2,500 / 12,000 / 400; HTTP 429 when exceeded; table dated September 2025; anonymous/free limits subject to change)
- https://huggingface.co/docs/dataset-viewer/search (/search uses DuckDB full-text search with BM25 and Porter stemmer (English); searches string columns; max 100 rows per request; requires Parquet export; only first 5GB indexed if dataset is larger; rows ordered by row index, not highlighted)
- https://huggingface.co/docs/dataset-viewer/quick_start (Dataset viewer API base URL, no setup needed for public datasets; private datasets supported only for PRO users or Enterprise orgs; /rows and /search max 100 rows per call)
- https://huggingface.co/docs/dataset-viewer/parquet (Automatic Parquet conversion requires public dataset or PRO/Enterprise owner; partial conversion above 5GB; ~500MB shards)
- https://huggingface.co/docs/hub/datasets-adding (Upload via web drag-and-drop, hf CLI, Python library, or Git; PDF (.pdf) listed as natively supported format; public vs private choice at creation)
- https://huggingface.co/terms-of-service (Content removal at HF's sole discretion; suspension with or without cause; no availability guarantee; perpetual license to users for public repos; effective date Sept 15, 2022)
- https://huggingface.co/content-policy ('Hosting excessive or irrelevant data in repositories' listed as abuse; restriction on publishing others' private information such as addresses; effective April 10, 2025)
- https://huggingface.co/docs/hub/storage-buckets (Existence of non-versioned Storage Buckets as an alternative HF repo type with the same free storage allowance policy (not researched in depth))
- https://huggingface.co/datasets/AingeruBeOr/RAG_legal_comparison_PDFs/resolve/main/data/guia-cookies.pdf (Live test 2026-10-18: resolve URL returns 302 to us.aws.cdn.hf.co signed URL (~1 hour expiry), final response content-type application/pdf, content-disposition inline, access-control-allow-origin *, byte-range (206) supported, CSP sandbox header present, ratelimit-policy q=3000 per 300s for anonymous)
- https://datasets-server.huggingface.co/search?dataset=cornell-movie-review-data/rotten_tomatoes&config=default&split=train&query=lawyer&length=5 (Live test 2026-10-18: 4 of 6 search calls returned HTTP 500 'the dataset index is loading' after 20-80 s; successful calls took 2.3 s and 5.3 s; no rate-limit headers returned)

## Internet Archive (archive.org) uploads of public-domain government PDFs (job A: original PDFs)

Confidence: medium

**Free:** Uploading, storing and public downloading all cost $0. You need a free archive.org account (help.archive.org/help/uploading-a-basic-guide). The Terms of Use say "Access to the Archive's Collections is provided at no cost to you." I found no published storage quota, monthly bandwidth cap or per-GB fee for ordinary uploads. There is also no official pricing page that promises in writing that storage stays free forever with no quota; that it is free is shown by the absence of any fee, not by a written guarantee. Bulk uploads can use the free "ia" command-line tool, the Python library or the S3-like API. API keys are free at archive.org/account/s3.php.

**Paid:** Ordinary archive.org uploads have no paid tier. The Internet Archive's separate paid product for institutions is called Vault. It uses a "one-time price per gigabyte/terabyte for data deposited", with "no additional annual storage fees or data egress costs". The actual price is not published; you get a quote through an interest form or vault@archive.org (archive-it.org/vault/).

**When the public downloads or searches:** $0 for you and for the public. The Archive publishes no egress fee and no bandwidth limit. Public file links look like https://archive.org/download/<identifier>/<filename> and redirect (HTTP 302) to a storage server, such as dn7xxxxx.ca.archive.org. Speed numbers are my own test, not official figures: on 2026-10-18, from a US cloud server (not from Hawaii), a 13.9 MB government PDF downloaded in 2.2 s and 3.2 s (about 4.3 to 6.3 MB/s), with 1.1 to 2.3 s before the first byte arrived. A 164 KB PDF took about 1.5 s in total. Byte-range requests worked (HTTP 206). The Archive asks automated tools to send a descriptive User-Agent and to obey 429 "Too Many Requests" responses. It gives no numeric rate limits.

**Size limits:** The Archive's own help pages disagree with each other, and none of them is dated:
(1) Uploading Tips: "there is a 1TB size limit for item pages"; recommends at most 1,000 files or 500 GB per item.
(2) Uploading Troubleshooting: a single file should be no larger than about 500 to 700 GB; items should hold fewer than 10,000 files (not a hard limit) and not exceed 1 TB; "the API will allow up to 250,000 files".
(3) Bulk-upload rules: at most 500 files or 500 GB per item, and at most 5,000 files uploaded per day. The daily data limit is literally written as "TK" (a placeholder, never filled in).
(4) Developer docs: as a rule of thumb, items should stay under 100 GB and 10,000 files.
For scale: your set is about 2,970 PDFs, about 13 to 16 GB in total, with the largest around 40 MB. That is far below every one of these limits. Under the 5,000-files-per-day rule, the whole set could go up in one day, whether as one PDF per item or grouped into items.

**Fit for this project:** What it does well: the Internet Archive would store all the PDFs and let anyone open or download them at no cost to you, however many people use the site. Your website would link to (or embed) each PDF at an archive.org address. For example, a "View original" button would point to archive.org/download/your-item/file.pdf. The Archive also automatically creates extra copies of each PDF: a searchable text version, OCR plain-text files and page images. These are free to download, and the documents also become full-text searchable on archive.org itself. Speeds in my one test were a few megabytes per second, so a typical 4.5 MB file would open in a few seconds.

What could be a problem:
(1) The Archive's upload rules say it does not want copies of material that is still available online elsewhere, unless there is evidence it is about to be removed. Uploading such material "may result in their removal from archive.org and your account being locked." Any of your PDFs that are still posted on Hawaii government websites fall under that wording. Whether the Archive actually enforces this against government documents is not stated.
(2) The files live on archive.org, not on hawaiipublicinfo.com. Your site depends on the Archive staying up and keeping your items. Its 2014 Terms of Use promise nothing about uptime ("as-is and as-available") and let it end an account at its discretion. The Archive was fully offline for over a week in October 2024 after a cyberattack.
(3) Everything uploaded is public to the whole world. Nothing can be made private.
(4) A custom PDF viewer built into your own web pages may not be able to load the files from archive.org, because no cross-site permission header was returned in my test. Ordinary links, the browser's own PDF viewer, and the Archive's embeddable viewer (archive.org/embed/<identifier>) do work.
(5) Processing after upload can take anywhere from seconds to days, and sometimes fails. You can only get your own named collection after you have at least 50 related items, and an Archive staff member has to create it (up to two weeks).

**Catches:**
- Rule against mirroring material that is still online: the official 'What is ok or not ok to upload' page says 'we do not want to mirror items that are online without actual evidence that their removal is imminent.' It asks you to keep local copies and upload only after the originals are removed, with evidence. 'Uploading them prior to that may result in their removal from archive.org and your account being locked.'
- The Terms of Use are dated 31 Dec 2014. They state that access 'is granted for scholarship and research purposes only'. Uploading grants the Archive 'a nonexclusive, royalty-free right to use that content'. The Archive 'may immediately terminate this Agreement at its sole discretion'. Collections are 'as-is and as-available', with no guarantee that access 'will be uninterrupted, timely, secure, or error free'. There is no uptime guarantee (SLA) and no paid support for ordinary uploads.
- Outages: the official blog says archive.org went down after cyberattacks on Oct 9, 2024. It came back read-only on Oct 21, 2024, and uploading was still unavailable on that date. There are also unofficial reports of an outage of about 4 hours on Aug 16, 2026 (power failure). I could not confirm those on any official Internet Archive page.
- Everything is public. The S3 API docs say 'ACLs are fake. permissions are: World readable, Item uploader writable.' Files cannot be made private or restricted.
- Links must use archive.org/download/<identifier>/<filename>. The developer docs warn 'DO NOT LINK' to the numbered storage servers (ia8xxxxx / dn7xxxxx) the links redirect to, because 'we move items to new servers all the time.' Each download therefore goes through one redirect, which adds roughly 1 second before the first byte in my test.
- In my test on 2026-10-18, PDF responses carried no Access-Control-Allow-Origin (CORS) header. A JavaScript PDF viewer running on hawaiipublicinfo.com would therefore probably be blocked from fetching the files directly. Plain links and the archive.org/embed/<identifier> iframe are not affected (no X-Frame-Options header was seen).
- Automatic processing ('derivation') 'can vary from a few seconds, hours or sometimes days' and items 'can often timeout and fail' (Uploading Tips page).
- Your own named collection is created only by Archive staff, and only for accounts with at least 50 related items. Creation can take up to two weeks. Until then, items sit in a public community collection.
- Do not upload to test_collection: items there are deleted automatically after about 30 days.
- Bulk rules: at most 5,000 files per day. The S3 API can answer '503 SlowDown' when overloaded, and there is a check_limit endpoint to test for this. No numeric rate limits are published.
- Removal: an uploader can remove their own items from the 'My uploads' page ('Remove items'), and this takes effect within minutes. The page does not say whether the data is permanently erased. The S3 API says 'DELETE bucket is not allowed'. Deleting your account does NOT remove your items.
- Copyright: the Archive removes content when it receives copyright complaints and terminates the accounts of 'repeat infringers'. Statutes and agency or court decisions are generally not copyrightable. Documents written by private companies, such as franchise disclosure documents, are a different matter. This is general legal background, not confirmed on an official Archive page during this research.
- Organization-level legal history, from secondary sources: the Archive lost Hachette v. Internet Archive and did not seek Supreme Court review (Dec 2024), and it settled the record labels' 'Great 78' lawsuit on confidential terms (Sept 2025). Neither case involved user-uploaded government documents.
- The help pages give conflicting limits and carry no dates, so I could not confirm when they were last updated. The Terms of Use text is dated 2014; the archive.org item that holds it was last modified around 2025-05-01.

**Sources:**
- https://help.archive.org/help/uploading-a-basic-guide/ (A free account is required to upload; there is no stated fee; OCR depends on the language field)
- https://help.archive.org/help/uploading-tips/ (1 TB size limit per item; recommendation of at most 1,000 files or 500 GB per item; processing takes seconds to days and can fail; test_collection items removed after about 30 days)
- https://help.archive.org/help/uploading-troubleshooting/ (Single file about 500 to 700 GB maximum; fewer than 10,000 files per item; items not over 1 TB; API allows up to 250,000 files; 503-slowdown error mentioned)
- https://help.archive.org/help/uploading-what-is-not-ok-or-not-ok-to-upload/ (Bulk rules (500 files or 500 GB per item, 5,000 files per day, daily data limit left as 'TK'); rule against mirroring material still online; risk of removal and account lock)
- https://help.archive.org/?p=433 (Same bulk-upload limits (500 files or 500 GB per item, 5,000 files per day))
- https://archive.org/metadata/ia-page-terms (Full text of the Terms of Use (dated 31 Dec 2014), served through the metadata API because archive.org/about/terms only loads with JavaScript: no-cost access, 'scholarship and research purposes only', license granted to IA, termination at sole discretion, as-is with no uptime warranty, copyright removal policy)
- https://archive.org/developers/items.html (Download URL format archive.org/download/<identifier>/<filename>; redirects to storage servers; 'DO NOT LINK' warning; rule of thumb of 100 GB and 10,000 files per item)
- https://archive.org/developers/ias3.html (S3-like upload API; free keys; 503 SlowDown and check_limit; 'DELETE bucket is not allowed'; 'ACLs are fake... World readable')
- https://archive.org/developers/bots.html (Automated access must send a descriptive User-Agent and honor 429/Retry-After; no numeric limits; test_collection removed after about 30 days; contact info@archive.org for a permanent collection)
- https://archive.org/developers/ (List of tools: ias3 API, metadata API, ia command-line tool, Python library, OCR services)
- https://help.archive.org/help/files-formats-and-derivatives-file-definitions-2/ (Files created automatically from PDF uploads: searchable text PDF, hOCR, djvu.txt, OCR search text fed to full-text search, JP2 page images, thumbnail)
- https://archive.org/metadata/cia-readingroom-document-cia-rdp91m00696r000100090026-9 (Real example item showing the original PDF kept (source=original) alongside the automatically created OCR text, text PDF and page-image files)
- https://help.archive.org/help/collections-a-basic-guide/ (Collections are created only by admins; minimum 50 items; up to two weeks; items sit in a public open-source collection until then)
- https://help.archive.org/help/removing-your-item-pages-from-archive-org/ (Uploaders can remove their own items through My uploads > Remove items, taking effect within minutes)
- https://help.archive.org/help/downloading-a-basic-guide/ (Download options; a single PDF opens in the browser; bulk download with wget or the ia tool)
- https://blog.archive.org/2024/10/21/internet-archive-services-update-2024-10-21/ (Official outage update: cyberattacks Oct 9, 2024; read-only archive.org from Oct 21; uploading unavailable at that time)
- https://pasqualepillitteri.it/en/news/11745/internet-archive-blackout-outage-business-continuity (Unofficial, secondary report of an outage of about 4 hours on Aug 16, 2026 (not confirmed by the Internet Archive))
- https://archive-it.org/vault/ (Vault paid preservation service: one-time per-GB/TB price, no annual or egress fees, price not published)
- https://www.publishersweekly.com/pw/print/20241209/96657-internet-archive-copyright-case-ends-without-supreme-court-review.html (Secondary source: Hachette v. Internet Archive ended without Supreme Court review (Dec 2024))
- https://www.digitalmusicnews.com/2025/09/16/great-78-project-lawsuit-settlement/ (Secondary source: Great 78 record-label lawsuit settled on confidential terms (Sept 2025))

## Cloudflare D1 (serverless SQLite database, with SQLite FTS5 full-text search) for job B, the searchable records database

Confidence: high

**Free:** On the Workers Free plan, per Cloudflare's D1 pricing and limits pages (both last updated Apr 21, 2026):
- 5 million rows read per day.
- 100,000 rows written per day.
- 5 GB total storage per account.
- Up to 10 databases, each capped at 500 MB.
- 50 queries per Worker invocation.
- 7 days of Time Travel (point-in-time restore). Time Travel is always on and costs nothing extra.
- The daily limits reset at 00:00 UTC, which is 2:00 PM Hawaii time.

Tables and indexes both count toward storage.

The website also needs a Cloudflare Worker to run the search, because D1 cannot be reached directly from a browser. The Workers Free plan gives 100,000 requests per day and 10 ms of CPU time per request. Requests for static assets are free and unlimited (Workers pricing page, updated Oct 2, 2026; Workers limits page, updated Oct 12, 2026).

FTS5 full-text search is officially supported: "FTS5 module for full-text search (including fts5vocab)" (SQL statements page, updated Apr 21, 2026).

**Paid:** Workers Paid costs at least $5 USD per month per account. The D1 usage it includes:
- Rows read: the first 25 billion per month are included, then $0.001 per million rows.
- Rows written: the first 50 million per month are included, then $1.00 per million rows.
- Storage: the first 5 GB are included, then $0.75 per GB-month.

The Workers part of the plan includes 10 million requests per month, then $0.30 per additional million. It also includes 30 million CPU-milliseconds per month, then $0.02 per additional million CPU-ms.

Paid limits:
- 10 GB per database, a cap Cloudflare says cannot be raised.
- 1 TB per account, which can be increased.
- 50,000 databases.
- 1,000 queries per Worker invocation.
- 30 days of Time Travel.

**When the public downloads or searches:** Cloudflare's D1 pricing page says: "There are no data transfer (egress) or throughput (bandwidth) charges for data accessed from D1."

What you pay for is rows read. That counts every row a query scans, not just the rows it returns, and a 1 KB row counts the same as a 100 KB row.

Cloudflare does not document how an FTS5 full-text search is counted in rows read. I found no official statement or example. The only way to know what one search costs is to test it, using the meta.rows_read field D1 returns with each query.

**Size limits:** From the D1 limits page (updated Apr 21, 2026):

Per database and per account:
- Max size of one database: 500 MB on Free, 10 GB on Paid. The 10 GB cap cannot be raised.
- Max storage per account: 5 GB on Free, 1 TB on Paid.
- Databases per account: 10 on Free, 50,000 on Paid.
- Rows per table: unlimited, apart from the database size cap.

Same on both plans:
- Max size of a single row, string or BLOB: 2 MB.
- Max length of one SQL statement: 100 KB.
- Max query duration: 30 seconds.
- 100 columns per table.
- 100 bound parameters per query.
- LIKE/GLOB pattern length: 50 bytes.

Import (from the import/export page):
- One file loaded with wrangler d1 execute can be up to 5 GiB.
- A raw .sqlite3 file cannot be imported directly.
- Data cannot be imported straight from MySQL or PostgreSQL.

How much space search adds (from sqlite.org, not Cloudflare): a full-text search index adds storage on top of the text. In SQLite's own test on about 1,636 MiB of email, the default index was 743 MiB, roughly 45% of the text size. Smaller settings were 340 MiB and 134 MiB. By default FTS5 also keeps a second copy of the text unless you set it up in "external content" mode. Cloudflare's index guide also warns that "FTS5 indexes increase storage and write costs."

**Fit for this project:** Here is how it fits, in plain terms.

**Search works.** D1 is a small SQL database that runs on Cloudflare, the same company where your domain is registered. It includes a real keyword search engine (SQLite's FTS5). That engine supports:
- matching words and exact phrases
- AND, OR and NOT
- words that start with something (prefix search)
- ranking results by relevance
- showing highlighted snippets of the matching text

That covers a public search bar over statutes, rules and hearing decisions. People reading the results costs nothing in bandwidth.

**Size today: it fits, but tightly.** A free database tops out at 500 MB. A few hundred MB of text, plus the search index that sits on top of it (often around half again the size of the text), could use up most or all of that 500 MB. It depends on how the search table is set up.

**Size later: free gets awkward.** Once the records grow to "a few GB," they won't fit in one free database. They would have to be split across up to 10 separate databases, 5 GB in total, and every search would then have to check each one. The paid plan ($5/month minimum) allows 10 GB in a single database, and the first 5 GB of storage are included. A few GB would therefore likely cost about $5/month. Above 10 GB in one database, the data has to be split again, even on paid.

**Daily allowance.** The free plan allows 5 million "rows read" per day. Cloudflare does not say how many rows one keyword search uses up, so it is unknown how many public searches per day that equals. You would have to measure it.

**What happens when the allowance runs out.** Since September 1, 2026, a free account that goes over its daily allowance has all its D1 queries refused. Search on the site would stop working until the counter resets at 2:00 PM Hawaii time. Loading data is limited too, to 100,000 rows written per day. A big batch upload, which also writes into the search index, may need to be spread over several days or done during a paid month.

**Building it.** You have to write a small Cloudflare Worker program to sit between the website and the database. The site cannot query D1 directly, and Cloudflare says D1's own web API is meant for admin use only.

**Backups are a real problem.** Cloudflare's normal "export" backup command refuses to work on any database that has a search index in it. One open bug report says a failed export left the database stuck and unusable. Built-in Time Travel (restore to any point in the last 7 days on free) still works. A full offline copy needs a workaround: remove the search table, export, then rebuild it, or use a script that exports table by table.

**Catches:**
- Free-tier daily limits are now enforced. Since Sept 1, 2026, a free account that goes over 5M rows read or 100K rows written in a day has every D1 query refused until midnight UTC, which is 2:00 PM Hawaii time. Stored data is not affected. Cloudflare sends an email alert. For a public site, this means search goes down for the rest of that day.
- How a full-text search is counted in 'rows read' is not documented by Cloudflare. I found no official page on it. The cost per search, and so how many searches a day fit in the free allowance, can only be learned by testing (the meta.rows_read field D1 returns).
- Export or backup does not work with FTS5. Cloudflare's docs say 'Export is not supported for virtual tables, including databases with virtual tables.' The official workaround is to drop the FTS tables, export, then recreate them. Two GitHub issues about this (#6305 and #9519, now moved to cloudflare/developer-platform) are still open as of Aug 2026. One reports the database got stuck with 'Currently processing a long-running export' and became unusable. The docs also say a running export blocks other requests to the database.
- The free plan's 500 MB per-database cap is small for this project once the search index is added. Growing to a few GB on free means splitting the data across up to 10 databases (5 GB account total). Paid raises this to 10 GB per database, a cap that cannot be raised.
- The paid plan has a $5/month minimum per account. Storage above 5 GB is $0.75 per GB-month.
- A Cloudflare Worker is required to query D1 from the website. That Worker uses the Workers Free allowance of 100,000 requests per day and 10 ms CPU per request, plus 50 D1 queries per Worker invocation. Cloudflare says D1's REST API is 'best suited for administrative use', because the global Cloudflare API rate limit applies to it.
- Writing to a full-text index adds rows written and storage. Cloudflare's index guide warns 'FTS5 indexes increase storage and write costs.' Each write to an indexed column also counts an extra row written.
- Per-item limits: one row, string or BLOB can be at most 2 MB, so a very long decision's full text would need splitting. One SQL statement can be at most 100 KB. The import guide says a 'Statement too long' error means splitting into smaller INSERTs, which may matter for long documents in .sql import files. Cloudflare does not say whether values passed as bound parameters count toward the 100 KB.
- D1 cannot import a raw .sqlite3 file directly, and cannot import straight from MySQL or PostgreSQL. Data has to be converted to SQL statements first.
- A third-party project (emdash-cms issue #252) reports that running an FTS5 'integrity-check' command corrupted D1's FTS5 shadow tables. This is a single unofficial report, not confirmed by Cloudflare.
- Not confirmed from an official page I could load: whether a credit card is needed to sign up for Workers Free. A search snippet attributed to Cloudflare marketing said 'no credit card required', but the Cloudflare pages I fetched did not mention credit cards at all.
- Lock-in: D1 is Cloudflare-only and is reached from Cloudflare Workers. The underlying data is plain SQLite, but getting a full export out runs into the FTS5 export limitation above.

**Sources:**
- https://developers.cloudflare.com/d1/platform/pricing/ (Free: 5M rows read/day, 100K rows written/day, 5 GB storage. Paid: 25B reads/mo + $0.001/M, 50M writes/mo + $1.00/M, 5 GB + $0.75/GB-month. No egress/bandwidth charges. Rows read = rows scanned. Tables and indexes count toward storage. Queries blocked when daily limits are hit; reset 00:00 UTC. Last updated Apr 21, 2026.)
- https://developers.cloudflare.com/d1/platform/limits/ (500 MB/DB on Free and 10 GB/DB on Paid (not raisable). 5 GB vs 1 TB per account. 10 vs 50,000 databases. 50 vs 1,000 queries per invocation. 2 MB row/string/BLOB. 100 KB SQL statement. 30 s query duration. 100 columns. 100 bound params. 50-byte LIKE pattern. Time Travel 7 vs 30 days. 5 GB import file. Last updated Apr 21, 2026.)
- https://developers.cloudflare.com/d1/sql-api/sql-statements/ (D1 supports the FTS5 module for full-text search (including fts5vocab), plus the JSON and math extensions. Only a subset of SQLite extensions is supported. Last updated Apr 21, 2026.)
- https://developers.cloudflare.com/d1/best-practices/import-export-data/ ('Export is not supported for virtual tables, including databases with virtual tables' (applies to FTS5); workaround is drop/export/recreate. Exports block other DB requests. 5 GiB import file limit. No raw .sqlite3 or MySQL/PostgreSQL import. 'Statement too long' handling. Last updated Apr 21, 2026.)
- https://developers.cloudflare.com/changelog/post/2026-09-01-d1-free-tier-limit-enforcement/ (Starting Sept 1, 2026, Workers Free D1 queries fail once the account exceeds daily row read/write limits, until midnight UTC; email alerts are sent; stored data is not affected.)
- https://developers.cloudflare.com/d1/best-practices/use-indexes/ (D1 bills by rows read/written, not rows returned. Suggests FTS5 trigram for substring search. Warns 'FTS5 indexes increase storage and write costs'. Use meta.rows_read to measure query cost.)
- https://developers.cloudflare.com/d1/reference/time-travel/ (Time Travel is always on at no additional cost; 7 days on Free, 30 days on Paid. Last updated Apr 21, 2026.)
- https://developers.cloudflare.com/workers/platform/pricing/ (Workers Free: 100,000 requests/day and 10 ms CPU per invocation. Workers Paid: $5/month minimum, 10M requests/mo + $0.30/M, 30M CPU-ms + $0.02/M. Static asset requests free and unlimited. Last updated Oct 2, 2026.)
- https://developers.cloudflare.com/workers/platform/limits/ (Workers Free: 100,000 requests/day resetting at midnight UTC; Error 1027 when exceeded; 10 ms CPU; 128 MB memory; 50 subrequests. Last updated Oct 12, 2026.)
- https://developers.cloudflare.com/d1/tutorials/build-an-api-to-access-d1/ (D1's REST API is 'best suited for administrative use' because the global Cloudflare API rate limit applies; outside access requires a Worker. Last updated Oct 12, 2026.)
- https://www.sqlite.org/fts5.html (FTS5 features: MATCH, bm25 ranking, highlight/snippet, prefix/phrase/NEAR, boolean operators, unicode61/porter/trigram tokenizers. Index size example: 743 MiB (detail=full), 340 MiB or 134 MiB with smaller settings, for ~1636 MiB of email. External-content and contentless options avoid storing a second copy of the text.)
- https://github.com/cloudflare/workers-sdk/issues/6305 (Open bug (moved to cloudflare/developer-platform #43 on Aug 17, 2026): wrangler d1 export fails on any DB with an FTS5 table; cause is SQLite .dump needing writable_schema, which D1 disallows.)
- https://github.com/cloudflare/workers-sdk/issues/9519 (Open bug (moved to cloudflare/developer-platform #11): attempting export of a DB with FTS5 left it returning 'Currently processing a long-running export' and unusable; no staff fix posted.)
- https://github.com/emdash-cms/emdash/issues/252 (Third-party report (unofficial) that an FTS5 integrity-check corrupted D1 FTS5 shadow tables.)

## Supabase hosted Postgres (for job B, the searchable records database)

Confidence: high

**Free:** Free plan is $0/month (https://supabase.com/pricing, fetched 2026-10-18). It includes:
- 500 MB database size per project, on a shared CPU with 500 MB RAM ("Nano" size). The compute docs list 500 MB as the recommended max database size for Nano, with up to 60 direct connections and 200 pooler clients.
- 5 GB uncached egress plus 5 GB cached egress per month. The 5 GB is shared by all projects in the organization combined, not given to each project.
- 2 active free projects. Paused projects do not count toward that limit.
- 1 GB file storage (50 MB max upload), 50,000 monthly active users, 500,000 Edge Function invocations.
- No automatic backups. Supabase tells Free users to export their data themselves with the CLI "db dump" command. Logs are kept for 1 day.
- Full-text search is included at no extra cost. It is ordinary Postgres search: tsvector/tsquery, websearch_to_tsquery (which handles quoted phrases, OR, and minus to exclude a word), GIN indexes, prefix matching, and ranking through database functions. The JavaScript client can call it with .textSearch(column, query, {type: 'websearch'}).
- Pausing: "Free projects are paused after 1 week of inactivity." Inactive means the database "does not receive sufficient user database activity over the past week." Per the docs, a few user requests to the database each day are enough to stay active. A warning email goes out about a week before the pause. Paid projects are never paused for inactivity.

**Paid:** Pro plan starts at $25/month per organization (https://supabase.com/pricing; the Billing FAQ example also uses $25).
- Includes $10/month of compute credit. That covers one project on the default Micro size ($0.01344/hour, about $10/month, 1 GB RAM, shared CPU, recommended max database size 10 GB). Each extra project costs about $10/month more.
- Database disk: 8 GB per project included, then $0.125 per GB per month (gp3 disk).
- Egress: 250 GB uncached included, then $0.09/GB. 250 GB cached included, then $0.03/GB.
- File storage: 100 GB included, then $0.0213/GB.
- Daily backups kept for 7 days. Point-in-time recovery is an extra add-on, from about $100/month for 7 days, and it requires a Small compute add-on or larger.
- A spend cap is on by default. With it on, usage of egress and disk stops at the quota instead of being billed. Compute is not covered by the cap.
- So one project on Pro costs about $25/month in total, unless you go over the included amounts and the cap is off.

**When the public downloads or searches:** Every search result or record sent to a visitor counts as egress.
- Free: 5 GB/month for the whole organization. Supabase lists no pay-per-GB option on Free. If you go over, Supabase emails the billing address and starts a grace period of unstated length. If you keep going over, the Fair Use Policy can apply: restrictions can include read-only mode, pausing, or answering every API request with a 402 error, applied to all projects in the organization. An egress restriction lifts at the start of the next billing cycle, or right away if you upgrade.
- Pro: 250 GB/month included, then $0.09/GB uncached. Supabase does not charge per query or per read; only data volume and compute are billed.
- Rough illustration (my own math, not a Supabase figure): if each search returns about 50 KB of text, 5 GB is roughly 100,000 searches a month.

**Size limits:** - Free: 500 MB database size. The 500 MB counts the data, the indexes and materialized views; it does not count WAL (internal change logs). Deleted rows keep taking space until a vacuum runs. Past 500 MB the project goes into read-only mode: writes fail with "cannot execute INSERT in a read-only transaction". Reads were not described as blocked.
- Pro: 8 GB disk included. The disk grows automatically when it is 90% full, by 50% each time. This works only if the spend cap is turned off; with the cap on, the 8 GB disk limit cannot be exceeded. Disk can be set as high as 60 TB per the database-size page, or 64 TB per the compute page. The Micro compute size recommends up to 10 GB of data.
- Free file uploads are capped at 50 MB each. That applies to Supabase Storage, not the database. Job A's largest PDF (about 40 MB) would fit under that cap, but the 1 GB total Free storage is far below 13-16 GB. Storage is outside this research scope.

**Fit for this project:** What it would do well: Supabase is a hosted version of Postgres, a widely used database. It has a built-in keyword search engine that suits a public search bar for statutes, rules and hearing decisions. Visitors could type phrases in quotes, use OR, or exclude words with a minus sign, and results can be ranked by relevance. Updating in batches and serving mostly reads is a normal way to use it. Search is part of the database itself, so no separate search service is needed.

What would be a problem on the free plan:
(1) Size. The free cap is 500 MB, and the search index counts toward it, not just the text. The project is "a few hundred MB now." Search indexes on full-text documents add substantial extra space; how much depends on the data (I have not measured it). So the free plan could fill up early. "A few GB later" would clearly exceed it. Once over the cap, the database goes read-only, so your batch updates would fail.
(2) Pausing. If the site gets almost no searches for about a week, the project is paused and the search bar stops working until you log in and resume it. Steady real visitor traffic keeps it awake.
(3) No backups on Free. You would have to export copies yourself.
(4) Traffic. 5 GB a month of data sent to visitors is a modest amount for a public site. Going well over it can lead to restrictions, including the database refusing all requests.

On the $25/month Pro plan, the size, pausing and backup problems mostly go away. 8 GB of disk and 250 GB of monthly traffic are included, which comfortably covers "a few GB later." But it is not $0.

**Catches:**
- The free 500 MB limit includes indexes. Full-text search indexes add substantial space on top of the raw text, so a few hundred MB of records may not fit.
- Past 500 MB the Free project goes read-only, so batch imports and updates fail until you shrink the data or upgrade.
- Free projects pause after about 1 week of low database activity. A paused project has to be resumed by hand from the dashboard. The pausing doc (fetched today) says a paused project can be restored for up to 1 year, but a Supabase troubleshooting page title refers to a 90-day window. That is an inconsistency on Supabase's own pages.
- Free has no automatic backups. You must export the data yourself.
- The 5 GB/month free egress is shared by all projects in the organization. If you keep going over, the Fair Use Policy can apply: read-only mode, pausing, or 402 errors on all API requests, across every project in the organization. The grace period length is not stated.
- Only 2 active free projects per account.
- Pro's spend cap is on by default. With it on, the 8 GB disk cannot autoscale and egress stops at the quota. Turning it off allows charges beyond $25. Compute is never covered by the cap.
- The Pro $25 covers one Micro project through the $10 compute credit. Each extra project adds about $10/month.
- The search is word-based Postgres full-text search. It matches word stems: per Supabase's guide, searching 'big' also finds 'bigger'. The JavaScript client cannot search several columns at once without a combined column or a database function.
- None of the Supabase pages fetched show a publication or last-updated date. The figures come from the live pages fetched 2026-10-18, and Supabase notes pricing may change.

**Sources:**
- https://supabase.com/pricing (Free $0: 500 MB database, shared CPU/500 MB RAM, 5 GB + 5 GB cached egress, 1 GB storage (50 MB max upload), 2 active projects, paused after 1 week of inactivity, no backups, 1-day logs. Pro from $25/month: 8 GB disk then $0.125/GB, 250 GB egress then $0.09/GB (cached $0.03/GB), 100 GB storage then $0.0213/GB, $10 compute credits, spend cap on by default, 7-day backups, no inactivity pausing. Fetched live 2026-10-18; no date on page.)
- https://supabase.com/docs/guides/platform/database-size (Free goes read-only past 500 MB database size; database size includes data, indexes and materialized views but not WAL; Pro autoscaling (grows 50% at 90% full, needs spend cap off to go past 8 GB); max disk 60 TB.)
- https://supabase.com/docs/guides/platform/compute-and-disk (Nano (Free) $0, up to 0.5 GB RAM, 500 MB recommended max DB; Micro $0.01344/hour (~$10/month), 1 GB RAM, 10 GB recommended max DB; 60 direct / 200 pooler connections; disk 8 GB included then $0.125/GB; max 64 TB.)
- https://supabase.com/docs/guides/platform/free-project-pausing (Definition of inactivity (insufficient user database activity over the past week), warning email about one week before the pause, ways to prevent a pause, restore window of up to 1 year, paid plans not paused.)
- https://supabase.com/docs/guides/troubleshooting/restore-project-after-90-days-pause (Seen only as a search-result title and snippet (not fetched): describes a 90-day restore window, which conflicts with the 1-year figure on the pausing page.)
- https://supabase.com/docs/guides/platform/billing-on-supabase (Two free projects (paused ones excluded); Free quotas: 5 GB egress, 500 MB DB, 50,000 MAU, 1 GB storage, 500,000 Edge Function invocations.)
- https://supabase.com/docs/guides/platform/billing-faq (Fair Use restrictions (pausing, read-only, 402 on all API requests, applied organization-wide); grace period of unstated length; Pro $25 example; $10 compute credits cover one default project; extra projects ~$10/month.)
- https://supabase.com/docs/guides/platform/manage-your-usage/egress (What counts as egress (database API responses, storage downloads, cached CDN); Free 5 GB/5 GB shared across the organization; Pro 250/250 GB, $0.09 and $0.03/GB overage; grace period and when restrictions clear.)
- https://supabase.com/docs/guides/platform/cost-control (Spend cap stops covered usage (egress, disk size) at quota; compute not covered; no charges on Free.)
- https://supabase.com/docs/guides/platform/backups (Pro 7 days of daily backups; Free has no automatic backups (advised to use CLI db dump); PITR from ~$100/month, requires Small compute or larger.)
- https://supabase.com/docs/guides/database/full-text-search (Full-text search with to_tsvector, to_tsquery, websearch_to_tsquery, the @@ operator, generated tsvector columns with GIN index, prefix matching, ranking via RPC functions; textSearch() in the client libraries; cannot search multiple columns from the client without a combined column or function.)

## Neon serverless Postgres ("Lakebase Postgres on Neon", now part of Databricks), for job B, the searchable records database

Confidence: high

**Free:** The Free plan costs $0/month. Neon calls it "permanent (not a trial); no credit card required." Per project you get: 1 GB of Postgres storage, with a cap of 20 GB across all projects on the account; 100 CU-hours of compute per month; autoscaling up to 2 CU (about 8 GB RAM); 10 branches; 5 GB of public network transfer (egress) per month; a 6-hour restore history (capped at 1 GB-month); 1 manual snapshot; and 1 day of monitoring. The account can have up to 100 projects. Neon's own example: 100 CU-hours is "enough to run a 0.25 CU compute in a project for 400 hours/month" (0.25 CU x 4 hours = 1 CU-hour). A month has about 730 hours (my arithmetic). Scale-to-zero is always on: the database goes to sleep after 5 minutes with no activity, and on Free this cannot be turned off. Neon says a sleeping database wakes "within a few hundred milliseconds." Compute hours and transfer reset every month. Storage, project and branch limits are ongoing caps. The Free plan also includes 5 GB of Neon Object Storage per project and Neon Functions (10 active / 400 waiting Capacity-Hours and 1M invocations per project). Neon's built-in Postgres full-text search works. Neon's BM25 keyword-search add-on, lakebase_text, needs Postgres 16 or later. Neon's extension list gives no plan restriction for it, and the Lakebase Search docs do not say which plans include it.

**Paid:** Launch plan: pay-as-you-go with no monthly minimum (invoices under $0.50 are not collected). Prices: compute $0.106 per CU-hour; storage $0.35 per GB-month, measured hourly, with no storage cap; 500 GB per project per month of egress included, then $0.10/GB; extra branches $1.50/branch-month; instant restore $0.20/GB-month; up to 16 CU; scale-to-zero after 5 minutes, which can be turned off. Scale plan: compute $0.222 per CU-hour; storage $0.35/GB-month; the same 500 GB egress then $0.10/GB; private network transfer $0.01/GB; adds an uptime SLA and SOC 2/HIPAA compliance. Object Storage on paid plans is $0.023/GB-month. Illustrations (my arithmetic, not Neon's figures): 3 GB of data on Launch costs about $1.05/month for storage. The smallest compute (0.25 CU) running all 730 hours of a month would be 182.5 CU-hours, about $19.35/month; with scale-to-zero you pay only for the hours it is awake.

**When the public downloads or searches:** There is no per-query or per-read charge. You pay for compute time (CU-hours) and for data sent out of the database (egress). Free: 5 GB of egress per project per month, with no option to pay for more. When the 5 GB or the 100 CU-hours run out, "your compute is suspended until the next billing period or until you upgrade." Launch/Scale: 500 GB per project per month included, then $0.10/GB. The egress allowance is shared by everything in the project: Postgres, Object Storage and Functions. Rough illustration (my estimate, not Neon's): if each search sends about 20 KB of results back to the website, 5 GB covers about 250,000 searches a month. Pages that show full decision texts would use it up faster.

**Size limits:** Free: 1 GB of Postgres storage per project and 20 GB across all projects. The two limits are enforced separately. Storage is measured as "logical data size," which Neon's glossary defines as "the size of the database, including all tables, indexes, views, and stored procedures." That means search indexes count against the 1 GB. At the cap, operations that add data (inserts, updates, deletes) fail until you free space or upgrade. Neon says "None of these limits delete your data." Paid plans: "Storage is unlimited... there's no hard per-branch size limit." Free compute goes up to 2 CU (8 GB RAM); Launch up to 16 CU (64 GB); Scale up to 16 CU autoscaling, or fixed sizes up to 56 CU. Neon Object Storage: 5 GiB maximum per object; 5 GB per project on Free.

**Fit for this project:** What it is: a full Postgres database in the cloud that sleeps when nobody is using it and wakes up when a request comes in. Postgres has keyword search built in, so the statutes, rules and hearing decisions could be stored as rows and searched from a public search bar. Neon also offers a newer, better-ranked keyword search add-on (BM25, "lakebase_text"). Neon announced it as generally available on Sep 30, 2026, and it requires Postgres 16 or newer. Neon publishes a guide for connecting from Cloudflare Workers, through Cloudflare's Hyperdrive or Neon's own driver, so it can sit behind a site whose domain is on Cloudflare. The closest Neon region to Hawaii is AWS US West (Oregon).

What works on the free plan: a few hundred MB of records fits under the 1 GB limit, as long as the search index also fits, because the index counts toward the 1 GB. The data is updated in batches and mostly read, which matches a database that can sleep between visits.

What would be a problem:
(1) Storage: the plan is to grow to "a few GB." That is over the 1 GB free limit per database. You would then need to pay (about $0.35 per GB per month for storage, plus compute time) or split the data across several free projects, which makes search harder to build.
(2) Awake time: the free plan covers about 400 hours a month of the smallest database, and a month has about 730. A public site that gets visits around the clock could keep the database awake longer than that. Once the free hours or the 5 GB monthly transfer run out, the database is switched off until the next month. To visitors, the search bar would stop working, not just slow down.
(3) Slow first search: after 5 minutes with no visitors the database sleeps, so the first search after a quiet period waits a moment (Neon says a few hundred milliseconds) while it wakes up.
(4) Not for job A: this would not hold the PDFs. Neon's own object storage gives only 5 GB free per project, against 13-16 GB of PDFs, and file downloads would count against the same 5 GB monthly transfer allowance.

**Catches:**
- Hard monthly limits on Free: running out of the 100 CU-hours or the 5 GB transfer suspends the database until next month. There is no option to pay for a little extra while staying on Free; you have to upgrade.
- The 1 GB free storage includes indexes (logical data size covers tables plus indexes), so a full-text search index uses up the same 1 GB as the text itself.
- Scale-to-zero after 5 minutes cannot be turned off on Free, so the first search after a quiet period has a short wake-up delay.
- Recent product churn: Neon was absorbed into Databricks branding ('Lakebase Postgres on Neon, from Databricks'). The previous BM25 search extension, pg_search (ParadeDB), was deprecated for new projects on March 19, 2026 and removed from existing projects on September 21, 2026. Its replacement, lakebase_text, is new: Neon announced it as GA on Sep 30, 2026, while a June 2026 changelog had listed Lakebase Search as Private Preview.
- Neon's Azure regions are deprecated. Free projects in Azure regions that have been inactive for 90+ days are subject to deletion as of October 5, 2026. The official pages give no general inactivity-deletion rule for AWS regions.
- lakebase_text requires Postgres 16 or newer, so you have to pick a recent Postgres version when creating the project.
- Free gets community support only, 1 day of monitoring, a 6-hour restore window and 1 manual snapshot. An uptime SLA comes only with the Scale plan.
- Neon Object Storage is not yet in the Oregon (aws-us-west-2) region, which is the region closest to Hawaii. Postgres is available there.
- Neon's pricing and plans pages show no 'last updated' date. The figures here were read live from them on 2026-10-18.

**Sources:**
- https://neon.com/pricing (Free plan $0, permanent, no credit card required; Launch $0.106/CU-hour, Scale $0.222/CU-hour; storage $0.35/GB-month; 500 GB egress then $0.10/GB; no monthly minimum; CU = ~4 GB RAM; 0.25 CU x 4 hours = 1 CU-hour; product now 'Lakebase Postgres... from Databricks')
- https://neon.com/docs/introduction/plans (Plan table: 100 projects; 10 branches; 100 CU-hours/project; up to 2 CU on Free; 1 GB/project and 20 GB total storage on Free; 5 GB egress/project on Free; scale-to-zero after 5 minutes, cannot be turned off on Free; 6-hour history; 1 snapshot; what happens at limits (compute suspended, writes fail, no data deleted); 400 hours at 0.25 CU; unlimited storage on paid plans; invoices under $0.50 not collected; Object Storage 5 GB Free and $0.023/GB-month paid; egress shared across products)
- https://neon.com/docs/reference/glossary (Logical data size includes all tables, indexes, views and stored procedures)
- https://neon.com/docs/introduction/scale-to-zero (Free plan scale-to-zero after 5 minutes is fixed; reactivates within a few hundred milliseconds)
- https://neon.com/docs/extensions/pg_search (pg_search deprecated for new projects March 19, 2026, retired from existing projects September 21, 2026; lakebase_text is the replacement)
- https://neon.com/docs/extensions/pg-extensions (lakebase_text 0.1.3 on PG16-18, pg_trgm and unaccent available, pg_search unavailable; no plan restriction listed for search extensions)
- https://neon.com/docs/extensions/lakebase-text (lakebase_text requires Postgres 16 or later; BM25 index type)
- https://neon.com/blog/lakebase-search-retrieval-agents (Blog dated Sep 30, 2026 stating Lakebase Search reached GA)
- https://neon.com/docs/ai/lakebase-search (Lakebase Search provides vector, BM25 keyword and hybrid search via lakebase_vector and lakebase_text extensions)
- https://neon.com/postgresql/postgresql-indexes/postgresql-full-text-search (Core Postgres full-text search works on Neon)
- https://neon.com/docs/guides/cloudflare-workers (Connecting Neon from Cloudflare Workers via Hyperdrive or the Neon serverless driver)
- https://neon.com/docs/introduction/regions (AWS US West (Oregon) region available for Postgres but not yet Object Storage; Azure regions deprecated, inactive Free Azure projects subject to deletion as of Oct 5, 2026)
- https://neon.com/docs/storage/overview (Object Storage limits: 5 GiB max object size, 5 GB per project on Free)

## MotherDuck (hosted DuckDB, Lite free plan) and DuckDB-WASM (DuckDB running in the visitor's browser, reading Parquet or .duckdb files from object storage), for job B, the searchable records database

Confidence: medium

**Free:** MOTHERDUCK LITE is $0 per organization per month and needs no credit card. It includes:
- 10 Compute Unit (CU) hours of "Pulse" compute per month. Pulse is metered per query, with a minimum charge of 1 CU-second per query.
- 10 GB of storage per month, measured on the compressed size.
- 3 active users and 2 service accounts.
- The Pulse instance size only. Read Scaling (read-only replica tokens) is listed as not available on Lite.
- 1 day of backup and community support. No SLA is listed.
- 30 minutes per day of F4 "Flights" (pipeline compute) without a card.
- A soft limit of 10 AI Units per user per day.
- A 7-day Business trial.
My own arithmetic, not a vendor figure: 10 CU-hours is 36,000 CU-seconds, so at most about 36,000 queries a month would fit in the free compute, and only if every query used the 1-second minimum. Real searches may use more.

DUCKDB-WASM is free, open-source software (MIT license on the @duckdb/duckdb-wasm npm package). There is no service and no account. It costs nothing by itself. The only costs come from wherever you host the data files and the engine file.

**Paid:** MOTHERDUCK usage beyond the Lite allowance, in the US regions (us-east-1 and us-west-2):
- Pulse compute: $0.60 per CU-hour.
- Storage: $0.04 per GB-month.
- Other regions cost more: Pulse is $0.73 in eu-central-1/eu-west-1 and $0.77 in ap-northeast-1/ap-southeast-2; storage is $0.043 and $0.044 per GB.
The docs say usage beyond the included amounts "is billed on a pay-as-you-go basis" and that Lite users "see invoices for any usage beyond the included 10 CU hours and 10 GB storage."

MotherDuck Business is $250 per organization per month plus usage. It adds Read Scaling (up to 16 replicas), larger instance sizes, query history, a 99.9% SLA and up to 90 days of backup. Business compute rates on the pricing page: Pulse $0.60 per CU-hour, Standard $2.40/hr, Jumbo $4.80/hr, Mega $12.00/hr. Giga is $24/hr on the pricing page but $36/hr in the Fees Addendum; the two official pages disagree. Enterprise pricing is custom.

DUCKDB-WASM has no price. You pay only for hosting and bandwidth of the files at your object-storage provider, which was not researched here.

**When the public downloads or searches:** MOTHERDUCK: I found no egress or data-transfer fee on the pricing page, the pricing docs or the Fees Addendum (last updated 02/02/2026). Only storage and compute are billed. Every search a visitor runs uses compute, at a minimum of 1 CU-second per query. That comes out of the 10 free CU-hours, and after that it costs $0.60 per CU-hour in the US regions.

DUCKDB-WASM: DuckDB charges nothing. Each visitor's browser downloads the data it needs directly from your object storage, so egress and read-request costs are whatever that storage host charges.
- The browser fetches only the byte ranges it needs from Parquet files, using HTTP range requests.
- Each first-time visitor also downloads the DuckDB engine. I measured it on 2026-10-18 from jsDelivr: duckdb-eh.wasm is about 7.1 MB compressed (brotli) and about 36 MB uncompressed. This is my own measurement, not a vendor figure.

**Size limits:** MOTHERDUCK LITE
- 10 GB of compressed storage is included. Beyond that it is billed at $0.04 per GB-month.
- I found no stated maximum database size or database count.
- CPU and memory for each instance size are not published.
- One region per organization, chosen when the organization is created: us-east-1, us-west-2, eu-central-1, eu-west-1, ap-northeast-1 or ap-southeast-2.

DUCKDB-WASM
- The official docs say: "WebAssembly limits the amount of available memory to 4 GB," and "browsers may impose even stricter limits."
- It runs on a single thread by default; multithreading is "still experimental."
- Remote files must be served over HTTPS, with CORS headers that allow your site, and with working HTTP range requests.
- Remote .duckdb database files can be attached over HTTPS, but only read-only.
- The docs say the latest stable DuckDB-WASM client is 1.5.6. On npm, the "latest" tag is 1.33.1-dev57.0, published 2026-06-22.

**Fit for this project:** In plain terms, there are two different ways to use DuckDB here.

1) MOTHERDUCK (a hosted database service)
- **Storage fits:** You would put the statutes, rules and hearing decisions in MotherDuck's cloud. A few hundred MB now and a few GB later fits inside the free 10 GB.
- **Keyword search is supported:** DuckDB has a built-in full-text search feature that ranks results by relevance. MotherDuck lists it as supported.
- **Rebuild after updates:** The search index does not update itself when data changes. It has to be rebuilt after each batch of updates. That suits data that changes in batches, but it is an extra step every time.
- **Free compute is limited:** Every search someone types on the public site uses some of the free monthly compute (10 CU-hours). Busy traffic or bots could use it up. After that, usage is billed, and I found no spending cap or automatic stop in the docs.
- **You would need a middleman server:** The read-only access keys meant for public apps (Read Scaling) are not included in the free plan. MotherDuck's own docs say to keep the key on a server, not in the web page. So the site would need a small server in between, such as a Cloudflare Worker. Workers connect through MotherDuck's Postgres-compatible connection, which is labeled "preview."
- **Unresolved terms question:** The Fees Addendum says free accounts may be used "solely for internal business purposes" and not in a service offered to third parties, and that free accounts can be suspended at any time. It defines a "Free Account" as one not tied to an Organization. Lite is sold per organization, so the terms don't say whether this rule covers Lite. That needs a direct answer from MotherDuck before building a public website on it.

2) DUCKDB-WASM (the database runs inside the visitor's own browser)
- **How it works:** The database software is free and runs on each visitor's computer. You put data files on file storage, and the browser reads the parts it needs. There is no database server to pay for or maintain.
- **Downsides:** Each new visitor downloads a roughly 7 MB engine first, and the browser is capped at about 4 GB of memory.
- **Keyword search is the hard part:** Parquet files have no built-in keyword index. Searching full text without an index means the browser has to pull down the text it is searching, which could be hundreds of MB for full hearing decisions.
- **Possible workaround, not confirmed:** Build a search index ahead of time inside a .duckdb file and attach it read-only over HTTPS. The official docs confirm read-only HTTPS attach works and that the search extension exists in WASM. They do not confirm that the two work together in the browser.
- **File host requirements:** The host must allow CORS and range requests. The docs warn that range requests can fail on Firefox.
- **Everything is downloadable:** All data is openly downloadable by anyone, which matters less for public records.

**Catches:**
- MotherDuck Fees Addendum (Last Updated 02/02/2026), Section 1.3: 'Customers having Free Accounts may use the Services solely for internal business purposes, and may not use the Services to deliver, or incorporate any part of the Services into, any product, service, or technology that is made available to third parties.' A 'Free Account' is defined as one 'not associated in the Services with an Organization', and Lite is a per-organization plan, so it is not stated whether Lite counts. Needs written confirmation from MotherDuck before a public website relies on it.
- MotherDuck Fees Addendum: 'MotherDuck may suspend a Free Account at any time and for any reason.' Free-account limits 'may change at any time.' A downgrade to a Free Account 'may result in the loss of account functionality and destruction of data.'
- MotherDuck docs do not say what happens when a card-less Lite organization goes past 10 CU-hours or 10 GB (blocked, throttled or invoiced). The billing docs say extra usage is 'billed on a pay-as-you-go basis'. A 2024 release note said free-plan queries 'may be throttled'. No spending cap, budget limit or hard-stop feature is documented.
- Read Scaling (read-only tokens meant for high-concurrency or public reads) is listed as not available on Lite in the pricing-model comparison table; it is a Business feature ($250 per month). MotherDuck's own guidance: 'Keep the MotherDuck read scaling token on the backend', and 'An unauthenticated proxy that injects a token lets anyone who can reach its URL query the data available to that token.'
- The MotherDuck Postgres endpoint is the documented way for Cloudflare Workers to connect. It is described as being in preview, plan availability is not stated, and it does not support SET statements, temporary tables, or INSTALL/LOAD.
- Lite has no SLA, fixed 1-day backup and community support only. Pulse is the only instance size.
- DuckDB full-text search: 'The FTS index will not update automatically when the input table changes.' It must be rebuilt after each batch. A MotherDuck release note (2024-08-21) said FTS index creation was not supported from the MotherDuck WASM client or web app, and current docs only say 'Not all features of extensions in the MotherDuck UI (Wasm) are supported.'
- DuckDB-WASM: about 7 MB compressed engine download per new visitor (my measurement, not official). 4 GB memory ceiling, possibly lower in some browsers. Single-threaded by default.
- DuckDB-WASM remote reads need CORS headers allowing your site, HTTPS, and working HTTP range requests. The official troubleshoot page says 'Range requests can fail on Firefox' and are 'not detected correctly for some S3 pre-signed URLs', which can force a full-file download.
- Parquet files carry no full-text index. Official docs do not confirm that DuckDB FTS search (match_bm25) works against a remote .duckdb file attached read-only in the browser. Treat browser-side keyword search as unproven until tested.
- The DuckDB-WASM docs say the latest stable client is 1.5.6, while the npm 'latest' tag is a dev-labelled build (1.33.1-dev57.0, 2026-06-22). The versioning is confusing to pin.
- Business compute price inconsistency between official pages: Giga is $24/hr on the pricing page and $36/hr in the Fees Addendum. This does not affect Pulse rates, which match.

**Sources:**
- https://motherduck.com/pricing/ (Lite $0: 3 users, 2 service accounts, 10 GB storage, 10 hours Pulse compute per month, Pulse only, 1-day snapshots, community support. Business $250 per org per month plus usage. Pulse $0.60 per CU-hour with a 1 CU-second minimum. Storage $0.04 per GB-month. Six AWS regions. No card needed for Lite. 7-day Business trial.)
- https://motherduck.com/docs/about-motherduck/billing/pricing/ (Plan comparison table: Read Scaling not on Lite. Lite extra usage billed at the listed rates. Regional Pulse ($0.60/$0.73/$0.77) and storage ($0.04/$0.043/$0.044) prices. Per-query CU metering with a 1 CU-second minimum. No SLA or query history on Lite.)
- https://motherduck.com/fees-addendum/ (Last Updated 02/02/2026. Lite included volumes and overage fees. Free Account terms: internal business use only, suspension at any time, consumption caps, no circumvention. Definitions of Free, Billed and Managed accounts. No egress fees listed. Giga $36/hr for Business us-east-1.)
- https://motherduck.com/docs/about-motherduck/billing/managing-billing/ (Lite includes 10 CU-hours and 10 GB at no cost. 'Additional usage is billed on a pay-as-you-go basis.' Lite users are invoiced for usage beyond the included amounts.)
- https://motherduck.com/docs/about-motherduck/billing/monitoring-usage/ (No spending cap or hard-stop feature is described. Lite '$0/month (includes 10 CU hours and 10 GB storage)'.)
- https://motherduck.com/docs/about-motherduck/billing/instances/ (Pulse is available on Lite and Business with about 100 ms startup and per-query metering (1 CU-second minimum). Other instance sizes are Business only.)
- https://motherduck.com/docs/concepts/duckdb-extensions/ (The fts extension is listed as supported in the MD UI, MD Cloud and DuckDB CLI, with a footnote that not all extension features work in the Wasm UI.)
- https://motherduck.com/docs/about-motherduck/release-notes-archive/ (2024-08-21: FTS added to MotherDuck, with index creation not supported from the WASM client or web app. A 2024 note that free-plan queries may be throttled. Read Scaling pool of up to 16 replicas for the Business plan.)
- https://motherduck.com/docs/concepts/resource-management/ (Describes the browser pattern where DuckDB WASM connects to MotherDuck with a read-only token. 'Tokens do not provide isolation.')
- https://motherduck.com/docs/key-tasks/ai-and-motherduck/securing-read-only-access/ ('Keep the MotherDuck read scaling token on the backend.' Warns that an unauthenticated proxy injecting a token lets anyone query the data that token can reach.)
- https://motherduck.com/docs/key-tasks/authenticating-and-connecting-to-motherduck/authenticating-to-motherduck/ (Token types are Read/Write (default) and Read Scaling. Read Scaling tokens are restricted to reads.)
- https://motherduck.com/docs/key-tasks/authenticating-and-connecting-to-motherduck/postgres-endpoint/ (Postgres wire-protocol endpoint. You write DuckDB SQL, not PostgreSQL SQL. No SET statements, temp tables or INSTALL/LOAD. Long-lived or pooled connections recommended.)
- https://motherduck.com/docs/integrations/serverless-compute/ (Cloudflare Workers connect to MotherDuck through the Postgres endpoint using the pg npm package.)
- https://motherduck.com/blog/motherduck-now-speaks-postgres/ (Vendor announcement of the Postgres endpoint. The preview status comes from the search summary of MotherDuck's docs and was not quoted verbatim from a fetched page.)
- https://duckdb.org/docs/current/clients/wasm/overview.html (Latest stable DuckDB-Wasm client is 1.5.6. 4 GB WebAssembly memory limit, with browsers possibly stricter. Single-threaded by default. The JS httpfs fetches only the required byte ranges.)
- https://duckdb.org/docs/current/clients/wasm/extensions.html (fts, json and parquet are available in DuckDB-Wasm, with autoloading on by default. The httpfs replacement must follow browser security rules, requests are upgraded to HTTPS, and CORS is required.)
- https://duckdb.org/docs/current/clients/wasm/data_ingestion.html (Remote Parquet can be read lazily over HTTP or by putting the URL in SQL. Reads are subject to the browser's CORS policy.)
- https://duckdb.org/docs/current/clients/wasm/troubleshoot (DuckDB relies on HTTP range requests. Range requests can fail on Firefox and on some S3 pre-signed URLs. Example CORS policy.)
- https://duckdb.org/docs/current/core_extensions/full_text_search.html (create_fts_index and match_bm25 (BM25 ranking). Porter stemming and an English stopword list by default. The index is stored in schema fts_main_<table> and does not update automatically when the table changes.)
- https://duckdb.org/docs/current/sql/statements/attach.html (ATTACH supports HTTP and S3 endpoints and creates a read-only connection by default.)
- https://registry.npmjs.org/@duckdb/duckdb-wasm (MIT license. dist-tag latest = 1.33.1-dev57.0 (2026-06-22) and next = 1.33.1-dev65.0 (2026-09-29).)
- https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.33.1-dev57.0/dist/duckdb-eh.wasm (My own measurement on 2026-10-18: about 35.9 MB raw and about 7.1 MB brotli-compressed engine download.)

## Second check

I found nothing to correct. I re-checked the most important numbers against live official pages on 2026-10-18, and each one matched the researchers' reports:

**Cloudflare R2** (https://developers.cloudflare.com/r2/pricing/, last updated Oct 1, 2026)
- Free tier: 10 GB-month, 1M Class A, 10M Class B, free egress, Standard storage only.
- Standard storage $0.015/GB-month. Infrequent Access $0.01/GB-month, Class A $9.00/M, Class B $0.90/M, retrieval $0.01/GB.
- Billing example totals: $14.85, $29.90 and $104.40.
- Cloudflare caches files up to 512 MB on Free, Pro and Business plans, and PDF is on the default cached list.

**Backblaze B2**
- $6.95/TB/month, first 10 GB free, 3x free egress then $0.01/GB, Class A/B/C calls free (https://www.backblaze.com/cloud-storage/pricing).
- The March 17, 2026 blog post confirms the $6 to $6.95 increase and the free API calls, both effective May 1 (https://www.backblaze.com/blog/?p=112830).

**Cloudflare D1** (limits page last updated Apr 21, 2026)
- 500 MB per database on Free, 10 GB on Paid. The page says 'the 10 GB limit of a D1 database cannot be further increased.'
- 5 GB per account on Free, 1 TB on Paid. 10 databases on Free, 50,000 on Paid.
- 2 MB maximum row size and 100 KB maximum SQL statement.
- The 2026-09-01 changelog that enforces the daily free limits exists, as reported.
- Workers Free allows 100,000 requests a day and 10 ms of CPU per request.

**Supabase**
- Free: 500 MB database, 5 GB egress plus 5 GB cached egress, 1 GB file storage with a 50 MB maximum upload, 2 active projects, pause after 1 week of inactivity.
- Pro: from $25, 8 GB disk then $0.125/GB, 250 GB egress then $0.09/GB, $10 compute credit.
- The official pausing page says paused projects can be restored for 1 year. The 90-day figure the researcher saw comes only from a troubleshooting page title.

**Neon** (https://neon.com/docs/introduction/plans)
- Free: 1 GB per project, 20 GB account total, 100 CU-hours per project, 5 GB transfer per project. Compute is suspended once a limit is reached.
- Launch and Scale: 500 GB transfer per project, then $0.10/GB. Compute $0.106 (Launch) and $0.222 (Scale) per CU-hour. Storage $0.35/GB-month.

**MotherDuck**
- Lite: 10 GB storage and 10 hours of Pulse compute.
- Pulse $0.60 per CU-hour. Standard, Jumbo, Mega and Giga cost $2.40, $4.80, $12 and $24 per hour. Storage $0.04/GB-month. Business plan $250 per month plus usage.

**Hugging Face**
- Free public storage is 'Best-effort', with the 'first few gigabytes' footnote. Private storage is 100 GB.
- Rate-limit table, labeled September '25: anonymous 500/3,000/100 and free 1,000/5,000/200 per 5 minutes.

**Internet Archive**
- The rule against mirroring material still online is quoted correctly.
- Bulk limits: 500 files or 500 GB per item, and 5,000 files per day.

**Cloudflare CDN terms** (updated Sep 28, 2026)
- They name 'the Developer Platform, Images, and Stream' after 'e.g.' and do not name R2. The researchers' wording is accurate.

**On the user's question about Postgres and SQL**
- Postgres and SQL both work for job B. Supabase and Neon are real Postgres with built-in full-text search. D1 and Turso are SQL (SQLite with FTS5).
- The limit is size on the free plans, not capability. Supabase's 500 MB and Neon's 1 GB both count the search indexes, so "a few GB later" goes past either free plan.
- The cheapest real Postgres past that point is probably Neon Launch: about $0.35/GB-month for storage, plus compute only while the database is awake, with no monthly minimum. This is my inference from the published rates.
- The only $0 Postgres I found with GB-scale room is self-hosting on Oracle's Always Free VM, which comes with real ops and idle-reclaim risk.

**On the missing options**
- Pagefind is probably the most competitive $0 option for a read-mostly, batch-updated public search bar. It avoids per-query quotas, daily cutoffs and inactivity pausing.
- Turso is the closest like-for-like alternative to D1, with a 5 GB free allowance in place of D1's 500 MB per database.

**What I could not verify**
- Oracle's signup or card requirement: oracle.com/cloud/free returned HTTP 403.
- Whether Turso Cloud accepts CREATE VIRTUAL TABLE ... USING fts5. Its docs list FTS5 as built-in but do not name the product.

### Options the checker added

- **Pagefind (free, open-source static search index), hosted on Cloudflare static assets or R2. Job B.**: The records are mostly read-only and updated in batches, so the search index can be built ahead of time and served as plain files. That means no database server, no daily query quota, and no pausing or suspension at $0. Pagefind's site says it 'can run a full-text search on a 10,000 page site with a total network payload under 300kB' (usually closer to 100kB) and 'does not have any server component.' Cloudflare Workers static-asset requests are free and unlimited (Workers pricing page). Limits to plan for: Workers static assets allow 20,000 files per Worker version on Free (100,000 on Paid), and each file must be 25 MiB or smaller (https://developers.cloudflare.com/workers/platform/limits/). Pagefind writes one fragment file per indexed page, so giving every statute section its own page could pass 20,000 files. In that case the index files could be served from R2 instead. Pagefind's docs list no tested maximum page count, so search across tens of thousands of long hearing decisions should be tested. (https://pagefind.app/)
- **Turso (hosted SQLite/libSQL), Free plan. Job B.**: This is a direct alternative to D1, with more room on the free plan. Its pricing page lists 100 databases, 5 GB storage, 500 million rows read and 10 million rows written per month, and 'no credit card required.' The paid Developer plan is $4.99/month with 9 GB storage. D1 caps each free database at 500 MB, while Turso's 5 GB of storage could hold a few GB of records plus an FTS5 index (Turso's pricing page shows no per-database cap). Turso's extensions page lists FTS5 as 'Built-in' (https://docs.turso.tech/extensions). Caveats: (1) Turso also has its own Tantivy-based search that is 'not SQLite's FTS3/FTS4/FTS5' (https://docs.turso.tech/sql-reference/functions/fts), and no page states which product supports what, so test FTS5 on Turso Cloud before committing. (2) Its CLI docs say 'Databases get archived after 10 days of inactivity for users on a free plan' (https://docs.turso.tech/cli/group/unarchive). (3) The website still needs a Worker or other server so the read token is not exposed in the browser. (https://turso.tech/pricing)
- **Oracle Cloud Always Free (Object Storage, plus an Arm VM running your own Postgres). Jobs A and B.**: This is the only $0 route found to Postgres without the 500 MB (Supabase) or 1 GB (Neon) free caps. Oracle's docs give every account 20 GB of Always Free Object Storage and 10 TB of outbound data per month. That holds today's 13-16 GB of PDFs with free downloads. It also gives Arm compute (1,500 OCPU-hours and 9,000 GB-hours a month, which Oracle says equals 2 OCPUs and 12 GB of memory) and 200 GB of block storage. On that VM you could run ordinary Postgres with full-text search for a few GB of records. Oracle also gives two Always Free Autonomous Databases with 20 GB each. Catches: (1) You run and patch the server, back it up, and handle security yourself. (2) Oracle 'may reclaim idle Always Free compute instances' that stay under 20% CPU (95th percentile), network and memory for 7 days. A quiet site could be hit by this. (3) PDFs past 20 GB would need a paid account. (4) oracle.com/cloud/free returned HTTP 403, so I could not confirm the signup requirements, such as a card, from an official page. (https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm)
