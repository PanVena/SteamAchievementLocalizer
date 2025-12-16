#!/usr/bin/env python3
"""
Update version script for Steam Achievement Localizer
Updates version in all relevant files:
- SteamAchievementLocalizer.py
- version_info.txt
- setup.py
"""

import re
import sys
from pathlib import Path


def update_version_in_file(file_path: Path, pattern: str, replacement: str, description: str):
    """Update version in a file using regex pattern"""
    try:
        content = file_path.read_text(encoding='utf-8')
        new_content, count = re.subn(pattern, replacement, content)
        
        if count > 0:
            file_path.write_text(new_content, encoding='utf-8')
            print(f"✓ Updated {description} in {file_path.name}")
            return True
        else:
            print(f"⚠ No matches found for {description} in {file_path.name}")
            return False
    except Exception as e:
        print(f"✗ Error updating {file_path.name}: {e}")
        return False


def update_all_versions(new_version: str):
    """Update version in all files"""
    # Validate version format
    if not re.match(r'^\d+\.\d+\.\d+$', new_version):
        print(f"✗ Invalid version format: {new_version}")
        print("  Expected format: X.Y.Z (e.g., 0.8.9)")
        return False
    
    # Convert to tuple for version_info.txt
    major, minor, patch = new_version.split('.')
    version_tuple = f"({major}, {minor}, {patch}, 0)"
    version_with_zero = f"{new_version}.0"
    
    project_root = Path(__file__).parent.parent
    success = True
    
    # 1. Update SteamAchievementLocalizer.py
    main_file = project_root / "SteamAchievementLocalizer.py"
    success &= update_version_in_file(
        main_file,
        r'APP_VERSION\s*=\s*"[^"]*"',
        f'APP_VERSION = "{new_version}"',
        "APP_VERSION"
    )
    
    # 2. Update version_info.txt (filevers)
    version_info = project_root / "version_info.txt"
    success &= update_version_in_file(
        version_info,
        r'filevers=\([^)]*\)',
        f'filevers={version_tuple}',
        "filevers"
    )
    
    # 3. Update version_info.txt (prodvers)
    success &= update_version_in_file(
        version_info,
        r'prodvers=\([^)]*\)',
        f'prodvers={version_tuple}',
        "prodvers"
    )
    
    # 4. Update version_info.txt (FileVersion string)
    success &= update_version_in_file(
        version_info,
        r"StringStruct\(u'FileVersion',\s*u'[^']*'\)",
        f"StringStruct(u'FileVersion', u'{version_with_zero}')",
        "FileVersion string"
    )
    
    # 5. Update version_info.txt (ProductVersion string)
    success &= update_version_in_file(
        version_info,
        r"StringStruct\(u'ProductVersion',\s*u'[^']*'\)",
        f"StringStruct(u'ProductVersion', u'{version_with_zero}')",
        "ProductVersion string"
    )
    
    # 6. Update setup.py (VERSION variable)
    setup_file = project_root / "setup.py"
    success &= update_version_in_file(
        setup_file,
        r'VERSION\s*=\s*"[^"]*"',
        f'VERSION = "{new_version}"',
        "VERSION in setup.py"
    )
    
    if success:
        print(f"\n✓ Successfully updated all files to version {new_version}")
        return True
    else:
        print(f"\n⚠ Some updates failed. Please check the output above.")
        return False


def main():
    if len(sys.argv) != 2:
        print("Usage: python update_version.py X.Y.Z")
        print("Example: python update_version.py 0.8.9")
        sys.exit(1)
    
    new_version = sys.argv[1]
    success = update_all_versions(new_version)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
