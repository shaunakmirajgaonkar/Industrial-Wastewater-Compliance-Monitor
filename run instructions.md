# Run Instructions

## macOS / Linux

```bash
cd Industrial_Wastewater_Compliance_Monitor
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

## Windows

```powershell
cd Industrial_Wastewater_Compliance_Monitor
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

## Sample CSV

Use:

`data/sample_wastewater_compliance_records.csv`

Dashboard location:

`📂 Data Operations` → `Upload CSV`

## Stop Streamlit

Press `Ctrl + C` in Terminal.
