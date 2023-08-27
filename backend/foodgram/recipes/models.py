from django.conf import settings
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from users.models import User


class Ingredient(models.Model):
    """Ингридиенты"""
    name = models.CharField(max_length=settings.MAX_LENGTH)
    measurement_unit = models.CharField(max_length=settings.MAX_LENGTH)

    class Meta:
        ordering = ['name']
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Tag(models.Model):
    """Тэг"""
    name = models.CharField(max_length=settings.MAX_LENGTH)
    color = models.CharField(
        max_length=7,
        null=True,
        validators=[
            RegexValidator(
                '^#([a-fA-F0-9]{6})',
                message='Введите значение цвета в формате HEX!',
            ),
        ],
    )
    slug = models.SlugField(max_length=settings.MAX_LENGTH,
                            unique=True, null=True)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Рецепты"""
    name = models.CharField(max_length=settings.MAX_LENGTH)
    text = models.TextField()
    cooking_time = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)])
    image = models.ImageField(upload_to='recipes/', blank=True)
    pub_date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        through_fields=('recipe', 'ingredient'),
        verbose_name='Ингредиенты',
    )
    tags = models.ManyToManyField(Tag, verbose_name='Теги')

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class Favorite(models.Model):
    """Избранное"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite_user',
        verbose_name='Добавил в избранное',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite_recipe',
        verbose_name='Избранный рецепт',
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite',
            ),
        ]


class RecipeIngredient(models.Model):
    """Ингридиенты в рецепте"""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredients',
        verbose_name='Ингредиент',
    )
    amount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)])

    class Meta:
        verbose_name = 'Ингредиенты в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_combination',
            ),
        ]

    def __str__(self):
        return f'{self.recipe.name}: {self.ingredient.name}'
        f'- {self.amount} {self.ingredient.measurement_unit}'


class ShoppingCart(models.Model):
    """Корзина рецептов"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_user',
        verbose_name='Добавил в корзину',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_recipe',
        verbose_name='Рецепт в корзине',
    )

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзина'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart',
            ),
        ]

    def __str__(self):
        return f'{self.user.username} в рецепте {self.recipe.name}'