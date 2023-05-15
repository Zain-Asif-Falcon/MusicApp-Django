from re import search

import django_filters

from .models import Media


class MediaFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='stage_name', lookup_expr='icontains')
    song_name = django_filters.CharFilter(field_name='song_name', lookup_expr='icontains')
