"""
Auto-update system for Smart File Organizer Pro
Checks GitHub releases for new versions and manages updates
"""
import requests
import logging
from datetime import datetime, timedelta
from pathlib import Path
import json
import sys

logger = logging.getLogger("FileOrganizer")

# Try to import version, fallback to defaults if not available
try:
    from app.version import APP_VERSION, UPDATE_CHECK_URL, ENABLE_AUTO_UPDATE_CHECK
except ImportError:
    APP_VERSION = "1.0.0"
    UPDATE_CHECK_URL = "https://api.github.com/repos/yourusername/smart-file-organizer/releases/latest"
    ENABLE_AUTO_UPDATE_CHECK = True
    logger.warning("Could not import app.version, using defaults")


class UpdateChecker:
    """
    Check for application updates from GitHub releases
    
    Usage:
        checker = UpdateChecker()
        if checker.check_for_updates():
            info = checker.get_update_info()
            print(f"New version available: {info['latest_version']}")
    """
    
    def __init__(self):
        self.current_version = APP_VERSION
        self.latest_version = None
        self.download_url = None
        self.release_notes = None
        self.release_date = None
        self.release_url = None
        self.update_cache_file = Path("update_cache.json")
    
    def should_check_for_updates(self):
        """
        Check if enough time has passed since last update check
        Returns: True if should check, False otherwise
        """
        if not ENABLE_AUTO_UPDATE_CHECK:
            logger.debug("Auto-update check is disabled")
            return False
        
        try:
            if self.update_cache_file.exists():
                with open(self.update_cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                    last_check_str = cache.get('last_check', '2000-01-01T00:00:00')
                    last_check = datetime.fromisoformat(last_check_str)
                    
                    # Check once per day
                    time_since_check = datetime.now() - last_check
                    if time_since_check < timedelta(days=1):
                        logger.debug(f"Update check skipped (last check: {time_since_check.seconds // 3600}h ago)")
                        return False
            
            logger.debug("Should check for updates")
            return True
            
        except Exception as e:
            logger.warning(f"Error reading update cache: {e}")
            return True
    
    def save_update_cache(self, update_available=False):
        """
        Save update check timestamp to cache file
        
        Args:
            update_available: Whether an update was found
        """
        try:
            cache = {
                'last_check': datetime.now().isoformat(),
                'update_available': update_available,
                'latest_version': self.latest_version,
                'current_version': self.current_version
            }
            
            with open(self.update_cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache, f, indent=2)
                
            logger.debug("Update cache saved")
            
        except Exception as e:
            logger.warning(f"Failed to save update cache: {e}")
    
    def check_for_updates(self, timeout=10):
        """
        Check if a new version is available on GitHub
        
        Args:
            timeout: Request timeout in seconds
            
        Returns:
            bool: True if update available, False otherwise
        """
        try:
            logger.info("Checking for updates...")
            
            # Make request to GitHub API
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': f'SmartFileOrganizer/{APP_VERSION}'
            }
            
            response = requests.get(
                UPDATE_CHECK_URL, 
                headers=headers, 
                timeout=timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Extract version information
            self.latest_version = data['tag_name'].lstrip('v')
            self.release_notes = data.get('body', 'No release notes available')
            self.release_date = data.get('published_at', '')
            self.release_url = data.get('html_url', '')
            
            # Find installer download URL
            self.download_url = None
            for asset in data.get('assets', []):
                asset_name = asset['name'].lower()
                # Look for Windows installer
                if asset_name.endswith('.exe') and 'setup' in asset_name:
                    self.download_url = asset['browser_download_url']
                    logger.debug(f"Found installer: {asset['name']}")
                    break
            
            # If no installer found, use release page URL
            if not self.download_url:
                self.download_url = self.release_url
                logger.debug("No installer asset found, using release page URL")
            
            # Compare versions
            comparison = self.compare_versions(self.latest_version, self.current_version)
            
            if comparison > 0:
                logger.info(f"Update available: v{self.latest_version} (current: v{self.current_version})")
                self.save_update_cache(update_available=True)
                return True
            elif comparison == 0:
                logger.info(f"Application is up to date (v{self.current_version})")
                self.save_update_cache(update_available=False)
                return False
            else:
                logger.info(f"Current version v{self.current_version} is newer than latest release v{self.latest_version}")
                self.save_update_cache(update_available=False)
                return False
                
        except requests.exceptions.Timeout:
            logger.error("Update check timed out")
            return False
            
        except requests.exceptions.ConnectionError:
            logger.error("Could not connect to update server (check internet connection)")
            return False
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error checking for updates: {e}")
            return False
            
        except KeyError as e:
            logger.error(f"Unexpected response format from GitHub API: {e}")
            return False
            
        except Exception as e:
            logger.error(f"Failed to check for updates: {e}", exc_info=True)
            return False
    
    def compare_versions(self, version1: str, version2: str) -> int:
        """
        Compare two version strings using semantic versioning
        
        Args:
            version1: First version string (e.g., "1.2.3")
            version2: Second version string (e.g., "1.2.0")
            
        Returns:
            int: 1 if version1 > version2
                 0 if version1 == version2
                -1 if version1 < version2
        """
        try:
            # Remove 'v' prefix if present
            v1 = version1.lstrip('v')
            v2 = version2.lstrip('v')
            
            # Split into parts
            v1_parts = [int(x) for x in v1.split('.')]
            v2_parts = [int(x) for x in v2.split('.')]
            
            # Pad with zeros to make equal length
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts += [0] * (max_len - len(v1_parts))
            v2_parts += [0] * (max_len - len(v2_parts))
            
            # Compare each part
            for i in range(max_len):
                if v1_parts[i] > v2_parts[i]:
                    return 1
                elif v1_parts[i] < v2_parts[i]:
                    return -1
            
            return 0
            
        except (ValueError, AttributeError) as e:
            logger.error(f"Error comparing versions '{version1}' and '{version2}': {e}")
            return 0
    
    def get_update_info(self):
        """
        Get information about available update
        
        Returns:
            dict: Update information including version, download URL, release notes
        """
        return {
            'current_version': self.current_version,
            'latest_version': self.latest_version,
            'download_url': self.download_url,
            'release_url': self.release_url,
            'release_notes': self.release_notes,
            'release_date': self.release_date,
            'is_newer': self.compare_versions(self.latest_version, self.current_version) > 0
        }
    
    def download_update(self, save_path: Path, progress_callback=None):
        """
        Download the update installer
        
        Args:
            save_path: Path where to save the installer
            progress_callback: Optional callback function(downloaded, total)
            
        Returns:
            bool: True if download successful, False otherwise
        """
        try:
            if not self.download_url:
                logger.error("No download URL available")
                return False
            
            # Check if URL is a release page (not direct download)
            if 'github.com' in self.download_url and '/releases/' in self.download_url:
                logger.info(f"Download URL is release page, opening in browser")
                import webbrowser
                webbrowser.open(self.download_url)
                return True
            
            logger.info(f"Downloading update from: {self.download_url}")
            
            # Create parent directory if it doesn't exist
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Download with progress
            response = requests.get(self.download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Call progress callback if provided
                        if progress_callback:
                            progress_callback(downloaded, total_size)
            
            logger.info(f"Update downloaded successfully: {save_path}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error downloading update: {e}")
            return False
            
        except IOError as e:
            logger.error(f"File error downloading update: {e}")
            return False
            
        except Exception as e:
            logger.error(f"Failed to download update: {e}", exc_info=True)
            return False
    
    def get_cached_update_info(self):
        """
        Get cached update information without checking online
        
        Returns:
            dict or None: Cached update info if available
        """
        try:
            if self.update_cache_file.exists():
                with open(self.update_cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.debug(f"Could not read update cache: {e}")
        
        return None
    
    def clear_update_cache(self):
        """Clear the update cache file"""
        try:
            if self.update_cache_file.exists():
                self.update_cache_file.unlink()
                logger.info("Update cache cleared")
        except Exception as e:
            logger.warning(f"Failed to clear update cache: {e}")


# Convenience function for quick update check
def check_for_updates():
    """
    Convenience function to quickly check for updates
    
    Returns:
        tuple: (update_available: bool, update_info: dict or None)
    """
    checker = UpdateChecker()
    
    if checker.check_for_updates():
        return True, checker.get_update_info()
    else:
        return False, None


# Test function
def test_update_checker():
    """Test the update checker functionality"""
    print("Testing Update Checker...")
    print(f"Current Version: {APP_VERSION}")
    print(f"Update URL: {UPDATE_CHECK_URL}")
    print()
    
    checker = UpdateChecker()
    
    print("Checking for updates...")
    if checker.check_for_updates():
        info = checker.get_update_info()
        print(f"\n✅ Update Available!")
        print(f"   Latest Version: {info['latest_version']}")
        print(f"   Download URL: {info['download_url']}")
        print(f"   Release Date: {info['release_date']}")
        print(f"\n   Release Notes:")
        print(f"   {info['release_notes'][:200]}...")
    else:
        print("\n✅ Application is up to date!")


if __name__ == "__main__":
    # Run test when executed directly
    test_update_checker()