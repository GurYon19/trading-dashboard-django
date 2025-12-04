"""
Context processors to make data available to all templates.
"""
from django.conf import settings
from .services.data_loader import find_instruments


def instruments_processor(request):
    """Make instrument list available to all templates."""
    try:
        instruments_dict = find_instruments(settings.CSV_FOLDER_PATH)
        instrument_names = sorted(list(instruments_dict.keys()))
    except:
        instrument_names = []
    
    return {
        'all_instruments': instrument_names
    }
