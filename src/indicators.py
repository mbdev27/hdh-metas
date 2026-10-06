from src.contract_registry import load
def indicators(): return load('indicators.yaml')['indicators']
