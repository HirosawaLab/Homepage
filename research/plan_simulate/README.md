## 概要

`plan.md` の要件に基づき、Al–Cu 合金の時効析出に対する KWN（Kampmann–Wagner Numerics）/コントロールボリューム法の Python 実装を `kwn_simulation.py` に用意しています。

- **ゴール**: 固溶 Cu 濃度 \(\bar C(t)\) を計算し、「過飽和分の 10% が析出へ移った時刻」 \(t_{10}^{\mathrm{sim}}\) を求める。
- **主な機能**:
  - Ce(T), D(T) の Arrhenius 近似
  - 核生成率 \(j(t)\)、成長速度 \(v_i\)、粒径分布の更新
  - 体積分率と質量保存から \(\bar C(t)\) を更新
  - 実験の \(t_{10}^{\mathrm{exp}}\) に対して A0 を 1 次元探索で同定

## 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

## 基本的な使い方

### 1. そのままデモ実行

```bash
python kwn_simulation.py
```

ダミーパラメータ（`example_parameters()`）で 1 回シミュレーションし、計算された `t10_sim` を標準出力に表示します。

### 2. 自分の条件で 1 回シミュレーション

Python からモジュールとして呼び出します（Jupyter Notebook でも可）。

```python
from kwn_simulation import run_single_simulation, example_parameters

thermo_params, grid_params = example_parameters()

# 温度や初期濃度などを実験条件に合わせて変更
thermo_params["T"] = 160.0 + 273.15  # 例: 160°C
thermo_params["C0"] = 0.04          # 例: Cu 原子分率

result = run_single_simulation(thermo_params, grid_params)
print("t10_sim =", result.t10_sim, "s")
```

`result` には以下が含まれます：

- `result.t`: 時間配列
- `result.C_bar`: 平均固溶濃度 \(\bar C(t)\)
- `result.f`: 析出物体積分率 \(f(t)\)
- `result.r_grid`: 粒子半径クラス
- `result.N`: 各時刻の粒子数密度分布
- `result.t10_sim`: 10%到達時刻（見つからないときは `None`）

### 3. 実験の t10_exp から A0 を同定

```python
from kwn_simulation import example_parameters, calibrate_A0

t10_exp = 3600.0  # 例: 実験から得た 10%到達時刻 [s]
thermo_params, grid_params = example_parameters()

A0_bounds = (1e38, 1e42)  # 探索範囲の例（実験系に合わせて調整）
A0_opt, t10_sim_opt = calibrate_A0(
    t10_exp=t10_exp,
    thermo_base=thermo_params,
    grid_params=grid_params,
    A0_bounds=A0_bounds,
)

print("A0* =", A0_opt)
print("t10_sim(A0*) =", t10_sim_opt)
```

`calibrate_A0` は `scipy.optimize.minimize_scalar` を使って  
\((t_{10}^{\mathrm{sim}}(A_0) - t_{10}^{\mathrm{exp}})^2\) を最小化する `A0` を探索します。

## パラメータ設定のポイント

- **Ce(T) 関連**: `C_solvus`, `Qs` はソルバス近似式の係数。状態図・文献から取得してください。
- **拡散係数 D(T)**: `D0`, `Qd` は Al 中 Cu の拡散データから。
- **界面エネルギー/モル体積**: `gamma`, `Vm` は文献値または推定値を使用。
- **濃度の単位**: `C0`, `C_solvus`, `Cp` は同じ単位系（推奨: 原子分率）に揃える。
- **グリッド**: `r_min`, `r_max`, `n_classes` は TEM などの粒径スケールと数値安定性の両方を見ながら調整。

数値安定性やパラメータの妥当性を確認しつつ、`plan.md` のフロー（2〜5章）に沿って  
実験データとの比較・パラメータ同定・条件振りの予測へと発展させてください。

