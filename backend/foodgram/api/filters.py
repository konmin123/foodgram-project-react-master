from django_filters.rest_framework import FilterSet, filters
from recipes.models import Recipe, Tag


class RecipeFilter(FilterSet):
    """Фильтр по полям рецептов"""

    tags = filters.ModelMultipleChoiceFilter(field_name='tags__slug',
                                             to_field_name='slug',
                                             queryset=Tag.objects.all())
    is_in_shopping_cart = filters.BooleanFilter(
        method='is_in_shopping_cart_filter')
    is_favorited = filters.BooleanFilter(
        method='is_favorited_filter')

    class Meta:
        model = Recipe
        fields = ('tags', 'author')

    def is_in_shopping_cart_filter(queryset, self, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(shopping_recipe__user=user)
        return queryset

    def is_favorited_filter(queryset, self, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorite_recipe__user=user)
        return queryset
