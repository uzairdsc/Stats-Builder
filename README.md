# PSL Batting Stats Summary

Password-protected Streamlit dashboard for T20 ball-by-ball batting analysis.

Build custom T20 batting and bowling tables. Filter by phase, competition, opposition, venue and date range. Every number from ball-by-ball records across 18 leagues — not aggregated scorecards.


## Data Sources
- CSV upload
- S3: `Multiple Uploaded Files to Select From`
- Local cache files

## Usage
1. Add credentials to `.streamlit/secrets.toml` (`[auth]` password, `[aws]` keys)
2. Run: `streamlit run app.py`
3. Load a dataset from the sidebar
4. Set filters → **Apply Filters** to generate the batting summary table
5. Use the **Rows** dropdown to control table size; **Clear Filters** resets everything

## Requirements
`streamlit`, `pandas`, `numpy`, `boto3`