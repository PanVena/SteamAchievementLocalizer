"""
CSV Handler Plugin for Steam Achievement Localizer
Handles CSV export and import functionality
"""
import csv
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path


class CSVHandler:
    """Handles CSV export and import operations"""
    
    def __init__(self):
        self.supported_encodings = ["utf-8-sig", "utf-8", "cp1251", "iso-8859-1"]
    
    def export_all_data(self, 
                       data_rows: List[Dict[str, str]], 
                       headers: List[str], 
                       filepath: str) -> bool:
        """Export all data to CSV file"""
        try:
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                for row in data_rows:
                    writer.writerow(row)
            return True
        except Exception as e:
            raise Exception(f"Failed to export CSV: {e}")
    
    def export_for_translation(self, 
                              data_rows: List[Dict[str, str]], 
                              context_column: str, 
                              filepath: str) -> bool:
        """Export data in translation-friendly format"""
        try:
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['key', 'english', 'translation', context_column])
                
                for row in data_rows:
                    writer.writerow([
                        row.get('key', ''),
                        row.get('english', ''),
                        row.get('ukrainian', ''),  # Default translation column
                        row.get(context_column, ''),
                    ])
            return True
        except Exception as e:
            raise Exception(f"Failed to export translation CSV: {e}")
    
    def import_translations(self, 
                           filepath: str, 
                           data_rows: List[Dict[str, str]], 
                           import_column: str) -> Tuple[bool, int, int, int, str]:
        """Import translations from CSV file
        
        Returns:
            Tuple of (success, imported_count, changed_count, skipped_count, reason)
        """
        try:
            # Try different encodings
            content = None
            for encoding in self.supported_encodings:
                try:
                    with open(filepath, 'r', encoding=encoding) as csvfile:
                        content = list(csv.reader(csvfile))
                        break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                return False, 0, 0, 0, "cannot_decode_csv"
            
            if not content:
                return False, 0, 0, 0, "error_empty"
            
            header = content[0]
            
            # Find required columns
            # Support both old format (ukrainian/russian/etc columns) and new format (translation column)
            try:
                key_idx = header.index('key')
            except ValueError:
                return False, 0, 0, 0, "error_no_key_column"
            
            # Try to find translation column (new format) or import_column directly (old format)
            translation_idx = None
            if 'translation' in header:
                translation_idx = header.index('translation')
            elif import_column in header:
                translation_idx = header.index(import_column)
            else:
                return False, 0, 0, 0, "error_no_translation_column"
            
            # Check if import_column exists in data_rows
            if data_rows and import_column not in data_rows[0]:
                return False, 0, 0, 0, "error_no_target_column"
            
            # Create mapping for fast lookup
            key_to_row = {row['key']: row for row in data_rows}
            imported_count = 0
            changed_count = 0
            skipped_count = 0
            
            for csv_row in content[1:]:  # Skip header
                if len(csv_row) <= max(key_idx, translation_idx):
                    skipped_count += 1
                    continue
                
                key = csv_row[key_idx].strip()
                translation = csv_row[translation_idx].strip()
                
                if not key:
                    skipped_count += 1
                    continue
                
                if key not in key_to_row:
                    skipped_count += 1
                    continue
                
                if not translation:
                    skipped_count += 1
                    continue
                
                # Check if value actually changed
                old_value = key_to_row[key].get(import_column, '')
                if old_value != translation:
                    key_to_row[key][import_column] = translation
                    changed_count += 1
                
                imported_count += 1
            
            reason = ""
            if changed_count == 0:
                if imported_count == 0:
                    reason = "reason_no_valid_translations"
                else:
                    reason = "reason_all_identical"
            
            return True, imported_count, changed_count, skipped_count, reason
            
        except Exception as e:
            return False, 0, 0, 0, "import_failed"
    
    def validate_csv_structure(self, filepath: str) -> Dict[str, Any]:
        """Validate CSV file structure and return info"""
        try:
            # Try to read with different encodings
            content = None
            used_encoding = None
            
            for encoding in self.supported_encodings:
                try:
                    with open(filepath, 'r', encoding=encoding) as csvfile:
                        content = list(csv.reader(csvfile))
                        used_encoding = encoding
                        break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                return {
                    'valid': False,
                    'error': 'Could not decode file with any supported encoding'
                }
            
            if not content:
                return {
                    'valid': False,
                    'error': 'File is empty'
                }
            
            header = content[0]
            row_count = len(content) - 1  # Exclude header
            
            return {
                'valid': True,
                'encoding': used_encoding,
                'columns': header,
                'row_count': row_count,
                'has_key_column': 'key' in header,
                'has_translation_column': 'translation' in header,
                'has_english_column': 'english' in header
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }
    
    def detect_delimiter(self, filepath: str, sample_size: int = 1024) -> str:
        """Auto-detect CSV delimiter"""
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as csvfile:
                sample = csvfile.read(sample_size)
                
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter
            return delimiter
            
        except Exception:
            return ','  # Default to comma
    
    def get_column_preview(self, 
                          filepath: str, 
                          max_rows: int = 10) -> Dict[str, Any]:
        """Get a preview of CSV columns and first few rows"""
        try:
            validation = self.validate_csv_structure(filepath)
            if not validation['valid']:
                return validation
            
            encoding = validation['encoding']
            
            with open(filepath, 'r', encoding=encoding) as csvfile:
                reader = csv.reader(csvfile)
                header = next(reader)
                
                preview_rows = []
                for i, row in enumerate(reader):
                    if i >= max_rows:
                        break
                    preview_rows.append(row)
            
            return {
                'valid': True,
                'header': header,
                'preview_rows': preview_rows,
                'total_rows': validation['row_count'],
                'encoding': encoding
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }
    
    def create_template_csv(self, 
                           headers: List[str], 
                           sample_data: Optional[List[Dict[str, str]]], 
                           filepath: str) -> bool:
        """Create a template CSV file for translations"""
        try:
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                
                if sample_data:
                    # Add a few sample rows
                    for i, row in enumerate(sample_data[:5]):  # Max 5 sample rows
                        sample_row = {}
                        for header in headers:
                            if header == 'translation':
                                sample_row[header] = f'[Translation for {row.get("key", f"item_{i}")}]'
                            else:
                                sample_row[header] = row.get(header, '')
                        writer.writerow(sample_row)
            
            return True
            
        except Exception as e:
            raise Exception(f"Failed to create template CSV: {e}")
    
    def merge_csv_files(self, 
                       primary_file: str, 
                       secondary_file: str, 
                       output_file: str, 
                       merge_column: str = 'key') -> bool:
        """Merge two CSV files based on a common column"""
        try:
            # Read primary file
            primary_data = {}
            primary_validation = self.validate_csv_structure(primary_file)
            if not primary_validation['valid']:
                raise Exception(f"Primary file invalid: {primary_validation['error']}")
            
            with open(primary_file, 'r', encoding=primary_validation['encoding']) as f:
                reader = csv.DictReader(f)
                primary_headers = reader.fieldnames
                for row in reader:
                    key_value = row.get(merge_column)
                    if key_value:
                        primary_data[key_value] = row
            
            # Read secondary file
            secondary_validation = self.validate_csv_structure(secondary_file)
            if not secondary_validation['valid']:
                raise Exception(f"Secondary file invalid: {secondary_validation['error']}")
            
            with open(secondary_file, 'r', encoding=secondary_validation['encoding']) as f:
                reader = csv.DictReader(f)
                secondary_headers = reader.fieldnames
                
                # Merge headers (primary first, then new from secondary)
                all_headers = list(primary_headers)
                for header in secondary_headers:
                    if header not in all_headers:
                        all_headers.append(header)
                
                # Update primary data with secondary data
                for row in reader:
                    key_value = row.get(merge_column)
                    if key_value and key_value in primary_data:
                        primary_data[key_value].update(row)
                    elif key_value:
                        # Add new row from secondary file
                        primary_data[key_value] = row
            
            # Write merged file
            with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=all_headers)
                writer.writeheader()
                for row in primary_data.values():
                    writer.writerow(row)
            
            return True
            
        except Exception as e:
            raise Exception(f"Failed to merge CSV files: {e}")