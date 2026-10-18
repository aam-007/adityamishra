# Aditya Mishra — research portfolio

A minimalist static portfolio with paper/terminal themes and a searchable research catalogue. No framework, package installation, or server is required for reading the site. Search and theme controls enhance the HTML; all papers remain accessible without JavaScript.

Website: [aam-007.github.io/adityamishra](https://aam-007.github.io/adityamishra/)

## Preview

Use Python 3.12 or newer:

```sh
python -m http.server 8000
```

Open http://localhost:8000. A local HTTP server is recommended for theme persistence. Relative links also support GitHub Pages deployment beneath `/adityamishra/`.

## Edit and build

- `content.json`: paper titles, summaries, topics, years, featured entries, and archive membership.
- `templates/`: the original page layouts and exact original styles, preserved as the design source.
- `scripts/build.py`: generates the homepage and contact window, research pages, legacy redirect, sitemap, custom 404, and surprise page. Edit the introduction here rather than in generated HTML.
- `assets/`: original styles extracted into reusable files, small functional accessibility additions, shared theme behavior, and catalogue filtering.

Research pages have a **Legacy mode** toggle beside the theme control. It switches the tables to the original centered, bold link lists, hiding columns and counts. The preference carries across research pages when browser storage is available. Search/filtering works in both views, and the publishing app updates both automatically from the same catalogue.

```sh
python scripts/build.py
python scripts/check.py
```

Commit source changes and regenerated HTML together. GitHub Actions rebuilds and checks generated files, local link targets, exact filename casing, anchors, metadata, and catalogue consistency.

## Add a paper

### Interactive publisher (recommended)

On Windows, double-click **Publish Research.cmd**, or run:

```sh
python publisher.py
```

Requires Python 3.12+ and Git. The app asks for the PDF path, title, summary, topic, publication year, and destination collection. Finance and technology papers are filed automatically by year, creating a year page when needed; equity research supports custom collections. Tables, counts, search filters, and the sitemap update automatically. Existing files are never overwritten.

It builds and validates a temporary copy first, then displays all files that will change. Choose **Save locally**, **Save, commit, and push to GitHub**, or **Cancel**. Local saves can be previewed with the command above. To publish a local save later, commit and push it with Git.

Publishing uses the repository’s `origin` remote and current branch (currently `main`). Authenticate Git with your existing GitHub credentials, for example through Git Credential Manager or `gh auth login` followed by `gh auth setup-git`. The app never asks for or stores a token. Save and commit the initial website/app changes before the first upload: publishing requires a clean working tree and a branch in sync with GitHub, so unrelated work cannot be uploaded accidentally. The app does not force-push, reset, or merge.

If a push fails, the validated files and local commit remain intact; the error shows the retry command. A successful push updates the branch; the site goes live when the repository’s GitHub Pages deployment completes. If a session crashes and leaves `.publisher.lock`, remove that file only after confirming the publisher is no longer running.

GitHub Actions checks the Python source syntax, rebuilds the site, validates local links and catalogue entries, and verifies that generated files are current. It does not require a `tests` folder.

### Manual catalogue editing (optional)

1. Add the PDF under the appropriate research directory. Prefer short, consistent new filenames; preserve existing public addresses.
2. Add a `content.json` entry with a unique `id`, project-relative `path`, `title`, `topic`, `summary`, and `year` (empty when unknown). Describe the paper without presenting its conclusions as established facts.
3. Add its path to the relevant page’s `documents` array in `content.json`. Archive tables and collection counts are generated from this data. The `featured` field is reserved for future use and does not change the homepage.
4. Build, validate, and preview at desktop and mobile widths. Open the document link.

Finance and technology have year-based archives. Phonex-L1, Phonex-SLM, PhonexCoin, and PhonexOS are dated 2025; the other original technology papers are dated 2026, as specified by the author. Existing PDFs retain their original addresses even when grouped under year pages. Alternate computational-leadership PDFs remain available as assets rather than duplicate catalogue entries. Editable document sources remain in their existing locations.

## Hidden extras

Five quick Space presses open `cheeky.html`. On phones, use five quick two-finger taps in the same area. Holding Space does not count as multiple presses. Links, buttons, forms, dialogs, selected text, modified keys, single-finger taps, swipes, and pinches do not trigger it. Pauses, scrolling, navigation, or leaving the page reset the sequence. Space scrolling is suppressed only while the page itself has focus; controls keep their normal behavior. Touch gestures never disable native browser scrolling or zooming. The trigger needs no browser storage. The 100 random messages live in `assets/surprise-message.js`; the birthday entry uses an ASCII cake. Consecutive visits avoid repeating the same message when session storage is available. The surprise page follows the saved theme, has no trigger of its own, and is excluded from the sitemap.

## Hosting

The subtle footer displays the visitor’s current year at runtime and links to `sitemap.html`. This theme-aware sitemap has native expandable collections, optional expand/collapse controls, every catalogued PDF, the surprise page, and the GitHub repository link. It rebuilds automatically when the publishing app adds research. `sitemap.xml` remains the crawler-facing sitemap; the noindex surprise page is listed only in the human-readable map.

Serve the generated files directly with GitHub Pages. `.nojekyll` disables Jekyll processing. Update `BASE` in `scripts/build.py` if the domain changes; it controls canonical URLs and the sitemap. The custom 404 page uses absolute recovery links for nested missing URLs.

The résumé supplies the biography and contact information. Papers and preprints retain their original documents and authorship; inclusion does not imply peer review.
