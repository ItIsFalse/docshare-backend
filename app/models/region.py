from sqlalchemy import Column, Integer, String, Boolean
from ..core.database import Base


class Region(Base):
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # <-- Это поле
    code = Column(String(10), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)

    # Добавьте эти свойства, если нужно
    @property
    def name_en(self):
        return self.name

    @property
    def name_uz(self):
        return self.name

    @property
    def name_ru(self):
        return self.name