"""
Visualization Generator for Performance Analysis
Generates publication-ready figures for research paper
"""

import json
import logging
import argparse
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from pathlib import Path

from config import (
    RESULTS_DIR,
    FIGURE_DPI,
    FIGURE_SIZE_LATENCY,
    FIGURE_SIZE_VELOCITY,
    LOG_LEVEL,
    LOG_FORMAT
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT
)
logger = logging.getLogger(__name__)

# Set style for publication-quality figures
sns.set_style('whitegrid')
sns.set_context('paper', font_scale=1.4)
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.facecolor'] = 'white'


class VisualizationGenerator:
    """Generate performance analysis visualizations"""
    
    def __init__(self, results_dir=RESULTS_DIR):
        """Initialize with results directory"""
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True, parents=True)
    
    def load_latency_data(self, filepath):
        """Load latency data from JSON file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            logger.info(f"✅ Loaded latency data from {filepath}")
            return data
        except Exception as e:
            logger.error(f"❌ Failed to load latency data: {e}")
            return None
    
    def load_velocity_data(self, filepath):
        """Load velocity data from JSON file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            logger.info(f"✅ Loaded velocity data from {filepath}")
            return data
        except Exception as e:
            logger.error(f"❌ Failed to load velocity data: {e}")
            return None
    
    def generate_latency_throughput_chart(self, latency_data, output_file='latency_throughput.png'):
        """
        Generate Dual-Axis Line Chart: Throughput vs. Latency
        
        Args:
            latency_data: Dictionary with latency statistics per throughput
            output_file: Output filename
        
        Returns:
            str: Path to saved figure
        """
        logger.info("📊 Generating Latency vs. Throughput chart...")
        
        # Extract data
        throughput_levels = []
        avg_latencies = []
        std_latencies = []
        min_latencies = []
        max_latencies = []
        
        for throughput_str, metrics in sorted(latency_data['latency_by_throughput'].items(), 
                                             key=lambda x: int(x[0])):
            throughput_levels.append(int(throughput_str))
            avg_latencies.append(metrics['avg_ms'])
            std_latencies.append(metrics.get('stdev_ms', 0))
            min_latencies.append(metrics['min_ms'])
            max_latencies.append(metrics['max_ms'])
        
        # Create figure
        fig, ax = plt.subplots(figsize=FIGURE_SIZE_LATENCY)
        
        # Main line plot with markers
        line = ax.plot(throughput_levels, avg_latencies, 
                      marker='o', markersize=10, linewidth=2.5,
                      color='#2E86AB', label='Average Latency')
        
        # Error bars (standard deviation)
        ax.errorbar(throughput_levels, avg_latencies, yerr=std_latencies,
                   fmt='none', ecolor='gray', elinewidth=1.5, capsize=5, alpha=0.6)
        
        # Shaded region (min-max range)
        ax.fill_between(throughput_levels, min_latencies, max_latencies,
                       alpha=0.2, color='#2E86AB', label='Min-Max Range')
        
        # Formatting
        ax.set_xlabel('Throughput (articles/minute)', fontsize=14, fontweight='bold')
        ax.set_ylabel('End-to-End Latency (ms)', fontsize=14, fontweight='bold')
        ax.set_title('Latency vs. Throughput Performance Analysis\n$L = T_{ES} - T_{Kafka}$', 
                    fontsize=16, fontweight='bold', pad=20)
        
        # Log scale for x-axis if large range
        if max(throughput_levels) / min(throughput_levels) > 10:
            ax.set_xscale('log')
            ax.set_xticks(throughput_levels)
            ax.set_xticklabels([str(t) for t in throughput_levels])
        
        # Grid
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.legend(loc='upper left', frameon=True, shadow=True, fontsize=11)
        
        # Add data labels
        for x, y in zip(throughput_levels, avg_latencies):
            ax.annotate(f'{y:.1f}ms', 
                       xy=(x, y), 
                       xytext=(0, 10),
                       textcoords='offset points',
                       ha='center',
                       fontsize=10,
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.3))
        
        plt.tight_layout()
        
        # Save figure
        output_path = self.results_dir / output_file
        plt.savefig(output_path, dpi=FIGURE_DPI, bbox_inches='tight', facecolor='white')
        logger.info(f"✅ Saved figure: {output_path}")
        plt.close()
        
        return str(output_path)
    
    def generate_peak_velocity_chart(self, velocity_data, cluster_key=None, output_file='peak_velocity_detection.png'):
        """
        Generate Temporal Area Chart: Peak Velocity Detection
        
        Args:
            velocity_data: Dictionary with velocity history per cluster
            cluster_key: Specific cluster to visualize (if None, use highest peak)
            output_file: Output filename
        
        Returns:
            str: Path to saved figure
        """
        logger.info("📊 Generating Peak Velocity Detection chart...")
        
        # Select cluster with highest peak velocity if not specified
        if cluster_key is None:
            cluster_key = max(velocity_data['clusters'].items(), 
                            key=lambda x: x[1]['peak_velocity_docs_per_min'])[0]
            logger.info(f"   Selected cluster: {cluster_key}")
        
        cluster_data = velocity_data['clusters'][cluster_key]
        velocity_history = cluster_data['velocity_history']
        
        if not velocity_history:
            logger.warning(f"⚠️ No velocity history for cluster {cluster_key}")
            return None
        
        # Extract timestamps and velocities
        timestamps = []
        velocities = []
        cumulative_docs = []
        cumulative = 0
        
        for point in velocity_history:
            timestamp = datetime.fromisoformat(point['timestamp'])
            timestamps.append(timestamp)
            velocities.append(point['velocity'])
            # Approximate cumulative (velocity * window / 60)
            cumulative += point['velocity'] * (velocity_data['window_seconds'] / 60)
            cumulative_docs.append(cumulative)
        
        # Convert to relative time (minutes from start)
        start_time = timestamps[0]
        relative_times = [(t - start_time).total_seconds() / 60 for t in timestamps]
        
        # Peak velocity info
        peak_velocity = cluster_data['peak_velocity_docs_per_min']
        peak_time_str = cluster_data.get('peak_time')
        first_time_str = cluster_data.get('first_article_time')
        detection_lag = cluster_data.get('detection_lag_seconds')
        
        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), 
                                       gridspec_kw={'height_ratios': [2, 1]})
        
        # ---- Subplot 1: Cumulative Documents ----
        ax1.fill_between(relative_times, cumulative_docs, alpha=0.3, color='#06A77D', label='Document Accumulation')
        ax1.plot(relative_times, cumulative_docs, linewidth=2.5, color='#06A77D')
        
        # Mark peak velocity point
        if peak_time_str:
            peak_time = datetime.fromisoformat(peak_time_str)
            peak_relative = (peak_time - start_time).total_seconds() / 60
            peak_idx = min(range(len(relative_times)), key=lambda i: abs(relative_times[i] - peak_relative))
            peak_docs = cumulative_docs[peak_idx]
            
            ax1.axvline(peak_relative, color='red', linestyle='--', linewidth=2, 
                       label=f'Peak Velocity: {peak_velocity:.1f} docs/min')
            ax1.plot(peak_relative, peak_docs, 'r*', markersize=20, 
                    label='Peak Velocity Point', zorder=5)
        
        # Mark detection lag region
        if first_time_str and peak_time_str and detection_lag:
            first_time = datetime.fromisoformat(first_time_str)
            first_relative = (first_time - start_time).total_seconds() / 60
            
            ax1.axvspan(first_relative, peak_relative, alpha=0.2, color='yellow',
                       label=f'Detection Lag: {detection_lag:.1f}s')
            ax1.axvline(first_relative, color='green', linestyle=':', linewidth=2,
                       label='First Article', alpha=0.7)
        
        ax1.set_xlabel('Time (minutes from start)', fontsize=13, fontweight='bold')
        ax1.set_ylabel('Cumulative Documents', fontsize=13, fontweight='bold')
        ax1.set_title(f'Peak Velocity Detection: {cluster_key}\n$V_p = \\max(\\Delta N / \\Delta t)$',
                     fontsize=15, fontweight='bold', pad=15)
        ax1.grid(True, alpha=0.3, linestyle='--')
        ax1.legend(loc='upper left', frameon=True, shadow=True, fontsize=10)
        
        # ---- Subplot 2: Instantaneous Velocity ----
        ax2.plot(relative_times, velocities, linewidth=2, color='#F97068', marker='o', markersize=4)
        ax2.fill_between(relative_times, velocities, alpha=0.2, color='#F97068')
        
        # Mark peak
        if peak_time_str:
            ax2.axhline(peak_velocity, color='red', linestyle='--', linewidth=1.5, alpha=0.7)
            ax2.axvline(peak_relative, color='red', linestyle='--', linewidth=1.5, alpha=0.7)
        
        ax2.set_xlabel('Time (minutes from start)', fontsize=13, fontweight='bold')
        ax2.set_ylabel('Velocity (docs/min)', fontsize=13, fontweight='bold')
        ax2.set_title('Instantaneous Ingestion Velocity', fontsize=14, fontweight='bold', pad=10)
        ax2.grid(True, alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        
        # Save figure
        output_path = self.results_dir / output_file
        plt.savefig(output_path, dpi=FIGURE_DPI, bbox_inches='tight', facecolor='white')
        logger.info(f"✅ Saved figure: {output_path}")
        plt.close()
        
        return str(output_path)
    
    def generate_all_visualizations(self, latency_file, velocity_file):
        """Generate all visualizations"""
        logger.info("🎨 Generating all visualizations...")
        
        results = {
            'latency_chart': None,
            'velocity_chart': None
        }
        
        # Load and generate latency chart
        latency_data = self.load_latency_data(latency_file)
        if latency_data and 'latency_by_throughput' in latency_data:
            results['latency_chart'] = self.generate_latency_throughput_chart(latency_data)
        else:
            logger.warning("⚠️ No latency data available for visualization")
        
        # Load and generate velocity chart
        velocity_data = self.load_velocity_data(velocity_file)
        if velocity_data and 'clusters' in velocity_data:
            results['velocity_chart'] = self.generate_peak_velocity_chart(velocity_data)
        else:
            logger.warning("⚠️ No velocity data available for visualization")
        
        logger.info("✅ All visualizations complete!")
        return results


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Generate Performance Analysis Visualizations'
    )
    parser.add_argument(
        '--latency-data',
        type=str,
        default='results/latency_data.json',
        help='Path to latency data JSON file'
    )
    parser.add_argument(
        '--velocity-data',
        type=str,
        default='results/velocity_data.json',
        help='Path to velocity data JSON file'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=RESULTS_DIR,
        help='Output directory for figures'
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize generator
        generator = VisualizationGenerator(results_dir=args.output_dir)
        
        # Generate all visualizations
        results = generator.generate_all_visualizations(
            latency_file=args.latency_data,
            velocity_file=args.velocity_data
        )
        
        # Print summary
        logger.info("\n" + "="*60)
        logger.info("📊 VISUALIZATION SUMMARY")
        logger.info("="*60)
        for viz_type, path in results.items():
            status = "✅" if path else "❌"
            logger.info(f"{status} {viz_type}: {path}")
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
