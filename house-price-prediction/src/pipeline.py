"""House Prices - full pipeline (clean -> features -> models -> submission)."""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from scipy.stats import skew
from scipy.special import boxcox1p
from sklearn.model_selection import KFold, cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import RobustScaler
from sklearn.linear_model import Ridge, Lasso, ElasticNet
from sklearn.ensemble import GradientBoostingRegressor
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor

SEED = 42

# ---------- 02 CLEANING ----------
NONE_CAT = ["PoolQC","MiscFeature","Alley","Fence","FireplaceQu","GarageType","GarageFinish",
            "GarageQual","GarageCond","BsmtQual","BsmtCond","BsmtExposure","BsmtFinType1",
            "BsmtFinType2","MasVnrType"]
ZERO_NUM = ["GarageYrBlt","GarageArea","GarageCars","BsmtFinSF1","BsmtFinSF2","BsmtUnfSF",
            "TotalBsmtSF","BsmtFullBath","BsmtHalfBath","MasVnrArea"]
MODE_CAT = ["MSZoning","Electrical","KitchenQual","Exterior1st","Exterior2nd","SaleType"]

def clean(train, test):
    train = train[~((train.GrLivArea > 4000) & (train.SalePrice < 300000))].reset_index(drop=True)
    y = np.log1p(train.pop("SalePrice"))
    n_train = len(train)
    df = pd.concat([train, test], ignore_index=True).drop(columns=["Id","Utilities"])
    for c in NONE_CAT: df[c] = df[c].fillna("None")
    for c in ZERO_NUM: df[c] = df[c].fillna(0)
    for c in MODE_CAT: df[c] = df[c].fillna(df[c].mode()[0])
    df["Functional"] = df["Functional"].fillna("Typ")
    df["LotFrontage"] = df.groupby("Neighborhood")["LotFrontage"].transform(lambda s: s.fillna(s.median()))
    df["LotFrontage"] = df["LotFrontage"].fillna(df["LotFrontage"].median())
    bad = df.GarageYrBlt > 2010                      # typo (2207) in test set
    df.loc[bad, "GarageYrBlt"] = df.loc[bad, "YearBuilt"]
    for c in ["MSSubClass","MoSold","YrSold"]: df[c] = df[c].astype(str)
    assert df.isna().sum().sum() == 0
    return df, y, n_train

# ---------- 03 FEATURE ENGINEERING ----------
QUAL = {"None":0,"Po":1,"Fa":2,"TA":3,"Gd":4,"Ex":5}
ORD = {
 **{c: QUAL for c in ["ExterQual","ExterCond","BsmtQual","BsmtCond","HeatingQC","KitchenQual",
                      "FireplaceQu","GarageQual","GarageCond","PoolQC"]},
 "BsmtExposure": {"None":0,"No":1,"Mn":2,"Av":3,"Gd":4},
 "BsmtFinType1": {"None":0,"Unf":1,"LwQ":2,"Rec":3,"BLQ":4,"ALQ":5,"GLQ":6},
 "BsmtFinType2": {"None":0,"Unf":1,"LwQ":2,"Rec":3,"BLQ":4,"ALQ":5,"GLQ":6},
 "GarageFinish": {"None":0,"Unf":1,"RFn":2,"Fin":3},
 "Functional": {"Sal":0,"Sev":1,"Maj2":2,"Maj1":3,"Mod":4,"Min2":5,"Min1":6,"Typ":7},
 "LotShape": {"IR3":0,"IR2":1,"IR1":2,"Reg":3},
 "LandSlope": {"Sev":0,"Mod":1,"Gtl":2},
 "PavedDrive": {"N":0,"P":1,"Y":2},
 "Fence": {"None":0,"MnWw":1,"GdWo":2,"MnPrv":3,"GdPrv":4},
 "CentralAir": {"N":0,"Y":1},
}

def engineer(df, skew_thresh=0.75):
    df = df.copy()
    for c, m in ORD.items(): df[c] = df[c].map(m).astype(int)
    df["TotalSF"] = df.TotalBsmtSF + df["1stFlrSF"] + df["2ndFlrSF"]
    df["TotalBath"] = df.FullBath + .5*df.HalfBath + df.BsmtFullBath + .5*df.BsmtHalfBath
    df["TotalPorchSF"] = df.OpenPorchSF + df.EnclosedPorch + df["3SsnPorch"] + df.ScreenPorch + df.WoodDeckSF
    df["HouseAge"] = (df.YrSold.astype(int) - df.YearBuilt).clip(lower=0)
    df["RemodAge"] = (df.YrSold.astype(int) - df.YearRemodAdd).clip(lower=0)
    df["IsRemodeled"] = (df.YearRemodAdd != df.YearBuilt).astype(int)
    df["IsNew"] = (df.YrSold.astype(int) == df.YearBuilt).astype(int)
    for name, col in [("HasPool","PoolArea"),("Has2ndFlr","2ndFlrSF"),("HasGarage","GarageArea"),
                      ("HasBsmt","TotalBsmtSF"),("HasFireplace","Fireplaces")]:
        df[name] = (df[col] > 0).astype(int)
    df["QualxSF"] = df.OverallQual * df.TotalSF
    df["QualxCond"] = df.OverallQual * df.OverallCond
    num = df.select_dtypes(include=[np.number]).columns
    sk = df[num].apply(lambda s: skew(s)); sk = sk[sk.abs() > skew_thresh].index
    flags = [c for c in sk if df[c].nunique() > 2]
    for c in flags: df[c] = boxcox1p(df[c], 0.15)
    df = pd.get_dummies(df, drop_first=True, dtype=int)
    df = df.loc[:, df.sum() >= 5]                      # drop ultra-rare dummies
    return df

# ---------- 04 MODELS ----------
def get_models():
    return {
     "Ridge": make_pipeline(RobustScaler(), Ridge(alpha=15)),
     "Lasso": make_pipeline(RobustScaler(), Lasso(alpha=0.0005, max_iter=50000)),
     "ElasticNet": make_pipeline(RobustScaler(), ElasticNet(alpha=0.0005, l1_ratio=.9, max_iter=50000)),
     "GBR": GradientBoostingRegressor(n_estimators=3000, learning_rate=0.02, max_depth=4, max_features="sqrt",
                min_samples_leaf=15, min_samples_split=10, loss="huber", subsample=.8, random_state=SEED),
     "XGB": XGBRegressor(n_estimators=2500, learning_rate=0.015, max_depth=3, min_child_weight=1.5,
                subsample=.7, colsample_bytree=.45, reg_alpha=.4, reg_lambda=.8, random_state=SEED, n_jobs=-1),
     "LGBM": LGBMRegressor(n_estimators=2500, learning_rate=0.01, num_leaves=6, max_bin=200, subsample=.7,
                subsample_freq=5, colsample_bytree=.3, reg_alpha=.1, reg_lambda=.1, min_child_samples=5,
                random_state=SEED, n_jobs=-1, verbose=-1),
    }

def cv_rmse(model, X, y, n=5):
    kf = KFold(n, shuffle=True, random_state=SEED)
    return -cross_val_score(model, X, y, scoring="neg_root_mean_squared_error", cv=kf, n_jobs=-1)

def blend_weights(oof, y):
    from scipy.optimize import nnls
    w, _ = nnls(oof.values, y.values); return w / w.sum()

def run(data_dir="data", out="submission.csv"):
    from sklearn.model_selection import cross_val_predict
    tr, te = pd.read_csv(f"{data_dir}/train.csv"), pd.read_csv(f"{data_dir}/test.csv")
    ids = te["Id"]
    df, y, n = clean(tr, te); X = engineer(df)
    Xtr, Xte = X.iloc[:n], X.iloc[n:]
    models, oof, preds = get_models(), {}, {}
    kf = KFold(5, shuffle=True, random_state=SEED)
    for k, m in models.items():
        oof[k] = cross_val_predict(m, Xtr, y, cv=kf, n_jobs=-1)
        print(f"{k:11s} CV RMSE {np.sqrt(np.mean((oof[k]-y)**2)):.4f}")
        preds[k] = m.fit(Xtr, y).predict(Xte)
    oof = pd.DataFrame(oof); w = blend_weights(oof, y)
    print("blend weights:", dict(zip(oof.columns, w.round(3))))
    print(f"Blend CV RMSE {np.sqrt(np.mean((oof.values@w-y)**2)):.4f}")
    final = np.expm1(pd.DataFrame(preds)[oof.columns].values @ w)
    pd.DataFrame({"Id": ids, "SalePrice": final}).to_csv(out, index=False)
    print("saved", out)

if __name__ == "__main__":
    run()
