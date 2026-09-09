import os
import subprocess

# Ensure an organized output directory structure exists
if not os.path.exists("output"):
    os.makedirs("output", exist_ok=True)

# ---------------------------------------------------------
# LAYER 1: SIMULATE CORE ODE DYNAMICS & EXPORT SWEEP DATA
# ---------------------------------------------------------
script_1_core = r"""import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt
import argparse
import os

def awareness_odes(t, y, lambda_A0):
    O, M, P = y
    dO_dt = lambda_A0 * (1.0 - O) * (1.0 + 0.1 * P) - 0.1 * O * M
    dM_dt = 0.05 * O - 0.02 * M
    dP_dt = 0.01 * M - 0.01 * P
    return [dO_dt, dM_dt, dP_dt]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sweep", action="store_true")
    args = parser.parse_args()

    t_span = (0, 100)
    t_eval = np.linspace(0, 100, 1001)
    initial_state = [25.0, 25.0, 25.0]
    
    lambdas = [0.1, 0.3, 0.5, 0.7] if args.sweep else [0.5]
    all_results = []
    
    for l_A0 in lambdas:
        sol = solve_ivp(awareness_odes, t_span, initial_state, args=(l_A0,), t_eval=t_eval, method='RK45')
        O, M, P = sol.y[0], sol.y[1], sol.y[2]
        R = O * M * P
        for i in range(len(sol.t)):
            all_results.append({
                'lambda_A0': l_A0, 'time': sol.t[i], 
                'O': O[i], 'M': M[i], 'P': P[i], 'R': R[i]
            })
            
    sweep_df = pd.DataFrame(all_results)
    sweep_csv_path = os.path.join("output", "core_timeseries_sweep.csv")
    sweep_df.to_csv(sweep_csv_path, index=False)
    print(f"[L1 Export] Saved core parameter sweep matrix to: {sweep_csv_path}")

    # Generate Figure H.1 Baseline Visual from the freshly exported dataset
    baseline_df = sweep_df[sweep_df['lambda_A0'] == 0.5].copy()
    
    plt.figure(figsize=(8.5, 5))
    plt.plot(baseline_df['time'], baseline_df['O'], color='#555555', linewidth=1.5, label='Observation (O)')
    plt.plot(baseline_df['time'], baseline_df['M'], color='#f2b035', linewidth=1.5, label='Memory (M)')
    plt.plot(baseline_df['time'], baseline_df['P'], color='#222222', linewidth=1.5, label='Pattern (P)')
    plt.plot(baseline_df['time'], baseline_df['R'], color='#444444', linestyle='--', linewidth=1.2, label='Awareness (R = OMP)')
    
    plt.title(r'L1: Core Dynamics Time-Series Transition ($\lambda_{A0} = 0.5$)', fontsize=10, fontweight='bold')
    plt.xlabel('Time (t)')
    plt.ylabel('Component Magnitude')
    plt.grid(True, linestyle=':', alpha=0.5)
    plt.legend(loc='upper right', frameon=False)
    plt.tight_layout()
    plt.savefig(os.path.join("output", "figure_h1_timeseries.png"), dpi=300)

if __name__ == '__main__':
    main()
"""

# ---------------------------------------------------------
# LAYER 2: THERMODYNAMIC BALANCE DEPENDS EXCLUSIVELY ON L1 CSV
# ---------------------------------------------------------
script_2_energy = r"""import pandas as pd
import numpy as np
import os

def calculate_entropy(row):
    states = np.array([max(1e-9, row['O']), max(1e-9, row['M']), max(1e-9, row['P'])])
    probs = states / np.sum(states)
    return -np.sum(probs * np.log(probs))

def main():
    input_path = os.path.join("output", "core_timeseries_sweep.csv")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Dependency violation: {input_path} is missing!")
        
    # Read L1 CSV output directly
    df = pd.read_csv(input_path)
    
    # Process mathematical thermodynamics
    df['Energy'] = df['O']**2 + df['M']**2 + df['P']**2
    df['Entropy'] = df.apply(calculate_entropy, axis=1)
    
    output_path = os.path.join("output", "energy_metrics.csv")
    df.to_csv(output_path, index=False)
    print(f"[L2 Export] Processed thermodynamics and exported to: {output_path}")

if __name__ == '__main__':
    main()
"""

# ---------------------------------------------------------
# LAYER 3: SPATIAL TURING SIMULATION DEPENDS EXCLUSIVELY ON L2 CSV
# ---------------------------------------------------------
script_3_spatial = r"""import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

def compute_laplacian(grid):
    return (
        np.roll(grid, 1, axis=0) + np.roll(grid, -1, axis=0) +
        np.roll(grid, 1, axis=1) + np.roll(grid, -1, axis=1) - 4 * grid
    )

def main():
    input_path = os.path.join("output", "energy_metrics.csv")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Dependency violation: {input_path} is missing!")
        
    # Read metrics directly from L2 output
    df = pd.read_csv(input_path)
    df_baseline = df[df['lambda_A0'] == 0.5].sort_values('time').reset_index()

    timesteps = len(df_baseline)
    np.random.seed(101)  
    grid_size = 50  
    
    Du, Dv, f, k = 0.16, 0.08, 0.035, 0.060
    U = np.ones((grid_size, grid_size))
    V = np.zeros((grid_size, grid_size))
    
    r = 10
    U[25-r:25+r, 25-r:25+r] = 0.50 + np.random.normal(0, 0.02, (2*r, 2*r))
    V[25-r:25+r, 25-r:25+r] = 0.25 + np.random.normal(0, 0.02, (2*r, 2*r))
    
    for t in range(timesteps):
        current_R = df_baseline.loc[t, 'R']
        scaled_f = f * (1.0 + 0.05 * np.log1p(current_R))
        
        Lu = compute_laplacian(U)
        Lv = compute_laplacian(V)
        
        uv2 = U * (V ** 2)
        U += Du * Lu - uv2 + scaled_f * (1.0 - U)
        V += Dv * Lv + uv2 - (scaled_f + k) * V
        
        U = np.clip(U, 0, 1)
        V = np.clip(V, 0, 1)
        
    spatial_field = U * 15.0 + V * 45.0
    np.save(os.path.join("output", "spatial_state.npy"), spatial_field)

    # Flatten matrix coordinate mapping array out to CSV
    x_indices, y_indices = np.indices(spatial_field.shape)
    spatial_df = pd.DataFrame({
        'Spatial_X': x_indices.flatten(),
        'Spatial_Y': y_indices.flatten(),
        'Awareness_Magnitude_R': spatial_field.flatten()
    })
    h2_csv_path = os.path.join("output", "figure_h2_spatial_data.csv")
    spatial_df.to_csv(h2_csv_path, index=False)
    print(f"[L3 Export] Saved dynamic emergent spatial data grid to: {h2_csv_path}")

    # Generate Figure H.2 Plot Visual
    plt.figure(figsize=(7.5, 6))
    im = plt.imshow(spatial_field, cmap='magma', origin='lower', aspect='auto')
    cbar = plt.colorbar(im)
    cbar.set_label('Awareness Field Texture (R)', rotation=270, labelpad=15)
    plt.title('L3: Nonlinear Turing Spatial Pattern Emergence', fontsize=10, fontweight='bold')
    plt.xlabel('Spatial X-coordinate')
    plt.ylabel('Spatial Y-coordinate')
    plt.tight_layout()
    plt.savefig(os.path.join("output", "figure_h2_spatial.png"), dpi=300)

if __name__ == '__main__':
    main()
"""

# ---------------------------------------------------------
# LAYER 4: TEMPORAL SPECTRAL COHERENCE HARNESS
# ---------------------------------------------------------
script_4_temporal = r"""import numpy as np
import pandas as pd
import os

def main():
    input_path = os.path.join("output", "energy_metrics.csv")
    metrics_df = pd.read_csv(input_path)
    baseline_series = metrics_df[metrics_df['lambda_A0'] == 0.5].sort_values('time')
    
    r_signals = baseline_series['R'].values
    n, dt = len(r_signals), 0.1
    fft_vals = np.fft.fft(r_signals - np.mean(r_signals))
    frequencies = np.fft.fftfreq(n, d=dt)
    positive_idx = np.where(frequencies > 0)[0]
    
    peak_freq = frequencies[positive_idx[np.argmax(np.abs(fft_vals[positive_idx]))]] if len(positive_idx) > 0 else 0.0
    print(f"[L4 Analysis] Dominant Rhythm Spectrum Peak discovered at: {peak_freq:.4f} Hz")

if __name__ == '__main__':
    main()
"""

# ---------------------------------------------------------
# LAYER 5: INTEGRATED SYSTEM RESCALING ENGINE
# ---------------------------------------------------------
script_5_integrated = r"""import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

def main():
    input_path = os.path.join("output", "energy_metrics.csv")
    df = pd.read_csv(input_path)
    summary_data = []
    lambdas = sorted(df['lambda_A0'].unique())
    
    for l_A0 in lambdas:
        sub_df = df[df['lambda_A0'] == l_A0].sort_values('time')
        mean_R = sub_df['R'].mean()
        final_R = sub_df['R'].iloc[-1]
        mean_E = sub_df['Energy'].mean()
        mean_S = sub_df['Entropy'].mean()
        
        eta = (mean_R / (final_R + 1e-6)) * 10 
        summary_data.append({
            'lambda_A0': l_A0, 'Efficiency': eta,
            'Mean_Energy': mean_E, 'Mean_Entropy': mean_S,
            'Final_Awareness': final_R
        })
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_csv(os.path.join("output", "integrated_summary_metrics.csv"), index=False)
    print(f"[L5 Export] Final system efficiency performance summaries saved.")

    # Generate Figure H.3 Plot Visual
    fig, axes = plt.subplots(3, 1, figsize=(7, 9), sharex=True)
    
    axes[0].plot(summary_df['lambda_A0'], summary_df['Efficiency'], '-o', color='#2b5c8f', linewidth=2, label=r'Efficiency ($\eta$)')
    axes[0].set_ylabel(r'Efficiency ($\eta$)')
    axes[0].set_ylim(0, 45)
    axes[0].grid(True, linestyle=':', alpha=0.6)
    axes[0].legend(loc='upper right')
    axes[0].set_title('L5: Integrated Metrics Triptych vs $\lambda_{A0}$', fontsize=10, fontweight='bold')

    axes[1].plot(summary_df['lambda_A0'], summary_df['Mean_Energy'], '-s', color='#c22d47', linewidth=2, label=r'Energy ($\bar{E}$)')
    axes[1].set_ylabel('Energy Magnitude', color='#c22d47')
    axes[1].tick_params(axis='y', labelcolor='#c22d47')
    axes[1].grid(True, linestyle=':', alpha=0.6)
    
    ax2_twin = axes[1].twinx()
    ax2_twin.plot(summary_df['lambda_A0'], summary_df['Mean_Entropy'], '-^', color='#e68a00', linewidth=2, label=r'Entropy ($\bar{S}$)')
    ax2_twin.set_ylabel('Entropy Magnitude', color='#e68a00')
    ax2_twin.tick_params(axis='y', labelcolor='#e68a00')
    
    lines, labels = axes[1].get_legend_handles_labels()
    lines2, labels2 = ax2_twin.get_legend_handles_labels()
    ax2_twin.legend(lines + lines2, labels + labels2, loc='upper right')

    axes[2].plot(summary_df['lambda_A0'], summary_df['Final_Awareness'], '-g^', color='#1e7d34', linewidth=2, label=r'Final Awareness ($R_{final}$)')
    axes[2].set_ylabel(r'Final Awareness ($R_{final}$)')
    axes[2].set_xlabel(r'Global Prior Awareness Bias ($\lambda_{A0}$)')
    axes[2].set_ylim(0, 850)
    axes[2].set_xticks([0.1, 0.3, 0.5, 0.7])
    axes[2].grid(True, linestyle=':', alpha=0.6)
    axes[2].legend(loc='upper left')

    plt.tight_layout()
    plt.savefig(os.path.join("output", "integrated_metrics_triptych.png"), dpi=300)

if __name__ == '__main__':
    main()
"""

# Write script configuration files to disk
with open("sim_core_dynamics.py", "w") as f: f.write(script_1_core)
with open("sim_energy_balance.py", "w") as f: f.write(script_2_energy)
with open("sim_spatial_field.py", "w") as f: f.write(script_3_spatial)
with open("sim_temporal_hierarchy.py", "w") as f: f.write(script_4_temporal)
with open("sim_integrated_system.py", "w") as f: f.write(script_5_integrated)

print("All standalone script assets compiled successfully.")
print("Executing chained data pipeline modules natively via system loops...\n")

# Execute scripts in strict sequence to respect data input/output links
subprocess.run(["python", "sim_core_dynamics.py", "--sweep"], capture_output=True)
subprocess.run(["python", "sim_energy_balance.py"], capture_output=True)
subprocess.run(["python", "sim_spatial_field.py"], capture_output=True)
subprocess.run(["python", "sim_temporal_hierarchy.py"], capture_output=True)
subprocess.run(["python", "sim_integrated_system.py"], capture_output=True)

# ---------------------------------------------------------
# EXPORT DATA & PLOT INTEGRITY VERIFICATION CHECKLIST
# ---------------------------------------------------------
from IPython.display import Image, display

print("\n" + "="*60)
print("VERIFYING EXPORTED CSV DATA TABLES AND IMAGES")
print("="*60)

artifacts = [
    "output/core_timeseries_sweep.csv",
    "output/energy_metrics.csv",
    "output/figure_h2_spatial_data.csv",
    "output/integrated_summary_metrics.csv",
    "output/figure_h1_timeseries.png",
    "output/figure_h2_spatial.png",
    "output/integrated_metrics_triptych.png"
]

for artifact in artifacts:
    status = "VERIFIED EXISTS" if os.path.exists(artifact) else "MISSING"
    print(f"[{status}] -> {artifact}")

print("\n" + "="*60)
print("RENDERING ALL VERIFIED ARTIFACT IMAGES INLINE")
print("="*60)

if os.path.exists('output/figure_h1_timeseries.png'):
    print("\n[Figure H.1: Core Dynamics Time-Series Transition]")
    display(Image('output/figure_h1_timeseries.png'))

if os.path.exists('output/figure_h2_spatial.png'):
    print("\n[Figure H.2: Spatial Self-Organization & Field Emergence]")
    display(Image('output/figure_h2_spatial.png'))

if os.path.exists('output/integrated_metrics_triptych.png'):
    print("\n[Figure H.3: Integrated Metrics and Energy Triptych Summary]")
    display(Image('output/integrated_metrics_triptych.png'))