import pandas as pd
def score(value,rule):
    if value is None or pd.isna(value): return None
    bands=rule['faixas']
    if isinstance(bands,dict): return bands.get(value)
    if not bands: return 0.0
    for threshold,points in bands:
        if (value<=threshold if rule['operador']=='<=' else value>=threshold): return float(points)
    return 0.0
