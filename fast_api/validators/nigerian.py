from __future__ import annotations

import re


class NigerianValidators:

    NIN_PATTERN = re.compile(r"^\d{11}$")
    BVN_PATTERN = re.compile(r"^\d{11}$")
    MSISDN_PATTERN = re.compile(r"^(\+234|0)[7-9][0-9]{9}$")
    PHONE_PATTERN = re.compile(r"^0[7-9][0-9]{9}$")

    @staticmethod
    def validate_nin(nin: str) -> tuple[bool, str]:
        if not nin:
            return False, "NIN cannot be empty"
        if not NigerianValidators.NIN_PATTERN.match(nin):
            return False, "NIN must be 11 digits"
        return True, ""

    @staticmethod
    def validate_bvn(bvn: str) -> tuple[bool, str]:
        if not bvn:
            return False, "BVN cannot be empty"
        if not NigerianValidators.BVN_PATTERN.match(bvn):
            return False, "BVN must be 11 digits"
        return True, ""

    @staticmethod
    def validate_msisdn(msisdn: str) -> tuple[bool, str]:
        if not msisdn:
            return False, "MSISDN cannot be empty"

        msisdn = str(msisdn).strip()

        if msisdn.startswith("234"):
            msisdn = "+" + msisdn

        if not NigerianValidators.MSISDN_PATTERN.match(msisdn):
            return False, "Invalid MSISDN format. Expected +234 or 0 followed by 7-9 and 9 digits"

        return True, ""

    @staticmethod
    def validate_phone_number(phone: str) -> tuple[bool, str]:
        if not phone:
            return False, "Phone number cannot be empty"

        phone = str(phone).strip()

        if not NigerianValidators.PHONE_PATTERN.match(phone):
            return False, "Invalid phone format. Expected 0 followed by 7-9 and 9 digits"

        return True, ""

    @staticmethod
    def normalize_msisdn(msisdn: str) -> str:
        msisdn = str(msisdn).strip()

        if msisdn.startswith("+234"):
            return msisdn

        if msisdn.startswith("234"):
            return "+" + msisdn

        if msisdn.startswith("0"):
            return "+234" + msisdn[1:]

        return msisdn

    @staticmethod
    def validate_sim_serial(serial: str) -> tuple[bool, str]:
        if not serial:
            return False, "SIM serial cannot be empty"
        if len(serial) < 1 or len(serial) > 50:
            return False, "SIM serial must be between 1 and 50 characters"
        return True, ""

    @staticmethod
    def validate_imsi(imsi: str) -> tuple[bool, str]:
        if not imsi:
            return False, "IMSI cannot be empty"
        if not re.match(r"^\d{15}$", imsi):
            return False, "IMSI must be 15 digits"
        return True, ""
