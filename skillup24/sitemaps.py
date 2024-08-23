# sitemaps.py
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'daily'

    def items(self):
        return ['home_page_app:home', 'home_page_app:about', 'home_page_app:instructor_list', 'home_page_app:event_list', 'home_page_app:course_list']

    def location(self, item):
        return reverse(item)
