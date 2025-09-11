import re, sys, argparse, pathlib

def calc_new_version(maj, mi, pa, kind):
    if kind == "major":
        return maj + 1, 0, 0
    if kind == "minor":
        return maj, mi + 1, 0
    if kind == "patch":
        return maj, mi, pa + 1
    return maj, mi, pa  # none

def main():
    p = argparse.ArgumentParser(description="Bump APP_VERSION in a Python file.")
    p.add_argument("--file", required=True, help="Path to file containing APP_VERSION")
    p.add_argument("--bump", required=True, choices=["major", "minor", "patch", "none"])
    args = p.parse_args()

    path = pathlib.Path(args.file)
    text = path.read_text(encoding="utf-8")

    m = re.search(r'APP_VERSION\s*=\s*"(\d+)\.(\d+)\.(\d+)"', text)
    if not m:
        print("ERROR: APP_VERSION pattern not found", file=sys.stderr)
        sys.exit(1)

    maj, mi, pa = map(int, m.groups())
    new_maj, new_mi, new_pa = calc_new_version(maj, mi, pa, args.bump)
    new_version = f"{new_maj}.{new_mi}.{new_pa}"

    old_version = f"{maj}.{mi}.{pa}"
    if new_version != old_version:
        new_text = re.sub(
            r'APP_VERSION\s*=\s*"\d+\.\d+\.\d+"',
            f'APP_VERSION = "{new_version}"',
            text,
            count=1
        )
        path.write_text(new_text, encoding="utf-8")

    # Виводимо завжди — workflow зчитає це як нову версію
    print(new_version)

if __name__ == "__main__":
    main()
