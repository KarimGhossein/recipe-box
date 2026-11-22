import os
DATA = os.environ.get("SR28_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "sr28", "package", "data"))
COLS="NDB_No Shrt_Desc Water Energ_Kcal Protein Lipid_Tot Ash Carbohydrt Fiber_TD Sugar_Tot Calcium Iron Magnesium Phosphorus Potassium Sodium Zinc Copper Manganese Selenium Vit_C Thiamin Riboflavin Niacin Panto_Acid Vit_B6 Folate_Tot Folic_Acid Food_Folate Folate_DFE Choline_Tot Vit_B12 Vit_A_IU Vit_A_RAE Retinol Alpha_Carot Beta_Carot Beta_Crypt Lycopene Lut_Zea Vit_E Vit_D_mcg Vit_D_IU Vit_K FA_Sat FA_Mono FA_Poly Cholestrl GmWt_1 GmWt_Desc1 GmWt_2 GmWt_Desc2 Refuse_Pct".split()
def parse(line):
    return [f.strip('~') for f in line.rstrip('\r\n').split('^')]
def load():
    rows={}
    for line in open(os.path.join(DATA, 'ABBREV.txt'), encoding='latin-1'):
        f=parse(line)
        if len(f)!=len(COLS): raise SystemExit(f'bad cols {len(f)}')
        d=dict(zip(COLS,f)); rows[d['NDB_No']]=d
    desc={}
    for line in open(os.path.join(DATA, 'FOOD_DES.txt'), encoding='latin-1'):
        f=parse(line)
        if len(f)>2: desc[f[0]]=f[2]
    return rows, desc
