from rest_framework.routers import SimpleRouter

from .views import BudgetViewSet

router = SimpleRouter()
router.register('', BudgetViewSet, basename='budget')

urlpatterns = router.urls