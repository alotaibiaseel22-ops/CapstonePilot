from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities import Recommendation


class RecommendationRepository(ABC):
    @abstractmethod
    def create(self, recommendation: Recommendation) -> Recommendation: ...

    @abstractmethod
    def list_by_project(self, project_id: UUID) -> list[Recommendation]: ...

    @abstractmethod
    def get_by_id(self, recommendation_id: UUID) -> Recommendation | None: ...

    @abstractmethod
    def update(self, recommendation: Recommendation) -> Recommendation: ...

    @abstractmethod
    def delete_by_project(self, project_id: UUID) -> None: ...
