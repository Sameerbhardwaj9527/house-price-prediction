import numpy as np
KQ = {"Po":1,"Fa":2,"TA":3,"Gd":4,"Ex":5}
FEATS = ["Neighborhood","OverallQual","OverallCond","GrLivArea","TotalBsmtSF","LotArea","GarageCars",
         "FullBath","BedroomAbvGr","YearBuilt","KitchenQual","Fireplaces","CentralAir"]

def prep(d):
    d = d[FEATS].copy()
    d["KitchenQual"] = d["KitchenQual"].map(KQ).fillna(3)
    d["CentralAir"] = (d["CentralAir"] == "Y").astype(int)
    for c in ["GrLivArea", "TotalBsmtSF", "LotArea"]: d[c] = np.log1p(d[c])
    return d
