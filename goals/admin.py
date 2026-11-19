from django.contrib import admin

from .models import Goal, GoalContribution


class ContributionInline(admin.TabularInline):
    model = GoalContribution
    extra = 0


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'target_amount', 'deadline')
    inlines = [ContributionInline]