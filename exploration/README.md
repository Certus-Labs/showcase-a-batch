# Notebooks

- `20260112_ingest.ipynb`: Data ingestion and initial profiling

Exploration and analysis notebooks for DVF data quality discovery.

## Summary of Documentation

### DVF Dataset Structure

**Source**: Notice descriptive des fichiers DVF ([PDF](https://static.data.gouv.fr/resources/demandes-de-valeurs-foncieres/20221017-153319/notice-descriptive-du-fichier-dvf-20221017.pdf))

#### Data Origin

- Fed by **BNDP** (Base nationale des données patrimoniales) from cadastral system (Majic) + land registry (Fidji)
- Only **onerous mutations** included (Vente, Échange, Expropriation, Adjudication)
- **Biannual updates** (April & October)
- **Coverage**: All France except Bas-Rhin, Haut-Rhin, Moselle, Mayotte

#### Row Structure (IMPORTANT)

- **One document** → multiple **dispositions** (transactions)
- **One disposition** → multiple **rows** (if multiple locaux or parcels)
- ⚠️ **Duplicated prices**: Same `Valeur fonciere` appears across rows of same disposition
- **Key**: `No disposition` identifies each unique transaction

#### Core Columns

| Column | Description | Notes |
|--------|-------------|-------|
| `No disposition` | Transaction ID | Unique within document |
| `Date mutation` | Transaction date | Format: DD/MM/YYYY |
| `Nature mutation` | Transaction type | Vente, Échange, Expropriation, Adjudication |
| `Valeur fonciere` | Price (euros) | Comma decimal (e.g., "1070000,00") |
| `Code departement` | Département code | 2 digits (e.g., "75" = Paris) |
| `Code commune` | Commune code | 3 digits within département |
| `Code postal` | Postal code | 5 digits |
| `Section` | Cadastral section | 2 letters |
| `No plan` | Parcel number | Within section |
| `Nombre de lots` | Number of lots | In transaction |

#### Partial Columns (Contextual, Not Missing)

**Built Properties** (~58% of rows):

- `Type local`: Maison (1), Appartement (2), Dépendance (3), Local industriel (4)
- `Surface reelle bati`: Built surface (m²)
- `Nombre pieces principales`: Number of main rooms

**Land** (~68% of rows):

- `Nature culture`: Land type code (AB=terrain à bâtir, T=terres, VI=vignes, etc.)
- `Surface terrain`: Land surface (m²)

#### Key Insights for Quality Analysis

1. **Deduplication required**: Group by `No disposition` to avoid double-counting prices
2. **41% nulls on `Type local`** = Land transactions, NOT data quality issues
3. **Multiple property types per transaction**: Same disposition can have both land + buildings
4. **Cadastral references**: `Code departement` + `Code commune` + `Section` + `No plan` = unique parcel

---
