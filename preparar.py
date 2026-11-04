import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder

# 1. Cargamos el archivo CSV con latin1 (porque tu archivo tiene acentos y la µ)
df = pd.read_csv('MUNDAKA.csv', sep=';', encoding='latin1')


df.columns = [col.replace('礸', 'µ') for col in df.columns]

df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')
df = df.sort_values('Date').reset_index(drop=True)

# 2. Creamos la categoría
df['categoria'] = pd.qcut(df['PM10 (µg/m3)'], q=4, labels=['buena', 'moderada', 'mala', 'muy_mala'], duplicates='drop')

# 3. Elegimos qué columnas usará la IA
df['Month'] = df['Date'].dt.month
df['DayOfWeek'] = df['Date'].dt.dayofweek

features_num = ['NO (µg/m3)', 'NOX (µg/m3)', 'NO2 (µg/m3)', 'O3 (µg/m3)', 'PM2,5 (µg/m3)']
features_cat = ['Month', 'DayOfWeek']
X = df[features_num + features_cat]

y_reg = df['PM10 (µg/m3)']  
y_clf = df['categoria']     

# 4. Dividimos los datos
X_train, X_test, y_reg_train, y_reg_test, y_clf_train, y_clf_test = train_test_split(
    X, y_reg, y_clf, test_size=0.2, random_state=42
)

# 5. Preparamos los datos
preprocesamiento = ColumnTransformer([
    ('num', Pipeline([('imp', SimpleImputer(strategy='median')), ('sc', StandardScaler())]), features_num),
    ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), features_cat)
])

X_train_t = preprocesamiento.fit_transform(X_train)
X_test_t = preprocesamiento.transform(X_test)

print("✅ ¡Datos preparados y listos para MIA!")