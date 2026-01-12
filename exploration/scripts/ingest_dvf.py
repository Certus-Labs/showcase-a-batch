#!/usr/bin/env python3
"""
DVF Data Ingestion Script

Downloads and processes DVF (Demandes de Valeurs Foncières) data from data.gouv.fr
and exports to parquet format.

Usage:
    python ingest_dvf.py [--year YEAR] [--output PATH]

Output:
    data/processed/dvf_{year}.parquet
"""

import argparse
import zipfile
from pathlib import Path

import pandas as pd
import requests


def search_dvf_dataset():
    """Search for the main DVF dataset on data.gouv.fr"""
    print("Searching for DVF dataset...")

    response = requests.get(
        "https://www.data.gouv.fr/api/1/datasets/",
        params={"q": "demandes valeurs foncieres", "page_size": 10},
    )
    response.raise_for_status()

    datasets = response.json().get("data", [])
    dvf_dataset = next((d for d in datasets if d["title"] == "Demandes de valeurs foncières"), None)

    if not dvf_dataset:
        raise ValueError("DVF dataset not found")

    print(f"✓ Found: {dvf_dataset['title']}")
    return dvf_dataset["id"]


def get_resource_url(dataset_id, year):
    """Get download URL for specific year"""
    print(f"Fetching resources for year {year}...")

    response = requests.get(f"https://www.data.gouv.fr/api/1/datasets/{dataset_id}/")
    response.raise_for_status()

    dataset = response.json()
    resources = dataset.get("resources", [])

    # Find resource for the specified year
    target_resource = None
    for r in resources:
        title = r.get("title", "")
        if str(year) in title and r.get("format") == "txt.zip":
            target_resource = r
            break

    if not target_resource:
        raise ValueError(f"No data found for year {year}")

    print(f"✓ Found: {target_resource['title']}")
    return target_resource["url"]


def download_and_extract(url, raw_dir):
    """Download zip file and extract TXT"""
    print("Downloading...")

    zip_path = raw_dir / "temp_download.zip"
    response = requests.get(url, stream=True)
    response.raise_for_status()

    with open(zip_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"✓ Downloaded: {zip_path.stat().st_size / 1024 / 1024:.2f} MB")

    # Extract
    with zipfile.ZipFile(zip_path, "r") as z:
        txt_file = z.namelist()[0]
        z.extractall(raw_dir)

    txt_path = raw_dir / txt_file
    print(f"✓ Extracted: {txt_path.name}")

    # Clean up zip
    zip_path.unlink()

    return txt_path


def load_and_transform(txt_path):
    """Load data and apply type transformations"""
    print("Loading data as strings...")

    df = pd.read_csv(txt_path, sep="|", encoding="utf-8", dtype=str, keep_default_na=False)
    print(f"✓ Loaded: {df.shape[0]:,} rows × {df.shape[1]} columns")

    print("Applying type transformations...")

    # Replace empty strings with NA
    df = df.replace("", pd.NA)

    # Define transformations (semantic types)
    transformations = {
        # Identifiers
        "No disposition": "int",
        # Dates
        "Date mutation": "date",
        # Monetary
        "Valeur fonciere": "float",
        # Codes/Identifiers (keep as string)
        "No voie": "str",
        "Code postal": "str",
        "Code voie": "str",
        "Code commune": "str",
        "Code departement": "str",
        "No plan": "str",
        "Section": "str",
        "Code type local": "str",
        # Quantitative integers
        "Nombre de lots": "int",
        "Nombre pieces principales": "int",
        # Surfaces
        "Surface reelle bati": "float",
        "Surface terrain": "float",
    }

    for col, dtype in transformations.items():
        if dtype == "str":
            df[col] = df[col].astype("object")
        elif dtype == "int":
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
        elif dtype == "float":
            if col == "Valeur fonciere":
                df[col] = df[col].str.replace(",", ".", regex=False)
            df[col] = pd.to_numeric(df[col], errors="coerce")
        elif dtype == "date":
            df[col] = pd.to_datetime(df[col], format="%d/%m/%Y", errors="coerce")

    print("✓ Transformations complete")
    return df


def export_to_parquet(df, output_path):
    """Export dataframe to parquet"""
    print(f"Exporting to {output_path}...")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False, compression="snappy")

    print(f"✓ Exported: {output_path}")
    print(f"  Size: {output_path.stat().st_size / 1024 / 1024:.2f} MB")
    print(f"  Rows: {df.shape[0]:,}")
    print(f"  Columns: {df.shape[1]}")


def main():
    parser = argparse.ArgumentParser(description="Ingest DVF data")
    parser.add_argument("--year", type=int, default=2023, help="Year to download (default: 2023)")
    parser.add_argument(
        "--output", type=str, help="Output path (default: data/processed/dvf_{year}.parquet)"
    )
    args = parser.parse_args()

    # Paths
    base_dir = Path(__file__).parent.parent.parent
    raw_dir = base_dir / "data" / "raw" / "dvf"
    processed_dir = base_dir / "data" / "processed"

    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    output_path = Path(args.output) if args.output else processed_dir / f"dvf_{args.year}.parquet"

    print(f"{'=' * 60}")
    print(f"DVF Data Ingestion - Year {args.year}")
    print(f"{'=' * 60}\n")

    try:
        # Pipeline
        dataset_id = search_dvf_dataset()
        url = get_resource_url(dataset_id, args.year)
        txt_path = download_and_extract(url, raw_dir)
        df = load_and_transform(txt_path)
        export_to_parquet(df, output_path)

        print(f"\n{'=' * 60}")
        print("✓ Ingestion complete")
        print(f"{'=' * 60}")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        raise


if __name__ == "__main__":
    main()
