# 🧠 Workday Job Scraper to Notion

This project automates the collection of job postings from Workday-powered career portals and uploads them to a Notion database for centralized tracking and analysis.

> ⚙️ Originally developed to scrape and track M&T Bank job listings, the scraper now supports **multi-institutional configuration** via YAML.

---

## 🚀 Features

- 🔁 Supports multiple institutions with distinct Workday URLs
- 📌 Filters jobs by location and keyword (`searchText`)
- 📥 Uploads job metadata to a Notion database
- 🔁 Avoids duplicates by checking existing Req IDs
- 📝 Parses job descriptions into Notion-friendly blocks
- 💾 Stores raw job data in structured JSON files
- 🧩 Modular design with clear separation of concerns
- 📊 Progress bars and log files with per-institution labeling

---

## 🗂️ Folder Structure

```bash
.
├── config/ # Institution config in YAML
│ └── institutions.yaml
├── json_output/ # Raw JSON responses (ignored in git)
├── docs/ # Architecture & version docs
│ └── v0.4.0_architecture.md
├── scraper.py # Main entry point
├── institution_runner.py # Runs scraping + upload per institution
├── notion_client.py # Notion API interface
├── job_parser.py # HTML to Notion block conversion
├── config_loader.py # Loads YAML config
└── .env # Notion token & DB IDs (not committed)
```

---

## ⚙️ Setup

### 1. Clone the Repo

```bash
git clone https://github.com/yourusername/workday_scraper.git
cd workday_scraper
```

### 2. Install Dependencies

### ✅ Option A: Using Conda (Recommended)

Create and activate the environment:

```bash
conda env create -f environment.yml
conda activate workday_scraper
```

> This installs all required packages in an isolated environment named workday_scraper.

### 🧪 Option B: Using pip (Alternative)

If you're not using Conda, manually install the required packages:

```bash
pip install requests python-dotenv tqdm beautifulsoup4 html2text PyYAML
```

Note: This project does not include a requirements.txt file by default.
If you’d like to generate one from an active environment:

```bash
pip freeze > requirements.txt
```

Then later you can reuse it with:

```bash
pip install -r requirements.txt
```

### 3. Create a .env File

```env
NOTION_TOKEN=your_notion_secret_token
DATABASE_ID=your_notion_database_id
APPLIED_DATABASE_ID=your_applied_jobs_database_id
```

### 4. Define Institutions

You may use the included `config/institutions.yaml` to work with those institutions.

Otherwise, edit `config/institutions.yaml` to define the Workday URLs and filters for each institution you wish to query using the sample format:

```yaml
institutions:
  - name: "<institution name>"
    workday_url: "<institution Workday URL>"
    locations:
      - "Remote, USA"
      - "Walla Walla, WA"
      - "Ding Dong, TX"
    search_text: "sql"
```

## 🧪 Usage

To run the scraper across all defined institutions:

```Bash
python scraper.py
```

- Logs will be written to `scraper.log`

- JSON job data is saved to `json_output/`

- Notion is updated with new postings

## 🧱 Versioning

This project follows [Semantic Versioning](https://semver.org/).

Detailed architecture docs are versioned under `/docs`.

## ✅ Example Notion Properties

To work with this scraper, your Notion database should include the following properties:

- Properties to be Scraped
  - `Company` (Title)
  - `Position` (Rich Text)
  - `Req ID` (Rich Text)
  - `Job Posting URL` (URL)
  - `Stage` (Status)
  - `Base Pay Low` (Number)
  - `Base Pay High` (Number)
  - `Application Deadline` (Date)
- Propertios for Manual Update(s)
  - `Due Date` (Date)
  - `Resume` (Files & media)
  - `Cover Letter` (Files & media)
  - `Ready to Apply Date` (Date)
  - `Applied Date` (Date)
  - `HR Screen Date` (Date)
  - `Interview Date` (Date)

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.

## 🙋‍♂️ Contributing

Contributions welcome! Feel free to open issues or submit pull requests.

## 📬 Contact

Maintained by [Jeremiah Haremza](https://github.com/jharemza).
