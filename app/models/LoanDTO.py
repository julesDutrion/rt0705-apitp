from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .BaseDTO import BaseDTO
from .LoanStatus import LoanStatus


@dataclass
class LoanDTO(BaseDTO):
    idLoan: int
    idUser: int
    idPhysicalSupport: int
    startDate: datetime
    expectedReturnDate: datetime
    actualReturnDate: datetime | None = None

    ID_FIELDS = frozenset({"idLoan"})

    def __post_init__(self) -> None:
        self.startDate = self._asUTC(self.startDate)
        self.expectedReturnDate = self._asUTC(self.expectedReturnDate)
        if self.actualReturnDate is not None:
            self.actualReturnDate = self._asUTC(self.actualReturnDate)

    @classmethod
    def fromDict(cls, data: Dict[str, Any]) -> "LoanDTO":
        return cls(
            idLoan=data["idLoan"],
            idUser=data["idUser"],
            idPhysicalSupport=data["idPhysicalSupport"],
            startDate=cls._parseDateTime(data["startDate"]),
            expectedReturnDate=cls._parseDateTime(data["expectedReturnDate"]),
            actualReturnDate=(
                cls._parseDateTime(data["actualReturnDate"])
                if data.get("actualReturnDate") is not None
                else None
            ),
        )

    def getStatus(self, now: Optional[datetime] = None) -> LoanStatus:
        if self.actualReturnDate is not None:
            return LoanStatus.RETURNED
        currentTime = self._asUTC(now or datetime.now(timezone.utc))
        if self.expectedReturnDate < currentTime:
            return LoanStatus.OVERDUE
        return LoanStatus.IN_PROGRESS

    def toPublicDict(self) -> Dict[str, Any]:
        data = self.toDict()
        status = self.getStatus()
        data["status"] = status.code
        data["statusLabel"] = status.label
        return data

    @staticmethod
    def _parseDateTime(value: Any) -> datetime:
        if isinstance(value, str):
            value = datetime.fromisoformat(value)
        if not isinstance(value, datetime):
            raise TypeError("Loan dates must be datetime values.")
        return LoanDTO._asUTC(value)

    @staticmethod
    def _asUTC(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
