# sitemaps.py
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'daily'

    def items(self):
        return ['home_page_app:home', 'home_page_app:about', 'home_page_app:contact', 'home_page_app:membership', 'home_page_app:faqs']

    def location(self, item):
        return reverse(item)
