from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import APIView, Response
from users.models import Subscribe, User

from .pagination import CustomPaginator
from .serializers import (IngredientSerializer, RecipeSmallSerializer,
                          SetPasswordSerializer, SubscribeAuthorSerializer,
                          SubscriptionsSerializer, TagSerializer,
                          UserCreateSerializer, UserReadSerializer)


class SubscriptionsViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """Управление подписками"""

    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPaginator

    def get_queryset(self):
        return User.objects.filter(subscribing__user=self.request.user)

    def get_serializer_class(self):
        return SubscriptionsSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True,
                                         context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
    )
    def subscribe(self, request, **kwargs):
        author = get_object_or_404(User, id=kwargs['pk'])

        if request.method == 'POST':
            if Subscribe.objects.filter(user=request.user,
                                        author=author).exists():
                return Response({'detail': 'Подписка уже существует'},
                                status=status.HTTP_400_BAD_REQUEST)

            serializer = SubscribeAuthorSerializer(author, data=request.data,
                                                   context={'request':
                                                            request})
            serializer.is_valid(raise_exception=True)
            Subscribe.objects.create(user=request.user, author=author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            get_object_or_404(Subscribe, user=request.user,
                              author=author).delete()
            return Response({'detail': 'Отписка'},
                            status=status.HTTP_204_NO_CONTENT)


class UserViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Управление пользователями"""

    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    pagination_class = CustomPaginator

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return UserReadSerializer
        return UserCreateSerializer

    @action(
        detail=False,
        methods=['get'],
        pagination_class=None,
        permission_classes=(IsAuthenticated),
    )
    def me(self, request):
        serializer = UserReadSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=(IsAuthenticated),
    )
    def set_password(self, request):
        serializer = SetPasswordSerializer(request.user, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        return Response({'detail': 'Пароль изменен'},
                        status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,),
        pagination_class=CustomPaginator,
    )
    def subscriptions(self, request):
        return SubscriptionsViewSet.as_view({'get': 'list'})(request)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated),
    )
    def subscribe(self, request, **kwargs):
        return SubscriptionsViewSet.as_view({'post':
                                             'subscribe',
                                             'delete':
                                             'subscribe'})(request, **kwargs)


class TagViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Получение тэгов"""

    permission_classes = (AllowAny,)
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Получение ингредиентов"""

    queryset = Ingredient.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)


class FavoriteAPIView(APIView):
    """Вью сет для избранного"""

    permission_classes = (IsAuthenticated,)

    def post(self, request, recipe_id):
        """Метод для добавления в избранное"""
        recipe = get_object_or_404(Recipe, id=recipe_id)
        if Favorite.objects.filter(
                user=request.user, recipe=recipe).exists():
            return Response(
                {'error': 'Рецепт в избранном'},
                status=status.HTTP_400_BAD_REQUEST)
        favorite_recipe = Favorite.objects.create(
            user=request.user, recipe=recipe)
        serializer = RecipeSmallSerializer(favorite_recipe.recipe)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, recipe_id):
        recipe = get_object_or_404(Recipe, id=recipe_id)
        favorite_recipe = Favorite.objects.filter(
            user=request.user, recipe=recipe)
        if favorite_recipe.exists():
            favorite_recipe.delete()
            return Response({'message': 'Рецепт удален из избранного'},
                            status=status.HTTP_204_NO_CONTENT)
        return Response({'message': 'Рецепта не было в избранном'},
                        status=status.HTTP_400_BAD_REQUEST)


class ShoppingCartViewSet(APIView):
    """Управление списком покупок"""

    permission_classes = (IsAuthenticated,)

    def post(self, request, recipe_id):
        """Добавления в избранное"""
        recipe = get_object_or_404(Recipe, id=recipe_id)
        if ShoppingCart.objects.filter(
                user=request.user, recipe=recipe).exists():
            return Response(
                {'error': 'Вы уже добавили этот рецепт в корзину'},
                status=status.HTTP_400_BAD_REQUEST)
        recipe_in_cart = ShoppingCart.objects.create(
            user=request.user, recipe=recipe)
        serializer = RecipeSmallSerializer(recipe_in_cart.recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, recipe_id):
        """Удаления рецепта из списка покупок"""
        recipe_in_cart = ShoppingCart.objects.filter(
            user=request.user, recipe=recipe_id)
        if recipe_in_cart.exists():
            recipe_in_cart.delete()
            return Response({'message': 'Рецепт удален из корзины'},
                            status=status.HTTP_204_NO_CONTENT)
        return Response({'message': 'Рецепта не было в корзине'},
                        status=status.HTTP_400_BAD_REQUEST)


class ShoppingListDownloadView(APIView):
    """Загрузка списка покупок"""

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        ingredients = (
            RecipeIngredient.objects
            .filter(recipe__shopping_recipe__user=request.user)
            .values('ingredient')
            .annotate(total_amount=Sum('amount'))
            .values_list('ingredient__name', 'total_amount',
                         'ingredient__measurement_unit')
        )
        file_list = []
        FILE_NAME = 'shopping_cart.txt'
        [file_list.append('{} - {} {}.'.format(*ingredient))
            for ingredient in ingredients]
        file = HttpResponse('Cписок покупок:\n' + '\n'.join(file_list),
                            content_type='text/plain')
        file['Content-Disposition'] = (f'attachment; filename={FILE_NAME}')
        return file
