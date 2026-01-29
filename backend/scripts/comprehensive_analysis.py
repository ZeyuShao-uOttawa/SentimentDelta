"""
Comprehensive Analysis of Consensus Price Comparison Outputs

This script:
1. Aggregates results from multiple ticker runs
2. Performs statistical analysis across all results
3. Generates visualizations and reports
4. Identifies patterns and trading signals
5. Exports results to CSV and JSON for further analysis
"""

import json
import csv
from typing import Dict, List, Any, Tuple
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict

# Configuration
OUTPUT_DIR = Path(__file__).parent.parent / "analysis_results"
OUTPUT_DIR.mkdir(exist_ok=True)

SIGNIFICANCE_LEVEL = 0.05

class ComprehensiveAnalyzer:
    """
    Main class for analyzing consensus price comparison outputs across multiple tickers.
    """
    
    def __init__(self):
        self.results = defaultdict(dict)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.report_path = OUTPUT_DIR / f"analysis_report_{self.timestamp}.txt"
        self.report_file = open(self.report_path, 'w', encoding='utf-8')

        self._classification_cache = None
        
    def log(self, message: str):
        """Log message to both console and file."""
        print(message)
        self.report_file.write(message + "\n")
        self.report_file.flush()
    
    def close(self):
        """Close the report file."""
        self.report_file.close()
        
    # ===========================
    # Data Aggregation
    # ===========================
    
    def add_ticker_results(self, ticker: str, results: Dict[str, Any]):
        """
        Add analysis results for a ticker.
        
        results dict should contain:
        - corr_results: correlation analysis
        - regression_coeffs: regression coefficients
        - logistic_metrics: logistic regression metrics
        - rf_metrics: random forest metrics
        - granger_pvals: Granger causality p-values
        - volatility_corr: correlation with volatility
        - monte_carlo_results: (real_coef, permuted_coefs)
        """
        self.results[ticker] = results
        
    # ===========================
    # Correlation Analysis
    # ===========================
    
    def analyze_correlations_across_tickers(self):
        """Analyze correlation statistics across all tickers."""
        self.log("\n" + "="*70)
        self.log("CORRELATION ANALYSIS ACROSS TICKERS")
        self.log("="*70)
        
        correlation_summary = defaultdict(list)
        
        for ticker, results in self.results.items():
            if 'corr_results' not in results:
                continue
                
            corr_results = results['corr_results']
            self.log(f"\n{ticker}:")
            
            for feature, (pearson, spearman) in corr_results.items():
                correlation_summary[feature].append({
                    'ticker': ticker,
                    'pearson': pearson,
                    'spearman': spearman
                })
                
                self.log(f"  {feature:15s} | Pearson: {pearson:7.4f} | Spearman: {spearman:7.4f}")
        
        # Calculate aggregate statistics
        self.log("\n" + "-"*70)
        self.log("AGGREGATE CORRELATION STATISTICS")
        self.log("-"*70)
        
        for feature, values in correlation_summary.items():
            if not values:
                continue
                
            pearson_vals = [v['pearson'] for v in values]
            spearman_vals = [v['spearman'] for v in values]
            
            self.log(f"\n{feature}:")
            self.log(f"  Pearson  - Mean: {np.mean(pearson_vals):7.4f}, Std: {np.std(pearson_vals):7.4f}, "
                    f"Min: {np.min(pearson_vals):7.4f}, Max: {np.max(pearson_vals):7.4f}")
            self.log(f"  Spearman - Mean: {np.mean(spearman_vals):7.4f}, Std: {np.std(spearman_vals):7.4f}, "
                    f"Min: {np.min(spearman_vals):7.4f}, Max: {np.max(spearman_vals):7.4f}")
        
        return correlation_summary
    
    # ===========================
    # Regression Analysis
    # ===========================
    
    def analyze_regression_coefficients(self):
        """Analyze regression coefficients across all tickers."""
        self.log("\n" + "="*70)
        self.log("REGRESSION COEFFICIENT ANALYSIS")
        self.log("="*70)
        
        coef_summary = defaultdict(list)
        
        for ticker, results in self.results.items():
            if 'regression_coeffs' not in results:
                continue
                
            reg_coeffs = results['regression_coeffs']
            self.log(f"\n{ticker}:")
            
            for feature, coef in reg_coeffs.items():
                coef_summary[feature].append({
                    'ticker': ticker,
                    'coefficient': coef
                })
                
                direction = "UP" if coef > 0 else "DOWN"
                self.log(f"  {feature:15s} {direction:>4s} {coef:8.6f}")
        
        # Aggregate statistics
        self.log("\n" + "-"*70)
        self.log("AGGREGATE COEFFICIENT STATISTICS")
        self.log("-"*70)
        
        for feature, values in coef_summary.items():
            if not values:
                continue
                
            coefs = [v['coefficient'] for v in values]
            self.log(f"\n{feature}:")
            self.log(f"  Mean: {np.mean(coefs):8.6f}, Std: {np.std(coefs):8.6f}")
            self.log(f"  Range: [{np.min(coefs):8.6f}, {np.max(coefs):8.6f}]")
            self.log(f"  Consensus: {'POSITIVE' if np.mean(coefs) > 0 else 'NEGATIVE'}")
        
        return coef_summary
    
    # ===========================
    # Classification Model Analysis
    # ===========================
    
    def analyze_classification_metrics(self):
        """Analyze classification model metrics."""
        self.log("\n" + "="*70)
        self.log("CLASSIFICATION MODEL ANALYSIS")
        self.log("="*70)
        
        logistic_accs = []
        logistic_aucs = []
        rf_accs = []
        rf_aucs = []
        
        for ticker, results in self.results.items():
            if 'logistic_metrics' in results:
                log_m = results['logistic_metrics']
                logistic_accs.append(log_m['accuracy'])
                logistic_aucs.append(log_m['auc'])
                
                self.log(f"\n{ticker} - Logistic Regression:")
                self.log(f"  Accuracy: {log_m['accuracy']:.4f}")
                self.log(f"  AUC:      {log_m['auc']:.4f}")
            
            if 'rf_metrics' in results:
                rf_m = results['rf_metrics']
                rf_accs.append(rf_m['accuracy'])
                rf_aucs.append(rf_m['auc'])
                
                self.log(f"\n{ticker} - Random Forest:")
                self.log(f"  Accuracy: {rf_m['accuracy']:.4f}")
                self.log(f"  AUC:      {rf_m['auc']:.4f}")
        
        # Aggregate
        self.log("\n" + "-"*70)
        self.log("AGGREGATE CLASSIFICATION METRICS")
        self.log("-"*70)
        
        if logistic_accs:
            self.log(f"\nLogistic Regression:")
            self.log(f"  Avg Accuracy: {np.mean(logistic_accs):.4f} ± {np.std(logistic_accs):.4f}")
            self.log(f"  Avg AUC:      {np.mean(logistic_aucs):.4f} ± {np.std(logistic_aucs):.4f}")
        
        if rf_accs:
            self.log(f"\nRandom Forest:")
            self.log(f"  Avg Accuracy: {np.mean(rf_accs):.4f} ± {np.std(rf_accs):.4f}")
            self.log(f"  Avg AUC:      {np.mean(rf_aucs):.4f} ± {np.std(rf_aucs):.4f}")
        
        metrics = {
            'logistic': {'accs': logistic_accs, 'aucs': logistic_aucs},
            'rf': {'accs': rf_accs, 'aucs': rf_aucs}
        }

        self.classification_cache = metrics

        return metrics
    
    # ===========================
    # Granger Causality Analysis
    # ===========================
    
    def analyze_granger_causality(self):
        """Analyze Granger causality results across tickers."""
        self.log("\n" + "="*70)
        self.log("GRANGER CAUSALITY ANALYSIS")
        self.log("="*70)
        
        granger_results = defaultdict(lambda: defaultdict(list))
        
        for ticker, results in self.results.items():
            if 'granger_pvals' not in results:
                continue
                
            granger_pvals = results['granger_pvals']
            self.log(f"\n{ticker}:")
            
            for lag, pval in granger_pvals.items():
                is_significant = pval < SIGNIFICANCE_LEVEL
                granger_results[lag][pval] = is_significant
                
                sig_marker = "[SIGNIFICANT]" if is_significant else "[Not significant]"
                self.log(f"  Lag {lag}: p-value = {pval:.4f} {sig_marker}")
        
        # Summary
        self.log("\n" + "-"*70)
        self.log("GRANGER CAUSALITY SUMMARY")
        self.log("-"*70)
        
        for lag in sorted(granger_results.keys()):
            pvals = [pv for pv, _ in granger_results[lag].items()]
            sig_count = sum(1 for _, sig in granger_results[lag].items() if sig)
            
            self.log(f"\nLag {lag}:")
            self.log(f"  Significant in {sig_count}/{len(pvals)} tickers")
            self.log(f"  Mean p-value: {np.mean(pvals):.4f}")
        
        return granger_results
    
    # ===========================
    # Monte Carlo Analysis
    # ===========================
    
    def analyze_monte_carlo_results(self):
        """Analyze Monte Carlo permutation test results."""
        self.log("\n" + "="*70)
        self.log("MONTE CARLO PERMUTATION TEST ANALYSIS")
        self.log("="*70)
        
        real_coefs = []
        monte_carlo_pvals = []
        
        for ticker, results in self.results.items():
            if 'monte_carlo' not in results:
                continue
                
            real_coef, permuted_coefs = results['monte_carlo']
            p_value = np.mean(np.abs(permuted_coefs) >= np.abs(real_coef))
            
            real_coefs.append(real_coef)
            monte_carlo_pvals.append(p_value)
            
            is_significant = p_value < SIGNIFICANCE_LEVEL
            sig_marker = "[SIGNIFICANT]" if is_significant else "[Not significant]"
            
            self.log(f"\n{ticker}:")
            self.log(f"  Real coefficient: {real_coef:.6f}")
            self.log(f"  Monte Carlo p-value: {p_value:.4f} {sig_marker}")
            self.log(f"  Interpretation: Sentiment has {'real' if is_significant else 'questionable'} predictive power")
        
        # Aggregate
        self.log("\n" + "-"*70)
        self.log("MONTE CARLO AGGREGATE STATISTICS")
        self.log("-"*70)
        
        if real_coefs:
            significant_count = sum(1 for p in monte_carlo_pvals if p < 0.05)
            self.log(f"\nSentiment predictive power:")
            self.log(f"  Significant in {significant_count}/{len(real_coefs)} tickers (p < 0.05)")
            self.log(f"  Mean real coefficient: {np.mean(real_coefs):.6f}")
            self.log(f"  Mean p-value: {np.mean(monte_carlo_pvals):.4f}")
        
        return {'real_coefs': real_coefs, 'pvals': monte_carlo_pvals}
    
    # ===========================
    # Trading Signal Generation
    # ===========================
    
    def generate_trading_signals(self, corr_threshold=0.10, accuracy_threshold=0.55, auc_threshold=0.55):
        """
        Generate trading signals based on analysis results.
        
        Signals are generated when:
        1. Sentiment metrics show meaningful correlation with returns
        2. Classification models beat random (>53% accuracy)
        3. Granger causality tests are significant
        """
        self.log("\n" + "="*70)
        self.log("TRADING SIGNAL GENERATION")
        self.log("="*70)
        
        signals = {}

        for ticker, results in self.results.items():
            signal_strength = 0
            signal_factors = []
            
            # Correlation signal
            if 'corr_results' in results:
                corr_results = results['corr_results']
                avg_pearson = np.mean([abs(p) for p, _ in corr_results.values()])
                
                if avg_pearson > corr_threshold:
                    signal_strength += 1
                    signal_factors.append(f"Correlation signal (avg: {avg_pearson:.4f})")
            
            # Classification signal
            if 'rf_metrics' in results:
                rf_acc = results['rf_metrics']['accuracy']
                rf_auc = results['rf_metrics']['auc']
                if rf_acc > accuracy_threshold and rf_auc > auc_threshold:
                    signal_strength += 1
                    signal_factors.append(f"RF accuracy signal ({rf_acc:.4f})")
            
            # Granger signal
            if 'granger_pvals' in results:
                granger_pvals = results['granger_pvals']
                if any(p < 0.05 for p in granger_pvals.values()):
                    signal_strength += 1
                    signal_factors.append("Granger causality signal")
            
            # Monte Carlo significance
            if 'monte_carlo' in results:
                real, perm = results['monte_carlo']
                p = np.mean(np.abs(perm) >= np.abs(real))
                if p < SIGNIFICANCE_LEVEL:
                    signal_strength += 1
                    signal_factors.append("Permutation significant")
            
            signal_quality = "WEAK"
            if signal_strength == 2:
                signal_quality = "MODERATE"
            elif signal_strength >= 3:
                signal_quality = "STRONG"
            
            signals[ticker] = {
                'strength': signal_strength,
                'quality': signal_quality,
                'factors': signal_factors
            }
            
            self.log(f"\n{ticker}:")
            self.log(f"  Signal Quality: {signal_quality} ({signal_strength}/3 factors)")
            for factor in signal_factors:
                self.log(f"    • {factor}")
        
        return signals
    
    # ===========================
    # Visualization
    # ===========================
    
    def create_visualizations(self):
        """Create summary visualizations."""
        self.log("\n" + "="*70)
        self.log("GENERATING VISUALIZATIONS")
        self.log("="*70)
        
        # 1. Correlation heatmap
        self._plot_correlation_heatmap()
        
        # 2. Regression coefficients
        self._plot_regression_coefficients()
        
        # 3. Model performance comparison
        self._plot_model_performance()
        
        # 4. Granger causality results
        self._plot_granger_results()
        
        self.log(f"\nVisualizations saved to {OUTPUT_DIR}/")
    
    def _plot_correlation_heatmap(self):
        """Plot correlation results as heatmap."""
        data = {}
        for ticker, results in self.results.items():
            if 'corr_results' in results:
                corr_results = results['corr_results']
                data[ticker] = {k: v[0] for k, v in corr_results.items()}  # Use Pearson
        
        if not data:
            return
        
        df = pd.DataFrame(data).T
        
        plt.figure(figsize=(10, 6))
        sns.heatmap(df, annot=True, fmt='.3f', cmap='RdBu_r', center=0,
                   cbar_kws={'label': 'Pearson Correlation'})
        plt.title('Sentiment-Return Correlations by Ticker')
        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / f"correlations_heatmap_{self.timestamp}.png", dpi=300)
        plt.close()
        
        self.log(f"  [OK] Correlation heatmap saved")
    
    def _plot_regression_coefficients(self):
        """Plot regression coefficients."""
        data = {}
        for ticker, results in self.results.items():
            if 'regression_coeffs' in results:
                data[ticker] = results['regression_coeffs']
        
        if not data:
            return
        
        df = pd.DataFrame(data).T
        
        fig, ax = plt.subplots(figsize=(12, 6))
        df.plot(kind='bar', ax=ax)
        plt.title('Regression Coefficients by Ticker')
        plt.ylabel('Coefficient Value')
        plt.xlabel('Ticker')
        plt.legend(title='Feature', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.axhline(y=0, color='k', linestyle='-', linewidth=0.5)
        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / f"regression_coefficients_{self.timestamp}.png", dpi=300)
        plt.close()
        
        self.log(f"  [OK] Regression coefficients plot saved")
    
    def _plot_model_performance(self):
        """Plot classification model performance."""
        metrics = self.analyze_classification_metrics()
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # Accuracy comparison
        if metrics['logistic']['accs'] and metrics['rf']['accs']:
            ax1.bar(['Logistic\nRegression', 'Random\nForest'],
                   [np.mean(metrics['logistic']['accs']), np.mean(metrics['rf']['accs'])],
                   yerr=[np.std(metrics['logistic']['accs']), np.std(metrics['rf']['accs'])],
                   capsize=5)
            ax1.axhline(y=0.5, color='r', linestyle='--', label='Random Baseline')
            ax1.set_ylabel('Accuracy')
            ax1.set_title('Model Accuracy Comparison')
            ax1.set_ylim([0.45, 0.75])
            ax1.legend()
        
        # AUC comparison
        if metrics['logistic']['aucs'] and metrics['rf']['aucs']:
            ax2.bar(['Logistic\nRegression', 'Random\nForest'],
                   [np.mean(metrics['logistic']['aucs']), np.mean(metrics['rf']['aucs'])],
                   yerr=[np.std(metrics['logistic']['aucs']), np.std(metrics['rf']['aucs'])],
                   capsize=5)
            ax2.axhline(y=0.5, color='r', linestyle='--', label='Random Baseline')
            ax2.set_ylabel('AUC Score')
            ax2.set_title('Model AUC Comparison')
            ax2.set_ylim([0.45, 0.75])
            ax2.legend()
        
        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / f"model_performance_{self.timestamp}.png", dpi=300)
        plt.close()
        
        self.log(f"  [OK] Model performance plot saved")
    
    def _plot_granger_results(self):
        """Plot Granger causality p-values."""
        granger_data = defaultdict(list)
        
        for ticker, results in self.results.items():
            if 'granger_pvals' in results:
                granger_pvals = results['granger_pvals']
                for lag, pval in granger_pvals.items():
                    granger_data[lag].append(pval)
        
        if not granger_data:
            return
        
        lags = sorted(granger_data.keys())
        pvals = [granger_data[lag] for lag in lags]
        
        plt.figure(figsize=(10, 6))
        bp = plt.boxplot(pvals, labels=lags)
        plt.axhline(y=0.05, color='r', linestyle='--', label='Significance level (0.05)')
        plt.ylabel('P-value')
        plt.xlabel('Lag')
        plt.title('Granger Causality Test Results by Lag')
        plt.legend()
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / f"granger_causality_{self.timestamp}.png", dpi=300)
        plt.close()
        
        self.log(f"  [OK] Granger causality plot saved")
    
    # ===========================
    # Export Results
    # ===========================
    
    def export_to_csv(self):
        """Export summary results to CSV."""
        csv_path = OUTPUT_DIR / f"analysis_summary_{self.timestamp}.csv"
        
        rows = []
        for ticker, results in self.results.items():
            row = {'ticker': ticker}
            
            if 'corr_results' in results:
                for feature, (pearson, spearman) in results['corr_results'].items():
                    row[f'{feature}_pearson'] = pearson
                    row[f'{feature}_spearman'] = spearman
            
            if 'regression_coeffs' in results:
                for feature, coef in results['regression_coeffs'].items():
                    row[f'{feature}_coef'] = coef
            
            if 'logistic_metrics' in results:
                row['logistic_accuracy'] = results['logistic_metrics']['accuracy']
                row['logistic_auc'] = results['logistic_metrics']['auc']
            
            if 'rf_metrics' in results:
                row['rf_accuracy'] = results['rf_metrics']['accuracy']
                row['rf_auc'] = results['rf_metrics']['auc']
            
            rows.append(row)
        
        df = pd.DataFrame(rows)
        df.to_csv(csv_path, index=False)
        self.log(f"[OK] Summary exported to {csv_path}")
    
    def export_to_json(self):
        """Export detailed results to JSON."""
        json_path = OUTPUT_DIR / f"analysis_detailed_{self.timestamp}.json"
        
        # Convert results to JSON-serializable format
        json_results = {}
        for ticker, results in self.results.items():
            json_results[ticker] = {
                k: v if not isinstance(v, (np.ndarray, np.generic)) else v.tolist()
                for k, v in results.items()
            }
        
        with open(json_path, 'w') as f:
            json.dump(json_results, f, indent=2, default=str)
        
        self.log(f"[OK] Detailed results exported to {json_path}")
    
    # ===========================
    # Main Run
    # ===========================
    
    def generate_full_report(self, results_dict: Dict[str, Dict]):
        """
        Generate comprehensive analysis report.
        
        results_dict format:
        {
            'TSLA': {
                'corr_results': {...},
                'regression_coeffs': {...},
                'logistic_metrics': {...},
                'rf_metrics': {...},
                'granger_pvals': {...},
                'monte_carlo': (real_coef, permuted_coefs)
            },
            ...
        }
        """
        # Add all results
        for ticker, results in results_dict.items():
            self.add_ticker_results(ticker, results)
        
        # Run analyses
        self.analyze_correlations_across_tickers()
        self.analyze_regression_coefficients()
        self.analyze_classification_metrics()
        self.analyze_granger_causality()
        self.analyze_monte_carlo_results()
        trading_signals = self.generate_trading_signals()
        
        # Create visualizations
        self.create_visualizations()
        
        # Export results
        self.export_to_csv()
        self.export_to_json()
        
        # Final summary
        self._print_executive_summary(trading_signals)
        
        self.close()
        
        return {
            'report_path': str(self.report_path),
            'output_dir': str(OUTPUT_DIR),
            'timestamp': self.timestamp
        }
    
    def _print_executive_summary(self, trading_signals):
        """Print executive summary."""
        self.log("\n" + "="*70)
        self.log("EXECUTIVE SUMMARY")
        self.log("="*70)
        
        self.log("\nTrading Signal Quality by Ticker:")
        for ticker, signal in trading_signals.items():
            self.log(f"\n  {ticker}: {signal['quality']}")
            for factor in signal['factors']:
                self.log(f"    • {factor}")
        
        self.log("\nSee detailed visualizations in analysis_outputs/")
        self.log("See CSV summary for quick reference")
        self.log(f"Analysis timestamp: {self.timestamp}")

if __name__ == "__main__":
    """
    Example: Running analysis on results from consensus_price_comparison.py
    
    This shows how to integrate with the existing pipeline:
    """
    
    # Example results (you would get these from running consensus_price_comparison.py)
    example_results = {
        # "TICKER": {
        #     "corr_results": {"sent_mean": (pearson, spearman), ...},
        #     "regression_coeffs": {"sent_mean": coef, ...},
        #     "logistic_metrics": {"accuracy": acc, "auc": auc},
        #     "rf_metrics": {"accuracy": acc, "auc": auc},
        #     "granger_pvals": {1: pval, 2: pval, 3: pval},
        #     "monte_carlo": (real_coef, permuted_coefs_array)
        # }
    }
    
    analyzer = ComprehensiveAnalyzer()
    # analyzer.generate_full_report(example_results)
    
    print("Comprehensive analyzer initialized.")
    print("To use: Pass results dict from consensus_price_comparison.py to generate_full_report()")
