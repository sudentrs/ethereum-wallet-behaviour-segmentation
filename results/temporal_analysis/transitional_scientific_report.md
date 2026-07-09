# Transitional Analysis of KMeans6 Behavioral States

This analysis adds a dynamic layer to the cluster-behavior study. The previous analyses treated clusters as static behavioral communities. Here, we ask whether wallets remain in the same behavioral role over time or move between roles month by month.

## 1. Mathematical Definition

Let:

`x_{i,t} in R^33`

be the expanded robust-scaled behavior vector of wallet `i` during month `t`.

Let:

`mu_k`

be the full-year median behavioral prototype of KMeans6 cluster `C_k`.

For every active wallet-month, we assign a monthly behavioral state:

`s_{i,t} = argmin_k ||x_{i,t} - mu_k||_2`

This means a wallet can have full-year cluster `C_1`, but in a specific month behave more like prototype `C_3`, `C_4`, etc.

The transition probability from state `a` to state `b` is:

`P_ab = #{i : s_{i,t}=a and s_{i,t+1}=b} / #{i : s_{i,t}=a}`

This gives a Markov-style transition matrix over behavioral states.

## 2. Visual Evidence

Monthly state composition:

![Monthly behavioral state composition](figures/monthly_behavior_state_composition.png)

Overall transition probability matrix:

![Overall transition probabilities](figures/overall_transition_probability_matrix.png)

Monthly self-transition rate:

![Monthly self transition rate](figures/monthly_self_transition_rate.png)

Transition counts:

![Overall transition counts](figures/overall_transition_count_matrix_log.png)

## 3. Overall Transition Probability Matrix

Rows are current monthly state; columns are next monthly state.

| From state | To C0 | To C1 | To C2 | To C3 | To C4 | To C5 |
|---:|---:|---:|---:|---:|---:|---:|
| C0 | 0.324 | 0.048 | 0.201 | 0.261 | 0.137 | 0.028 |
| C1 | 0.252 | 0.457 | 0.070 | 0.111 | 0.074 | 0.036 |
| C2 | 0.059 | 0.006 | 0.519 | 0.326 | 0.074 | 0.016 |
| C3 | 0.074 | 0.011 | 0.276 | 0.524 | 0.087 | 0.028 |
| C4 | 0.145 | 0.016 | 0.226 | 0.283 | 0.276 | 0.054 |
| C5 | 0.141 | 0.029 | 0.102 | 0.265 | 0.229 | 0.234 |

## 4. Behavioral State Stability

Self-transition probability measures how often wallets remain in the same monthly behavior state.

| State | Self-transition probability | Entropy | Top destinations |
|---:|---:|---:|---|
| C0 | 0.324 | 2.247 | C0=0.324; C3=0.261; C2=0.201 |
| C1 | 0.457 | 2.089 | C1=0.457; C0=0.252; C3=0.111 |
| C2 | 0.519 | 1.676 | C2=0.519; C3=0.326; C4=0.074 |
| C3 | 0.524 | 1.802 | C3=0.524; C2=0.276; C4=0.087 |
| C4 | 0.276 | 2.240 | C3=0.283; C4=0.276; C2=0.226 |
| C5 | 0.234 | 2.366 | C3=0.265; C5=0.234; C4=0.229 |

### Interpretation

- **C2 and C3 are the most stable monthly behavior states.**
  - C2 self-transition: `0.519`
  - C3 self-transition: `0.524`
- **C1 is moderately stable**, with self-transition `0.457`.
- **C4 and C5 are transitional states**, not highly persistent states.
  - C4 self-transition: `0.276`
  - C5 self-transition: `0.234`
- **C0 is also mixed/transitional**, with only `0.324` self-transition.

## 5. Main Transition Pathways

The strongest off-diagonal pathways are:

- **C2 -> C3:** `0.326`
- **C3 -> C2:** `0.276`
- **C4 -> C3:** `0.283`
- **C5 -> C3:** `0.265`
- **C0 -> C3:** `0.261`
- **C1 -> C0:** `0.252`
- **C5 -> C4:** `0.229`
- **C4 -> C2:** `0.226`

This suggests that **C3 acts as a dynamic attractor or bridge state**. Many states transition into C3, and C3 also transitions strongly into C2.

## 6. Monthly Persistence

The month-to-month self-transition rate ranges from:

- minimum: `0.432` for 202210 -> 202211
- maximum: `0.480` for 202211 -> 202212

| Month transition | Wallets active in both months | Self-transition rate |
|---|---:|---:|
| 202201 -> 202202 | 637,370 | 0.454 |
| 202202 -> 202203 | 685,583 | 0.462 |
| 202203 -> 202204 | 741,183 | 0.458 |
| 202204 -> 202205 | 724,343 | 0.447 |
| 202205 -> 202206 | 665,077 | 0.455 |
| 202206 -> 202207 | 667,813 | 0.476 |
| 202207 -> 202208 | 723,881 | 0.433 |
| 202208 -> 202209 | 817,520 | 0.445 |
| 202209 -> 202210 | 835,572 | 0.448 |
| 202210 -> 202211 | 820,720 | 0.432 |
| 202211 -> 202212 | 811,689 | 0.480 |

This means monthly behavior is only moderately persistent. Roughly **43-48%** of active wallets remain in the same behavior state from one month to the next, while the rest shift to another state.

## 7. Monthly Composition Shifts

Monthly state shares show that the dynamic behavior distribution changes over time:

- C3 dominates many months, often around `40-49%` of active wallets.
- C2 is also consistently large, around `27-35%`.
- C4 rises sharply in September 2022, reaching `18.5%`.
- C5 is usually small but spikes in August 2022 to `6.7%`.
- C1 remains a small monthly state despite being an important full-year cluster, suggesting C1 behavior requires persistence over longer windows.

This is an important interpretation: **full-year clusters and monthly states are not identical objects**. Full-year clusters summarize long-term behavior; monthly states capture short-term behavioral expression.

## 8. Scientific Conclusion

The clusters should be interpreted dynamically:

`full-year KMeans6 cluster = long-term behavioral identity`

`monthly assigned state = short-term behavioral expression`

The transition matrix shows that some states are stable roles and others are temporary phases:

- Stable behavioral states: **C2, C3**
- Moderately stable: **C1**
- Transitional/mixed states: **C0, C4, C5**

The most important dynamic pathway is around C3:

`C2 <-> C3`, `C4 -> C3`, `C5 -> C3`, and `C0 -> C3`.

So C3 can be described as a dynamic bridge or attractor state in monthly wallet behavior.

This strengthens the behavioral story: KMeans6 clusters are not only static segments; they also define a behavioral state space through which wallets move over time.

