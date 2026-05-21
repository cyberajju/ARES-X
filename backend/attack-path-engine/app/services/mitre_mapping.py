"""MITRE ATT&CK technique mapping service."""

from dataclasses import dataclass


@dataclass
class MITRETechnique:
    """A MITRE ATT&CK technique."""

    id: str
    name: str
    tactic: str
    description: str
    applicable_asset_types: list[str]
    base_probability: float


# Hardcoded subset of MITRE ATT&CK techniques
MITRE_TECHNIQUES: dict[str, MITRETechnique] = {
    "T1190": MITRETechnique(
        id="T1190",
        name="Exploit Public-Facing Application",
        tactic="Initial Access",
        description="Adversaries may exploit vulnerabilities in internet-facing applications to gain initial access.",
        applicable_asset_types=["server", "application", "load_balancer", "cloud_vm"],
        base_probability=0.6,
    ),
    "T1133": MITRETechnique(
        id="T1133",
        name="External Remote Services",
        tactic="Initial Access",
        description="Adversaries may leverage external-facing remote services for initial access.",
        applicable_asset_types=["server", "cloud_vm", "application"],
        base_probability=0.5,
    ),
    "T1078": MITRETechnique(
        id="T1078",
        name="Valid Accounts",
        tactic="Initial Access",
        description="Adversaries may obtain and abuse credentials of existing accounts.",
        applicable_asset_types=["identity", "server", "workstation", "cloud_vm", "application"],
        base_probability=0.55,
    ),
    "T1021": MITRETechnique(
        id="T1021",
        name="Remote Services",
        tactic="Lateral Movement",
        description="Adversaries may use valid accounts to interact with remote services.",
        applicable_asset_types=["server", "workstation", "cloud_vm"],
        base_probability=0.5,
    ),
    "T1053": MITRETechnique(
        id="T1053",
        name="Scheduled Task/Job",
        tactic="Execution",
        description="Adversaries may abuse task scheduling to execute malicious code.",
        applicable_asset_types=["server", "workstation", "cloud_vm"],
        base_probability=0.4,
    ),
    "T1055": MITRETechnique(
        id="T1055",
        name="Process Injection",
        tactic="Defense Evasion",
        description="Adversaries may inject code into processes to evade defenses and elevate privileges.",
        applicable_asset_types=["server", "workstation", "container"],
        base_probability=0.35,
    ),
    "T1059": MITRETechnique(
        id="T1059",
        name="Command and Scripting Interpreter",
        tactic="Execution",
        description="Adversaries may abuse command and script interpreters to execute commands.",
        applicable_asset_types=["server", "workstation", "cloud_vm", "container"],
        base_probability=0.6,
    ),
    "T1068": MITRETechnique(
        id="T1068",
        name="Exploitation for Privilege Escalation",
        tactic="Privilege Escalation",
        description="Adversaries may exploit software vulnerabilities to elevate privileges.",
        applicable_asset_types=["server", "workstation", "cloud_vm", "container"],
        base_probability=0.45,
    ),
    "T1110": MITRETechnique(
        id="T1110",
        name="Brute Force",
        tactic="Credential Access",
        description="Adversaries may use brute force to obtain credentials.",
        applicable_asset_types=["server", "application", "identity"],
        base_probability=0.3,
    ),
    "T1136": MITRETechnique(
        id="T1136",
        name="Create Account",
        tactic="Persistence",
        description="Adversaries may create accounts to maintain access.",
        applicable_asset_types=["server", "cloud_vm", "identity", "application"],
        base_probability=0.4,
    ),
    "T1195": MITRETechnique(
        id="T1195",
        name="Supply Chain Compromise",
        tactic="Initial Access",
        description="Adversaries may manipulate products or delivery mechanisms prior to receipt.",
        applicable_asset_types=["application", "container", "server"],
        base_probability=0.2,
    ),
    "T1210": MITRETechnique(
        id="T1210",
        name="Exploitation of Remote Services",
        tactic="Lateral Movement",
        description="Adversaries may exploit remote services to gain access to internal systems.",
        applicable_asset_types=["server", "workstation", "cloud_vm", "database"],
        base_probability=0.5,
    ),
    "T1484": MITRETechnique(
        id="T1484",
        name="Domain Policy Modification",
        tactic="Defense Evasion",
        description="Adversaries may modify domain policy settings to evade defenses.",
        applicable_asset_types=["server", "identity"],
        base_probability=0.35,
    ),
    "T1543": MITRETechnique(
        id="T1543",
        name="Create or Modify System Process",
        tactic="Persistence",
        description="Adversaries may create or modify system processes to execute malicious payloads.",
        applicable_asset_types=["server", "workstation", "cloud_vm"],
        base_probability=0.4,
    ),
    "T1548": MITRETechnique(
        id="T1548",
        name="Abuse Elevation Control Mechanism",
        tactic="Privilege Escalation",
        description="Adversaries may circumvent mechanisms designed to control elevated privileges.",
        applicable_asset_types=["server", "workstation", "cloud_vm"],
        base_probability=0.45,
    ),
    "T1556": MITRETechnique(
        id="T1556",
        name="Modify Authentication Process",
        tactic="Credential Access",
        description="Adversaries may modify authentication mechanisms to access user credentials.",
        applicable_asset_types=["server", "identity", "application"],
        base_probability=0.3,
    ),
    "T1562": MITRETechnique(
        id="T1562",
        name="Impair Defenses",
        tactic="Defense Evasion",
        description="Adversaries may disable or tamper with security tools and logging.",
        applicable_asset_types=["server", "workstation", "firewall", "cloud_vm"],
        base_probability=0.4,
    ),
    "T1570": MITRETechnique(
        id="T1570",
        name="Lateral Tool Transfer",
        tactic="Lateral Movement",
        description="Adversaries may transfer tools between systems within a compromised environment.",
        applicable_asset_types=["server", "workstation", "cloud_vm", "container"],
        base_probability=0.55,
    ),
    "T1574": MITRETechnique(
        id="T1574",
        name="Hijack Execution Flow",
        tactic="Persistence",
        description="Adversaries may execute payloads by hijacking the way an OS runs programs.",
        applicable_asset_types=["server", "workstation", "container"],
        base_probability=0.35,
    ),
    "T1612": MITRETechnique(
        id="T1612",
        name="Build Image on Host",
        tactic="Defense Evasion",
        description="Adversaries may build container images on a host to bypass defenses.",
        applicable_asset_types=["container", "cloud_vm"],
        base_probability=0.25,
    ),
}


class MITREMapper:
    """Maps assets and vulnerabilities to MITRE ATT&CK techniques."""

    def get_all_techniques(self) -> dict[str, MITRETechnique]:
        """Return all registered MITRE techniques."""
        return MITRE_TECHNIQUES

    def get_technique(self, technique_id: str) -> MITRETechnique | None:
        """Get a specific technique by ID."""
        return MITRE_TECHNIQUES.get(technique_id)

    def map_technique_to_asset_type(self, asset_type: str) -> list[MITRETechnique]:
        """Return techniques applicable to a given asset type."""
        results = []
        for technique in MITRE_TECHNIQUES.values():
            if asset_type in technique.applicable_asset_types:
                results.append(technique)
        return results

    def map_vulnerability_to_technique(self, cve_id: str) -> list[MITRETechnique]:
        """Map a CVE to relevant MITRE techniques based on heuristics.

        Uses keyword matching on common CVE patterns to determine relevant techniques.
        """
        cve_lower = cve_id.lower()
        results = []

        # Heuristic mapping based on common vulnerability patterns
        if "rce" in cve_lower or "remote" in cve_lower:
            if "T1210" in MITRE_TECHNIQUES:
                results.append(MITRE_TECHNIQUES["T1210"])
            if "T1190" in MITRE_TECHNIQUES:
                results.append(MITRE_TECHNIQUES["T1190"])

        if "priv" in cve_lower or "escalat" in cve_lower:
            if "T1068" in MITRE_TECHNIQUES:
                results.append(MITRE_TECHNIQUES["T1068"])
            if "T1548" in MITRE_TECHNIQUES:
                results.append(MITRE_TECHNIQUES["T1548"])

        if "auth" in cve_lower or "credential" in cve_lower:
            if "T1078" in MITRE_TECHNIQUES:
                results.append(MITRE_TECHNIQUES["T1078"])
            if "T1556" in MITRE_TECHNIQUES:
                results.append(MITRE_TECHNIQUES["T1556"])

        # Default: exploitation of remote services
        if not results:
            if "T1210" in MITRE_TECHNIQUES:
                results.append(MITRE_TECHNIQUES["T1210"])

        return results

    def get_technique_probability(self, technique_id: str, context: dict) -> float:
        """Calculate the probability of a technique succeeding given context.

        Context may include: asset_type, patch_level, has_edr, network_zone.
        """
        technique = MITRE_TECHNIQUES.get(technique_id)
        if technique is None:
            return 0.0

        probability = technique.base_probability

        # Adjust based on context
        if context.get("patch_level") == "outdated":
            probability = min(probability * 1.4, 0.95)
        elif context.get("patch_level") == "current":
            probability *= 0.6

        if context.get("has_edr", False):
            probability *= 0.5

        if context.get("network_zone") == "dmz":
            probability = min(probability * 1.3, 0.95)
        elif context.get("network_zone") == "internal":
            probability *= 0.8

        return min(max(probability, 0.0), 1.0)
