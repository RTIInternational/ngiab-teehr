"""A collection of helper functions for the TEEHR-Nextgen project."""
import glob
import os
import logging
import sqlite3
import json

import geopandas as gpd
import pandas as pd
import xarray as xr

logger = logging.getLogger(__name__)

USGS_NWM30_XWALK = "s3://ciroh-rti-public-data/teehr-data-warehouse/common/crosswalks/usgs_nwm30_crosswalk.conus.parquet"  # noqa
USGS_POINT_GEOMETRY = "s3://ciroh-rti-public-data/teehr-data-warehouse/common/geometry/usgs_point_geometry.all.parquet"  # noqa


def get_usgs_nwm30_crosswalk():
    return pd.read_parquet(
        USGS_NWM30_XWALK,
        storage_options={
            "client_kwargs":
                {"region_name": "us-east-2"},
                "anon": True
            }
        )


def get_usgs_point_geometry():
    return gpd.read_parquet(
        USGS_POINT_GEOMETRY,
        storage_options={
            "client_kwargs":
                {"region_name": "us-east-2"},
                "anon": True
            }
        )


def get_simulation_output_format(folder_to_eval):
    """
    determines the output format from files in the outputs/troute folder
    the troute config was called ngen.yaml and now is called troute.yaml
    so we can just check the output folder for the types
    """
    # check for netcdf files
    nc_file = folder_to_eval / "outputs" / "troute" / "*.nc"
    nc_files = glob.glob(str(nc_file))
    if len(nc_files) > 0:
        return "netcdf"
    # check for csv files
    csv_file = folder_to_eval / "outputs" / "troute" / "*.csv"
    csv_files = glob.glob(str(csv_file))
    if len(csv_files) > 0:
        return "csv"
    raise FileNotFoundError("No output files found in the outputs/troute folder")


def get_simulation_output_netcdf(wb_id, folder_to_eval):
    """Read Nextgen simulation output from netcdf file.

    Ref: https://github.com/JoshCu/ngiab_eval/blob/b39e5af6eb382d64f07a5c55a7acb0109dd26f8f/ngiab_eval/core.py#L109  # noqa
    """
    nc_file = folder_to_eval / "outputs" / "troute" / "*.nc"
    # find the nc file
    nc_files = glob.glob(str(nc_file))
    if len(nc_files) == 0:
        raise FileNotFoundError(
            "No netcdf file found in the outputs/troute folder"
        )
    if len(nc_files) > 1:
        logger.warning(
            "Multiple netcdf files found in the outputs/troute folder"
        )
        logger.warning("Using the most recent file")
        nc_files.sort(key=os.path.getmtime)
        file_to_open = nc_files[-1]
    if len(nc_files) == 1:
        file_to_open = nc_files[0]
    all_output = xr.open_dataset(file_to_open)
    # print(all_output)
    id_stem = wb_id.split("-")[1]
    gage_output = all_output.sel(feature_id=int(id_stem))
    gage_output = gage_output.drop_vars(["type", "velocity", "depth", "nudge", "feature_id"])
    gage_output = gage_output.rename({"time": "current_time"})
    gage_output = gage_output.to_dataframe()
    # print(gage_output)
    return gage_output.reset_index()


def get_simulation_output_csv(wb_id, folder_to_eval):
    """
    NOTE: ONLY WORKS FOR CSV OUTPUT

    Ref: https://github.com/JoshCu/ngiab_eval/blob/2e8fd96b21a369bb93b2a491b0c303a4018a290e/ngiab_eval/core.py
    """
    csv_file = folder_to_eval / "outputs" / "troute" / "*.csv"
    # find the nc file
    csv_files = glob.glob(str(csv_file))
    if len(csv_files) == 0:
        raise FileNotFoundError(
            "No CSV file found in the outputs/troute folder"
        )
    if len(csv_files) > 1:
        logger.warning("Multiple CSV files found in the outputs/troute folder")
        logger.warning("Using the most recent file")
        csv_files.sort(key=os.path.getmtime)
        file_to_open = csv_files[-1]
    if len(csv_files) == 1:
        file_to_open = csv_files[0]
    all_output = pd.read_csv(file_to_open)
    id_stem = wb_id.split("-")[1]
    gage_output = all_output[all_output.featureID == int(id_stem)][
        ["flow", "current_time"]
    ].copy()
    gage_output["ngen_id"] = id_stem
    return gage_output.reset_index()


def get_gages_from_hydrofabric(folder_to_eval):
    """
    Get the gages from the hydrofabric.

    Ref: https://github.com/JoshCu/ngiab_eval/blob/2e8fd96b21a369bb93b2a491b0c303a4018a290e/ngiab_eval/core.py
    """
    # search inside the folder for _subset.gpkg recursively
    gpkg_file = None
    config_dir = os.path.join(folder_to_eval,"config")
    for root, dirs, files in os.walk(config_dir):
        for file in files:
            if file.endswith(".gpkg"):
                gpkg_file = os.path.join(root, file)
                break

    if gpkg_file is None:
        raise FileNotFoundError("No subset.gpkg file found in folder")

    # figure out if the hf is v20.1 or v2.2
    # 2.2 has a pois table, 20.1 does not
    with sqlite3.connect(gpkg_file) as conn:
        results = conn.execute(
            "SELECT count(*) FROM gpkg_contents WHERE table_name = 'pois'"
        ).fetchall()

    if results[0][0] == 0:
        with sqlite3.connect(gpkg_file) as conn:
            results = conn.execute(
                "SELECT id, rl_gages FROM flowpath_attributes WHERE rl_gages IS NOT NULL"
            ).fetchall()
            # Fixme Take only the first result if a gage shows up more than once.
            # Should be fixed upstream in hydrofabric with only error handling here.
            results = [(r[0], r[1].split(",")[0]) for r in results]
    else:
        with sqlite3.connect(gpkg_file) as conn:
            results = conn.execute(
                "SELECT id, gage FROM 'flowpath-attributes' WHERE gage IS NOT NULL"
            ).fetchall()

    return results


def get_simulation_start_end_time(folder_to_eval):
    """
    Get start and  end time of the simulation.

    Ref: https://github.com/JoshCu/ngiab_eval/blob/2e8fd96b21a369bb93b2a491b0c303a4018a290e/ngiab_eval/core.py#L77 # noqa
    """
    realization = folder_to_eval / "config" / "realization.json"
    with open(realization) as f:
        realization = json.load(f)
    start = realization["time"]["start_time"]
    end = realization["time"]["end_time"]
    return start, end
