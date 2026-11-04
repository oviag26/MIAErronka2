import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.neural_network import MLPRegressor, MLPClassifier
from sklearn.metrics import mean_absolute_error, r2_score, accuracy_score
import joblib

# 1. Preparamos los datos
df = pd.read_csv('MUNDAKA.csv', sep=';', encoding='latin1')
df.columns = [col.replace('礸', 'µ') for col in df.columns]
df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')
df = df.sort_values('Date').reset_index(drop=True)
df['categoria'] = pd.qcut(df['PM10 (µg/m3)'], q=4, labels=['buena', 'moderada', 'mala', 'muy_mala'], duplicates='drop')
df['Month'] = df['Date'].dt.month
df['DayOfWeek'] = df['Date'].dt.dayofweek

# 🔥 LA SOLUCIÓN: Borramos las filas donde PM10 esté vacío (NaN)
df = df.dropna(subset=['PM10 (µg/m3)'])

features_num = ['NO (µg/m3)', 'NOX (µg/m3)', 'NO2 (µg/m3)', 'O3 (µg/m3)', 'PM2,5 (µg/m3)']
features_cat = ['Month', 'DayOfWeek']
X = df[features_num + features_cat]
y_reg = df['PM10 (µg/m3)']  
y_clf = df['categoria']     

X_train, X_test, y_reg_train, y_reg_test, y_clf_train, y_clf_test = train_test_split(X, y_reg, y_clf, test_size=0.2, random_state=42)

preprocesamiento = ColumnTransformer([
    ('num', Pipeline([('imp', SimpleImputer(strategy='median')), ('sc', StandardScaler())]), features_num),
    ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), features_cat)
])
X_train_t = preprocesamiento.fit_transform(X_train)
X_test_t = preprocesamiento.transform(X_test)

# ==========================================
# ENTRENAR MODELOS
# ==========================================
print("--- ENTRENANDO REGRESIÓN ---")
mod_reg = RandomForestRegressor(random_state=42)
mod_reg.fit(X_train_t, y_reg_train)
pred_reg = mod_reg.predict(X_test_t)
print(f"Error (MAE): {mean_absolute_error(y_reg_test, pred_reg):.2f}")

print("\n--- ENTRENANDO CLASIFICACIÓN ---")
mod_clf = RandomForestClassifier(random_state=42)
mod_clf.fit(X_train_t, y_clf_train)
pred_clf = mod_clf.predict(X_test_t)
print(f"Acierto (Accuracy): {accuracy_score(y_clf_test, pred_clf) * 100:.2f}%")

print("\n--- ENTRENANDO RED NEURONAL (MLP) ---")
mlp_clf = MLPClassifier(hidden_layer_sizes=(32, 16), max_iter=500, random_state=42)
mlp_clf.fit(X_train_t, y_clf_train)
pred_mlp = mlp_clf.predict(X_test_t)
print(f"Acierto Red Neuronal: {accuracy_score(y_clf_test, pred_mlp) * 100:.2f}%")

print("\n--- GUARDANDO MODELOS ---")
joblib.dump(mod_reg, 'modelo_reg.pkl')
joblib.dump(mod_clf, 'modelo_clf.pkl')
joblib.dump(mlp_clf, 'modelo_mlp.pkl')
print("✅ ¡Modelos guardados en archivos .pkl!")