# Commodity Monitoring System: Frequency Detection and Z-score Alerting

This documentation describes the workflow for a Python-based system that loads commodity price time series, determines whether updates are **daily or weekly**, and computes **z-scores** to flag notable moves.

---

## 1. Objective
Commodity data often comes in **different update frequencies**:
- **Daily commodities**: prices change every trading day (e.g., Brent crude, iron ore).
- **Weekly commodities**: prices are only updated once a week but forward-filled into daily time series by data providers.

Directly computing daily returns on weekly-forward-filled data causes distorted volatility and inflated z-scores.  
This workflow **auto-detects update frequency** and adjusts calculations to ensure fair comparisons.

---

## 2. Workflow Overview

### Step 1: Load the Data
- Input: Daily commodity price time series.
- Example:

```
Date        Price
2025-01-01  100
2025-01-02  100
2025-01-03  100
2025-01-04  105
```

---

### Step 2: Compute Daily Returns
```python
df["Return"] = df["Price"].pct_change()
```
- Weekly commodities will show **long stretches of zeros** followed by jumps.

---

### Step 3: Detect Frequency
- Look at the last N days (default: 90).
- Measure ratio of **nonzero daily returns**:
  - If ratio > 0.5 → classify as **daily**.
  - Else → classify as **weekly**.

```python
nonzero_ratio = (df["Return"].tail(90) != 0).mean()
if nonzero_ratio > 0.5:
    freq = "daily"
else:
    freq = "weekly"
```

---

### Step 4: Resample to Native Frequency
- If **daily**: keep as is.
- If **weekly**: resample to `"W"` (end of week).

```python
if freq == "weekly":
    series = df["Price"].resample("W").last()
else:
    series = df["Price"]
```

---

### Step 5: Compute Returns at Correct Frequency
```python
returns = series.pct_change()
```

---

### Step 6: Rolling Mean & Standard Deviation
- Always use **30 observations** (not 30 days).
- This normalizes across different frequencies.

```python
rolling_mean = returns.rolling(window=30).mean()
rolling_std  = returns.rolling(window=30).std()
```

---

### Step 7: Calculate Z-score
```python
zscore = (returns - rolling_mean) / rolling_std
```

Interpretation:
- z = 0 → today’s return equals average historical return.
- z = 1 → today’s return is 1 standard deviation above average.
- z = -2 → today’s return is 2 standard deviations below average.

---

### Step 8: Flag Notable Moves
Thresholds (industry practice):
- |z| ≥ 1 → analysts should **take notice**.
- |z| ≥ 2 → **notable move**.
- |z| ≥ 3 → **extreme move**.

```python
df["Zscore"] = zscore
df["Flag"] = df["Zscore"].apply(
    lambda z: "notable" if abs(z) >= 2 else ""
)
```

---

## 3. Example Flow

1. Load daily series (with forward-fill).
2. Detect commodity as **weekly**.
3. Resample to weekly.
4. Compute returns.
5. Apply 30-week rolling z-score.
6. Flag last point if |z| ≥ 2.

---

## 4. Benefits
- **Automatic detection** of update frequency.
- **Consistent statistics** (30 observations for both daily & weekly).
- Avoids inflated volatility from forward-fill zeros.
- Produces meaningful alerts for both traders and analysts.

---

## 5. Extensions
- Add **monthly detection** (resample to `"M"`, use 12 months).
- Track **regime changes**: log when commodities switch from daily → weekly updates.
- Support **dual Z-scores**:
  - **Return-based z-scores** for short-term moves.
  - **Price-based z-scores** for long-term valuation context.

---
