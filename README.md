# Brussels 20km Race Analysis Dashboard (2026)

An interactive **Streamlit** data analysis dashboard for exploring race results and benchmarking individual runner performance from the **20 km of Brussels (2026)**.

## Overview

The **Brussels 20km Race Analysis Dashboard** parses official race split data and turns it into clear, interactive performance insights. Runners and race enthusiasts can look up any participant by name to compare their 5 km, 10 km, 15 km, and finish times against gender averages, see where they rank on the overall time distribution, and explore aggregate race statistics.

## Key Features

- **Individual Runner Lookup & Split Comparison**
  - Search any runner by name to view their 5 km, 10 km, 15 km, and 20 km finish times alongside the gender-specific averages and exact time differences (faster or slower).
- **Percentile & Distribution Benchmarking**
  - Plots each runner's split and finish times directly onto gender-specific density histograms (with KDE curves), highlighting their percentile rank (e.g., top 10%, top 25%, top 50%) at every checkpoint.
- **Overall Race Visualizations**
  - **Finish Time Distribution:** Histogram and KDE curve showing the overall spread of finish times across all participants.
  - **Gender Comparison:** Overlaid finish time distributions segmented by gender.
  - **Split Time Analysis:** Side-by-side box plots comparing 5 km, 10 km, and 15 km split times by gender.
- **Cached Data Processing**
  - Automatically parses and cleans raw JSON race records (`brussels_20km_2026.json`) into structured time metrics, using Streamlit's `@st.cache_data` for fast interactive exploration.

## Tech Stack

- **App Framework:** [Streamlit](https://streamlit.io/)
- **Data Processing:** Pandas, NumPy
- **Visualization:** Matplotlib, Seaborn

## Project Structure

```text
20km-bx-2026-dashboard/
├── race_dashboard.py         # Main Streamlit dashboard application
├── brussels_20km_2026.json   # Raw 2026 race results dataset
└── requirements.txt          # Python dependencies
```

## Getting Started

### Prerequisites

- Python 3.9+

### Installation & Usage

1. Clone the repository:
   ```bash
   git clone https://github.com/Jean-VM/20km-bx-2026-dashboard.git
   cd 20km-bx-2026-dashboard
   ```

2. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Launch the dashboard:
   ```bash
   streamlit run race_dashboard.py
   ```
