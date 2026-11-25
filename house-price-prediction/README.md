# House Prices — Advanced Regression Techniques

Kaggle: https://www.kaggle.com/competitions/house-prices-advanced-regression-techniques

Predict `SalePrice` of Ames, Iowa homes from 79 features. Metric: RMSE on log(SalePrice).

## Results
| Model | 5-fold CV RMSE (log) |
|---|---|
| Ridge | 0.1144 |
| Lasso | 0.1139 |
| ElasticNet | 0.1140 |
| Gradient Boosting | 0.1122 |
| XGBoost | 0.1158 |
| LightGBM | 0.1154 |
| **Blend (Lasso + GBR)** | **0.1089** |

## Pipeline
1. `01_eda` — target skew (1.88 → log fixes it), missing values, correlations, outliers
2. `02_data_cleaning` — drop 2 outliers, NA-means-absent imputation, neighborhood-median LotFrontage, fix GarageYrBlt typo
3. `03_feature_engineering` — ordinal encoding, TotalSF / TotalBath / HouseAge etc., Box-Cox on skewed columns, one-hot
4. `04_model_training` — 6 models, out-of-fold predictions, non-negative blend, writes `submission.csv`

`src/pipeline.py` is the whole thing as one script: `python src/pipeline.py`

## Run
Put Kaggle's `train.csv` and `test.csv` in `data/`, then run notebooks 01 → 04 in order (or the script).

```
pip install -r requirements.txt
```

The interactive app lives in its own project: `../house-price-app`.
