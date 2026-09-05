"""
Phase 50, step 4a: dependency-closure check -- byte-for-byte SHA-256
comparison of every packaged file (except main.py, which is package-local and
has no repo-root equivalent) against its repo source. Mirrors Phase 47's own
equivalent check.
"""
import hashlib
import os
import tarfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TAR_PATH = os.path.join(ROOT, "kaggriculture_phase50_submission_K.tar.gz")


def sha256_bytes(data):
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def main():
    mismatches = []
    checked = []
    with tarfile.open(TAR_PATH, "r:gz") as tar:
        for member in tar.getmembers():
            if member.name == "main.py":
                continue  # package-local, no repo-root equivalent by design
            repo_path = os.path.join(ROOT, member.name)
            if not os.path.isfile(repo_path):
                mismatches.append((member.name, "MISSING FROM REPO"))
                continue
            packaged_bytes = tar.extractfile(member).read()
            with open(repo_path, "rb") as f:
                repo_bytes = f.read()
            packaged_hash = sha256_bytes(packaged_bytes)
            repo_hash = sha256_bytes(repo_bytes)
            checked.append((member.name, packaged_hash, repo_hash, packaged_hash == repo_hash))
            if packaged_hash != repo_hash:
                mismatches.append((member.name, f"packaged={packaged_hash} repo={repo_hash}"))

    print(f"Checked {len(checked)} files (excluding main.py) against repo sources:\n")
    for name, ph, rh, ok in checked:
        status = "OK" if ok else "MISMATCH"
        print(f"  [{status}] {name}  sha256={ph}")

    if mismatches:
        print(f"\n{len(mismatches)} MISMATCH(ES) FOUND:")
        for name, detail in mismatches:
            print(f"  {name}: {detail}")
        raise SystemExit(1)
    else:
        print(f"\nAll {len(checked)} packaged files are byte-for-byte identical to their repo sources. Clean.")


if __name__ == "__main__":
    main()
