"""
Performance Benchmarks for HYDRUS1D Phase 3
============================================

Measures solver performance for various problem sizes and conditions.
"""

import numpy as np
import sys
from pathlib import Path
import time

# Add packages to path
phase3_path = str(Path(__file__).parent.parent)
phase2_path = str(Path(__file__).parent.parent.parent / 'phase2')
sys.path.insert(0, phase2_path)
sys.path.insert(0, phase3_path)

from hydrus1dpy import HydrusModel
from hydrus1dpy.materials import VanGenuchten


class Benchmark:
    """Base class for benchmarks."""
    def __init__(self, name):
        self.name = name
        self.time_elapsed = None
        self.stats = None

    def run(self):
        """Run benchmark and measure time."""
        raise NotImplementedError

    def report(self):
        """Print benchmark results."""
        print(f"\n{self.name}")
        print("-" * 70)
        if self.time_elapsed is not None:
            print(f"Total time: {self.time_elapsed:.3f} seconds")
        if self.stats is not None:
            for key, value in self.stats.items():
                print(f"  {key}: {value}")


class ScalingBenchmark(Benchmark):
    """Benchmark solver scaling with domain size."""

    def __init__(self):
        super().__init__("Scaling Benchmark: Domain Size")
        self.results = []

    def run(self):
        """Test different domain sizes."""
        print(f"\nRunning: {self.name}")
        print("="*70)

        vg = VanGenuchten(0.078, 0.430, 0.036, 1.56, 24.96, 0.5)

        sizes = [11, 21, 51, 101, 201]

        print(f"{'Nodes':>6s} {'Time (s)':>10s} {'Steps':>8s} {'Avg Iter':>10s}")
        print("-" * 70)

        for n_nodes in sizes:
            model = HydrusModel(depth=100.0, n_nodes=n_nodes, material=vg)
            model.set_top_bc('flux', flux=0.5)
            model.set_bottom_bc('free_drainage')
            model.set_initial_conditions('uniform', h=-200.0)

            t_start = time.time()
            results = model.run(t_end=1.0, dt_init=0.01, dt_max=0.1, verbose=False)
            t_elapsed = time.time() - t_start

            stats = results['statistics']
            print(f"{n_nodes:6d} {t_elapsed:10.3f} {stats['total_steps']:8d} "
                  f"{stats['avg_iterations']:10.2f}")

            self.results.append({
                'n_nodes': n_nodes,
                'time': t_elapsed,
                'steps': stats['total_steps'],
                'avg_iter': stats['avg_iterations']
            })

        self.time_elapsed = sum(r['time'] for r in self.results)


class AccuracyBenchmark(Benchmark):
    """Benchmark accuracy vs computational cost."""

    def __init__(self):
        super().__init__("Accuracy Benchmark: Grid Refinement")
        self.results = []

    def run(self):
        """Test grid refinement."""
        print(f"\nRunning: {self.name}")
        print("="*70)

        vg = VanGenuchten(0.078, 0.430, 0.036, 1.56, 24.96, 0.5)

        # Reference solution with fine grid
        print("Computing reference solution (501 nodes)...")
        model_ref = HydrusModel(depth=100.0, n_nodes=501, material=vg)
        model_ref.set_top_bc('constant_head', head=0.0)
        model_ref.set_bottom_bc('free_drainage')
        model_ref.set_initial_conditions('uniform', h=-200.0)

        results_ref = model_ref.run(t_end=1.0, dt_init=0.001, dt_max=0.01, verbose=False)
        theta_ref = results_ref['theta'][-1]

        print(f"\n{'Nodes':>6s} {'Time (s)':>10s} {'Error (L2)':>12s} {'Error (max)':>12s}")
        print("-" * 70)

        node_counts = [21, 51, 101, 201]

        for n_nodes in node_counts:
            model = HydrusModel(depth=100.0, n_nodes=n_nodes, material=vg)
            model.set_top_bc('constant_head', head=0.0)
            model.set_bottom_bc('free_drainage')
            model.set_initial_conditions('uniform', h=-200.0)

            t_start = time.time()
            results = model.run(t_end=1.0, dt_init=0.001, dt_max=0.01, verbose=False)
            t_elapsed = time.time() - t_start

            theta_coarse = results['theta'][-1]

            # Interpolate to reference grid for comparison
            from scipy.interpolate import interp1d
            z_coarse = np.linspace(0, -100, n_nodes)
            z_ref = np.linspace(0, -100, 501)

            interp = interp1d(z_coarse, theta_coarse, kind='linear')
            theta_interp = interp(z_ref)

            l2_error = np.sqrt(np.mean((theta_interp - theta_ref)**2))
            max_error = np.max(np.abs(theta_interp - theta_ref))

            print(f"{n_nodes:6d} {t_elapsed:10.3f} {l2_error:12.6f} {max_error:12.6f}")

            self.results.append({
                'n_nodes': n_nodes,
                'time': t_elapsed,
                'l2_error': l2_error,
                'max_error': max_error
            })


class StressTestBenchmark(Benchmark):
    """Stress test with challenging conditions."""

    def __init__(self):
        super().__init__("Stress Test: Challenging Conditions")

    def run(self):
        """Test solver robustness."""
        print(f"\nRunning: {self.name}")
        print("="*70)

        vg = VanGenuchten(0.078, 0.430, 0.036, 1.56, 24.96, 0.5)

        tests = [
            ("Dry infiltration", {'h_init': -1000, 'q': 1.0}),
            ("Strong infiltration", {'h_init': -200, 'q': 10.0}),
            ("Drainage from saturation", {'h_init': -5, 'q': 0.0}),
        ]

        print(f"{'Test':>30s} {'Success':>10s} {'Time (s)':>10s} {'Steps':>8s}")
        print("-" * 70)

        for test_name, params in tests:
            try:
                model = HydrusModel(depth=50.0, n_nodes=51, material=vg)
                model.set_top_bc('flux', flux=params['q'])
                model.set_bottom_bc('free_drainage')
                model.set_initial_conditions('uniform', h=params['h_init'])

                t_start = time.time()
                results = model.run(t_end=0.5, dt_init=0.0001, dt_max=0.01, verbose=False)
                t_elapsed = time.time() - t_start

                stats = results['statistics']
                success = "✓ PASS"
                time_str = f"{t_elapsed:.3f}"
                steps_str = f"{stats['total_steps']}"

            except Exception as e:
                success = "✗ FAIL"
                time_str = "-"
                steps_str = "-"

            print(f"{test_name:>30s} {success:>10s} {time_str:>10s} {steps_str:>8s}")


def run_benchmarks():
    """Run all performance benchmarks."""
    print("\n" + "="*70)
    print("RICHARDS SOLVER: PERFORMANCE BENCHMARKS")
    print("="*70)

    benchmarks = [
        ScalingBenchmark(),
        StressTestBenchmark(),
    ]

    # Only run accuracy benchmark if scipy available
    try:
        from scipy.interpolate import interp1d
        benchmarks.insert(1, AccuracyBenchmark())
    except ImportError:
        print("\nNote: Skipping AccuracyBenchmark (requires scipy)")

    total_time = 0
    for benchmark in benchmarks:
        benchmark.run()
        if benchmark.time_elapsed is not None:
            total_time += benchmark.time_elapsed

    # Summary
    print("\n" + "="*70)
    print("BENCHMARK SUMMARY")
    print("="*70)
    print(f"Total time: {total_time:.2f} seconds")

    # Performance insights
    if isinstance(benchmarks[0], ScalingBenchmark):
        scaling = benchmarks[0].results
        if len(scaling) >= 2:
            # Estimate complexity
            n1, t1 = scaling[0]['n_nodes'], scaling[0]['time']
            n2, t2 = scaling[-1]['n_nodes'], scaling[-1]['time']

            # Assuming O(n^p) scaling
            if t1 > 0 and t2 > 0:
                p = np.log(t2/t1) / np.log(n2/n1)
                print(f"\nScaling: O(n^{p:.2f}) where n = number of nodes")
                print(f"  100 nodes: ~{scaling[-2]['time']:.2f}s for 1 day simulation")

    print("\n✓ Benchmarks complete!")


if __name__ == '__main__':
    run_benchmarks()
