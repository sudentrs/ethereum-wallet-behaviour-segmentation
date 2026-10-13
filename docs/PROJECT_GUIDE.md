# Project Guide

## Big Picture

This repository supports an academic study of Ethereum wallet behaviour segmentation.

The current project focuses on externally owned accounts (EOAs), not smart contracts.

The central goal is to test whether unsupervised wallet clusters can be interpreted as meaningful behavioural states rather than arbitrary model outputs.

## Research Question

Can Ethereum EOAs be organized into behavioural states that remain meaningful across aggregate wallet features, transaction-network evidence, and temporal activity patterns?

## Why This Matters

Ethereum transaction data is public but difficult to understand directly.

Millions of wallet addresses interact at different activity levels, value-flow scales, and temporal rhythms.

Wallet segmentation gives a compact way to describe this population, but clustering alone is not enough.

Because unsupervised learning has no ground-truth labels, a proposed wallet taxonomy should be tested against evidence that was not directly used to create the clusters.

## Current Analysis Path

### 1. Data Preparation

Raw ERC-20 transfer data is converted into wallet-level and wallet-day activity tables.

Smart contract addresses are filtered out so the main analysis focuses on EOAs.

### 2. Feature Engineering

Wallets are represented using activity, value-flow, directionality, concentration, volatility, and temporal-persistence features.

Features are robust-scaled before clustering.

### 3. Behavioural Clustering

The current paper compares K4, K5, and K6 KMeans taxonomies.

K5 is used as the main descriptive taxonomy because it provides a richer behavioural vocabulary while retaining stronger seed stability than K6.

K4 and K6 remain important robustness comparisons.

### 4. Feature And Role Interpretation

Cluster profiles, feature-family holdouts, and role summaries are used to check whether the clusters are interpretable.

The role labels should be read as behavioural states, not verified real-world identities.

### 5. Network Validation

Monthly transaction-network tests compare observed same-role transaction concentration against shuffled-label null models.

This checks whether the behavioural taxonomy also appears in transaction-flow structure.

### 6. Temporal Validation

Monthly state assignments are used to measure self-transition, role movement, and two-step return behaviour.

This treats wallet labels as dynamic behavioural states that may persist, change, or recur.

### 7. Temporal Signal Analysis

Full-population daily activity signals are used to compare aggregate K5 roles with time-domain and frequency-domain activity states.

This layer tests whether aggregate roles carry daily rhythm signatures.

## Main Claim Boundary

Use:

> Ethereum EOAs can be described through behavioural states that are supported by multiple validation layers.

Avoid:

> The clusters identify wallet owners or permanent real-world wallet identities.

Use:

> K5 is a defensible descriptive taxonomy under the current evidence.

Avoid:

> K5 is the only true number of Ethereum wallet types.

Use:

> Network evidence for K5 is mixed and time-varying.

Avoid:

> K5 is a stable transaction-community partition in every month.

## Best Contribution Statement

This project contributes a layered validation framework for Ethereum EOA wallet segmentation.

The framework combines aggregate feature profiles, feature-family perturbations, transaction-network null tests, monthly transition analysis, two-step return tests, and temporal signal analysis to evaluate whether unsupervised wallet roles are academically defensible.
