# SceneFlow

This repository contains the paper and the code of "Scene Flow Specifications: Encoding and Monitoring Rich Temporal Safety Properties of Autonomous Systems". The code is written in Python and requires [conda](https://docs.anaconda.com/free/anaconda/install/linux/) and [7z](https://www.7-zip.org/download.html) to be installed. The code was tested using Ubuntu 20.04.

- [Installation](#installation)
- [Replication](#replication)

## Example violations
Below are three example violations from the `HazardAtSideLaneTwoWays` scenarios that were automatically identified by the technique.

### Property 6: The opposing lane must be clear when passing vehicles
The vehicle crosses into the opposing lane to pass the bikes in its lane. This is allowed as the opposing lane is free.
However, the vehicle remains in the opposing lane too long after passing the bikes, coming too close to a vehicle approaching in the opposing lane.
This is a violation as the opposing lane was not clear for the duration of the maneuver.

![Vehicle crosses into opposing lane to pass two bikes; does not get back into its lane fast enough when traffic comes](./videos/518.gif)

### Property 5: Passing a bike too closely
While the three-foot distance cited in the driving code is observed here, it is only barely met.
These violations were identified by increasing the required safety buffer.

#### Bike 1:
![Vehicle comes too close to a bike while passing. Bike 1](./videos/435.gif)

#### Bike 2:
![Vehicle comes too close to a bike while passing. Bike 2](./videos/476.gif)

## Installation
This has been tested on a Ubuntu 20.04.

To install everything needed to run the code, execute the following command:
```bash
./unpack_data.sh
```
The installation script will do the following:
1) Unpack the included study data from `study_data.7z`
2) Create the conda environments as needed.
3) Install [mona](https://www.brics.dk/mona/) using the `install_mona.sh` script

## Replication
To reproduce the results of the paper, execute the following command:
```bash
./run.sh
```
This will run for ~6 hours. If you are running on a machine with at least 10 cores, you can substantially reduce this time by using the multithreaded version below.
```bash
./run_threaded.sh
```

This script will do the following:
1) Activate the conda environments as needed.
2) Unpack the scene graphs used in the experiment for RQ2 and RQ3.
3) Check the properties specified in the paper, located in the `symbolic_properties.py` file, using the scene graphs and the monitor instantiation. The violations will appear in `./results/`
4) Generate tables that show the property violations for each RQ.
