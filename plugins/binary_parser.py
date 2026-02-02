"""
Binary Parser Plugin for Steam Achievement Localizer
Handles parsing and manipulation of Steam binary files
"""
import re
from typing import List, Dict, Optional, Tuple, Union


class BinaryParser:
    """Handles parsing of Steam binary achievement files"""
    
    EXCLUDE_WORDS = {
        b'max', b'maxchange', b'min', b'token', b'name', b'hidden', 
        b'icon_gray', b'Hidden', b'', b'russian', b'Default', b'gamename', 
        b'id', b'incrementonly', b'max_val', b'min_val', b'operand1', 
        b'operation', b'type', b'version', b'schinese', b'tchinese'
    }
    
    def __init__(self):
        self.chunks: List[bytes] = []
        self.raw_data: bytes = b""
    
    def split_chunks(self, data: bytes) -> List[bytes]:
        """Split binary data into chunks based on Steam format patterns"""
        pattern = re.compile(b'\x00bits\x00|\x02bit\x00|(?:^|\x00)[0-9]+\x00')
        positions = [m.start() for m in pattern.finditer(data)]
        
        chunks = []
        for i in range(len(positions)):
            start = positions[i]
            end = positions[i + 1] if i + 1 < len(positions) else len(data)
            chunks.append(data[start:end])
        
        return chunks
    
    def extract_key_and_data(self, chunk: bytes) -> Optional[str]:
        """Extract key from binary chunk"""
        key_pattern = re.compile(b'\x00\x01name\x00(.*?)\x00', re.DOTALL)
        key_match = key_pattern.search(chunk)
        
        if not key_match:
            return None
        
        # Skip chunks without english field
        if b'\x01english\x00' not in chunk:
            return None
            
        return key_match.group(1).decode(errors='ignore')
    
    def extract_words(self, chunk: bytes) -> List[str]:
        """Extract words from binary chunk, filtering out excluded words"""
        pattern = re.compile(b'\x01(.*?)\x00', re.DOTALL)
        matches = pattern.findall(chunk)
        
        words = []
        for word in matches:
            if word in self.EXCLUDE_WORDS:
                continue
            words.append(word.decode(errors='ignore'))
        
        return words
    
    def extract_values(self, chunk: bytes, words: List[str]) -> List[str]:
        """Extract values corresponding to words from binary chunk"""
        values = []
        pos = 0
        
        for word in words:
            search_pattern = b'\x01' + word.encode() + b'\x00'
            idx = chunk.find(search_pattern, pos)
            
            if idx == -1:
                values.append('')
                continue
                
            idx += len(search_pattern)
            end_idx = chunk.find(b'\x00', idx)
            
            if end_idx == -1:
                values.append('')
                pos = idx
                continue
                
            val = chunk[idx:end_idx].decode(errors='ignore')
            values.append(val)
            pos = end_idx + 1
        
        return values
    
    def parse_binary_data(self, data: bytes) -> Tuple[List[Dict[str, str]], List[str]]:
        """Parse binary data and return rows and headers"""
        self.raw_data = data
        chunks = self.split_chunks(data)
        self.chunks = chunks
        
        all_rows = []
        all_columns = set()
        
        for chunk in chunks:
            key = self.extract_key_and_data(chunk)
            if not key:
                continue
                
            words = self.extract_words(chunk)
            values = self.extract_values(chunk, words)
            
            word_counts = {}
            unique_row = {'key': key}
            description_row = {'key': f'{key}_opis'}
            
            for word, val in zip(words, values):
                count = word_counts.get(word, 0)
                if count == 0:
                    unique_row[word] = val
                else:
                    if word in description_row:
                        description_row[word] += '; ' + val
                    else:
                        description_row[word] = val
                word_counts[word] = count + 1
            
            all_rows.append(unique_row)
            if len(description_row) > 1:
                all_rows.append(description_row)
            
            for row in [unique_row, description_row]:
                for col in row.keys():
                    if col != 'key':
                        all_columns.add(col)
        
        # Ensure english column exists (always needed as base language)
        for row in all_rows:
            if 'english' not in row:
                row['english'] = ''
        
        # Define headers - icon first (if exists), then key, then other columns sorted
        all_columns = set()
        for row in all_rows:
            for col in row:
                if col not in ['key', 'icon']:
                    all_columns.add(col)
        
        # Check if any row has icon data
        has_icons = any('icon' in row for row in all_rows)
        
        # Build headers: icon (if exists) -> key -> sorted other columns
        if has_icons:
            headers = ['icon', 'key'] + sorted(all_columns)
        else:
            headers = ['key'] + sorted(all_columns)
        
        return all_rows, headers
    
    def extract_metadata(self, data: bytes, marker: str) -> Optional[str]:
        """Extract metadata (version, gamename) from binary data"""
        try:
            marker_bytes = f"\x01{marker}\x00".encode()
            pos = data.find(marker_bytes)
            
            if pos == -1:
                return None
            
            start = pos + len(marker_bytes)
            end = data.find(b"\x00", start)
            
            if end == -1:
                return None
            
            result = data[start:end].decode("utf-8", errors="ignore").strip()
            return result if result else None
            
        except Exception:
            return None
    
    def get_version(self, data: bytes) -> Optional[Union[int, str]]:
        """Extract version from binary data"""
        version_str = self.extract_metadata(data, "version")
        if version_str is None:
            return None
        
        try:
            return int(version_str)
        except ValueError:
            return version_str
    
    def get_gamename(self, data: bytes) -> Optional[str]:
        """Extract game name from binary data"""
        return self.extract_metadata(data, "gamename")

    def get_achievement_count(self, data: bytes) -> int:
        """Count achievements in binary data"""
        chunks = self.split_chunks(data)
        return sum(1 for chunk in chunks if b'\x01english\x00' in chunk and chunk.count(b'\x01english\x00') >= 2)