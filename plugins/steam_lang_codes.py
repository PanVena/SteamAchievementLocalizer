"""
Steam Language Codes Mapping
Simple display names for Steam language codes in table headers
"""

# Steam's standard language codes with display names
STEAM_LANGUAGE_CODES = {
    'arabic': 'Arabic (العربية)',
    'bulgarian': 'Bulgarian (български)',
    'czech': 'Czech (čeština)',
    'danish': 'Danish (Dansk)',
    'dutch': 'Dutch (Nederlands)',
    'english': 'English',
    'finnish': 'Finnish (Suomi)',
    'french': 'French (Français)',
    'german': 'German (Deutsch)',
    'greek': 'Greek (Ελληνικά)',
    'hungarian': 'Hungarian (Magyar)',
    'indonesian': 'Indonesian (Bahasa Indonesia)',
    'italian': 'Italian (Italiano)',
    'japanese': 'Japanese (日本語)',
    'koreana': 'Korean (한국어)',
    'norwegian': 'Norwegian (Norsk)',
    'polish': 'Polish (Polski)',
    'portuguese': 'Portuguese (Português)',
    'brazilian': 'Portuguese - Brazil (Português-Brasil)',
    'romanian': 'Romanian (Română)',
    'spanish': 'Spanish (Español-España)',
    'latam': 'Spanish - Latin America (Español-Latinoamérica)',
    'swedish': 'Swedish (Svenska)',
    'thai': 'Thai (ไทย)',
    'turkish': 'Turkish (Türkçe)',
    'ukrainian': 'Ukrainian (Українська)',
    'vietnamese': 'Vietnamese (Tiếng Việt)'
}

def get_display_name(steam_code: str) -> str:
    """Get display name for Steam language code"""
    return STEAM_LANGUAGE_CODES.get(steam_code, steam_code.title())

def get_code_from_display_name(display_name: str) -> str:
    """Get Steam language code from display name"""
    for code, display in STEAM_LANGUAGE_CODES.items():
        if display == display_name:
            return code
    return display_name.lower()  # Fallback

def get_available_languages_for_selection() -> list:
    """
    Get list of available Steam languages for selection, 
    sorted by display name
    """
    languages = [(code, display) for code, display in STEAM_LANGUAGE_CODES.items()]
    languages.sort(key=lambda x: x[1])  # Sort by display name
    
    return [code for code, _ in languages]