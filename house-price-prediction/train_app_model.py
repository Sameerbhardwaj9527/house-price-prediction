"""Train the small 'estimator' model used by the app (13 user-friendly inputs). Run: python train_app_model.py"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, joblib, json
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, FunctionTransformer

from common import FEATS, prep

df = pd.read_csv("data/train.csv")
df = df[~((df.GrLivArea > 4000) & (df.SalePrice < 300000))].reset_index(drop=True)
y = np.log1p(df.SalePrice)
X = prep(df)
model = Pipeline([
  ("ct", ColumnTransformer([("oh", OneHotEncoder(handle_unknown="ignore"), ["Neighborhood"])], remainder="passthrough")),
  ("gbr", GradientBoostingRegressor(n_estimators=800, learning_rate=0.03, max_depth=3, subsample=.8,
                                    min_samples_leaf=10, loss="huber", random_state=42))])
oof = cross_val_predict(model, X, y, cv=KFold(5, shuffle=True, random_state=42), n_jobs=-1)
rmse = float(np.sqrt(np.mean((oof - y) ** 2)))
print(f"CV RMSE (log): {rmse:.4f}")
model.fit(X, y)

joblib.dump({"model": model, "prep_cols": FEATS}, "app_assets/model.joblib")
keep = FEATS + ["SalePrice","Id","GarageArea","Fireplaces"]
df[list(dict.fromkeys(keep))].to_csv("app_assets/app_data.csv", index=False)
pd.DataFrame({"actual": np.expm1(y), "predicted": np.expm1(oof)}).to_csv("app_assets/oof.csv", index=False)
meta = {"cv_rmse_log": rmse,
        "mape": float(np.mean(np.abs(np.expm1(oof) - np.expm1(y)) / np.expm1(y))),
        "neighborhoods": sorted(df.Neighborhood.unique().tolist()),
        "median": {c: float(df[c].median()) for c in ["GrLivArea","TotalBsmtSF","LotArea","YearBuilt"]}}
json.dump(meta, open("app_assets/meta.json", "w"), indent=1)
print(meta["mape"])
