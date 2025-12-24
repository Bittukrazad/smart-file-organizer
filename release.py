# ============================================
# FILE 4: release.py
# Automated build and release script
# ============================================

"""
Automated build and release script for Smart File Organizer Pro
Usage: python release.py [version]
"""
import subprocess
import sys
import os
from pathlib import Path

# Import version
sys.path.insert(0, str(Path(__file__).parent))
from app.version import APP_VERSION


def run_command(cmd, description, shell=True, env=None):
    """Run command and handle errors"""
    print(f"\n{'='*70}")
    print(f"  {description}")
    print(f"{'='*70}")
    
    result = subprocess.run(
        cmd,
        shell=shell,
        capture_output=True,
        text=True,
        env=env
    )
    
    if result.stdout:
        print(result.stdout)
    
    if result.returncode != 0:
        print(f"\n❌ ERROR: {description} failed!")
        if result.stderr:
            print(result.stderr)
        sys.exit(1)
    
    print(f"✅ {description} completed successfully")
    return result


def check_prerequisites():
    """Check if required tools are installed"""
    print("\n🔍 Checking prerequisites...")
    
    # Check PyInstaller
    try:
        subprocess.run(['pyinstaller', '--version'], capture_output=True, check=True)
        print("✅ PyInstaller found")
    except:
        print("❌ PyInstaller not found. Installing...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)
    
    # Check Inno Setup
    inno_path = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    if not Path(inno_path).exists():
        print("❌ Inno Setup not found!")
        print("   Download from: https://jrsoftware.org/isdl.php")
        sys.exit(1)
    else:
        print("✅ Inno Setup found")
    
    return inno_path


def clean_build():
    """Clean previous build artifacts"""
    print("\n🧹 Cleaning previous builds...")
    
    dirs_to_clean = ['build', 'dist', '__pycache__']
    
    for dir_name in dirs_to_clean:
        dir_path = Path(dir_name)
        if dir_path.exists():
            import shutil
            shutil.rmtree(dir_path)
            print(f"   Removed: {dir_name}/")
    
    print("✅ Cleanup complete")


def build_exe():
    """Build EXE with PyInstaller"""
    run_command(
        'pyinstaller build_exe.spec --clean --noconfirm',
        'Building EXE with PyInstaller'
    )

    # Verify EXE was created (ROBUST CHECK)
    dist_dir = Path('dist')
    exe_files = list(dist_dir.rglob('*.exe'))

    if not exe_files:
        print("❌ No EXE found in dist folder!")
        sys.exit(1)

    exe_path = exe_files[0]
    exe_size = exe_path.stat().st_size / (1024 * 1024)
    print(f"   EXE created: {exe_path}")
    print(f"   EXE size: {exe_size:.2f} MB")


def build_installer(inno_path):
    """Build installer with Inno Setup"""
    env = os.environ.copy()
    env["APP_VERSION"] = APP_VERSION  

    run_command(
        f'"{inno_path}" installer.iss',
        'Building Installer with Inno Setup',
        env=env
    )

    
    # Verify installer was created
    installer_pattern = f"SmartFileOrganizer_Setup_v{APP_VERSION}.exe"
    installer_path = Path('release') / installer_pattern
    
    if not installer_path.exists():
        print(f"❌ Installer not found: {installer_path}")
        sys.exit(1)
    
    installer_size = installer_path.stat().st_size / (1024 * 1024)
    print(f"   Installer size: {installer_size:.2f} MB")
    print(f"   Location: {installer_path}")


def create_portable_zip():
    """Create portable ZIP version"""
    import shutil
    
    print("\n📦 Creating portable ZIP...")
    
    zip_name = f"SmartFileOrganizer_Portable_v{APP_VERSION}"
    dist_folder = Path('dist/SmartFileOrganizer')
    
    if dist_folder.exists():
        shutil.make_archive(
            f'release/{zip_name}',
            'zip',
            'dist',
            'SmartFileOrganizer'
        )
        
        zip_path = Path(f'release/{zip_name}.zip')
        if zip_path.exists():
            zip_size = zip_path.stat().st_size / (1024 * 1024)
            print(f"✅ Portable ZIP created: {zip_size:.2f} MB")
        else:
            print("⚠️ Failed to create ZIP")
    else:
        print("⚠️ Distribution folder not found, skipping ZIP creation")


def print_summary():
    """Print build summary"""
    print("\n" + "="*70)
    print("  🎉 BUILD COMPLETE!")
    print("="*70)
    print(f"\nVersion: {APP_VERSION}")
    print(f"\nOutput files:")
    print(f"  📦 Installer: release/SmartFileOrganizer_Setup_v{APP_VERSION}.exe")
    print(f"  📁 Portable:  release/SmartFileOrganizer_Portable_v{APP_VERSION}.zip")
    print(f"\n✅ Next steps:")
    print(f"  1. Test the installer")
    print(f"  2. git add . && git commit -m 'Release v{APP_VERSION}'")
    print(f"  3. git tag -a v{APP_VERSION} -m 'Version {APP_VERSION}'")
    print(f"  4. git push origin main && git push origin v{APP_VERSION}")
    print(f"  5. Create GitHub release and upload installer")
    print()


def main():
    """Main build process"""
    print("\n" + "="*70)
    print("  Smart File Organizer Pro - Automated Build Script")
    print("="*70)
    Path("release").mkdir(exist_ok=True)  # 🔒 REQUIRED
    print(f"\n📦 Building version: {APP_VERSION}\n")

    
    try:
        # Run build steps
        inno_path = check_prerequisites()
        clean_build()
        build_exe()
        build_installer(inno_path)
        create_portable_zip()
        print_summary()
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Build cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Build failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

