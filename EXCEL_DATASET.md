# Excel Dataset Integration

The Excel file (**Analiz-Lokman Hekim Rev.00.2.xlsx** or any compatible file) is used as an **auxiliary data source** only. It does **not** replace:

- Deterministic KPI formulas
- Rule-based efficiency classification
- The existing RAG pipeline

## How the dataset is used

1. **Validation** – Compare a building’s energy per m² to the distribution (min/mean/max) in the dataset.
2. **Benchmarking** – Expose dataset statistics (e.g. via `/dataset/stats`) for reference.
3. **RAG context** – Optionally feed “similar” records (by building type and energy/m²) into the AI prompt so explanations can refer to real or simulated reference data.

## Setup

1. **Install dependencies**
   ```bash
   pip install pandas openpyxl
   ```

2. **Set the path to your Excel file**
   - **Windows (PowerShell):**
     ```powershell
     $env:EXCEL_DATASET_PATH = "c:\Users\E\Downloads\Analiz-Lokman Hekim Rev.00.2.xlsx"
     ```
   - **Or** copy the Excel file into the project as `data/building_energy_data.xlsx` (optional fallback).

3. **Restart the backend** so it picks up the env var.

## API endpoints

- **`GET /dataset/stats`** – Returns how many records were loaded and stats (min/mean/max for total kWh, area, energy per m²). Use for benchmarking.
- **`GET /dataset/validate?total_energy_kwh=720893&building_area_m2=10200&building_type=hospital`** – Returns your energy per m² and dataset stats; use to check if a building lies within the dataset range.

## Excel structure expected

The loader supports the **Lokman Hekim** style sheets:

- **Referans Tablolar** – Table with a year column and a “Toplam … Enerji … [kWh]” column. Each row = one year’s total energy (kWh).
- **Gösterge Tablolar** – Table with a row for “Bina İnşaat Alanı” (m²) and a row for “Yıllık Toplam Enerji Tüketimi” (kWh), with years as columns (e.g. 2022, 2023, 2024). Each column = one year; area and total kWh are read from the corresponding rows.

Other Excel files with similar structure (year, total kWh, optional area) can be used; set `EXCEL_DATASET_PATH` to the file path.

## KPI clarification: period vs annual

- **Energy per m² (for period)** = `total_energy_kwh / building_area_m2` for the **selected period** (e.g. 6 or 12 months). Unit: kWh/m².
- **Annual energy per m²** = value above **normalized to one year**:  
  `energy_per_sqm_kwh * (12 / period_months)`. Unit: kWh/m²/year.

If the selected period is **12 months**, the two values are the same by design. For any other period (e.g. 1 or 6 months), the annual value is scaled so benchmarks (which are in kWh/m²/year) can be applied correctly.
