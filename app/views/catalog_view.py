"""Versioned, read-only catalog endpoints."""

from functools import lru_cache
from pathlib import Path

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from app.catalog_repository import (
    CatalogIntegrityError,
    CatalogNotFound,
    CatalogRepository,
)


@lru_cache(maxsize=4)
def _repository(root: str) -> CatalogRepository:
    return CatalogRepository(Path(root))


def configured_repository() -> CatalogRepository:
    root = getattr(settings, "UWPATH_CATALOG_ROOT", None)
    if not root:
        raise CatalogIntegrityError("UWPATH_CATALOG_ROOT is not configured")
    return _repository(root)


def active_year(repository: CatalogRepository, requested_year: str) -> str:
    preferred_year = getattr(settings, "UWPATH_ACTIVE_ACADEMIC_YEAR", None)
    return repository.resolve_year(requested_year, preferred_year)


def error_response(error: Exception) -> Response:
    if isinstance(error, CatalogNotFound):
        response_status = status.HTTP_404_NOT_FOUND
        code = "catalog_not_found"
    else:
        response_status = status.HTTP_503_SERVICE_UNAVAILABLE
        code = "catalog_unavailable"
    return Response(
        {"error": {"code": code, "message": str(error)}}, status=response_status
    )


def catalog_response(request, snapshot, payload) -> Response:
    if request.headers.get("If-None-Match") == snapshot.etag:
        response = Response(status=status.HTTP_304_NOT_MODIFIED)
    else:
        response = Response(payload)
    response["ETag"] = snapshot.etag
    response["Cache-Control"] = "public, max-age=300"
    return response


class CatalogList(APIView):
    def get(self, request, format=None):
        try:
            repository = configured_repository()
            years = repository.available_years()
            preferred_year = getattr(settings, "UWPATH_ACTIVE_ACADEMIC_YEAR", None)
            resolved_active_year = (
                repository.resolve_year("active", preferred_year) if years else None
            )
            catalogs = [repository.load(year).metadata for year in years]
            return Response(
                {
                    "active_academic_year": resolved_active_year,
                    "catalogs": catalogs,
                }
            )
        except (CatalogIntegrityError, CatalogNotFound) as error:
            return error_response(error)


class CatalogDetail(APIView):
    def get(self, request, academic_year, format=None):
        try:
            repository = configured_repository()
            year = active_year(repository, academic_year)
            snapshot = repository.load(year)
            return catalog_response(request, snapshot, snapshot.metadata)
        except (CatalogIntegrityError, CatalogNotFound) as error:
            return error_response(error)


class CatalogCourses(APIView):
    def get(self, request, academic_year, format=None):
        try:
            repository = configured_repository()
            year = active_year(repository, academic_year)
            snapshot = repository.load(year)
            return catalog_response(
                request,
                snapshot,
                {
                    "academic_year": year,
                    "schema_version": snapshot.manifest["schema_version"],
                    "courses": snapshot.courses,
                },
            )
        except (CatalogIntegrityError, CatalogNotFound) as error:
            return error_response(error)


class CatalogPrograms(APIView):
    def get(self, request, academic_year, format=None):
        try:
            repository = configured_repository()
            year = active_year(repository, academic_year)
            snapshot = repository.load(year)
            return catalog_response(
                request,
                snapshot,
                {
                    "academic_year": year,
                    "schema_version": snapshot.manifest["schema_version"],
                    "programs": snapshot.programs,
                },
            )
        except (CatalogIntegrityError, CatalogNotFound) as error:
            return error_response(error)
