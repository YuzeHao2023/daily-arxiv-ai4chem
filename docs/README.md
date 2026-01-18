# AI4Chem ArXiv Daily - Usage Instructions

## Overview

AI4Chem ArXiv Daily automatically fetches the latest papers from arXiv related to AI for Chemistry (AI4Chem) topics and organizes them by category.

## Usage

### Manual Trigger

You can manually trigger the workflow from the GitHub Actions tab:
1. Go to your repository
2. Click on the "Actions" tab
3. Select either:
   - "Run Arxiv Papers Daily" - To fetch and update papers
   - "Run Update Paper Links Weekly" - To update GitHub code links for papers
4. Click "Run workflow"

### Automatic Scheduling

The workflows run automatically on schedules:
- **Daily Papers**: Every 5 days at 00:00 UTC (configurable in `.github/workflows/ai4chem-arxiv-daily.yml`)
- **Update Links**: Every Monday at 08:00 UTC (configurable in `.github/workflows/update-paper-links.yml`)

## Output Files

The script generates the following files:
- `README.md` - Main markdown file with all papers
- `docs/ai4chem-arxiv-daily.json` - JSON data for main README
- `docs/ai4chem-arxiv-daily-web.json` - JSON data for web version
- `docs/index.md` - GitHub Pages version
- `docs/ai4chem-arxiv-daily-wechat.json` - WeChat version data
- `docs/wechat.md` - WeChat version markdown

## Configuration

Edit `config.yaml` to customize:
- Keywords and search filters
- Output file paths
- Publication options (README, GitHub Pages, WeChat)
- Maximum number of results per search

## Paper Categories

The default configuration searches for papers in these AI4Chem categories:
1. Molecular Representation & Learning
2. Generative Design & Molecule Optimization
3. Property Prediction & ADMET
4. Reaction, Synthesis & Catalysis
5. Quantum Chemistry & Force Fields
6. Protein & Biomolecules
7. Large Language Models & Materials

## Requirements

- Python 3.10+
- Dependencies listed in `requirements.txt`:
  - arxiv
  - requests
  - pyyaml

## Troubleshooting

### GitHub Actions Failing
1. Check the workflow logs in the Actions tab
2. Verify GitHub token permissions
3. Ensure `docs/` directory exists (should be auto-created)
4. Check `config.yaml` for syntax errors

### No Papers Found
- Verify keywords in `config.yaml`
- Check if ArXiv API is accessible
- Review the workflow logs for search queries used

