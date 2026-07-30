# Time-Domain ve Wavelength Signal Analizi Sonuc Raporu

Bu rapor, full EOA-only wallet evreni uzerinde uretilen temporal signal sonuclarini yorumlamak icin hazirlandi. Analiz toplam `2,443,868` wallet uzerinden yapildi ve ana davranis taksonomisi olarak mevcut `Behavior K5` cluster dosyasi kullanildi.

Raporun akisi once signal tarafindan baslar: once time-domain, sonra wavelength. En sonda bu signal cluster'larin Behavior K5 ile nasil iliskilendigi ve paper icin hangi sonuc cumlesinin kullanilabilecegi verilir.

## 1. Time-Domain Signal Model Selection

Time-domain feature seti wallet'larin yil icindeki aktivite surekliligini, bosluklarini, patlama davranisini ve aktif/inaktif gecislerini olcer. Kullanilan ana ozellikler sunlardir:

- `active_days`
- `active_ratio`
- `total_tx`
- `mean_tx_active_day`
- `tx_burstiness_cv`
- `max_to_mean_tx_ratio`
- `longest_active_streak`
- `longest_inactive_gap`
- `active_inactive_switches`
- `max_weekly_tx_change`

Model selection otomatik skora gore `K=3` onerdi:

| K | Silhouette | Mean ARI | Min Share | Max Share | Entropy | Selection Score |
|---:|---:|---:|---:|---:|---:|---:|
| 3 | 0.3011 | 0.2618 | 1.77% | 76.41% | 0.5544 | 0.3525 |
| 4 | 0.1315 | 0.3642 | 2.14% | 39.96% | 0.8367 | 0.2226 |
| 5 | 0.1638 | 0.5591 | 3.81% | 36.57% | 0.8999 | 0.3035 |
| 6 | 0.1455 | 0.3249 | 3.76% | 31.00% | 0.8836 | 0.2267 |
| 7 | 0.1418 | 0.5809 | 1.63% | 26.30% | 0.8688 | 0.2870 |
| 8 | 0.1822 | 0.4516 | 0.58% | 31.94% | 0.8123 | 0.2909 |

### Time-domain icin karar

Otomatik skor `K=3` dese de, paper icin time-domain tarafinda `K=5` daha savunulabilir gorunuyor.

Sebep su: `K=3` silhouette acisindan guclu, fakat cluster yapisi cok dengesiz. Wallet'larin `76.41%`'i tek bir cluster'a yigiliyor ve seed stability dusuk kaliyor (`mean ARI=0.2618`). Bu sonuc, time-domain davranisinin kaba bir ayrimini verir ama zengin davranis state'leri icin fazla genis kalir.

`K=5` ise silhouette olarak biraz daha dusuk olsa da cok daha iyi bir denge kuruyor:

- Mean ARI `0.5591`, yani K3'e gore cok daha stabil.
- En buyuk cluster `36.57%`, yani tek bir dev gruba cokme yok.
- Entropy `0.8999`, yani cluster dagilimi daha dengeli.
- State yorumlari daha kullanisli: sparse long-gap, low-activity mixed ve intermittent switching gibi ayrimlar gorulebiliyor.

Bu nedenle time-domain icin sonuc:

> Time-domain signal clustering'de `K=3` en kompakt ayrimi verir, fakat `K=5` daha dengeli, daha stabil ve davranis state'lerini daha iyi aciklayan ana cozumdur.

## 2. Time-Domain K5 Profilleri

Time-domain K5 profilleri sunlari gosteriyor:

| TD Cluster | Label | Wallet Share | Ana Profil |
|---:|---|---:|---|
| 0 | sparse long-gap state | 15.51% | Orta aktif gun, uzun inaktif bosluk, bursty davranis |
| 1 | sparse long-gap state | 21.95% | Cok az aktif gun, en uzun inaktif bosluk |
| 2 | sparse long-gap state | 36.57% | Dusuk aktiflik, daha duzenli sparse pattern |
| 3 | low-activity mixed state | 22.17% | Dusuk/orta aktiflik, daha karisik gecis davranisi |
| 4 | intermittent switching state | 3.81% | Cok daha aktif, cok daha fazla switch, yuksek burstiness |

En kritik state `TD4`tur. Bu cluster sadece `3.81%` wallet icerir ama davranissal olarak en belirgin gruptur:

- Ortalama aktif gun: `93.73`
- Ortalama aktif/inaktif switch: `87.71`
- Ortalama total tx: yaklasik `1,099.8`
- Burstiness CV: `1.016`
- Max/mean tx ratio: `6.248`

Bu, paper'da "intermittent switching state" olarak guclu bir temporal davranis bulgusu olabilir.

## 3. Wavelength Signal Model Selection

Wavelength feature seti wallet aktivitesinin frekans/ritim tarafini olcer. Bu kisim, zaman serisindeki kisa donemli ve uzun donemli ritimleri yakalamak icin spektral ozellikleri kullanir:

- dominant frequency
- dominant period days
- peak power share
- low/medium/high frequency power share
- weekly/monthly band power share
- spectral entropy

Wavelength model selection sonucu cok daha nettir. Otomatik skor da, metriklerin yorumu da `K=3`u destekliyor:

| K | Silhouette | Mean ARI | Min Share | Max Share | Entropy | Selection Score |
|---:|---:|---:|---:|---:|---:|---:|
| 3 | 0.1946 | 0.8317 | 6.41% | 52.66% | 0.8006 | 0.4026 |
| 4 | 0.1743 | 0.4396 | 4.99% | 43.04% | 0.8290 | 0.2842 |
| 5 | 0.1277 | 0.5361 | 4.27% | 34.09% | 0.8888 | 0.2617 |
| 6 | 0.1186 | 0.6262 | 3.08% | 31.60% | 0.8639 | 0.2751 |
| 7 | 0.1267 | 0.5173 | 1.10% | 31.91% | 0.8285 | 0.2561 |
| 8 | 0.1305 | 0.4423 | 0.49% | 30.89% | 0.8475 | 0.2360 |

### Wavelength icin karar

Wavelength icin ana secim net olarak `K=3` olmali.

`K=3` hem en yuksek silhouette degerine sahip (`0.1946`) hem de cok yuksek seed stability gosteriyor (`mean ARI=0.8317`). Ayrica cluster boyutlari kabul edilebilir: en kucuk cluster `6.41%`, en buyuk cluster `52.66%`.

Bu nedenle wavelength tarafinda ek bir karma sikmaya gerek yok:

> Wavelength signal clustering icin `K=3`, hem istatistiksel hem de yorumlanabilirlik acisindan en guclu cozumdur.

## 4. Wavelength K3 Profilleri

Wavelength K3 cluster'lari sunlari gosteriyor:

| W Cluster | Wallet Share | Dominant Period | TX High-Frequency Share | TX Low-Frequency Share | Entropy | Yorum |
|---:|---:|---:|---:|---:|---:|---|
| 0 | 52.66% | 74.73 days | 0.821 | 0.057 | 6.952 | Kisa/orta donem dagitik high-frequency ritim |
| 1 | 40.93% | 299.92 days | 0.701 | 0.131 | 6.789 | Daha uzun donemli ama hala dagitik ritim |
| 2 | 6.41% | 342.51 days | 0.429 | 0.366 | 5.799 | Daha concentrated, slow-cycle ritim |

Otomatik label'lar hepsini "distributed high-frequency rhythm" olarak adlandirsa da, profiller daha ince bir ayrim veriyor. Ozellikle `W2`, digerlerinden ayriliyor:

- Dominant period yaklasik `342.5` gun.
- Low-frequency share `0.366`, digerlerinden cok daha yuksek.
- Spectral entropy `5.799`, yani enerji daha konsantre.

Bu nedenle rapor dilinde `W2` icin "slow-cycle / concentrated rhythm" demek daha anlamli.

## 5. Behavior K5 ile Time-Domain Iliskisi

Signal cluster'lari ana Behavior K5 taksonomisiyle karsilastirdigimizda, temporal state'lerin behavior cluster'lara rastgele dagilmadigi goruluyor.

| Behavior K5 | Baskin TD State | Pay | Enrichment | Ana Yorum |
|---:|---|---:|---:|---|
| 0 | TD2 sparse long-gap | 66.2% | 1.81x | Cok belirgin sparse/uzun bosluklu temporal davranis |
| 1 | TD2 + TD3 | 33.2% / 28.0% | 0.91x / 1.26x | Tek state'e indirgenmeyen karisik temporal profil |
| 2 | TD1 sparse long-gap | 76.5% | 3.49x | En guclu uzun-inaktif-gap davranisi |
| 3 | TD0 + TD4 | 33.5% / 20.3% | 2.16x / 5.32x | Intermittent switching'e en yakin behavior cluster |
| 4 | TD3 + TD0 | 44.8% / 34.7% | 2.02x / 2.24x | Low-activity mixed ve sparse pattern birlikte |

En guclu bulgu:

> Behavior K5 cluster 3, intermittent switching state'te `5.32x` overrepresented.

Bu, Behavior K5 cluster 3'un sadece statik feature'larla ayrilmadigini, ayni zamanda yil icinde daha hareketli ve gecisli bir temporal pattern tasidigini gosterir.

Ikinci guclu bulgu:

> Behavior K5 cluster 2, TD1 sparse long-gap state'te `3.49x` overrepresented.

Bu da Behavior K5 cluster 2'nin belirgin bicimde uzun sure inaktif kalan, cok seyrek hareket eden wallet profilini temsil ettigini destekler.

## 6. Behavior K5 ile Wavelength Iliskisi

Wavelength K3 ile Behavior K5 karsilastirmasi daha ritmik/spektral bir okuma verir.

| Behavior K5 | Baskin W State | Pay | Enrichment | Ana Yorum |
|---:|---|---:|---:|---|
| 0 | W0 / W1 | 50.2% / 46.0% | 0.95x / 1.12x | Iki dagitik ritim arasinda bolunmus |
| 1 | W0 | 69.9% | 1.33x | Daha kisa/orta donem high-frequency ritme yakin |
| 2 | W1 | 58.0% | 1.42x | Daha uzun donemli distributed ritme yakin |
| 3 | W1 + W2 | 48.8% / 29.2% | 1.19x / 4.55x | Slow-cycle/concentrated ritimde cok guclu enrichment |
| 4 | W1 + W0 | 46.9% / 41.2% | 1.15x / 0.78x | Karisik ritim, W2'de orta guclu enrichment |

En guclu wavelength bulgusu:

> Behavior K5 cluster 3, W2 slow-cycle/concentrated rhythm grubunda `4.55x` overrepresented.

Behavior K5 cluster 4 de W2 tarafinda `1.85x` overrepresented. Bu, K5 cluster 3 ve 4'un yalnizca aktiflik miktariyla degil, ritim yapisiyla da digerlerinden ayrildigini gosterir.

## 7. Simdiye Kadar Gelen Ana Sonuc

Bu analizden sonra elimizde uc katmanli daha guclu bir hikaye var:

1. Ana davranis taksonomisi `Behavior K5` olarak korunabilir.
2. Time-domain tarafinda `K5`, zengin temporal state yorumu icin daha iyi.
3. Wavelength tarafinda `K3`, net ve stabil ritim cozumudur.
4. Behavior K5 cluster'lari bu signal cluster'larla anlamli sekilde iliskileniyor.

Bu ozellikle su iddiayi guclendirir:

> EOA wallet davranis rolleri sadece toplu islem/akim ozelliklerinden ibaret degildir; bu roller yil icindeki aktivite surekliligi, inaktiflik bosluklari, burst davranisi ve spektral ritim yapilariyla da ayrisir.

## 8. Paper Icin Sonuc Odakli Yorum

Paper'da bu bolum su sekilde konumlanabilir:

> To strengthen the temporal interpretation of the EOA-only K5 wallet taxonomy, we separately clustered two complementary temporal signal spaces: time-domain activity features and wavelength/spectral rhythm features. The time-domain analysis shows that a richer K5 state representation captures sparse long-gap, low-activity mixed, and intermittent switching regimes. The wavelength analysis supports a compact K3 rhythm structure, separating wallets into distributed high-frequency and concentrated slow-cycle rhythm profiles. Cross-tabulation with the main Behavior K5 taxonomy shows that these temporal signals are not uniformly distributed across wallet roles: Behavior K5 cluster 3 is strongly enriched in intermittent switching states and slow-cycle wavelength patterns, while Behavior K5 cluster 2 is strongly enriched in sparse long-gap states. These results support the interpretation that the main wallet roles encode not only static transaction intensity but also distinct temporal activity regimes.

## 9. Net Karar

Son karar:

- Ana behavior taxonomy: `Behavior K5`
- Time-domain signal clustering: `K5` ana yorum icin, `K3` kompakt robustness olarak belirtilebilir
- Wavelength signal clustering: `K3`
- En guclu bulgu: `Behavior K5 cluster 3`, hem `intermittent switching` time-domain state'te hem de `slow-cycle/concentrated` wavelength state'te guclu bicimde overrepresented
- En temiz akademik iddia: Behavior K5, temporal signal layer ile destekleniyor; ama bu nedensel degil, davranissal/associational evidence olarak yazilmali

