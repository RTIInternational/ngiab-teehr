===========================================================================
### Note: 

This repo is no longer actively maintained. 

Please refer to the CIROH fork
at https://github.com/CIROH-UA/ngiab-teehr/tree/main
for up-to-date changes

===========================================================================

# ngiab-teehr
A repository for coupling [TEEHR](https://rtiinternational.github.io/teehr/) with [Nextgen-In-A-Box (NGIAB)](https://github.com/jameshalgren/NGIAB-CloudInfra) simulation output.

Warning: This code is experimental!

The `example_guide.sh` script demonstrates running a TEEHR evaluation (see `scripts/teehr_ngen.py`) on NGIAB output.

### To build and push the TEEHR image to the AWI CIROH registry

Customize the metrics calculated by TEEHR or any other code related to the workflow:

1. Create a branch off of main
2. Make your edits to `scripts/teehr_ngen.py` and/or `scripts/utils.py`
3. Update the `Changelog` so that your changes can be associated with a tag
4. Submit and PR and merge
5. Then checkout main and pull the new changes, and push your tag:
```bash
git checkout main
git pull
git tag -a v0.x.x -m "version 0.x.x"
git push origin v0.x.x
```

This will trigger a `github action` to build and push the image with your tag, and the `latest` tag, to the AWI CIROH registry.

To build and push locally:
```
docker build -t awiciroh/ngiab-teehr:<tag name> .
docker push awiciroh/ngiab-teehr:<tag name>
```

Now you can specify the image tag in the guide.sh script.

| | |
| --- | --- |
| ![alt text](https://ciroh.ua.edu/wp-content/uploads/2022/08/CIROHLogo_200x200.png) | Funding for this project was provided by the National Oceanic & Atmospheric Administration (NOAA), awarded to the Cooperative Institute for Research to Operations in Hydrology (CIROH) through the NOAA Cooperative Agreement with The University of Alabama (NA22NWS4320003). |
