"""
================================================================================
  WATER PUMP DIGITAL TWIN — MACHINE LEARNING MODEL TRAINING PIPELINE
  Dataset: UCI AI4I 2020 Predictive Maintenance Dataset (10,000 records)
  Model Architecture: Random Forest (Detection + Multi-Class Diagnosis + RUL)
================================================================================
"""

import os
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

print("=" * 70)
print("   🚀 TRAINING DIGITAL TWIN AI/ML MODEL PIPELINE")
print("=" * 70)

# ──────────────────────────────────────────────────────────────
# STEP 1: LOAD RAW DATASET
# ──────────────────────────────────────────────────────────────
csv_file = "ai4i2020.csv"
if not os.path.exists(csv_file):
    csv_file = os.path.join(os.path.dirname(__file__), "ai4i2020.csv")

print(f"[STEP 1/5] Loading dataset from: {csv_file}")
df = pd.read_csv(csv_file)
print(f"           Dataset Shape: {df.shape[0]} rows, {df.shape[1]} columns")

# Quick EDA Summary
print("\n[EDA SUMMARY]")
print(f"  • Total Operating Cycles: {len(df):,}")
print(f"  • Normal Operating Cycles: {(df['Machine failure'] == 0).sum():,} ({(df['Machine failure'] == 0).mean()*100:.1f}%)")
print(f"  • Failure Cycles Detected: {(df['Machine failure'] == 1).sum():,} ({(df['Machine failure'] == 1).mean()*100:.1f}%)")

# ──────────────────────────────────────────────────────────────
# STEP 2: PHYSICS-INFORMED FEATURE ENGINEERING
# ──────────────────────────────────────────────────────────────
print("\n[STEP 2/5] Engineering Physics-Informed Features...")

# 1. Thermal Dissipation Gradient: ΔT = Process Temp - Air Temp (Kelvin)
df['Temp_Diff'] = df['Process temperature [K]'] - df['Air temperature [K]']

# 2. Hydraulic Shaft Power: P = 2π·N·τ / 60,000 (Kilowatts)
df['Power_kW'] = (df['Torque [Nm]'] * (2 * np.pi * df['Rotational speed [rpm]'] / 60)) / 1000.0

# 3. Mechanical Fatigue Overstrain: σ = Tool Wear × Torque (min·Nm)
df['Overstrain'] = df['Tool wear [min]'] * df['Torque [Nm]']

# Map Ground-Truth Failure Modes for multi-class classification
def label_failure_mode(row):
    if row['Machine failure'] == 0:
        return 'NORMAL'
    if row['HDF'] == 1:
        return 'Heat Dissipation Failure (HDF)'
    if row['PWF'] == 1:
        return 'Power Failure (PWF)'
    if row['OSF'] == 1:
        return 'Overstrain Failure (OSF)'
    if row['TWF'] == 1:
        return 'Tool Wear Failure (TWF)'
    if row['RNF'] == 1:
        return 'Random Failure (RNF)'
    return 'General Machine Failure'

df['Failure_Mode'] = df.apply(label_failure_mode, axis=1)

feature_cols = [
    'Air temperature [K]',
    'Process temperature [K]',
    'Rotational speed [rpm]',
    'Torque [Nm]',
    'Tool wear [min]',
    'Temp_Diff',
    'Power_kW',
    'Overstrain'
]

X = df[feature_cols]
y_binary = df['Machine failure']
y_mode   = df['Failure_Mode']

print(f"           Feature Matrix X: {X.shape}")
print(f"           Features Used: {', '.join(feature_cols)}")

# ──────────────────────────────────────────────────────────────
# STEP 3: TRAIN BINARY ANOMALY DETECTOR (RANDOM FOREST)
# ──────────────────────────────────────────────────────────────
print("\n[STEP 3/5] Training Binary Fault Detector (Random Forest)...")
X_tr, X_te, y_tr, y_te = train_test_split(X, y_binary, test_size=0.20, random_state=42, stratify=y_binary)

binary_clf = RandomForestClassifier(
    n_estimators=100,
    max_depth=12,
    class_weight='balanced',
    random_state=42,
    n_jobs=-1
)
binary_clf.fit(X_tr, y_tr)
bin_pred = binary_clf.predict(X_te)
bin_acc  = accuracy_score(y_te, bin_pred)
print(f"           ✅ Binary Fault Detection Accuracy: {bin_acc * 100:.2f}%")

# ──────────────────────────────────────────────────────────────
# STEP 4: TRAIN MULTI-CLASS ROOT-CAUSE CLASSIFIER
# ──────────────────────────────────────────────────────────────
print("\n[STEP 4/5] Training Multi-Class Failure Mode Classifier...")
X_mtr, X_mte, ym_tr, ym_te = train_test_split(X, y_mode, test_size=0.20, random_state=42, stratify=y_mode)

mode_clf = RandomForestClassifier(
    n_estimators=100,
    max_depth=12,
    class_weight='balanced',
    random_state=42,
    n_jobs=-1
)
mode_clf.fit(X_mtr, ym_tr)
mode_pred = mode_clf.predict(X_mte)
mode_acc  = accuracy_score(ym_te, mode_pred)
print(f"           ✅ Multi-Class Diagnostic Accuracy: {mode_acc * 100:.2f}%")

# ──────────────────────────────────────────────────────────────
# STEP 5: TRAIN REMAINING USEFUL LIFE (RUL) REGRESSOR
# ──────────────────────────────────────────────────────────────
print("\n[STEP 5/5] Training Prognostic Remaining Useful Life (RUL) Regressor...")
def compute_rul_target(row):
    wear = row['Tool wear [min]']
    strain_factor = 1.0
    if row['Temp_Diff'] < 8.6 and row['Rotational speed [rpm]'] < 1380:
        strain_factor += 0.5
    if row['Overstrain'] > 11000:
        strain_factor += 0.8
    remaining_wear = max(0.0, 250.0 - wear)
    base_hours = remaining_wear * 1.6
    return max(0.0, base_hours / strain_factor)

df['RUL_Hours'] = df.apply(compute_rul_target, axis=1)

rul_regressor = RandomForestRegressor(
    n_estimators=60,
    max_depth=10,
    random_state=42,
    n_jobs=-1
)
rul_regressor.fit(X, df['RUL_Hours'])
print("           ✅ RUL Prognostic Regressor Trained.")

# ──────────────────────────────────────────────────────────────
# SAVE FULL MODEL BUNDLE TO DISK
# ──────────────────────────────────────────────────────────────
output_model_path = os.path.join(os.path.dirname(__file__), "pump_ai_model.pkl")

model_bundle = {
    'binary_model': binary_clf,
    'mode_model':   mode_clf,
    'rul_model':    rul_regressor,
    'feature_cols': feature_cols,
    'classes':      [str(c) for c in mode_clf.classes_]
}

joblib.dump(model_bundle, output_model_path)
print("=" * 70)
print(f"🎉 MODEL BUNDLE SAVED SUCCESSFULLY AT:\n   {output_model_path}")
print("=" * 70)

if __name__ == "__main__":
    print("\nTraining complete! You can re-run this script anytime with: python train_model.py")
