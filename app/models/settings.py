from sqlalchemy import Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class AppSettings(Base):
    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    auto_change_background: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    allow_registration: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
