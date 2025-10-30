from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views import View

from sbomify.apps.core.apis import get_project
from sbomify.apps.core.errors import error_response
from sbomify.apps.sboms.models import SBOM


class ProjectDetailsPublicView(View):
    def get(self, request: HttpRequest, project_id: str) -> HttpResponse:
        status_code, project = get_project(request, project_id)
        if status_code != 200:
            return error_response(
                request, HttpResponse(status=status_code, content=project.get("detail", "Unknown error"))
            )

        has_downloadable_content = SBOM.objects.filter(component__projects=project["id"]).exists()
        current_team = request.session.get("current_team", {})
        brand = current_team.get("branding_info")

        return render(
            request,
            "core/project_details_public.html.j2",
            {
                "project": project,
                "brand": brand,
                "has_downloadable_content": has_downloadable_content,
            },
        )
