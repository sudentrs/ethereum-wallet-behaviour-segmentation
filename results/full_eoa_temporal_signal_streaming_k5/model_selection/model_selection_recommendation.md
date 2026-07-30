# Temporal Signal K Selection

- time_domain: recommended K=3 (score=0.3525, silhouette=0.3011, mean ARI=0.2618, max share=0.7641).
- wavelength: recommended K=3 (score=0.4026, silhouette=0.1946, mean ARI=0.8317, max share=0.5266).

Selection score is a practical ranking, not a theorem: silhouette rewards separation, seed ARI rewards stability,
and very dominant or tiny clusters are penalized. Final choice should also inspect the profile and label CSVs.