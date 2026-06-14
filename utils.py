import pandas as pd

def load_categories(csv_path):
    df = pd.read_csv(csv_path)
    required = {'name','min','max','priority','alpha'}
    if not required.issubset(set(df.columns)):
        raise ValueError(f"CSV must contain columns: {required}")
    return df

def save_allocation(allocation_dict, out_csv):
    df = pd.DataFrame([{"category":k, "amount":v} for k,v in allocation_dict.items()])
    df.to_csv(out_csv, index=False)
    return out_csv

