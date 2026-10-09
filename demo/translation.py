from modeltranslation.translator import TranslationOptions, register

from demo.models import Category, Product, Tag
from demo.models.catalog import PRODUCT_TRANSLATED_FIELDS


@register(Category)
class CategoryTranslation(TranslationOptions):
    fields = ["name", "description"]


@register(Tag)
class TagTranslation(TranslationOptions):
    fields = ["name", "description"]


@register(Product)
class ProductTranslation(TranslationOptions):
    fields = PRODUCT_TRANSLATED_FIELDS
