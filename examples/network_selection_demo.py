#!/usr/bin/env python3

import time
from gsmmodem.modem import GsmModem

PORT = "/dev/ttyACM1"
BAUDRATE = 115200
PIN = None

TWENTY_SECONDS = 20
FIVE_SECONDS = 5
ONE_SECOND = 1

FORBIDDEN_NETWORK_STATUS = 3

# default URAT is 5,3
#                 │ │
#                 │ preferred = LTE
#                 │
#              GSM/LTE dual mode
#
URAT_DEFAULT_PARAMS = (5, 3)
URAT_SELECTED_ACCESS_TECHNOLOGY_GSM = 0
URAT_SELECTED_ACCESS_TECHNOLOGY_LTE = 3

COPS_URAT_ACCESS_TECHNOLOGY_MAPPING = {
    0: URAT_SELECTED_ACCESS_TECHNOLOGY_GSM,
    1: URAT_SELECTED_ACCESS_TECHNOLOGY_GSM,
    3: URAT_SELECTED_ACCESS_TECHNOLOGY_GSM,
    7: URAT_SELECTED_ACCESS_TECHNOLOGY_LTE,
}


def main():
    print("Initializing modem...")
    modem = GsmModem(PORT, BAUDRATE)
    modem.connect(PIN)

    modem.disconnectNetwork()
    modem.setRadioAccessTechnology(*URAT_DEFAULT_PARAMS)

    networks = modem.getAvailableNetworks()
    print(
        "Available networks: \n{}".format(
            "\n".join(
                [
                    "({}, {}, {})".format(
                        network["operator_long"],
                        network["operator_numeric"],
                        network["access_technology"],
                    )
                    for network in networks
                ]
            )
        )
    )

    for network in networks:
        operator = network["operator_numeric"]
        access_technology = network["access_technology"]
        forbidden = network["status"] == FORBIDDEN_NETWORK_STATUS

        if forbidden:
            print(
                "✗ Skipping forbidden network {} on AcT {}".format(
                    operator, access_technology
                )
            )
            print("└→ Extended error report: {}".format(modem.getExtendedErrorReport()))
            continue

        modem.disconnectNetwork()
        # as advised, wait a bit to prevent conflicting
        # network selection states with the provider
        time.sleep(FIVE_SECONDS)

        # enforce usage of access_technology, i.e. not that it automatically switch to LTE
        selected_urat_access_technology = COPS_URAT_ACCESS_TECHNOLOGY_MAPPING[
            access_technology
        ]
        modem.setRadioAccessTechnology(selected_urat_access_technology)
        print(
            "Running measurements for {} on AcT {}".format(operator, access_technology)
        )

        try:
            modem.setManualNetworkSelection(operator, access_technology)
        except Exception as e:
            print("✗ Skipping {} error: {}".format(operator, e))
            print("└→ Extended error report: {}".format(modem.getExtendedErrorReport()))
            continue

        try:
            modem.waitForNetworkCoverage(TWENTY_SECONDS)
            creg = modem.getNetworkRegistrationStatus()
            print("Network registration status: {}".format(creg))
        except Exception:
            print(
                "✗ Skipping {}. Unable to register on network (timeout).".format(
                    operator
                )
            )
            print("└→ Extended error report: {}".format(modem.getExtendedErrorReport()))
            continue

        print("✓ Connected to netwok {}".format(modem.networkName))
        print("(rxlev, ber, rscp, ecn0)")

        for _ in range(0, 20):
            print(modem.signalStrengthExtended())
            time.sleep(ONE_SECOND)

    modem.disconnectNetwork()
    modem.setRadioAccessTechnology(*URAT_DEFAULT_PARAMS)


if __name__ == "__main__":
    main()
