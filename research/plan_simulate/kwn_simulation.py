"""
Al–Cu 合金の時効析出（KWN/コントロールボリューム法）による
10%到達時刻 t10_sim を計算するためのシミュレーションコード。

plan.md の要件に対応：
- Ce(T), D(T) の Arrhenius 近似
- 核生成率 j(t)
- 界面濃度（ギブス・トムソン）
- 拡散律速成長速度 v_i
- 粒径分布のコントロールボリューム更新
- 体積分率と質量保存から平均濃度 bar_C(t) を計算
- bar_C <= C_stop となる最初の時刻を t10_sim として返す

依存ライブラリ:
- numpy
- scipy (A0 同定に使う場合)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Tuple, Optional, Dict

import numpy as np

try:
    from scipy.optimize import minimize_scalar
    _HAS_SCIPY = True
except ImportError:  # scipy が無くてもシミュレーション本体は動く
    _HAS_SCIPY = False


R_GAS = 8.3145  # J/(mol K)


@dataclass
class ThermoParams:
    """熱力学・拡散・核生成に関するパラメータ."""

    # 平衡固溶度 Ce(T) = C_solvus * exp(-Qs / (R T))
    C_solvus: float  # 無次元濃度（原子分率など）
    Qs: float  # J/mol

    # 拡散係数 D(T) = D0 * exp(-Qd / (R T))
    D0: float  # m^2/s
    Qd: float  # J/mol

    # その他
    gamma: float  # 界面エネルギー [J/m^2]
    Vm: float  # モル体積 [m^3/mol]
    Cp: float  # 析出相中の Cu 濃度（原子分率）

    # 核生成率パラメータ j(t)
    j0: float  # 前指数 [1/(m^3 s)]
    A0: float  # 無次元パラメータ（同定対象）

    # 温度
    T: float  # K

    # 初期濃度
    C0: float  # 初期平均濃度


@dataclass
class GridParams:
    """粒子サイズグリッドと時間に関するパラメータ."""

    r_min: float  # 最小半径 [m]
    r_max: float  # 最大半径 [m]
    n_classes: int  # クラス数
    dt_initial: float  # 初期時間刻み [s]
    t_max: float  # 安全のための最大計算時間 [s]
    cfl_factor: float = 0.5  # Δt <= cfl_factor * min(Δr_i / |v_i|)


@dataclass
class SimulationResult:
    t: np.ndarray  # 時間配列
    C_bar: np.ndarray  # 平均固溶濃度
    f: np.ndarray  # 析出物体積分率
    r_grid: np.ndarray  # 半径クラス代表値
    N: np.ndarray  # 粒子数密度分布 (time, n_classes)
    t10_sim: Optional[float]  # 10%到達時刻（見つからない場合 None）


def Ce(T: float, params: ThermoParams) -> float:
    """平衡固溶度 Ce(T)."""
    return params.C_solvus * np.exp(-params.Qs / (R_GAS * T))


def D(T: float, params: ThermoParams) -> float:
    """拡散係数 D(T)."""
    return params.D0 * np.exp(-params.Qd / (R_GAS * T))


def critical_radius(C_bar: float, Ce_T: float, params: ThermoParams) -> float:
    """臨界半径 r*."""
    if C_bar <= Ce_T:
        # 過飽和でなければ臨界半径は無限大とみなす
        return np.inf
    return 2.0 * params.gamma * params.Vm / (R_GAS * params.T * np.log(C_bar / Ce_T))


def nucleation_rate(C_bar: float, Ce_T: float, params: ThermoParams) -> float:
    """核生成率 j(t)."""
    if C_bar <= Ce_T:
        return 0.0
    ln_term = np.log(C_bar / Ce_T)
    expo = -params.A0 / (params.T ** 3 * ln_term ** 2) - params.Qd / (R_GAS * params.T)
    return params.j0 * np.exp(expo)


def interface_concentration(r: np.ndarray, Ce_T: float, params: ThermoParams) -> np.ndarray:
    """界面濃度 C_i (Gibbs–Thomson)."""
    # r が 0 に非常に近いと数値不安定になるので下限を設ける
    r_safe = np.maximum(r, 1e-12)
    return Ce_T * np.exp(2.0 * params.gamma * params.Vm / (R_GAS * params.T * r_safe))


def growth_velocity(
    r: np.ndarray, C_bar: float, Ce_T: float, params: ThermoParams
) -> np.ndarray:
    """拡散律速成長速度 v_i = dr/dt."""
    D_T = D(params.T, params)
    Ci = interface_concentration(r, Ce_T, params)
    # 分母がゼロに近い場合を避ける
    denom = np.clip(params.Cp - Ci, 1e-12, None)
    v = (C_bar - Ci) / denom * D_T / np.maximum(r, 1e-12)
    return v


def mass_balance_C_bar(f: float, params: ThermoParams) -> float:
    """質量保存から平均固溶濃度 bar_C を計算."""
    if f >= 1.0:
        # 極端な場合の保険（f→1なら固溶Cu→Ce 近傍になるはずだが）
        f = 1.0 - 1e-9
    return (params.C0 - f * params.Cp) / (1.0 - f)


class KWNModel:
    """KWN/コントロールボリューム法による時効析出シミュレーション."""

    def __init__(self, thermo: ThermoParams, grid: GridParams):
        self.thermo = thermo
        self.grid = grid

        # 半径グリッド：対数均等 or 線形。ここでは対数刻みを基本とする
        self.r_edges = np.logspace(
            np.log10(grid.r_min), np.log10(grid.r_max), grid.n_classes + 1
        )
        # 代表値（セル中心）
        self.r_centers = np.sqrt(self.r_edges[:-1] * self.r_edges[1:])
        self.dr = np.diff(self.r_edges)

    def run(
        self,
        C_stop: float,
        t_max: Optional[float] = None,
        record_history: bool = True,
    ) -> SimulationResult:
        """シミュレーションを実行し、t10_sim を含む結果を返す."""
        thermo = self.thermo
        grid = self.grid

        if t_max is None:
            t_max = grid.t_max

        Ce_T = Ce(thermo.T, thermo)

        # 初期条件
        t = 0.0
        C_bar = thermo.C0
        N = np.zeros_like(self.r_centers)  # 粒子数密度

        # 記録
        times = [t]
        C_bars = [C_bar]
        fs = [0.0]
        Ns = [N.copy()]

        dt = grid.dt_initial
        t10_sim: Optional[float] = None

        while t < t_max and C_bar > C_stop:
            # (A) 臨界半径（ここでは値を記録しないが、解析には利用可能）
            _r_crit = critical_radius(C_bar, Ce_T, thermo)

            # (B) 核生成率
            j_val = nucleation_rate(C_bar, Ce_T, thermo)
            dN_nuc = j_val * dt  # 最小クラスに追加

            # (D) 成長速度
            v = growth_velocity(self.r_centers, C_bar, Ce_T, thermo)

            # (E) 対流項のコントロールボリューム更新（一次精度上流差分）
            # クラス境界におけるフラックス F_{i+1/2} = v_{face} * N_upwind
            # ここでは簡略化して、セル中心速度 v_i を使う
            F = np.zeros_like(self.r_edges)

            # 内部境界
            for i in range(1, len(self.r_edges) - 1):
                # 左セル i-1, 右セル i
                # 境界速度を右側セルの速度で近似
                v_face = v[i - 1]
                if v_face > 0.0:
                    N_up = N[i - 1]
                else:
                    N_up = N[i] if i < len(N) else 0.0
                F[i] = v_face * N_up

            # 左端・右端境界（外側への流出は消滅とみなす）
            F[0] = 0.0
            F[-1] = 0.0

            # N の更新
            dN = -(F[1:] - F[:-1]) / self.dr
            N_new = N + dt * dN

            # 非負性の確保
            N_new = np.maximum(N_new, 0.0)

            # 核生成による最小クラスへの追加
            N_new[0] += dN_nuc

            # (F) 体積分率と質量保存
            f = (4.0 / 3.0) * np.pi * np.sum(self.r_centers**3 * N_new)
            C_bar_new = mass_balance_C_bar(f, thermo)

            # (G) 時間更新
            t_new = t + dt

            # 次の時間刻みの安定性チェック
            # Δt <= cfl_factor * min(Δr / |v|)
            v_abs = np.abs(v)
            safe_mask = v_abs > 0.0
            if np.any(safe_mask):
                dt_cfl = np.min(self.dr[safe_mask] / v_abs[safe_mask])
                dt_next = grid.cfl_factor * dt_cfl
                # あまり小さくしすぎないように下限も設ける
                dt = float(np.clip(dt_next, 1e-6, grid.dt_initial))
            else:
                # 成長速度がほぼゼロなら、時間刻みは増やしてもよい
                dt = min(dt * 2.0, grid.dt_initial)

            # 記録
            if record_history:
                times.append(t_new)
                C_bars.append(C_bar_new)
                fs.append(f)
                Ns.append(N_new.copy())

            # 10%到達時刻の判定（初めて C_bar <= C_stop になったら線形補間）
            if (C_bar > C_stop) and (C_bar_new <= C_stop):
                alpha = (C_bar - C_stop) / max(C_bar - C_bar_new, 1e-12)
                t10_sim = t + alpha * (t_new - t)

            # 状態更新
            t, C_bar, N = t_new, C_bar_new, N_new

            # 万一 f が 1 に近づきすぎたら停止
            if f >= 0.99:
                break

        if not record_history:
            times = [t]
            C_bars = [C_bar]
            fs = [f]
            Ns = [N.copy()]

        return SimulationResult(
            t=np.asarray(times),
            C_bar=np.asarray(C_bars),
            f=np.asarray(fs),
            r_grid=self.r_centers.copy(),
            N=np.asarray(Ns),
            t10_sim=t10_sim,
        )


def compute_C_stop(C0: float, Ce_T: float) -> float:
    """C_stop = 0.90*C0 + 0.10*Ce."""
    return 0.90 * C0 + 0.10 * Ce_T


def run_single_simulation(
    thermo_params: Dict,
    grid_params: Dict,
) -> SimulationResult:
    """辞書で与えたパラメータから t10_sim までシミュレーションを1回実行."""
    thermo = ThermoParams(**thermo_params)
    grid = GridParams(**grid_params)

    Ce_T = Ce(thermo.T, thermo)
    C_stop = compute_C_stop(thermo.C0, Ce_T)

    model = KWNModel(thermo, grid)
    result = model.run(C_stop=C_stop)
    return result


def calibrate_A0(
    t10_exp: float,
    thermo_base: Dict,
    grid_params: Dict,
    A0_bounds: Tuple[float, float],
) -> Tuple[float, float]:
    """
    実験値 t10_exp に対して A0 を 1 次元探索で同定する。

    戻り値:
        (A0_opt, t10_sim_opt)
    """
    if not _HAS_SCIPY:
        raise RuntimeError("scipy がインポートできないため A0 の同定機能は使えません。")

    def objective(A0_val: float) -> float:
        thermo_dict = dict(thermo_base)
        thermo_dict["A0"] = float(A0_val)
        res = run_single_simulation(thermo_dict, grid_params)
        if res.t10_sim is None:
            # 10%到達しなかった場合は大きなペナルティ
            return 1e24
        return (res.t10_sim - t10_exp) ** 2

    opt_res = minimize_scalar(objective, bounds=A0_bounds, method="bounded")
    A0_opt = float(opt_res.x)

    thermo_opt = dict(thermo_base)
    thermo_opt["A0"] = A0_opt
    res_opt = run_single_simulation(thermo_opt, grid_params)
    t10_sim_opt = res_opt.t10_sim if res_opt.t10_sim is not None else np.nan

    return A0_opt, t10_sim_opt


def example_parameters() -> Tuple[Dict, Dict]:
    """
    テスト・雛形用のパラメータセットを返す。
    数値はダミーも含まれるので、実際の解析では文献値に置き換えてください。
    """
    # 例: 160°C
    T = 160.0 + 273.15

    # ここでは「必ず 10% 到達が起こる」ことを優先した、やや極端な例を入れている。
    # 実際に研究で使うときは文献値で上書きしてください。
    thermo_params = dict(
        C_solvus=0.01,  # 例: Ce(T) ≈ 0.01 * exp(-Qs/RT)
        Qs=80e3,  # J/mol（やや小さめにして過飽和を強める）
        D0=1e-3,  # m^2/s（拡散を速く）
        Qd=120e3,  # J/mol
        gamma=0.1,  # J/m^2
        Vm=1.0e-5,  # m^3/mol
        Cp=0.25,  # Al2Cu の Cu 原子分率の例
        j0=1e25,  # 例: 核生成を起こりやすく
        A0=1.0e38,  # 例: バリアをやや下げておく
        T=T,
        C0=0.03,  # 初期 Cu 濃度（原子分率、Ce より十分大きい）
    )

    grid_params = dict(
        r_min=5e-10,   # 0.5 nm
        r_max=5e-7,    # 0.5 µm
        n_classes=60,
        dt_initial=0.5,  # s
        t_max=5.0e5,     # s（十分長くして 10% 到達を狙う）
        cfl_factor=0.5,
    )

    return thermo_params, grid_params


def main():
    """
    コマンドラインから直接実行したときの簡単なデモ。

    実務では、ノートブックや別スクリプトから
    - example_parameters() を呼んで値をコピーして調整
    - run_single_simulation() で t10_sim を計算
    - calibrate_A0() で A0 を同定
    という流れを推奨。
    """
    thermo_params, grid_params = example_parameters()
    res = run_single_simulation(thermo_params, grid_params)
    print(f"t10_sim = {res.t10_sim} s")


if __name__ == "__main__":
    main()

