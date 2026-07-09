# Project Guide

## Big Picture

This project began as an AI-governed crypto-bank simulator.

The project later shifted toward an empirical research question: before simulating blockchain users, can real Ethereum wallets be grouped into behavioural roles using transaction data?

The final project is therefore not mainly a simulator. It is a data-analysis and validation pipeline for Ethereum wallet behaviour segmentation.

## Final Research Question

Can Ethereum wallets be organized into interpretable behavioural roles that are reproducible across feature sets, aligned with transaction-network structure, and persistent enough over time to support meaningful analysis of wallet behaviour?

## Why This Matters

Ethereum transaction data is public but hard to interpret directly.

Millions of wallet addresses interact with contracts, exchanges, bridges, DeFi protocols, and other wallets.

Instead of treating every address separately, this project asks whether wallets can be summarized into broader behavioural roles.

## What We Actually Did

### 1. Feature Engineering

Raw daily transaction data was transformed into wallet-level features.

The features describe activity intensity, value flow, directionality, persistence, volatility, and concentration.

### 2. Behavioural Clustering

KMeans with six clusters was used as the main segmentation model.

The output was a six-role behavioural vocabulary for Ethereum wallets.

### 3. Network Validation

The clusters were checked against transaction-network structure.

The main idea was: if the roles are meaningful, wallets with similar roles should show non-random structure in the transaction graph.

### 4. Temporal Analysis

Wallets were assigned monthly behavioural states.

Monthly transitions were used to measure persistence, role movement, and temporary return patterns.

### 5. Paper-Focused Robustness Checks

Additional validation was added:

- Bipartite/Hungarian cluster matching.
- Distance-metric cluster correspondence.
- Cross-feature-set Spearman analysis.
- Permutation testing against random labels.
- Minimum observation/subsampling experiment.
- Within-cluster subcluster analysis.

## Main Findings

The six roles are interpretable from transaction features.

The roles align strongly with transaction-network structure.

Wallet roles show moderate monthly persistence rather than random movement.

Cross-analysis checks show non-random role correspondence.

The feature sets are related but not redundant.

Some smaller/specialized roles appear less stable and require careful wording.

## Careful Wording

Use:

> behavioural roles

Avoid:

> verified real-world identities

Use:

> K=6 is an interpretable and validated solution under our tests.

Avoid:

> K=6 is the true number of Ethereum wallet types.

Use:

> stability supports reproducibility under tested perturbations.

Avoid:

> stability proves correctness.

## Best Contribution Statement

This project contributes an unsupervised Ethereum wallet segmentation framework that discovers behavioural roles from transaction features and validates them through transaction-network structure, random-label testing, cross-feature-set correspondence, subsampling stability, and temporal transition analysis.

