"""
File Manager Plugin for Steam Achievement Localizer
Handles file operations, binary data manipulation and file I/O
"""
import os
import json
import re
from typing import List, Dict, Optional, Union, Any
from .binary_parser import BinaryParser


class FileManager:
    """Handles file operations and binary data manipulation"""
    
    def __init__(self):
        self.binary_parser = BinaryParser()
        self.current_file_path: Optional[str] = None
        self.raw_data: bytes = b""
    
    def load_binary_file(self, filepath: str) -> bytes:
        """Load binary file and return raw data"""
        try:
            with open(filepath, "rb") as f:
                data = f.read()
            self.current_file_path = filepath
            self.raw_data = data
            return data
        except Exception as e:
            raise Exception(f"Failed to load binary file: {e}")
    
    def save_binary_file(self, data: bytes, filepath: str) -> bool:
        """Save binary data to file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, "wb") as f:
                f.write(data)
            return True
        except Exception as e:
            raise Exception(f"Failed to save binary file: {e}")
    
    def load_json_with_fallback(self, filepath: str) -> Dict[str, Any]:
        """Load JSON file with encoding fallback"""
        encodings = ["utf-8-sig", "utf-8", "cp1251"]
        
        for encoding in encodings:
            try:
                with open(filepath, "r", encoding=encoding) as f:
                    return json.load(f)
            except Exception:
                continue
        
        raise Exception(f"Cannot decode JSON file: {filepath}")
    
    def get_resource_path(self, relative_path: str) -> str:
        """Get correct path to resources for both .py and .exe"""
        import sys
        
        if getattr(sys, 'frozen', False):
            # Running as bundled exe
            base_path = sys._MEIPASS if hasattr(sys, "_MEIPASS") else os.path.dirname(sys.executable)
        else:
            # Running as normal .py file
            base_path = os.path.dirname(os.path.dirname(__file__))  # Go up from plugins/
        
        return os.path.join(base_path, relative_path)
    
    def parse_binary_data(self, data: bytes) -> tuple:
        """Parse binary data using binary parser"""
        return self.binary_parser.parse_binary_data(data)
    
    def replace_language_in_binary(self, 
                                  data: bytes, 
                                  data_rows: List[Dict[str, str]]) -> bytes:
        """Replace language data in binary format"""
        try:
            lang_columns = [col for col in data_rows[0].keys() if col != "key"]
            cleaned = bytearray(data)
            
            for selected_column in lang_columns:
                values = [row.get(selected_column, '') for row in data_rows]
                
                if selected_column == "english":
                    cleaned = self._replace_english_values(cleaned, values)
                else:
                    cleaned = self._replace_language_values(cleaned, selected_column, values)
            
            return bytes(cleaned)
            
        except Exception as e:
            raise Exception(f"Failed to replace language in binary: {e}")
    
    def _replace_english_values(self, data: bytearray, values: List[str]) -> bytearray:
        """Replace English values in binary data"""
        english_marker = b'\x01english\x00'
        output = bytearray()
        i = 0
        v_idx = 0
        
        while i < len(data):
            idx = data.find(english_marker, i)
            if idx == -1:
                output.extend(data[i:])
                break
                
            output.extend(data[i:idx + len(english_marker)])
            i = idx + len(english_marker)
            
            end = data.find(b'\x00', i)
            if end == -1:
                break
            
            if v_idx < len(values):
                val = values[v_idx]
                output.extend(val.encode("utf-8"))
            
            output.extend(b'\x00')
            i = end + 1
            v_idx += 1
        
        return output
    
    def _replace_language_values(self, 
                                data: bytearray, 
                                language: str, 
                                values: List[str]) -> bytearray:
        """Replace specific language values in binary data"""
        # Delete old markers of this language
        marker = b'\x01' + language.encode("utf-8") + b'\x00'
        new_cleaned = bytearray()
        i = 0
        
        while i < len(data):
            idx = data.find(marker, i)
            if idx == -1:
                new_cleaned.extend(data[i:])
                break
                
            new_cleaned.extend(data[i:idx])
            i = idx + len(marker)
            
            end = data.find(b'\x00', i)
            if end == -1:
                break
            i = end + 1
        
        cleaned = new_cleaned
        
        # Insert new markers and values
        english_marker = b'\x01english\x00'
        output = bytearray()
        i = 0
        v_idx = 0
        
        while i < len(cleaned):
            idx = cleaned.find(english_marker, i)
            if idx == -1:
                output.extend(cleaned[i:])
                break
                
            output.extend(cleaned[i:idx])
            
            # Insert new marker if there is a value
            if v_idx < len(values):
                val = values[v_idx]
                if val:
                    output.extend(b'\x01' + language.encode("utf-8") + b'\x00' + 
                                val.encode("utf-8") + b'\x00')
            
            output.extend(english_marker)
            i = idx + len(english_marker)
            
            end = cleaned.find(b'\x00', i)
            if end == -1:
                break
                
            output.extend(cleaned[i:end+1])
            i = end + 1
            v_idx += 1
        
        return output
    
    def extract_game_metadata(self, data: bytes) -> Dict[str, Optional[Union[str, int]]]:
        """Extract game metadata (version, name) from binary data"""
        metadata = {}
        
        # Extract version
        version = self.binary_parser.get_version(data)
        metadata['version'] = version
        
        # Extract game name
        gamename = self.binary_parser.get_gamename(data)
        metadata['gamename'] = gamename
        
        return metadata
    
    def backup_file(self, filepath: str, backup_suffix: str = ".backup") -> str:
        """Create a backup of the file"""
        backup_path = filepath + backup_suffix
        counter = 1
        
        # Find unique backup name
        while os.path.exists(backup_path):
            backup_path = f"{filepath}{backup_suffix}.{counter}"
            counter += 1
        
        try:
            import shutil
            shutil.copy2(filepath, backup_path)
            return backup_path
        except Exception as e:
            raise Exception(f"Failed to create backup: {e}")
    
    def validate_binary_file(self, filepath: str) -> Dict[str, Any]:
        """Validate if file is a proper Steam stats binary file"""
        try:
            if not os.path.exists(filepath):
                return {'valid': False, 'error': 'File does not exist'}
            
            # Check file extension
            if not filepath.lower().endswith('.bin'):
                return {'valid': False, 'error': 'File is not a .bin file'}
            
            # Check if it's a UserGameStatsSchema file
            filename = os.path.basename(filepath)
            if not re.match(r'UserGameStatsSchema_\d+\.bin$', filename):
                return {
                    'valid': False, 
                    'error': 'File is not a UserGameStatsSchema file'
                }
            
            # Try to load and parse
            data = self.load_binary_file(filepath)
            
            # Check for basic Steam binary markers
            if b'\x01english\x00' not in data:
                return {
                    'valid': False, 
                    'error': 'File does not contain expected Steam data markers'
                }
            
            # Try to parse
            rows, headers = self.parse_binary_data(data)
            
            return {
                'valid': True,
                'file_size': len(data),
                'achievement_count': len([r for r in rows if not r['key'].endswith('_opis')]),
                'languages': [h for h in headers if h not in ['key']],
                'metadata': self.extract_game_metadata(data)
            }
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    def get_file_info(self, filepath: str) -> Dict[str, Any]:
        """Get comprehensive file information"""
        try:
            if not os.path.exists(filepath):
                return {'exists': False}
            
            stat = os.stat(filepath)
            
            info = {
                'exists': True,
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'created': stat.st_ctime,
                'extension': os.path.splitext(filepath)[1],
                'basename': os.path.basename(filepath),
                'dirname': os.path.dirname(filepath)
            }
            
            # If it's a binary file, add validation info
            if filepath.lower().endswith('.bin'):
                validation = self.validate_binary_file(filepath)
                info.update(validation)
            
            return info
            
        except Exception as e:
            return {'exists': False, 'error': str(e)}
    
    def cleanup_temp_files(self, directory: str, pattern: str = "*.tmp") -> int:
        """Clean up temporary files in directory"""
        import glob
        
        try:
            temp_files = glob.glob(os.path.join(directory, pattern))
            cleaned_count = 0
            
            for temp_file in temp_files:
                try:
                    os.remove(temp_file)
                    cleaned_count += 1
                except Exception:
                    continue
            
            return cleaned_count
            
        except Exception:
            return 0