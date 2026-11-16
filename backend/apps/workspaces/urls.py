from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    WorkspaceMemberDetailAPIView,
    WorkspaceMemberListCreateAPIView,
    WorkspaceOwnershipTransferAPIView,
    WorkspaceViewSet,
)

router = DefaultRouter()
router.register(
    "workspaces",
    WorkspaceViewSet,
    basename="workspace",
)

urlpatterns = [
    path(
        "workspaces/<int:workspace_id>/miembros/",
        WorkspaceMemberListCreateAPIView.as_view(),
        name="workspace-members",
    ),
    path(
        "workspaces/<int:workspace_id>/miembros/<int:membership_id>/",
        WorkspaceMemberDetailAPIView.as_view(),
        name="workspace-member-detail",
    ),
    path(
        "workspaces/<int:workspace_id>/transferir-propiedad/",
        WorkspaceOwnershipTransferAPIView.as_view(),
        name="workspace-transfer-ownership",
    ),
] + router.urls
