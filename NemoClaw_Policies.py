#!/usr/bin/env python3
# =============================================================================
# nemoclaw_policies.py
#
# Displays NemoClaw's active sandbox network policies as a formatted table,
# showing which hosts are allowed and which binaries can access them.
# =============================================================================

import argparse
import os
import sys

DEFAULT_POLICY_PATH = "/app/nemoclaw-blueprint/policies/openclaw-sandbox.yaml"

parser = argparse.ArgumentParser(
    description = "Display NemoClaw sandbox network policies as a formatted table."
)
parser.add_argument(
    "--policy",
    default = DEFAULT_POLICY_PATH,
    help = f"Path to openclaw-sandbox.yaml (default: {DEFAULT_POLICY_PATH})"
)
args = parser.parse_args()

if not os.path.exists(args.policy):
    print(f"ERROR: Policy file not found: {args.policy}")
    print("       Run this script from inside the AKS pod shell:")
    print("       kubectl exec -it -n nemoclaw deployment/nemoclaw-poc -- bash")
    sys.exit(1)

lines = open(args.policy).readlines()

POLICY_W = 20
HOST_W   = 45
BINARY_W = 30
TOTAL_W  = POLICY_W + HOST_W + BINARY_W + 2

policy = ""
hosts  = []
bins   = []
rows   = []

def flush_block(policy, hosts, bins, rows):
    """Convert current policy block into table rows."""
    if not policy:
        return
    count = max(len(hosts), len(bins), 1)
    for i in range(count):
        rows.append((
            policy if i == 0 else "",
            hosts[i] if i < len(hosts) else "",
            bins[i]  if i < len(bins)  else "",
        ))
    rows.append(("", "", ""))  # blank separator between policies

for line in lines:
    s = line.rstrip()
    if (s.startswith("  ")
            and s.endswith(":")
            and not s.startswith("   ")
            and "policy"   not in s
            and "landlock"  not in s
            and "process"   not in s
            and "version"   not in s
            and "filesystem" not in s):
        flush_block(policy, hosts, bins, rows)
        policy = s.strip().rstrip(":")
        hosts  = []
        bins   = []

    elif s.startswith("      - host:"):
        hosts.append(s.split("host:")[1].strip())

    elif s.startswith("      - { path:"):
        bins.append(s.split("path:")[1].replace("}", "").strip())

flush_block(policy, hosts, bins, rows)  # flush last block

print()
print(f"  NemoClaw Sandbox — Active Network Policies")
print(f"  Policy file: {args.policy}")
print()
print(f"  {'POLICY':<{POLICY_W}} {'ALLOWED HOST':<{HOST_W}} {'RESTRICTED TO BINARY':<{BINARY_W}}")
print(f"  {'-' * TOTAL_W}")

for policy, host, binary in rows:
    if policy == "" and host == "" and binary == "":
        print()
    else:
        print(f"  {policy:<{POLICY_W}} {host:<{HOST_W}} {binary:<{BINARY_W}}")

print()
print(f"NOTE: Binary restrictions mean ONLY the listed binary can reach")
print(f"that host. curl, wget, python etc. are blocked at kernel level")
print(f"by OpenShell even if the agent is compromised.")
print()
