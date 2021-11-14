#!/bin/bash
# Copyright lowRISC contributors.
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

set -o errexit
set -o pipefail
set -o nounset

if [ "$#" -ne 2 ]; then
    echo "Two toolchain path arguments expected" 1>&2
    exit 1
fi

TOOLCHAIN1=`realpath $1`
TOOLCHAIN2=`realpath $2`

if [[ ! -d opentitan ]]; then
    git clone https://github.com/lowRISC/opentitan.git opentitan
fi
if [[ ! -d opentitan2 ]]; then
    git clone opentitan opentitan2
fi

pushd opentitan
./meson_init.sh -ft $TOOLCHAIN1
ninja -C build-out all
popd

pushd opentitan2
./meson_init.sh -ft $TOOLCHAIN2
ninja -C build-out all
popd

pushd opentitan
if [[ ! -f build/lowrisc_dv_chip_verilator_sim_0.1/sim-verilator/Vchip_sim_tb ]]; then
    fusesoc --cores-root . run --flag=fileset_top --target=sim --setup --build lowrisc:dv:chip_verilator_sim
fi
popd
