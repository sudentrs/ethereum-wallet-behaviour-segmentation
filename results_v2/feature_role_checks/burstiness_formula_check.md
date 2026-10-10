# Burstiness Formula Check

The time-domain signal script does not compute the standard Goh-Barabasi burstiness coefficient.
In `src/validation/build_full_eoa_temporal_signal_streaming.py`, the reported transaction burstiness field is named `tx_burstiness_cv`.
It is computed as:

`std_tx_active / mean_tx_active`

where `std_tx_active` and `mean_tx_active` are calculated from daily transaction counts on active days only.

This is a coefficient of variation, not the standard burstiness coefficient `B = (sigma - mu) / (sigma + mu)`.
Therefore values above 1, such as TD4 = 1.016, are possible and are not mathematically invalid under this definition.

Paper wording should use `transaction-count coefficient of variation on active days` or `tx burstiness CV`.
Avoid saying that the value is the standard burstiness coefficient.
